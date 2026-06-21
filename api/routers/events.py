from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.events import EventListResponse, EventResponse, EventUpdateRequest
from app.database.repositories.events import SecurityEventRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("")
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    severity: str | None = None,
    event_type: str | None = None,
    chat_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = SecurityEventRepository(session)
    events = await repo.list(
        limit=limit,
        offset=offset,
        status=status,
        severity=severity,
        event_type=event_type,
        chat_id=chat_id,
    )
    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in events],
        total=len(events),
    )


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = SecurityEventRepository(session)
    event = await repo.get_by_id(uuid.UUID(event_id))
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse.model_validate(event)


@router.patch("/{event_id}")
async def update_event(
    event_id: str,
    body: EventUpdateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = SecurityEventRepository(session)
    event = await repo.update_status(
        uuid.UUID(event_id),
        status=body.status,
        officer_id=body.assigned_officer_id,
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    from app.database.repositories.officers import OfficerRepository

    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="event_status_update",
        resource_type="event",
        resource_id=event_id,
        details={"new_status": body.status},
    )
    return EventResponse.model_validate(event)
