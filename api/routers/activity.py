from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.activity import (
    CaptureSettingsResponse,
    CaptureSettingsUpdateRequest,
    ObservedMessageListResponse,
    ObservedMessageResponse,
)
from app.database.repositories.activity import ActivityRepository, CAPTURE_MODES
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


@router.get("/messages")
async def list_messages(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    chat_id: int | None = None,
    sender_id: int | None = None,
    flagged_only: bool = False,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ActivityRepository(session)
    messages = await repo.list_messages(
        limit=limit,
        offset=offset,
        chat_id=chat_id,
        sender_id=sender_id,
        flagged_only=flagged_only,
    )
    return ObservedMessageListResponse(
        items=[ObservedMessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.get("/live")
async def live_messages(
    limit: int = Query(50, ge=1, le=100),
    chat_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ActivityRepository(session)
    messages = await repo.list_messages(
        limit=limit,
        chat_id=chat_id,
        flagged_only=True,
    )
    return ObservedMessageListResponse(
        items=[ObservedMessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.get("/groups/{chat_id}/settings")
async def get_group_capture_settings(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ActivityRepository(session)
    settings = await repo.get_or_create_settings(chat_id)
    return CaptureSettingsResponse.model_validate(settings)


@router.patch("/groups/{chat_id}/settings")
async def update_group_capture_settings(
    chat_id: int,
    body: CaptureSettingsUpdateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
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
        updated_by_officer_id=officer.telegram_id,
    )
    return CaptureSettingsResponse.model_validate(settings)
