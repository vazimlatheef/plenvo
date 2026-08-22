from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrainingAssignmentRow(BaseModel):
    """One assignee row for completion summary table."""

    model_config = ConfigDict(from_attributes=True)

    assignee_full_name: str
    assignee_email: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None


class TrainingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=50_000)
    content_type: Literal["upload", "external_link", "youtube"]
    external_url: str | None = Field(default=None, max_length=2048)
    youtube_video_id: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_by_content_type(self) -> Self:
        if self.content_type == "youtube":
            if not (self.youtube_video_id and self.youtube_video_id.strip()):
                raise ValueError('Field "youtube_video_id" is required when content_type is "youtube".')
        if self.content_type == "external_link":
            if not (self.external_url and str(self.external_url).strip()):
                raise ValueError('Field "external_url" is required when content_type is "external_link".')
        return self


class TrainingPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    content_type: str
    external_url: str | None
    youtube_video_id: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class TrainingListItem(TrainingPublic):
    total_assigned: int = 0
    completed: int = 0


class TrainingSummary(BaseModel):
    training_id: int
    training_title: str
    total_assigned: int
    completed: int
    in_progress: int
    not_started: int
    rows: list[TrainingAssignmentRow]


class TrainingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=50_000)
    content_type: Literal["upload", "external_link", "youtube"] | None = None
    external_url: str | None = Field(default=None, max_length=2048)
    youtube_video_id: str | None = Field(default=None, max_length=32)
