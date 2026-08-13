from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TrainingTokenStatusUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]


class TrainingTokenPublicResponse(BaseModel):
    assignment_id: int
    status: str
    training_title: str
    training_description: str | None
    content_type: str
    youtube_video_id: str | None
    external_url: str | None
    assignee_first_name: str
    assignee_last_name: str
    assignee_email: str
    assigned_by_full_name: str
    started_at: datetime | None
    completed_at: datetime | None
    token_expires_at: datetime


class TrainingTokenStatusResponse(BaseModel):
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    message: str
