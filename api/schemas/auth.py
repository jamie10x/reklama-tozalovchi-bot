import uuid

from pydantic import BaseModel


class LoginRequest(BaseModel):
    telegram_id: int
    token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    officer: dict


class MeResponse(BaseModel):
    id: uuid.UUID
    telegram_id: int
    role: str
    display_name: str | None
    is_active: bool
