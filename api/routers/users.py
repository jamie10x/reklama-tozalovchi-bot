from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.activity import ObservedMessageResponse
from api.schemas.users import UserListResponse, UserResponse
from app.database.repositories.activity import ActivityRepository
from app.database.repositories.users import ObservedUserRepository
from app.database.secadmin_models import (
    MemberRiskSignal,
    ObservedMessage,
    ObservedUser,
    Officer,
    UserChatProfile,
    UserObservedName,
)

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
        stmt = (
            select(ObservedUser).order_by(ObservedUser.last_seen_at.desc().nullslast()).limit(limit)
        )
        result = await session.execute(stmt)
        users = list(result.scalars().all())
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=len(users),
    )


@router.get("/{telegram_id}/intel")
async def get_user_intel(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = ObservedUserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    user_payload = (
        UserResponse.model_validate(user)
        if user is not None
        else {
            "telegram_id": telegram_id,
            "current_username": None,
            "current_first_name": None,
            "current_last_name": None,
            "is_bot": False,
            "language_code": None,
            "risk_score": 0,
            "first_seen_at": None,
            "last_seen_at": None,
        }
    )

    profile_result = await session.execute(
        select(UserChatProfile).where(UserChatProfile.user_id == telegram_id)
    )
    alias_result = await session.execute(
        select(UserObservedName)
        .where(UserObservedName.user_id == telegram_id)
        .order_by(UserObservedName.last_seen_at.desc().nullslast())
        .limit(50)
    )
    signal_result = await session.execute(
        select(MemberRiskSignal)
        .where(MemberRiskSignal.user_id == telegram_id)
        .order_by(MemberRiskSignal.created_at.desc())
        .limit(50)
    )
    activity_repo = ActivityRepository(session)
    messages = await activity_repo.list_messages(
        sender_id=telegram_id,
        flagged_only=False,
        limit=50,
    )
    cross_group_result = await session.execute(
        select(
            ObservedMessage.chat_id,
            func.count().label("message_count"),
            func.sum(cast(ObservedMessage.detection_status != "clean", Integer)).label("flagged_count"),
            func.max(ObservedMessage.created_at).label("last_seen_at"),
        )
        .where(ObservedMessage.sender_id == telegram_id)
        .group_by(ObservedMessage.chat_id)
        .order_by(func.max(ObservedMessage.created_at).desc())
        .limit(20)
    )
    timeline = []
    for message in messages[:25]:
        timeline.append(
            {
                "type": "message",
                "chat_id": message.chat_id,
                "message_id": message.message_id,
                "status": message.detection_status,
                "risk_score": message.risk_score,
                "text": message.text if message.text_stored else None,
                "created_at": message.created_at,
            }
        )
    aliases = list(alias_result.scalars().all())
    signals = list(signal_result.scalars().all())
    profiles = list(profile_result.scalars().all())
    for alias in aliases[:20]:
        timeline.append(
            {
                "type": "alias",
                "username": alias.username,
                "first_name": alias.first_name,
                "last_name": alias.last_name,
                "created_at": alias.last_seen_at or alias.first_seen_at,
            }
        )
    for signal in signals[:20]:
        timeline.append(
            {
                "type": "risk_signal",
                "chat_id": signal.chat_id,
                "signal_type": signal.signal_type,
                "signal_value": signal.signal_value,
                "created_at": signal.detected_at or signal.created_at,
            }
        )
    timeline.sort(
        key=lambda item: item["created_at"].timestamp() if item.get("created_at") else 0,
        reverse=True,
    )

    return {
        "user": user_payload,
        "profiles": [
            {
                "chat_id": p.chat_id,
                "membership_status": p.membership_status,
                "is_admin": p.is_admin,
                "message_count": p.message_count,
                "link_message_count": p.link_message_count,
                "deleted_message_count": p.deleted_message_count,
                "security_event_count": p.security_event_count,
                "confirmed_event_count": p.confirmed_event_count,
                "last_message_at": p.last_message_at,
                "last_security_event_at": p.last_security_event_at,
            }
            for p in profiles
            if p.chat_id != 0
        ],
        "aliases": [
            {
                "username": a.username,
                "first_name": a.first_name,
                "last_name": a.last_name,
                "first_seen_at": a.first_seen_at,
                "last_seen_at": a.last_seen_at,
            }
            for a in aliases
        ],
        "risk_signals": [
            {
                "chat_id": s.chat_id,
                "signal_type": s.signal_type,
                "signal_value": s.signal_value,
                "detected_at": s.detected_at,
                "created_at": s.created_at,
            }
            for s in signals
        ],
        "cross_group_activity": [
            {
                "chat_id": row.chat_id,
                "message_count": int(row.message_count or 0),
                "flagged_count": int(row.flagged_count or 0),
                "last_seen_at": row.last_seen_at,
            }
            for row in cross_group_result
        ],
        "timeline": timeline[:80],
        "messages": [ObservedMessageResponse.model_validate(m) for m in messages],
    }


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
