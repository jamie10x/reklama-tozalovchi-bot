import uuid
from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: uuid.UUID
    event_number: int
    chat_id: int
    message_id: int | None
    sender_id: int | None
    event_type: str
    severity: str
    score: int
    confidence: float | None
    title: str | None
    message_excerpt: str | None
    detection_reasons: dict | None
    detected_indicators: dict | None
    ad_score: int | None
    security_score: int | None
    ai_score: int | None
    ai_analysis: dict | None
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
