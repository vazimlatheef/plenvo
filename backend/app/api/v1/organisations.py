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
from app.services.email import send_invite_email, generate_temp_password

router = APIRouter(tags=["organisations"])

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env") 

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
print(f"DEBUG: Stripe key loaded = {stripe.api_key[:20]}...{stripe.api_key[-10:]}")
STRIPE_PRICE_ID_PERSONAL = os.getenv("STRIPE_PRICE_ID_PERSONAL", "")  # £9.99/mo
STRIPE_PRICE_ID_TEAM = os.getenv("STRIPE_PRICE_ID_TEAM", "")  # £25/mo
STRIPE_PRICE_ID_ENTERPRISE = os.getenv("STRIPE_PRICE_ID_ENTERPRISE", "")   # £49/mo


# ---------- Schemas ----------

class SignupRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=300)
    position: str = Field(min_length=1, max_length=100)
    plan: str = Field(default="team")  # "personal", "team", or "enterprise"
    stripe_payment_method_id: str


class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    position: str = Field(default=None, max_length=100)


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
    try:
        # Select correct price ID based on plan
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
                detail=f"Pricing not configured for {payload.plan} plan. Contact hi@plenvo.io"
            )

        # 1. Create Stripe customer + attach card
        customer = stripe.Customer.create(
            email=payload.email,
            name=payload.full_name,
            metadata={"company": payload.company_name, "plan": payload.plan},
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
            items=[{"price": price_id}],
            trial_period_days=30,
            payment_settings={"save_default_payment_method": "on_subscription"},
        )

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
        
    except Exception as e:
        print(f"SIGNUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

@router.post("/invite", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def invite_employee(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Admin invites an employee to their organisation.
    Generates temporary password and sends email with credentials.
    """
    if not current_user.organisation_id:
        raise HTTPException(status_code=400, detail="Your account has no organisation.")

    # Generate temporary password
    temp_password = generate_temp_password()

    # Create employee user
    user = User(
        organisation_id=current_user.organisation_id,
        email=payload.email.strip().lower(),
        password_hash=hash_password(temp_password),
        full_name=payload.name,
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

    # Send invite email with credentials
    org = db.query(Organisation).filter_by(id=current_user.organisation_id).first()
    email_sent = send_invite_email(
        to_email=user.email,
        employee_name=user.full_name,
        temp_password=temp_password,
        organisation_name=org.name if org else None,
    )

    if not email_sent:
        print(f"⚠️ Warning: Failed to send invite email to {user.email}")
        # Don't fail the request - user created successfully

    return user