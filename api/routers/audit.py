from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from app.database.repositories.officers import OfficerRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action_type: str | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = OfficerRepository(session)
    logs = await repo.list_audit_logs(
        limit=limit,
        offset=offset,
        action_type=action_type,
    )
    return {
        "items": [
            {
                "id": str(log.id),
                "officer_id": str(log.officer_id) if log.officer_id else None,
                "action_type": log.action_type,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "total": len(logs),
    }
