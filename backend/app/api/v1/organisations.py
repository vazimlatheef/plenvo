"""
Organisation signup flow.
POST /signup  → creates Organisation (team trial) + admin User from email/password only
POST /invite  → admin invites employees to their org

Card collection / Stripe subscription happens later on explicit upgrade to a paid plan.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.core.security import hash_password
from app.models.models import Organisation, User
from app.schemas.user import UserPublic
from app.services.contact_service import find_org_contact_by_email, link_contact_to_user
from app.services.email import generate_temp_password, send_invite_email, send_verification_email

router = APIRouter(tags=["organisations"])

TRIAL_DAYS = 14
DEFAULT_PLAN_TIER = "team"
_CONSUMER_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "icloud.com",
        "me.com",
        "proton.me",
        "protonmail.com",
        "aol.com",
        "mail.com",
    }
)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    position: str | None = Field(default=None, max_length=100)
    # Captured on first invite when the admin skipped team_size at signup.
    team_size: str | None = Field(default=None, max_length=20)


class SignupResponse(BaseModel):
    user: UserPublic
    organisation_name: str
    trial_ends_at: datetime
    plan_tier: str
    message: str


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:280] or "workspace"


def make_unique_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    counter = 2
    while db.query(Organisation).filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split(None, 1)
    if not parts:
        return "Team", "Member"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _defaults_from_email(email: str) -> tuple[str, str, str]:
    """Derive first_name, last_name, company_name from an email address."""
    local, _, domain = email.partition("@")
    local_clean = re.sub(r"[^a-zA-Z0-9]+", " ", local).strip() or "Admin"
    parts = local_clean.split()
    first_name = parts[0].capitalize()
    last_name = " ".join(p.capitalize() for p in parts[1:]) if len(parts) > 1 else ""

    if domain and domain.lower() not in _CONSUMER_EMAIL_DOMAINS:
        label = domain.split(".")[0]
        company_name = re.sub(r"[^a-zA-Z0-9]+", " ", label).strip().title() or "My workspace"
    else:
        company_name = f"{first_name}'s workspace"
    return first_name, last_name, company_name


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        email = str(payload.email).strip().lower()
        first_name, last_name, company_name = _defaults_from_email(email)
        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)
        slug = make_unique_slug(db, slugify(company_name))

        org = Organisation(
            name=company_name,
            slug=slug,
            plan_tier=DEFAULT_PLAN_TIER,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            trial_ends_at=trial_ends_at,
        )
        db.add(org)
        db.flush()

        user = User(
            organisation_id=org.id,
            email=email,
            password_hash=hash_password(payload.password),
            first_name=first_name,
            last_name=last_name,
            role="admin",
            company_name=company_name,
            team_size=None,
            is_verified=False,
            verification_token=str(uuid.uuid4()),
            verification_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from None

        db.refresh(user)

        email_sent = send_verification_email(
            to_email=user.email,
            first_name=user.first_name,
            verification_token=user.verification_token,
        )
        if not email_sent:
            print(f"⚠️ Warning: Failed to send verification email to {user.email}")

        return SignupResponse(
            user=UserPublic.model_validate(user),
            organisation_name=org.name,
            trial_ends_at=trial_ends_at,
            plan_tier=org.plan_tier,
            message=f"Welcome to Plenvo! Your {TRIAL_DAYS}-day free trial has started. Check your inbox to verify your email.",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"SIGNUP ERROR: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.") from e


@router.post("/invite", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def invite_employee(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    if not current_user.organisation_id:
        raise HTTPException(status_code=400, detail="Your account has no organisation.")

    # Capture team_size on first invite if the admin never set it at signup.
    if not current_user.team_size:
        if not payload.team_size:
            raise HTTPException(
                status_code=400,
                detail="team_size is required on your first invite.",
            )
        current_user.team_size = payload.team_size.strip()

    first_name, last_name = _split_name(payload.name)
    temp_password = generate_temp_password()

    user = User(
        organisation_id=current_user.organisation_id,
        email=str(payload.email).strip().lower(),
        password_hash=hash_password(temp_password),
        first_name=first_name,
        last_name=last_name,
        role="employee",
        position=payload.position,
        company_name=current_user.company_name,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from None

    db.refresh(user)
    db.refresh(current_user)

    contact = find_org_contact_by_email(db, current_user.organisation_id, user.email)
    if contact and contact.user_id is None:
        link_contact_to_user(db, contact, user)
        db.commit()
        db.refresh(contact)

    org = db.query(Organisation).filter_by(id=current_user.organisation_id).first()
    email_sent = send_invite_email(
        to_email=user.email,
        employee_name=user.full_name,
        temp_password=temp_password,
        organisation_name=org.name if org else None,
    )
    if not email_sent:
        print(f"⚠️ Warning: Failed to send invite email to {user.email}")

    return user
