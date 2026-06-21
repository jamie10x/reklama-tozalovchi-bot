from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import Officer, OfficerAuditLog, OfficerSession


class OfficerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        telegram_id: int,
        role: str = "analyst",
        display_name: str | None = None,
    ) -> Officer:
        officer = Officer(
            telegram_id=telegram_id,
            role=role,
            display_name=display_name,
        )
        self._session.add(officer)
        await self._session.flush()
        return officer

    async def get_by_id(self, officer_id: uuid.UUID) -> Officer | None:
        stmt = select(Officer).where(Officer.id == officer_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Officer | None:
        stmt = select(Officer).where(Officer.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Officer]:
        stmt = select(Officer).where(Officer.is_active == True).order_by(Officer.display_name)  # noqa: E712
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_role(self, officer_id: uuid.UUID, role: str) -> Officer | None:
        stmt = (
            update(Officer)
            .where(Officer.id == officer_id)
            .values(role=role, updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(officer_id)

    async def deactivate(self, officer_id: uuid.UUID) -> Officer | None:
        stmt = (
            update(Officer)
            .where(Officer.id == officer_id)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(officer_id)

    async def record_login(self, telegram_id: int) -> None:
        stmt = (
            update(Officer)
            .where(Officer.telegram_id == telegram_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def create_session(
        self,
        officer_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OfficerSession:
        session = OfficerSession(
            officer_id=officer_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        stmt = (
            update(OfficerSession)
            .where(OfficerSession.id == session_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_session_by_token_hash(self, token_hash: str) -> OfficerSession | None:
        stmt = select(OfficerSession).where(
            OfficerSession.token_hash == token_hash,
            OfficerSession.revoked_at.is_(None),
            OfficerSession.expires_at > datetime.now(timezone.utc),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_audit_log(
        self,
        officer_id: uuid.UUID | None,
        action_type: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> OfficerAuditLog:
        log = OfficerAuditLog(
            officer_id=officer_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        officer_id: uuid.UUID | None = None,
        action_type: str | None = None,
    ) -> list[OfficerAuditLog]:
        conditions = []
        if officer_id is not None:
            conditions.append(OfficerAuditLog.officer_id == officer_id)
        if action_type is not None:
            conditions.append(OfficerAuditLog.action_type == action_type)
        stmt = (
            select(OfficerAuditLog)
            .where(*conditions)
            .order_by(OfficerAuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
