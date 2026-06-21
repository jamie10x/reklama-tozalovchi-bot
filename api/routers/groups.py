from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.groups import GroupListResponse, GroupResponse, GroupUpdateRequest
from app.database.models import Chat
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.get("")
async def list_groups(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
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


@router.get("/{chat_id}")
async def get_group(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
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
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
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
