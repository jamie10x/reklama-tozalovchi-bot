from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import (
    MemberRiskSignal,
    ObservedUser,
    UserChatProfile,
    UserObservedName,
)


class ObservedUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_bot: bool = False,
        language_code: str | None = None,
        is_premium: bool = False,
    ) -> ObservedUser:
        stmt = select(ObservedUser).where(ObservedUser.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if existing is not None:
            changed = False
            if username is not None and username != existing.current_username:
                await self._record_name_change(
                    existing.telegram_id,
                    existing.current_username,
                    existing.current_first_name,
                    existing.current_last_name,
                    now,
                )
                existing.current_username = username
                changed = True
            if first_name is not None and first_name != existing.current_first_name:
                if not changed:
                    await self._record_name_change(
                        existing.telegram_id,
                        existing.current_username,
                        existing.current_first_name,
                        existing.current_last_name,
                        now,
                    )
                existing.current_first_name = first_name
                changed = True
            if last_name is not None and last_name != existing.current_last_name:
                if not changed:
                    await self._record_name_change(
                        existing.telegram_id,
                        existing.current_username,
                        existing.current_first_name,
                        existing.current_last_name,
                        now,
                    )
                existing.current_last_name = last_name
                changed = True
            if language_code is not None:
                existing.language_code = language_code
            if is_premium:
                existing.is_premium = is_premium
            existing.last_seen_at = now
            existing.updated_at = now
            await self._session.flush()
            return existing

        user = ObservedUser(
            telegram_id=telegram_id,
            current_username=username,
            current_first_name=first_name,
            current_last_name=last_name,
            is_bot=is_bot,
            language_code=language_code,
            is_premium=is_premium,
            first_seen_at=now,
            last_seen_at=now,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def _record_name_change(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        now: datetime,
    ) -> None:
        observed = UserObservedName(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            last_seen_at=now,
        )
        self._session.add(observed)

    async def get_by_telegram_id(self, telegram_id: int) -> ObservedUser | None:
        stmt = select(ObservedUser).where(ObservedUser.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_risk_score(
        self, telegram_id: int, score: int, signals: dict | None = None
    ) -> None:
        values: dict = {"risk_score": score, "updated_at": datetime.now(timezone.utc)}
        if signals is not None:
            values["risk_signals"] = signals
        stmt = update(ObservedUser).where(ObservedUser.telegram_id == telegram_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()

    async def upsert_profile(
        self,
        user_id: int,
        chat_id: int,
        membership_status: str | None = None,
        is_admin: bool = False,
    ) -> UserChatProfile:
        stmt = select(UserChatProfile).where(
            UserChatProfile.user_id == user_id,
            UserChatProfile.chat_id == chat_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if existing is not None:
            if membership_status is not None:
                existing.membership_status = membership_status
            existing.is_admin = is_admin
            existing.updated_at = now
            await self._session.flush()
            return existing

        profile = UserChatProfile(
            user_id=user_id,
            chat_id=chat_id,
            membership_status=membership_status,
            is_admin=is_admin,
            joined_at=now,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def add_risk_signal(
        self,
        user_id: int,
        chat_id: int,
        signal_type: str,
        signal_value: str | None = None,
    ) -> MemberRiskSignal:
        signal = MemberRiskSignal(
            user_id=user_id,
            chat_id=chat_id,
            signal_type=signal_type,
            signal_value=signal_value,
            detected_at=datetime.now(timezone.utc),
        )
        self._session.add(signal)
        await self._session.flush()
        return signal

    async def increment_message_count(self, user_id: int, chat_id: int) -> None:
        stmt = select(UserChatProfile).where(
            UserChatProfile.user_id == user_id,
            UserChatProfile.chat_id == chat_id,
        )
        result = await self._session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is not None:
            profile.message_count = UserChatProfile.message_count + 1
            profile.last_message_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def search(self, query: str, limit: int = 20) -> list[ObservedUser]:
        stmt = (
            select(ObservedUser)
            .where(
                ObservedUser.current_username.ilike(f"%{query}%")
                | ObservedUser.current_first_name.ilike(f"%{query}%")
                | ObservedUser.current_last_name.ilike(f"%{query}%")
                | ObservedUser.telegram_id.cast(str).like(f"%{query}%")
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
