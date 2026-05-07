from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"  # pending, in_progress, completed
    priority: Optional[str] = "medium"  # low, medium, high
    deadline: Optional[datetime] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    deadline: Optional[datetime]
    project_id: Optional[int]
    assigned_to: Optional[int]
    organisation_id: int
    created_at: datetime

    class Config:
        from_attributes = True