from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class AssignmentCreate(BaseModel):
    training_id: int = Field(gt=0)
    assignee_emails: list[EmailStr] = Field(default_factory=list)
    assignee_user_ids: list[int] = Field(default_factory=list)
    assignee_contact_ids: list[int] = Field(default_factory=list)

    @field_validator("assignee_emails", mode="after")
    @classmethod
    def dedupe_emails(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(e.strip().lower() for e in v if e and str(e).strip()))

    @field_validator("assignee_user_ids", "assignee_contact_ids", mode="after")
    @classmethod
    def dedupe_ids(cls, v: list[int]) -> list[int]:
        seen: set[int] = set()
        out: list[int] = []
        for item in v:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    @model_validator(mode="after")
    def require_assignees(self) -> "AssignmentCreate":
        if not self.assignee_emails and not self.assignee_user_ids and not self.assignee_contact_ids:
            raise ValueError("Provide at least one assignee via email, user id, or contact id.")
        return self


class AssignmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_id: int
    assignee_user_id: int | None
    assignee_contact_id: int | None
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
    assignee_contact_id: int | None = None
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
