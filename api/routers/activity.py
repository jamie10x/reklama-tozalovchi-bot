from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_public_db, require_any_role
from api.schemas.activity import (
    CaptureSettingsResponse,
    CaptureSettingsUpdateRequest,
    ObservedMessageListResponse,
    ObservedMessageResponse,
)
from app.database.repositories.activity import ActivityRepository, CAPTURE_MODES
from app.database.models import Chat
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


async def _get_known_group(public_session: AsyncSession, chat_id: int) -> Chat:
    result = await public_session.execute(select(Chat).where(Chat.telegram_chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if chat is None or chat.removed_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return chat


def _message_export_row(message) -> dict:
    return {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "sender_id": message.sender_id,
        "sender_username": message.sender_username,
        "sender_first_name": message.sender_first_name,
        "sender_last_name": message.sender_last_name,
        "message_type": message.message_type,
        "text": message.text if message.text_stored else None,
        "text_stored": message.text_stored,
        "has_text": message.has_text,
        "is_edited": message.is_edited,
        "is_forwarded": message.is_forwarded,
        "reply_to_message_id": message.reply_to_message_id,
        "detection_status": message.detection_status,
        "risk_score": message.risk_score,
        "ad_score": message.ad_score,
        "security_score": message.security_score,
        "ai_score": message.ai_score,
        "detection_result": message.detection_result,
        "message_date": message.message_date.isoformat() if message.message_date else None,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }


@router.get("/messages")
async def list_messages(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    chat_id: int | None = None,
    sender_id: int | None = None,
    flagged_only: bool = False,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    repo = ActivityRepository(session)
    messages = await repo.list_messages(
        limit=limit,
        offset=offset,
        chat_id=chat_id,
        sender_id=sender_id,
        flagged_only=flagged_only,
    )
    total = await repo.count_messages(chat_id=chat_id, sender_id=sender_id, flagged_only=flagged_only)
    return ObservedMessageListResponse(items=[ObservedMessageResponse.model_validate(m) for m in messages], total=total)


@router.get("/live")
async def live_messages(
    limit: int = Query(50, ge=1, le=100),
    chat_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    repo = ActivityRepository(session)
    messages = await repo.list_messages(
        limit=limit,
        chat_id=chat_id,
        flagged_only=True,
    )
    total = await repo.count_messages(chat_id=chat_id, flagged_only=True)
    return ObservedMessageListResponse(items=[ObservedMessageResponse.model_validate(m) for m in messages], total=total)


@router.get("/groups/{chat_id}/settings")
async def get_group_capture_settings(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    await _get_known_group(public_session, chat_id)
    repo = ActivityRepository(session)
    settings = await repo.get_or_create_settings(chat_id)
    return CaptureSettingsResponse.model_validate(settings)


@router.patch("/groups/{chat_id}/settings")
async def update_group_capture_settings(
    chat_id: int,
    body: CaptureSettingsUpdateRequest,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("responder")),
):
    await _get_known_group(public_session, chat_id)
    if body.capture_mode is not None and body.capture_mode not in CAPTURE_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported capture mode",
        )
    repo = ActivityRepository(session)
    settings = await repo.update_settings(
        chat_id=chat_id,
        enabled=body.enabled,
        capture_mode=body.capture_mode,
        metadata_retention_days=body.metadata_retention_days,
        flagged_retention_days=body.flagged_retention_days,
        updated_by_officer_id=officer.telegram_id,
    )
    return CaptureSettingsResponse.model_validate(settings)


@router.get("/groups/{chat_id}/export")
async def export_group_messages(
    chat_id: int,
    limit: int = Query(200, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("analyst", "responder")),
):
    chat = await _get_known_group(public_session, chat_id)
    repo = ActivityRepository(session)
    messages = await repo.list_messages(limit=limit, chat_id=chat_id)
    payload = {
        "chat_id": chat_id,
        "title": chat.title,
        "limit": limit,
        "count": len(messages),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": officer.telegram_id,
        "source": "observed_messages_database",
        "telegram_history_note": (
            "Telegram Bot API cannot fetch old chat history. This export contains only messages "
            "the bot already observed and stored according to the capture policy."
        ),
        "messages": [_message_export_row(message) for message in messages],
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    filename = f"observed-messages-{chat_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/groups/{chat_id}/retention")
async def get_group_retention(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    await _get_known_group(public_session, chat_id)
    repo = ActivityRepository(session)
    return await repo.retention_stats(chat_id)
