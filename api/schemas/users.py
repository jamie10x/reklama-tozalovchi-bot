from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    telegram_id: int
    current_username: str | None
    current_first_name: str | None
    current_last_name: str | None
    is_bot: bool
    language_code: str | None
    risk_score: int
    first_seen_at: datetime | None
    last_seen_at: datetime | None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
