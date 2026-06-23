from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db, get_public_db, require_any_role
from api.schemas.enforcement import (
    EnforcementActionCreateRequest,
    EnforcementActionResponse,
)
from app.database.repositories.enforcement import EnforcementRepository
from app.database.repositories.officers import OfficerRepository
from app.database.models import Chat
from app.database.repositories.activity import ActivityRepository
from app.database.secadmin_models import Officer, UserChatProfile

router = APIRouter(prefix="/api/v1/enforcement", tags=["enforcement"])

INTEL_ACTIONS = {
    "get_chat_info",
    "get_chat_administrators",
    "get_chat_member_count",
    "get_user_profile_photos",
    "save_observed_state",
    "send_recent_messages",
}
RESPONDER_ACTIONS = {
    "delete_message",
    "trust_sender",
    "block_indicator",
    "allow_indicator",
    "refresh_member",
    "refresh_group_permissions",
    "restrict_member",
    "mute_member",
    "ban_member",
}
MESSAGE_ACTIONS = {"delete_message"}
MEMBER_ACTIONS = {"trust_sender", "refresh_member", "restrict_member", "mute_member", "ban_member"}
GROUP_ACTIONS = {
    "delete_message",
    "trust_sender",
    "refresh_member",
    "refresh_group_permissions",
    "restrict_member",
    "mute_member",
    "ban_member",
    "get_chat_info",
    "get_chat_administrators",
    "get_chat_member_count",
    "save_observed_state",
    "send_recent_messages",
}
DELETE_PERMISSION_ACTIONS = {"delete_message"}


def _can_run_action(officer: Officer, action_type: str) -> bool:
    if officer.role == "super_admin":
        return True
    if action_type in RESPONDER_ACTIONS:
        return officer.role == "responder"
    if action_type in INTEL_ACTIONS:
        return officer.role in {"analyst", "responder"}
    return False


async def _get_group(public_session: AsyncSession, chat_id: int) -> Chat:
    result = await public_session.execute(select(Chat).where(Chat.telegram_chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if chat is None or chat.removed_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not chat.enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group monitoring is disabled")
    return chat


async def _validate_member(session: AsyncSession, chat_id: int, user_id: int) -> None:
    result = await session.execute(
        select(UserChatProfile).where(
            UserChatProfile.chat_id == chat_id,
            UserChatProfile.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Target user has not been observed in this group",
        )


async def _preflight_action(
    body: EnforcementActionCreateRequest,
    officer: Officer,
    session: AsyncSession,
    public_session: AsyncSession,
) -> dict:
    action_type = body.action_type
    if not _can_run_action(officer, action_type):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Officer role cannot run this command")

    checks: dict = {"officer_role": officer.role, "action_type": action_type}
    chat = None
    if action_type in GROUP_ACTIONS:
        if body.target_chat_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="target_chat_id is required")
        chat = await _get_group(public_session, body.target_chat_id)
        checks["group"] = {
            "title": chat.title,
            "enabled": chat.enabled,
            "bot_can_delete_messages": chat.bot_can_delete_messages,
        }

    if action_type in DELETE_PERMISSION_ACTIONS and chat is not None and not chat.bot_can_delete_messages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bot does not currently have delete-message permission in this group",
        )

    if action_type in MESSAGE_ACTIONS:
        if body.target_message_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="target_message_id is required")
        repo = ActivityRepository(session)
        message = await repo.get_message(body.target_chat_id, body.target_message_id)  # type: ignore[arg-type]
        if message is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Target message has not been observed by this bot",
            )
        checks["message"] = {"observed": True, "detection_status": message.detection_status}

    if action_type in MEMBER_ACTIONS:
        if body.target_user_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="target_user_id is required")
        await _validate_member(session, body.target_chat_id, body.target_user_id)  # type: ignore[arg-type]
        checks["member"] = {"observed_in_group": True}

    if action_type == "get_user_profile_photos" and body.target_user_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="target_user_id is required")

    return checks


async def _audit_action(
    session: AsyncSession,
    officer: Officer,
    action,
    body: EnforcementActionCreateRequest,
    preflight: dict | None = None,
) -> None:
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
            "target_indicator_id": str(body.target_indicator_id) if body.target_indicator_id else None,
            "preflight": preflight,
        },
    )


@router.get("")
async def list_enforcement(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    action_type: str | None = None,
    chat_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(require_any_role("analyst", "responder", "auditor")),
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
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("responder")),
):
    command_body = EnforcementActionCreateRequest(
        action_type="delete_message",
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        target_user_id=body.target_user_id,
        target_indicator_id=body.target_indicator_id,
    )
    preflight = await _preflight_action(command_body, officer, session, public_session)
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type="delete_message",
        target_chat_id=command_body.target_chat_id,
        target_message_id=command_body.target_message_id,
        requested_by_officer_id=officer.telegram_id,
    )
    await _audit_action(session, officer, action, command_body, preflight)
    return EnforcementActionResponse.model_validate(action)


@router.post("/actions")
async def create_enforcement_action(
    body: EnforcementActionCreateRequest,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(get_current_officer),
):
    preflight = await _preflight_action(body, officer, session, public_session)
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type=body.action_type,
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        target_user_id=body.target_user_id,
        target_indicator_id=body.target_indicator_id,
        requested_by_officer_id=officer.telegram_id,
    )
    await _audit_action(session, officer, action, body, preflight)
    return EnforcementActionResponse.model_validate(action)


@router.post("/actions/{action_id}/retry")
async def retry_enforcement_action(
    action_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = EnforcementRepository(session)
    original = await repo.get_by_id(action_id)
    if original is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")
    body = EnforcementActionCreateRequest(
        action_type=original.action_type,
        target_chat_id=original.target_chat_id,
        target_message_id=original.target_message_id,
        target_user_id=original.target_user_id,
        target_indicator_id=original.target_indicator_id,
    )
    preflight = await _preflight_action(body, officer, session, public_session)
    action = await repo.create(
        action_type=body.action_type,
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        target_user_id=body.target_user_id,
        target_indicator_id=body.target_indicator_id,
        requested_by_officer_id=officer.telegram_id,
    )
    await _audit_action(session, officer, action, body, {**preflight, "retry_of": str(action_id)})
    return EnforcementActionResponse.model_validate(action)


@router.post("/trust-sender")
async def trust_sender(
    body: EnforcementActionCreateRequest,
    session: AsyncSession = Depends(get_db),
    public_session: AsyncSession = Depends(get_public_db),
    officer: Officer = Depends(require_any_role("responder")),
):
    command_body = EnforcementActionCreateRequest(
        action_type="trust_sender",
        target_chat_id=body.target_chat_id,
        target_message_id=body.target_message_id,
        target_user_id=body.target_user_id,
        target_indicator_id=body.target_indicator_id,
    )
    preflight = await _preflight_action(command_body, officer, session, public_session)
    repo = EnforcementRepository(session)
    action = await repo.create(
        action_type="trust_sender",
        target_user_id=command_body.target_user_id,
        target_chat_id=command_body.target_chat_id,
        requested_by_officer_id=officer.telegram_id,
    )
    await _audit_action(session, officer, action, command_body, preflight)
    return EnforcementActionResponse.model_validate(action)
