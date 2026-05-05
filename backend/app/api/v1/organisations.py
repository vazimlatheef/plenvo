"""
Organisation signup flow.
POST /signup  → creates Organisation + admin User + Stripe customer + starts 30-day trial
POST /invite  → admin invites employees to their org
"""

import re
import os
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.core.security import hash_password
from app.models.models import Organisation, User
from app.schemas.user import UserPublic

router = APIRouter(tags=["organisations"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # your €19/mo price ID


# ---------- Schemas ----------

class SignupRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=300)
    position: str = Field(min_length=1, max_length=100)
    # position examples: CEO, Manager, Team Lead, Director
    stripe_payment_method_id: str
    # Frontend collects card via Stripe.js, sends payment_method id


class InviteRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    position: str = Field(min_length=1, max_length=100)


class SignupResponse(BaseModel):
    user: UserPublic
    organisation_name: str
    trial_ends_at: datetime
    message: str


# ---------- Helpers ----------

def slugify(name: str) -> str:
    """Convert 'Acme Corp' → 'acme-corp'"""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:280]


def make_unique_slug(db: Session, base_slug: str) -> str:
    """Append number if slug taken: acme-corp-2, acme-corp-3..."""
    slug = base_slug
    counter = 2
    while db.query(Organisation).filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


# ---------- Routes ----------

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Manager signs up → Organisation created → Stripe trial starts.
    Card is captured now but NOT charged for 30 days.
    """
    # 1. Create Stripe customer + attach card
    try:
        customer = stripe.Customer.create(
            email=payload.email,
            name=payload.full_name,
            metadata={"company": payload.company_name},
        )
        stripe.PaymentMethod.attach(
            payload.stripe_payment_method_id,
            customer=customer.id,
        )
        stripe.Customer.modify(
            customer.id,
            invoice_settings={"default_payment_method": payload.stripe_payment_method_id},
        )
        # Create subscription with 30-day trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": STRIPE_PRICE_ID}],
            trial_period_days=30,
            payment_settings={"save_default_payment_method": "on_subscription"},
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e)) from e

    trial_ends_at = datetime.now(timezone.utc) + timedelta(days=30)

    # 2. Create Organisation
    slug = make_unique_slug(db, slugify(payload.company_name))
    org = Organisation(
        name=payload.company_name,
        slug=slug,
        stripe_customer_id=customer.id,
        stripe_subscription_id=subscription.id,
        trial_ends_at=trial_ends_at,
    )
    db.add(org)
    db.flush()  # get org.id without committing

    # 3. Create admin User
    user = User(
        organisation_id=org.id,
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin",
        position=payload.position,
        company_name=payload.company_name,
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


@router.post("/invite", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def invite_employee(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Admin invites an employee to their organisation.
    Employee inherits the same org — data isolation guaranteed.
    """
    if not current_user.organisation_id:
        raise HTTPException(status_code=400, detail="Your account has no organisation.")

    user = User(
        organisation_id=current_user.organisation_id,
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
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
    return user