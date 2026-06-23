import uuid
from datetime import datetime

from pydantic import BaseModel


class IndicatorResponse(BaseModel):
    id: uuid.UUID
    indicator_type: str
    indicator_value: str
    status: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    seen_count: int
    event_count: int
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class IndicatorListResponse(BaseModel):
    items: list[IndicatorResponse]
    total: int


class IndicatorUpdateRequest(BaseModel):
    status: str
    notes: str | None = None
