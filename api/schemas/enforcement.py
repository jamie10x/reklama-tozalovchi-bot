import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EnforcementActionType = Literal[
    "delete_message",
    "trust_sender",
    "block_indicator",
    "allow_indicator",
    "refresh_member",
    "refresh_group_permissions",
    "restrict_member",
    "mute_member",
    "ban_member",
    "get_chat_info",
    "get_chat_administrators",
    "get_chat_member_count",
    "get_user_profile_photos",
    "save_observed_state",
    "send_recent_messages",
]


class EnforcementActionResponse(BaseModel):
    id: uuid.UUID
    action_type: str
    target_chat_id: int | None
    target_message_id: int | None
    target_user_id: int | None
    target_indicator_id: uuid.UUID | None
    status: str
    result: dict | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class EnforcementActionCreateRequest(BaseModel):
    action_type: EnforcementActionType
    target_chat_id: int | None = None
    target_message_id: int | None = None
    target_user_id: int | None = None
    target_indicator_id: uuid.UUID | None = None
