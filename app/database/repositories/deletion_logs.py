from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DeletionLog


class DeletionLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        chat_id: uuid.UUID,
        telegram_message_id: int,
        score: int,
        reasons: list[str] | None = None,
        detected_domains: list[str] | None = None,
        detected_telegram_entities: list[str] | None = None,
        message_excerpt: str | None = None,
        sender_user_id: int | None = None,
        sender_chat_id: int | None = None,
        sender_is_bot: bool = False,
        expires_at: datetime | None = None,
    ) -> DeletionLog:
        if expires_at is None:
            expires_at = datetime.now(timezone.utc)
        log = DeletionLog(
            chat_id=chat_id,
            telegram_message_id=telegram_message_id,
            score=score,
            reasons=reasons or [],
            detected_domains=detected_domains or [],
            detected_telegram_entities=detected_telegram_entities or [],
            message_excerpt=message_excerpt,
            sender_user_id=sender_user_id,
            sender_chat_id=sender_chat_id,
            sender_is_bot=sender_is_bot,
            expires_at=expires_at,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_recent(self, chat_id: uuid.UUID, limit: int = 10) -> list[DeletionLog]:
        stmt = (
            select(DeletionLog)
            .where(DeletionLog.chat_id == chat_id)
            .order_by(DeletionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_today(self, chat_id: uuid.UUID) -> int:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(DeletionLog.id)).where(
            DeletionLog.chat_id == chat_id,
            DeletionLog.created_at >= today_start,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_chat_id(self, chat_id: uuid.UUID) -> int:
        stmt = select(func.count(DeletionLog.id)).where(DeletionLog.chat_id == chat_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = select(DeletionLog).where(DeletionLog.expires_at <= now)
        result = await self._session.execute(stmt)
        logs = list(result.scalars().all())
        total = len(logs)
        for log in logs:
            await self._session.delete(log)
        await self._session.flush()
        return total
