from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import load_api_config
from api.deps import get_current_officer, get_db
from app.core.logging import get_logger
from app.database.secadmin_models import Officer, OfficerSession

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    telegram_id: int
    token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    officer: dict


class MeResponse(BaseModel):
    id: str
    telegram_id: int
    role: str
    display_name: str | None
    is_active: bool


@router.post("/login")
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    config = load_api_config()

    if body.token != config.secret_key:
        req_id = getattr(request.state, "req_id", None)
        logger.warning("Login failed: bad token", telegram_id=body.telegram_id, req_id=req_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    stmt = select(Officer).where(
        Officer.telegram_id == body.telegram_id,
        Officer.is_active,
    )
    result = await session.execute(stmt)
    officer = result.scalar_one_or_none()
    if officer is None:
        req_id = getattr(request.state, "req_id", None)
        logger.warning(
            "Login failed: officer not found",
            telegram_id=body.telegram_id,
            req_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=config.session_ttl_hours)

    db_session = OfficerSession(
        officer_id=officer.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(db_session)
    await session.flush()
    await session.commit()

    officer.last_login_at = datetime.now(timezone.utc)
    await session.flush()
    await session.commit()

    logger.info("Login successful", officer_id=str(officer.id), telegram_id=officer.telegram_id)

    return LoginResponse(
        access_token=raw_token,
        officer={
            "id": str(officer.id),
            "telegram_id": officer.telegram_id,
            "role": officer.role,
            "display_name": officer.display_name,
        },
    )


@router.post("/logout")
async def logout(
    authorization: str | None = None,
    officer: Officer = Depends(get_current_officer),
    session: AsyncSession = Depends(get_db),
):
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            from sqlalchemy import select

            stmt = select(OfficerSession).where(OfficerSession.token_hash == token_hash)
            result = await session.execute(stmt)
            db_session = result.scalar_one_or_none()
            if db_session is not None:
                db_session.revoked_at = datetime.now(timezone.utc)
                await session.flush()
                await session.commit()
    logger.info("Logout", officer_id=str(officer.id))
    return {"ok": True}


@router.get("/me")
async def me(
    officer: Officer = Depends(get_current_officer),
):
    return MeResponse(
        id=str(officer.id),
        telegram_id=officer.telegram_id,
        role=officer.role,
        display_name=officer.display_name,
        is_active=officer.is_active,
    )
