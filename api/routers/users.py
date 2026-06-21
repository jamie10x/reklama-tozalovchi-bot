from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.users import UserListResponse, UserResponse
from app.database.repositories.users import ObservedUserRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("")
async def list_users(
    query: str = Query("", min_length=0, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ObservedUserRepository(session)
    if query:
        users = await repo.search(query, limit=limit)
    else:
        from sqlalchemy import select

        from app.database.secadmin_models import ObservedUser

        stmt = (
            select(ObservedUser).order_by(ObservedUser.last_seen_at.desc().nullslast()).limit(limit)
        )
        result = await session.execute(stmt)
        users = list(result.scalars().all())
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=len(users),
    )


@router.get("/{telegram_id}")
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ObservedUserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await repo.upsert_profile(user_id=telegram_id, chat_id=0)
    from sqlalchemy import select

    from app.database.secadmin_models import UserChatProfile

    stmt = select(UserChatProfile).where(UserChatProfile.user_id == telegram_id)
    result = await session.execute(stmt)
    chat_profiles = list(result.scalars().all())

    return {
        "user": UserResponse.model_validate(user),
        "chat_profiles": [
            {
                "chat_id": p.chat_id,
                "membership_status": p.membership_status,
                "is_admin": p.is_admin,
                "message_count": p.message_count,
                "link_message_count": p.link_message_count,
                "deleted_message_count": p.deleted_message_count,
                "security_event_count": p.security_event_count,
                "last_message_at": p.last_message_at,
            }
            for p in chat_profiles
            if p.chat_id != 0
        ],
    }
