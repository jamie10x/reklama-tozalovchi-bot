from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import SecurityEvent


class SecurityEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        chat_id: int,
        event_type: str,
        severity: str,
        score: int,
        message_id: int | None = None,
        sender_id: int | None = None,
        confidence: float | None = None,
        title: str | None = None,
        message_excerpt: str | None = None,
        detection_reasons: dict | None = None,
        detected_indicators: dict | None = None,
        ad_score: int | None = None,
        security_score: int | None = None,
        expires_at: datetime | None = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            event_type=event_type,
            severity=severity,
            score=score,
            confidence=confidence,
            title=title,
            message_excerpt=message_excerpt,
            detection_reasons=detection_reasons,
            detected_indicators=detected_indicators,
            ad_score=ad_score,
            security_score=security_score,
            expires_at=expires_at,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> SecurityEvent | None:
        stmt = select(SecurityEvent).where(SecurityEvent.id == event_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        severity: str | None = None,
        chat_id: int | None = None,
        event_type: str | None = None,
    ) -> list[SecurityEvent]:
        conditions = []
        if status is not None:
            conditions.append(SecurityEvent.status == status)
        if severity is not None:
            conditions.append(SecurityEvent.severity == severity)
        if chat_id is not None:
            conditions.append(SecurityEvent.chat_id == chat_id)
        if event_type is not None:
            conditions.append(SecurityEvent.event_type == event_type)
        stmt = (
            select(SecurityEvent)
            .where(and_(*conditions) if conditions else True)
            .order_by(SecurityEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, event_id: uuid.UUID, status: str, officer_id: int | None = None
    ) -> SecurityEvent | None:
        values: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if officer_id is not None:
            values["assigned_officer_id"] = officer_id
        stmt = update(SecurityEvent).where(SecurityEvent.id == event_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(event_id)

    async def count_by_status(self, status: str) -> int:
        stmt = select(SecurityEvent).where(SecurityEvent.status == status)
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def count_critical_open(self) -> int:
        stmt = select(SecurityEvent).where(
            SecurityEvent.status == "open",
            SecurityEvent.severity.in_(["critical", "high"]),
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = select(SecurityEvent).where(SecurityEvent.expires_at <= now)
        result = await self._session.execute(stmt)
        events = list(result.scalars().all())
        total = len(events)
        for event in events:
            await self._session.delete(event)
        await self._session.flush()
        return total
