from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import EventIndicator, Indicator


class IndicatorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        indicator_type: str,
        indicator_value: str,
        chat_id: int | None = None,
        created_by_officer_id: int | None = None,
    ) -> Indicator:
        stmt = select(Indicator).where(
            Indicator.indicator_type == indicator_type,
            Indicator.indicator_value == indicator_value,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if existing is not None:
            existing.last_seen_at = now
            existing.seen_count = Indicator.seen_count + 1
            if chat_id is not None:
                chat_ids = existing.chat_ids or []
                if isinstance(chat_ids, list) and chat_id not in chat_ids:
                    chat_ids.append(chat_id)
                    existing.chat_ids = chat_ids
            await self._session.flush()
            return existing
        indicator = Indicator(
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            first_seen_at=now,
            last_seen_at=now,
            chat_ids=[chat_id] if chat_id is not None else None,
            created_by_officer_id=created_by_officer_id,
        )
        self._session.add(indicator)
        await self._session.flush()
        return indicator

    async def get_by_id(self, indicator_id: uuid.UUID) -> Indicator | None:
        stmt = select(Indicator).where(Indicator.id == indicator_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_type_and_value(
        self, indicator_type: str, indicator_value: str
    ) -> Indicator | None:
        stmt = select(Indicator).where(
            Indicator.indicator_type == indicator_type,
            Indicator.indicator_value == indicator_value,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        indicator_type: str | None = None,
        status: str | None = None,
    ) -> list[Indicator]:
        conditions = []
        if indicator_type is not None:
            conditions.append(Indicator.indicator_type == indicator_type)
        if status is not None:
            conditions.append(Indicator.status == status)
        stmt = (
            select(Indicator)
            .where(and_(*conditions) if conditions else True)
            .order_by(Indicator.last_seen_at.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, indicator_id: uuid.UUID, status: str) -> Indicator | None:
        stmt = update(Indicator).where(Indicator.id == indicator_id).values(status=status)
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(indicator_id)

    async def link_to_event(self, event_id: uuid.UUID, indicator_id: uuid.UUID) -> EventIndicator:
        link = EventIndicator(
            event_id=event_id,
            indicator_id=indicator_id,
            extracted_at=datetime.now(timezone.utc),
        )
        self._session.add(link)
        await self._session.flush()
        return link

    async def get_indicators_for_event(self, event_id: uuid.UUID) -> list[Indicator]:
        stmt = (
            select(Indicator)
            .join(EventIndicator, Indicator.id == EventIndicator.indicator_id)
            .where(EventIndicator.event_id == event_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
