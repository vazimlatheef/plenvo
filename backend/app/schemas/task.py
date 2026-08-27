from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.schemas.link import LinkItem
from app.services.due_times import parse_time_string


def _coerce_time(value) -> time | None:
    if value is None or value == "":
        return None
    if isinstance(value, time):
        return value
    return parse_time_string(str(value))


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    links: Optional[List[LinkItem]] = None
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_contact_id: Optional[int] = None

    @field_validator("due_time", mode="before")
    @classmethod
    def _validate_due_time(cls, value):
        return _coerce_time(value)

    @model_validator(mode="after")
    def _assignee_and_due(self):
        if self.assignee_id is not None and self.assignee_contact_id is not None:
            raise ValueError("Provide either assignee_id or assignee_contact_id, not both.")
        if self.due_time is not None and self.due_date is None:
            raise ValueError("due_time requires due_date.")
        return self


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    links: Optional[List[LinkItem]] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_contact_id: Optional[int] = None
    # When true, clear both assignee fields (unassign).
    clear_assignee: Optional[bool] = None

    @field_validator("due_time", mode="before")
    @classmethod
    def _validate_due_time(cls, value):
        return _coerce_time(value)

    @model_validator(mode="after")
    def _assignee_and_due(self):
        if self.assignee_id is not None and self.assignee_contact_id is not None:
            raise ValueError("Provide either assignee_id or assignee_contact_id, not both.")
        if self.due_time is not None and self.due_date is None:
            raise ValueError("due_time requires due_date.")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    links: Optional[List[LinkItem]] = None
    status: str
    priority: str
    due_date: Optional[date]
    due_time: Optional[time] = None
    project_id: Optional[int]
    assignee_id: Optional[int]
    assignee_contact_id: Optional[int] = None
    organisation_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
