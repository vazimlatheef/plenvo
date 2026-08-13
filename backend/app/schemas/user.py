from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


class UserCreate(BaseModel):
    """Used by admin to create employees directly (legacy flow)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: Literal["admin", "employee"]
    position: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = None
    job_title: str | None = None
    linkedin_url: str | None = None
    phone_country: str | None = None
    phone_number: str | None = None
    country: str | None = None
    team_size: str | None = None
    timezone: str | None = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    position: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    linkedin_url: str | None = None
    phone_country: str | None = None
    phone_number: str | None = None
    country: str | None = None
    team_size: str | None = None
    timezone: str | None = None
    organisation_id: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
