from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: str
    event_number: int
    chat_id: int
    message_id: int | None
    sender_id: int | None
    event_type: str
    severity: str
    score: int
    title: str | None
    status: str
    assigned_officer_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int


class EventUpdateRequest(BaseModel):
    status: str
    assigned_officer_id: int | None = None
