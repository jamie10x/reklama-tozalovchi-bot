from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import EnforcementAction


class EnforcementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        action_type: str,
        target_chat_id: int | None = None,
        target_message_id: int | None = None,
        target_user_id: int | None = None,
        target_indicator_id: uuid.UUID | None = None,
        requested_by_officer_id: int | None = None,
    ) -> EnforcementAction:
        action = EnforcementAction(
            action_type=action_type,
            target_chat_id=target_chat_id,
            target_message_id=target_message_id,
            target_user_id=target_user_id,
            target_indicator_id=target_indicator_id,
            requested_by_officer_id=requested_by_officer_id,
        )
        self._session.add(action)
        await self._session.flush()
        return action

    async def get_by_id(self, action_id: uuid.UUID) -> EnforcementAction | None:
        stmt = select(EnforcementAction).where(EnforcementAction.id == action_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def claim_next(self, worker_id: str, batch_size: int = 5) -> list[EnforcementAction]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(EnforcementAction)
            .where(EnforcementAction.status == "pending")
            .order_by(EnforcementAction.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        actions = list(result.scalars().all())
        for action in actions:
            action.status = "claimed"
            action.locked_by = worker_id
            action.locked_at = now
        await self._session.flush()
        return actions

    async def mark_completed(self, action_id: uuid.UUID, result: dict | None = None) -> None:
        values: dict = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc),
        }
        if result is not None:
            values["result"] = result
        stmt = update(EnforcementAction).where(EnforcementAction.id == action_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_failed(self, action_id: uuid.UUID, result: dict | None = None) -> None:
        values: dict = {"status": "failed"}
        if result is not None:
            values["result"] = result
        stmt = update(EnforcementAction).where(EnforcementAction.id == action_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        action_type: str | None = None,
        chat_id: int | None = None,
    ) -> list[EnforcementAction]:
        conditions = []
        if status is not None:
            conditions.append(EnforcementAction.status == status)
        if action_type is not None:
            conditions.append(EnforcementAction.action_type == action_type)
        if chat_id is not None:
            conditions.append(EnforcementAction.target_chat_id == chat_id)
        stmt = (
            select(EnforcementAction)
            .where(and_(*conditions) if conditions else True)
            .order_by(EnforcementAction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
