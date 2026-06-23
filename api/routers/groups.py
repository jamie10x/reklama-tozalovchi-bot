from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_public_db, require_any_role
from api.schemas.groups import GroupHealthListResponse, GroupHealthResponse, GroupListResponse, GroupResponse, GroupUpdateRequest
from app.database.models import Chat
from app.database.secadmin_models import EnforcementAction, GroupCaptureSetting, ObservedMessage, Officer

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.get("")
async def list_groups(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    stmt = (
        select(Chat)
        .where(Chat.enabled, Chat.removed_at.is_(None))
        .order_by(Chat.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    chats = list(result.scalars().all())
    return GroupListResponse(
        items=[GroupResponse.model_validate(c) for c in chats],
        total=len(chats),
    )


@router.get("/health", response_model=GroupHealthListResponse)
async def list_group_health(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    public_session: AsyncSession = Depends(get_public_db),
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    result = await public_session.execute(
        select(Chat)
        .where(Chat.enabled, Chat.removed_at.is_(None))
        .order_by(Chat.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    chats = list(result.scalars().all())
    items: list[GroupHealthResponse] = []
    for chat in chats:
        settings_result = await session.execute(
            select(GroupCaptureSetting).where(GroupCaptureSetting.chat_id == chat.telegram_chat_id)
        )
        settings = settings_result.scalar_one_or_none()
        observed_result = await session.execute(
            select(func.count(), func.max(ObservedMessage.created_at)).where(
                ObservedMessage.chat_id == chat.telegram_chat_id
            )
        )
        observed_count, last_observed_at = observed_result.one()
        flagged_result = await session.execute(
            select(func.count()).where(
                ObservedMessage.chat_id == chat.telegram_chat_id,
                ObservedMessage.detection_status != "clean",
            )
        )
        text_result = await session.execute(
            select(func.count()).where(
                ObservedMessage.chat_id == chat.telegram_chat_id,
                ObservedMessage.text_stored.is_(True),
            )
        )
        pending_result = await session.execute(
            select(func.count()).where(
                EnforcementAction.target_chat_id == chat.telegram_chat_id,
                EnforcementAction.status.in_(("pending", "claimed")),
            )
        )
        last_command_result = await session.execute(
            select(EnforcementAction)
            .where(EnforcementAction.target_chat_id == chat.telegram_chat_id)
            .order_by(EnforcementAction.created_at.desc())
            .limit(1)
        )
        last_command = last_command_result.scalar_one_or_none()
        items.append(
            GroupHealthResponse(
                telegram_chat_id=chat.telegram_chat_id,
                title=chat.title,
                username=chat.username,
                enabled=chat.enabled,
                mode=chat.mode,
                bot_can_delete_messages=chat.bot_can_delete_messages,
                capture_enabled=settings.enabled if settings else None,
                capture_mode=settings.capture_mode if settings else None,
                metadata_retention_days=settings.metadata_retention_days if settings else None,
                flagged_retention_days=settings.flagged_retention_days if settings else None,
                observed_messages=int(observed_count or 0),
                flagged_messages=int(flagged_result.scalar_one() or 0),
                stored_text_messages=int(text_result.scalar_one() or 0),
                pending_commands=int(pending_result.scalar_one() or 0),
                last_observed_at=last_observed_at,
                last_command_at=last_command.created_at if last_command else None,
                last_command_status=last_command.status if last_command else None,
                last_command_type=last_command.action_type if last_command else None,
            )
        )
    return GroupHealthListResponse(items=items, total=len(items))


@router.get("/{chat_id}")
async def get_group(
    chat_id: int,
    session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
):
    stmt = select(Chat).where(Chat.telegram_chat_id == chat_id)
    result = await session.execute(stmt)
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return GroupResponse.model_validate(chat)


@router.patch("/{chat_id}")
async def update_group(
    chat_id: int,
    body: GroupUpdateRequest,
    session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("responder")),
):
    stmt = select(Chat).where(Chat.telegram_chat_id == chat_id)
    result = await session.execute(stmt)
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if body.enabled is not None:
        chat.enabled = body.enabled
    if body.mode is not None:
        chat.mode = body.mode
    await session.flush()
    return GroupResponse.model_validate(chat)
