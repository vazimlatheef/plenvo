from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.link import LinkItem


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    links: Optional[List[LinkItem]] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    links: Optional[List[LinkItem]] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    links: Optional[List[LinkItem]] = Field(default=None)
    organisation_id: int
    manager_id: int
    status: str
    deadline: Optional[date]
    created_at: datetime
