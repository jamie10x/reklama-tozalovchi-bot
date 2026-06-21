from datetime import datetime

from pydantic import BaseModel


class EnforcementActionResponse(BaseModel):
    id: str
    action_type: str
    target_chat_id: int | None
    target_message_id: int | None
    target_user_id: int | None
    status: str
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class EnforcementActionCreateRequest(BaseModel):
    action_type: str
    target_chat_id: int | None = None
    target_message_id: int | None = None
    target_user_id: int | None = None
    target_indicator_id: str | None = None
