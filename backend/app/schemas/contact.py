from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ContactRole = Literal["Member", "Manager", "Contractor", "Client", "Other"]


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    role: ContactRole = "Member"


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    role: Optional[ContactRole] = None


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
    user_id: Optional[int] = None
    invited_at: Optional[datetime] = None
    created_at: datetime
