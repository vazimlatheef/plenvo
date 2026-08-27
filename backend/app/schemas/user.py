from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator

from app.schemas.profile_validators import normalize_optional_str, validate_linkedin_url, validate_phone
from app.services.timezones import normalize_timezone


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
    team_division: str | None = None
    address: str | None = None
    company_name: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    phone_country: str | None = None
    phone_number: str | None = None
    country: str | None = None
    team_size: str | None = None
    timezone: str | None = None
    overdue_email_enabled: bool | None = None

    @field_validator("job_title", "company_name", "position", "team_division", mode="before")
    @classmethod
    def empty_to_none_text(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str):
            return normalize_optional_str(v, max_len=200)
        return v

    @field_validator("address", mode="before")
    @classmethod
    def empty_to_none_address(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str):
            return normalize_optional_str(v, max_len=500)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def check_timezone(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            normalized = normalize_timezone(v)
            if normalized is None:
                raise ValueError("Invalid timezone. Use an IANA name like Europe/London.")
            return normalized
        return v

    @field_validator("phone", "phone_number", mode="before")
    @classmethod
    def check_phone(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return validate_phone(v)
        return v

    @field_validator("linkedin_url", mode="before")
    @classmethod
    def check_linkedin(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return validate_linkedin_url(v)
        return v


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
    team_division: str | None = None
    address: str | None = None
    linkedin_url: str | None = None
    phone_country: str | None = None
    phone_number: str | None = None
    country: str | None = None
    team_size: str | None = None
    timezone: str | None = None
    organisation_id: int | None = None
    is_active: bool
    is_verified: bool = False
    overdue_email_enabled: bool = True
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @computed_field
    @property
    def phone(self) -> str | None:
        return self.phone_number
