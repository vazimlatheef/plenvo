from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.professional_roles import DEFAULT_ROLE, PROFESSIONAL_ROLES, normalise_contact_role
from app.schemas.profile_validators import normalize_optional_str, validate_linkedin_url, validate_phone

ContactRole = Literal[
    "CEO",
    "CFO",
    "COO",
    "Division Head",
    "Manager",
    "Project Manager",
    "Team Member",
    "Individual Contributor",
    "Other",
]


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    role: ContactRole = DEFAULT_ROLE
    role_other: Optional[str] = Field(default=None, max_length=200)
    team_division: Optional[str] = Field(default=None, max_length=200)
    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=64)
    linkedin_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("team_division", "role_other", "company", mode="before")
    @classmethod
    def empty_optional_text(cls, v: object) -> object:
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

    @model_validator(mode="after")
    def validate_role(self) -> "ContactCreate":
        try:
            role, role_other = normalise_contact_role(self.role, self.role_other)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        self.role = role  # type: ignore[assignment]
        self.role_other = role_other
        return self


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    role: Optional[ContactRole] = None
    role_other: Optional[str] = Field(default=None, max_length=200)
    team_division: Optional[str] = Field(default=None, max_length=200)
    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=64)
    linkedin_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("team_division", "role_other", "company", mode="before")
    @classmethod
    def empty_optional_text(cls, v: object) -> object:
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

    @model_validator(mode="after")
    def validate_role(self) -> "ContactUpdate":
        if self.role is None and self.role_other is None:
            return self
        role = self.role or DEFAULT_ROLE
        try:
            normalised_role, role_other = normalise_contact_role(role, self.role_other)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        self.role = normalised_role  # type: ignore[assignment]
        self.role_other = role_other
        return self


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
    role_other: Optional[str] = None
    team_division: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    user_id: Optional[int] = None
    invited_at: Optional[datetime] = None
    created_at: datetime
