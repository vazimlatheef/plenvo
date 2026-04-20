from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AssignmentCreate(BaseModel):
    training_id: int = Field(gt=0)
    assignee_emails: list[EmailStr] = Field(min_length=1)

    @field_validator("assignee_emails", mode="after")
    @classmethod
    def dedupe_emails(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(e.strip().lower() for e in v if e and str(e).strip()))


class AssignmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_id: int
    assignee_user_id: int
    assigned_by_id: int
    due_date: date | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssignmentBatchResponse(BaseModel):
    created: int
    items: list[AssignmentPublic]


class AssignmentListItem(BaseModel):
    """Assignment row with training fields for UI."""

    id: int
    training_id: int
    training_title: str
    training_description: str | None
    content_type: str
    youtube_video_id: str | None
    external_url: str | None
    storage_key: str | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    due_date: date | None
    assignee_email: str
    assignee_full_name: str
    assigned_by_full_name: str
    created_at: datetime


class AssignmentListResponse(BaseModel):
    items: list[AssignmentListItem]
    total: int


class AssignmentProgressUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]


class AssignmentProgressResponse(BaseModel):
    id: int
    training_id: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
