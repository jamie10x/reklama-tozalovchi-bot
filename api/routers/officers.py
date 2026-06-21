from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.deps import require_super_admin
from api.deps import get_db
from api.schemas.officers import (
    OfficerCreateRequest,
    OfficerListResponse,
    OfficerResponse,
    OfficerUpdateRequest,
)
from app.database.repositories.officers import OfficerRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/officers", tags=["officers"])


@router.get("")
async def list_officers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_super_admin),
):
    stmt = select(Officer).order_by(Officer.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    officers = list(result.scalars().all())
    return OfficerListResponse(
        items=[OfficerResponse.model_validate(o) for o in officers],
        total=len(officers),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_officer(
    body: OfficerCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_super_admin),
):
    repo = OfficerRepository(session)
    existing = await repo.get_by_telegram_id(body.telegram_id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Officer already exists")
    new_officer = await repo.create(
        telegram_id=body.telegram_id,
        role=body.role,
        display_name=body.display_name,
    )
    return OfficerResponse.model_validate(new_officer)


@router.patch("/{officer_id}")
async def update_officer(
    officer_id: str,
    body: OfficerUpdateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_super_admin),
):
    repo = OfficerRepository(session)
    if body.role is not None:
        await repo.update_role(uuid.UUID(officer_id), body.role)
    if body.is_active is not None and not body.is_active:
        await repo.deactivate(uuid.UUID(officer_id))
    if body.display_name is not None:
        existing = await repo.get_by_id(uuid.UUID(officer_id))
        if existing is not None:
            existing.display_name = body.display_name
            await session.flush()
    updated = await repo.get_by_id(uuid.UUID(officer_id))
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")
    return OfficerResponse.model_validate(updated)


@router.delete("/{officer_id}")
async def deactivate_officer(
    officer_id: str,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_super_admin),
):
    repo = OfficerRepository(session)
    result = await repo.deactivate(uuid.UUID(officer_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")
    return {"ok": True}
