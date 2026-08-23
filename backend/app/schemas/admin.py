from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus


class PriorityUpdate(BaseModel):
    priority: ComplaintPriority


class StatusUpdate(BaseModel):
    status: ComplaintStatus
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class ResidentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class ComplaintPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    storage_key: str | None
    created_at: datetime


class AdminComplaintListItem(BaseModel):
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
    is_overdue: bool = False


class OverdueThresholdResponse(BaseModel):
    threshold_days: int


class OverdueThresholdUpdate(BaseModel):
    threshold_days: int = Field(ge=1, le=365)


class AdminComplaintListResponse(BaseModel):
    items: list[AdminComplaintListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class AdminComplaintDetail(AdminComplaintListItem):
    resident: ResidentBrief
    photos: list[ComplaintPhotoResponse]


class AdminComplaintHistoryItem(BaseModel):
    id: int
    status: ComplaintStatus
    actor_id: int
    actor_name: str
    actor_email: str
    note: str | None
    created_at: datetime
