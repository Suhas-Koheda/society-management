from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus

MAX_DESCRIPTION_LENGTH = 2000


class ComplaintCreate(BaseModel):
    category: ComplaintCategory
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Description cannot be empty or whitespace only")
        return trimmed


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resident_id: int
    category: ComplaintCategory
    description: str
    status: ComplaintStatus
    priority: ComplaintPriority
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int


class ComplaintHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ComplaintStatus
    actor_id: int
    note: str | None
    created_at: datetime


class ComplaintPhotoResponse(BaseModel):
    id: int
    url: str
    created_at: datetime
