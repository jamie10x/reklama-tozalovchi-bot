import uuid
from datetime import datetime

from pydantic import BaseModel


class CaptureSettingsResponse(BaseModel):
    chat_id: int
    enabled: bool
    capture_mode: str
    metadata_retention_days: int
    flagged_retention_days: int
    updated_by_officer_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaptureSettingsUpdateRequest(BaseModel):
    enabled: bool | None = None
    capture_mode: str | None = None


class ObservedMessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: int
    message_id: int
    sender_id: int | None
    sender_username: str | None
    sender_first_name: str | None
    sender_last_name: str | None
    sender_is_bot: bool
    sender_chat_id: int | None
    message_type: str
    text: str | None
    text_stored: bool
    has_text: bool
    is_edited: bool
    is_forwarded: bool
    forward_from_chat_id: int | None
    reply_to_message_id: int | None
    detection_status: str
    risk_score: int
    ad_score: int | None
    security_score: int | None
    ai_score: int | None
    detection_result: dict | None
    event_id: uuid.UUID | None
    message_date: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ObservedMessageListResponse(BaseModel):
    items: list[ObservedMessageResponse]
    total: int
