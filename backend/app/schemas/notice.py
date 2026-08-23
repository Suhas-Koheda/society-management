from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 5000


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    content: str = Field(min_length=1, max_length=MAX_CONTENT_LENGTH)
    is_important: bool = False

    @field_validator("title")
    @classmethod
    def clean_title(cls, v):
        cleaned = _clean(v)
        if not cleaned:
            raise ValueError("Title cannot be empty or whitespace only")
        return cleaned

    @field_validator("content")
    @classmethod
    def clean_content(cls, v):
        cleaned = _clean(v)
        if not cleaned:
            raise ValueError("Content cannot be empty or whitespace only")
        return cleaned


class NoticeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_LENGTH)
    content: str | None = Field(default=None, min_length=1, max_length=MAX_CONTENT_LENGTH)
    is_important: bool | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, v):
        if v is None:
            return None
        cleaned = _clean(v)
        if not cleaned:
            raise ValueError("Title cannot be empty or whitespace only")
        return cleaned

    @field_validator("content")
    @classmethod
    def clean_content(cls, v):
        if v is None:
            return None
        cleaned = _clean(v)
        if not cleaned:
            raise ValueError("Content cannot be empty or whitespace only")
        return cleaned


class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    is_important: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


class NoticeListResponse(BaseModel):
    items: list[NoticeResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
