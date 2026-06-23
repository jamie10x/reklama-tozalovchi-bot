from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.cases import (
    CaseCreateRequest,
    CaseListResponse,
    CaseNoteCreateRequest,
    CaseNoteResponse,
    CaseResponse,
    CaseUpdateRequest,
)
from app.database.repositories.cases import CaseRepository
from app.database.repositories.officers import OfficerRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.get("")
async def list_cases(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    severity: str | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    cases = await repo.list(limit=limit, offset=offset, status=status, severity=severity)
    return CaseListResponse(
        items=[CaseResponse.model_validate(c) for c in cases],
        total=len(cases),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CaseCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    case = await repo.create(
        title=body.title,
        severity=body.severity,
        description=body.description,
        assigned_officer_id=body.assigned_officer_id,
    )
    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="case_created",
        resource_type="case",
        resource_id=str(case.id),
        details={"title": body.title},
    )
    return CaseResponse.model_validate(case)


@router.get("/{case_id}")
async def get_case(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    case = await repo.get_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    notes = await repo.get_notes(case_id)
    return {
        "case": CaseResponse.model_validate(case),
        "notes": [CaseNoteResponse.model_validate(n) for n in notes],
    }


@router.patch("/{case_id}")
async def update_case(
    case_id: uuid.UUID,
    body: CaseUpdateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    case = await repo.get_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if body.status is not None:
        case = await repo.update_status(case_id, body.status, body.resolution)
    if body.severity is not None:
        case.severity = body.severity
    if body.title is not None:
        case.title = body.title
    if body.description is not None:
        case.description = body.description

    await session.flush()

    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="case_updated",
        resource_type="case",
        resource_id=str(case_id),
        details=body.model_dump(exclude_none=True),
    )
    return CaseResponse.model_validate(case)


@router.post("/{case_id}/notes")
async def add_note(
    case_id: uuid.UUID,
    body: CaseNoteCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    note = await repo.add_note(
        case_id=case_id,
        officer_id=officer.telegram_id,
        content=body.content,
    )
    return CaseNoteResponse.model_validate(note)


@router.post("/{case_id}/events/{event_id}")
async def link_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    await repo.link_event(
        case_id=case_id,
        event_id=event_id,
        officer_id=officer.telegram_id,
    )
    return {"ok": True}


@router.delete("/{case_id}/events/{event_id}")
async def unlink_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = CaseRepository(session)
    ok = await repo.unlink_event(case_id, event_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return {"ok": True}
