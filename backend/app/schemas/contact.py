from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.profile_validators import normalize_optional_str, validate_linkedin_url, validate_phone

ContactRole = Literal["Member", "Manager", "Contractor", "Client", "Other"]


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    role: ContactRole = "Member"
    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=64)
    linkedin_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("company", mode="before")
    @classmethod
    def empty_company(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return normalize_optional_str(v, max_len=200)
        return v

    @field_validator("phone", mode="before")
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


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    role: Optional[ContactRole] = None
    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=64)
    linkedin_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("company", mode="before")
    @classmethod
    def empty_company(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return normalize_optional_str(v, max_len=200)
        return v

    @field_validator("phone", mode="before")
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


class ContactInviteRequest(BaseModel):
    # Captured on first invite when the admin skipped team_size at signup.
    team_size: Optional[str] = Field(default=None, max_length=20)


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    name: str
    email: str
    role: str
    company: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    user_id: Optional[int] = None
    invited_at: Optional[datetime] = None
    created_at: datetime
