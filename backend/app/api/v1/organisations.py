"""
Organisation signup flow.
POST /signup  → creates Organisation + admin User + Stripe customer + starts 30-day trial
POST /invite  → admin invites employees to their org
"""

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.core.security import hash_password
from app.models.models import Organisation, User
from app.schemas.user import UserPublic
from app.services.email import generate_temp_password, send_invite_email

router = APIRouter(tags=["organisations"])

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID_PERSONAL = os.getenv("STRIPE_PRICE_ID_PERSONAL", "")
STRIPE_PRICE_ID_TEAM = os.getenv("STRIPE_PRICE_ID_TEAM", "")
STRIPE_PRICE_ID_ENTERPRISE = os.getenv("STRIPE_PRICE_ID_ENTERPRISE", "")


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=300)
    position: str = Field(min_length=1, max_length=100)
    phone_country: str | None = Field(default=None, max_length=8)
    phone_number: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=8)
    team_size: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=64)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    plan: str = Field(default="team")
    stripe_payment_method_id: str


class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    position: str | None = Field(default=None, max_length=100)


class SignupResponse(BaseModel):
    user: UserPublic
    organisation_name: str
    trial_ends_at: datetime
    message: str


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:280]


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


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        if payload.plan == "personal":
            price_id = STRIPE_PRICE_ID_PERSONAL
        elif payload.plan == "team":
            price_id = STRIPE_PRICE_ID_TEAM
        elif payload.plan == "enterprise":
            price_id = STRIPE_PRICE_ID_ENTERPRISE
        else:
            raise HTTPException(status_code=400, detail="Invalid plan. Choose 'personal', 'team', or 'enterprise'.")

        if not price_id:
            raise HTTPException(
                status_code=500,
                detail=f"Pricing not configured for {payload.plan} plan. Contact hi@plenvo.io",
            )

        full_name = f"{payload.first_name} {payload.last_name}".strip()
        customer = stripe.Customer.create(
            email=payload.email,
            name=full_name,
            metadata={"company": payload.company_name, "plan": payload.plan},
        )
        stripe.PaymentMethod.attach(payload.stripe_payment_method_id, customer=customer.id)
        stripe.Customer.modify(
            customer.id,
            invoice_settings={"default_payment_method": payload.stripe_payment_method_id},
        )
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            trial_period_days=30,
            payment_settings={"save_default_payment_method": "on_subscription"},
        )

        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=30)
        slug = make_unique_slug(db, slugify(payload.company_name))
        org = Organisation(
            name=payload.company_name,
            slug=slug,
            stripe_customer_id=customer.id,
            stripe_subscription_id=subscription.id,
            trial_ends_at=trial_ends_at,
        )
        db.add(org)
        db.flush()

        user = User(
            organisation_id=org.id,
            email=str(payload.email).strip().lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            role="admin",
            position=payload.position,
            job_title=payload.position,
            company_name=payload.company_name,
            phone_country=payload.phone_country,
            phone_number=payload.phone_number,
            country=payload.country,
            team_size=payload.team_size,
            timezone=payload.timezone,
            linkedin_url=payload.linkedin_url,
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
        return SignupResponse(
            user=UserPublic.model_validate(user),
            organisation_name=org.name,
            trial_ends_at=trial_ends_at,
            message="Welcome to Plenvo! Your 30-day free trial has started.",
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
