from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import SecurityObservationOutbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        update_id: int,
        chat_id: int,
        message_id: int,
        sender_id: int | None = None,
        text_hash: str | None = None,
        text: str | None = None,
        entities: dict | None = None,
        detection_result: dict | None = None,
        urls: dict | None = None,
        telegram_entities: dict | None = None,
        expires_at: datetime | None = None,
    ) -> SecurityObservationOutbox:
        entry = SecurityObservationOutbox(
            update_id=update_id,
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            text_hash=text_hash,
            text=text,
            entities=entities,
            detection_result=detection_result,
            urls=urls,
            telegram_entities=telegram_entities,
            expires_at=expires_at,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def exists_by_update_id(self, update_id: int) -> bool:
        stmt = select(SecurityObservationOutbox).where(
            SecurityObservationOutbox.update_id == update_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_message(self, chat_id: int, message_id: int) -> bool:
        stmt = select(SecurityObservationOutbox).where(
            SecurityObservationOutbox.chat_id == chat_id,
            SecurityObservationOutbox.message_id == message_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def claim_next(
        self, worker_id: str, batch_size: int = 5
    ) -> list[SecurityObservationOutbox]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(SecurityObservationOutbox)
            .where(
                SecurityObservationOutbox.status == "pending",
                SecurityObservationOutbox.retry_count < SecurityObservationOutbox.max_retries,
            )
            .order_by(SecurityObservationOutbox.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        entries = list(result.scalars().all())
        for entry in entries:
            entry.status = "claimed"
            entry.locked_by = worker_id
            entry.locked_at = now
        await self._session.flush()
        return entries

    async def mark_completed(self, entry_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(SecurityObservationOutbox)
            .where(SecurityObservationOutbox.id == entry_id)
            .values(status="completed", processed_at=now)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_failed(self, entry_id: uuid.UUID) -> None:
        stmt = (
            update(SecurityObservationOutbox)
            .where(SecurityObservationOutbox.id == entry_id)
            .values(
                status="failed",
                retry_count=SecurityObservationOutbox.retry_count + 1,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_expired(self, entry_id: uuid.UUID) -> None:
        stmt = (
            update(SecurityObservationOutbox)
            .where(SecurityObservationOutbox.id == entry_id)
            .values(status="expired")
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_pending_count(self) -> int:
        stmt = select(SecurityObservationOutbox).where(
            SecurityObservationOutbox.status == "pending"
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = select(SecurityObservationOutbox).where(SecurityObservationOutbox.expires_at <= now)
        result = await self._session.execute(stmt)
        entries = list(result.scalars().all())
        total = len(entries)
        for entry in entries:
            await self._session.delete(entry)
        await self._session.flush()
        return total
