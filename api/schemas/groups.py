from datetime import datetime

from pydantic import BaseModel


class GroupResponse(BaseModel):
    telegram_chat_id: int
    title: str | None
    username: str | None
    enabled: bool
    mode: str
    bot_can_delete_messages: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    items: list[GroupResponse]
    total: int


class GroupUpdateRequest(BaseModel):
    enabled: bool | None = None
    mode: str | None = None


class GroupHealthResponse(BaseModel):
    telegram_chat_id: int
    title: str | None
    username: str | None
    enabled: bool
    mode: str
    bot_can_delete_messages: bool
    capture_enabled: bool | None = None
    capture_mode: str | None = None
    metadata_retention_days: int | None = None
    flagged_retention_days: int | None = None
    observed_messages: int = 0
    flagged_messages: int = 0
    stored_text_messages: int = 0
    pending_commands: int = 0
    last_observed_at: datetime | None = None
    last_command_at: datetime | None = None
    last_command_status: str | None = None
    last_command_type: str | None = None


class GroupHealthListResponse(BaseModel):
    items: list[GroupHealthResponse]
    total: int
