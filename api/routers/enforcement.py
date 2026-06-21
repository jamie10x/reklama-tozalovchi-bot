from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.enforcement import (
    EnforcementActionCreateRequest,
    EnforcementActionResponse,
)
from app.database.repositories.enforcement import EnforcementRepository
from app.database.repositories.officers import OfficerRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/enforcement", tags=["enforcement"])


@router.get("")
async def list_enforcement(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    action_type: str | None = None,
    chat_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = EnforcementRepository(session)
    actions = await repo.list(
        limit=limit,
        offset=offset,
        status=status,
        action_type=action_type,
        chat_id=chat_id,
    )
    return {
        "items": [EnforcementActionResponse.model_validate(a) for a in actions],
        "total": len(actions),
    }


@router.post("/delete-message")
async def request_delete_message(
    body: EnforcementActionCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type="delete_message",
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        requested_by_officer_id=officer.telegram_id,
    )
    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="enforcement_requested",
        resource_type="enforcement",
        resource_id=str(action.id),
        details={"action_type": "delete_message"},
    )
    return EnforcementActionResponse.model_validate(action)


@router.post("/actions")
async def create_enforcement_action(
    body: EnforcementActionCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type=body.action_type,
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        target_user_id=body.target_user_id,
        target_indicator_id=body.target_indicator_id,
        requested_by_officer_id=officer.telegram_id,
    )
    officer_repo = OfficerRepository(session)
    await officer_repo.create_audit_log(
        officer_id=officer.id,
        action_type="enforcement_requested",
        resource_type="enforcement",
        resource_id=str(action.id),
        details={
            "action_type": body.action_type,
            "target_chat_id": body.target_chat_id,
            "target_message_id": body.target_message_id,
            "target_user_id": body.target_user_id,
            "target_indicator_id": str(body.target_indicator_id)
            if body.target_indicator_id
            else None,
        },
    )
    return EnforcementActionResponse.model_validate(action)


@router.post("/trust-sender")
async def trust_sender(
    body: EnforcementActionCreateRequest,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type="trust_sender",
        target_user_id=body.target_user_id,
        target_chat_id=body.target_chat_id,
        requested_by_officer_id=officer.telegram_id,
    )
    return EnforcementActionResponse.model_validate(action)
