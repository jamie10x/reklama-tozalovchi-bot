from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.indicators import (
    IndicatorListResponse,
    IndicatorResponse,
    IndicatorUpdateRequest,
)
from app.database.repositories.indicators import IndicatorRepository
from app.database.repositories.officers import OfficerRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router.get("")
async def list_indicators(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    indicator_type: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = IndicatorRepository(session)
    indicators = await repo.list(
        limit=limit,
        offset=offset,
        indicator_type=indicator_type,
        status=status,
    )
    return IndicatorListResponse(
        items=[IndicatorResponse.model_validate(i) for i in indicators],
        total=len(indicators),
    )


@router.get("/{indicator_id}")
async def get_indicator(
    indicator_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = IndicatorRepository(session)
    indicator = await repo.get_by_id(indicator_id)
    if indicator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")
    return IndicatorResponse.model_validate(indicator)


@router.patch("/{indicator_id}")
async def update_indicator(
    indicator_id: uuid.UUID,
    body: IndicatorUpdateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = IndicatorRepository(session)
    indicator = await repo.update_status(indicator_id, body.status)
    if indicator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")

    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="indicator_status_update",
        resource_type="indicator",
        resource_id=str(indicator_id),
        details={"new_status": body.status},
    )
    return IndicatorResponse.model_validate(indicator)
