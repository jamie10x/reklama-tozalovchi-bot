from __future__ import annotations

from fastapi import Depends, HTTPException, status

from api.deps import get_current_officer
from app.database.secadmin_models import Officer


async def require_super_admin(officer: Officer = Depends(get_current_officer)) -> Officer:
    if officer.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return officer


async def require_analyst(officer: Officer = Depends(get_current_officer)) -> Officer:
    if officer.role not in ("super_admin", "analyst", "responder"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required",
        )
    return officer
