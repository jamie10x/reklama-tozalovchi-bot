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
