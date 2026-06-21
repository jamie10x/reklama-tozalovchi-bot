from datetime import datetime

from pydantic import BaseModel


class OfficerResponse(BaseModel):
    id: str
    telegram_id: int
    role: str
    display_name: str | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class OfficerListResponse(BaseModel):
    items: list[OfficerResponse]
    total: int


class OfficerCreateRequest(BaseModel):
    telegram_id: int
    role: str = "analyst"
    display_name: str | None = None


class OfficerUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    display_name: str | None = None
