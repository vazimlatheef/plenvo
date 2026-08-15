from datetime import datetime, timedelta, timezone
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserPublic
from app.services.email import send_password_reset_email

router = APIRouter(tags=["auth"])


class VerifyEmailResponse(BaseModel):
    status: Literal["verified", "already_verified", "expired", "invalid"]
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    # Unverified users may still log in — verification is additive, not a gate.
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/api/v1/auth/verify-email", response_model=VerifyEmailResponse)
def verify_email(
    token: str = Query(..., min_length=8, max_length=64),
    db: Session = Depends(get_db),
) -> VerifyEmailResponse:
    """Mark a user verified from the emailed UUID token. Does not require auth."""
    user = db.scalar(select(User).where(User.verification_token == token.strip()))
    if user is None:
        return VerifyEmailResponse(
            status="invalid",
            message="This verification link is invalid or has already been used.",
        )

    if user.is_verified:
        return VerifyEmailResponse(
            status="already_verified",
            message="Your email is already verified. You can sign in.",
        )

    expires_at = user.verification_token_expires_at
    if expires_at is not None:
        # Normalize naive datetimes from DB drivers to UTC for comparison.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return VerifyEmailResponse(
                status="expired",
                message="This verification link has expired. Sign in and request a new one later.",
            )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()

    return VerifyEmailResponse(
        status="verified",
        message="Your email has been verified. Welcome to Plenvo!",
    )


@router.post("/api/v1/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    """Generate a 1h reset token and email a link. Always returns the same message."""
    generic = ForgotPasswordResponse(
        message="If an account exists for that email, we've sent a password reset link.",
    )
    user = db.scalar(select(User).where(User.email == str(payload.email).strip().lower()))
    if user is None or not user.is_active:
        return generic

    user.reset_token = str(uuid.uuid4())
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    sent = send_password_reset_email(
        to_email=user.email,
        first_name=user.first_name,
        reset_token=user.reset_token,
    )
    if not sent:
        print(f"⚠️ Warning: Failed to send password reset email to {user.email}")

    return generic


@router.post("/api/v1/auth/reset-password", response_model=ResetPasswordResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> ResetPasswordResponse:
    """Validate reset token, set new password hash, invalidate token."""
    user = db.scalar(select(User).where(User.reset_token == payload.token.strip()))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has already been used.",
        )

    expires_at = user.reset_token_expires_at
    if expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has already been used.",
        )
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        user.reset_token = None
        user.reset_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired. Request a new one from the sign-in page.",
        )

    user.password_hash = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()

    return ResetPasswordResponse(message="Your password has been updated. You can sign in now.")
