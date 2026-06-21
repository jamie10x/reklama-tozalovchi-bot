from datetime import datetime

from pydantic import BaseModel


class CaseResponse(BaseModel):
    id: str
    case_number: int
    title: str
    severity: str
    status: str
    assigned_officer_id: int | None
    description: str | None
    resolution: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int


class CaseCreateRequest(BaseModel):
    title: str
    severity: str = "medium"
    description: str | None = None
    assigned_officer_id: int | None = None


class CaseUpdateRequest(BaseModel):
    status: str | None = None
    severity: str | None = None
    title: str | None = None
    description: str | None = None
    resolution: str | None = None


class CaseNoteResponse(BaseModel):
    id: str
    officer_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseNoteCreateRequest(BaseModel):
    content: str
