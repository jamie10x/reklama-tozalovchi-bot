from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.secadmin_models import Officer, OfficerSession
from app.database.session import get_secadmin_sessionmaker, get_sessionmaker

logger = get_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    sm = get_secadmin_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_current_officer(
    request: Request,
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_db),
) -> Officer:
    req_id = getattr(request.state, "req_id", None)

    if authorization is None:
        logger.warning("Missing auth header", req_id=req_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        logger.warning("Invalid auth scheme", req_id=req_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
        )
    token_hash = _hash_token(token)
    from sqlalchemy import select

    stmt = select(OfficerSession).where(
        OfficerSession.token_hash == token_hash,
        OfficerSession.revoked_at.is_(None),
        OfficerSession.expires_at > datetime.now(timezone.utc),
    )
    result = await session.execute(stmt)
    db_session = result.scalar_one_or_none()
    if db_session is None:
        logger.warning("Invalid session token", req_id=req_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    stmt = select(Officer).where(Officer.id == db_session.officer_id, Officer.is_active)
    result = await session.execute(stmt)
    officer = result.scalar_one_or_none()
    if officer is None:
        logger.warning("Inactive officer", req_id=req_id, officer_id=str(db_session.officer_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Officer not found or inactive",
        )
    return officer


def require_any_role(*roles: str):
    allowed = set(roles)

    async def _check(officer: Officer = Depends(get_current_officer)) -> Officer:
        if officer.role == "super_admin" or officer.role in allowed:
            return officer
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires one of roles: {', '.join(sorted(allowed))}",
        )

    return _check


async def require_role(role: str) -> type:
    async def _check(officer: Officer = Depends(get_current_officer)) -> Officer:
        if officer.role == "super_admin":
            return officer
        if officer.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role}",
            )
        return officer

    return _check
