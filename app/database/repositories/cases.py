from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import Case, CaseEvent, CaseNote


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        title: str,
        severity: str = "medium",
        description: str | None = None,
        assigned_officer_id: int | None = None,
    ) -> Case:
        case = Case(
            title=title,
            severity=severity,
            description=description,
            assigned_officer_id=assigned_officer_id,
        )
        self._session.add(case)
        await self._session.flush()
        return case

    async def get_by_id(self, case_id: uuid.UUID) -> Case | None:
        stmt = select(Case).where(Case.id == case_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[Case]:
        conditions = []
        if status is not None:
            conditions.append(Case.status == status)
        if severity is not None:
            conditions.append(Case.severity == severity)
        stmt = (
            select(Case)
            .where(and_(*conditions) if conditions else True)
            .order_by(Case.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, case_id: uuid.UUID, status: str, resolution: str | None = None
    ) -> Case | None:
        values: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if status in ("resolved", "closed") and resolution is not None:
            values["resolution"] = resolution
            values["resolved_at"] = datetime.now(timezone.utc)
        stmt = update(Case).where(Case.id == case_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(case_id)

    async def assign(self, case_id: uuid.UUID, officer_id: int) -> Case | None:
        stmt = (
            update(Case)
            .where(Case.id == case_id)
            .values(assigned_officer_id=officer_id, updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(case_id)

    async def link_event(
        self, case_id: uuid.UUID, event_id: uuid.UUID, officer_id: int | None = None
    ) -> CaseEvent:
        link = CaseEvent(
            case_id=case_id,
            event_id=event_id,
            added_by_officer_id=officer_id,
            added_at=datetime.now(timezone.utc),
        )
        self._session.add(link)
        await self._session.flush()
        return link

    async def unlink_event(self, case_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        stmt = select(CaseEvent).where(
            CaseEvent.case_id == case_id,
            CaseEvent.event_id == event_id,
        )
        result = await self._session.execute(stmt)
        link = result.scalar_one_or_none()
        if link is not None:
            await self._session.delete(link)
            await self._session.flush()
            return True
        return False

    async def add_note(self, case_id: uuid.UUID, officer_id: int, content: str) -> CaseNote:
        note = CaseNote(
            case_id=case_id,
            officer_id=officer_id,
            content=content,
        )
        self._session.add(note)
        await self._session.flush()
        return note

    async def get_notes(self, case_id: uuid.UUID) -> list[CaseNote]:
        stmt = (
            select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_events(self, case_id: uuid.UUID) -> list[CaseEvent]:
        stmt = select(CaseEvent).where(CaseEvent.case_id == case_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
