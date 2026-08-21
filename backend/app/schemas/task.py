from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_contact_id: Optional[int] = None

    @model_validator(mode="after")
    def _one_assignee(self):
        if self.assignee_id is not None and self.assignee_contact_id is not None:
            raise ValueError("Provide either assignee_id or assignee_contact_id, not both.")
        return self


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    assignee_id: Optional[int] = None
    assignee_contact_id: Optional[int] = None
    # When true, clear both assignee fields (unassign).
    clear_assignee: Optional[bool] = None

    @model_validator(mode="after")
    def _one_assignee(self):
        if self.assignee_id is not None and self.assignee_contact_id is not None:
            raise ValueError("Provide either assignee_id or assignee_contact_id, not both.")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    project_id: Optional[int]
    assignee_id: Optional[int]
    assignee_contact_id: Optional[int] = None
    organisation_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
