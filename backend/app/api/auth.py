from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserPublic

router = APIRouter(tags=["auth"])


class VerifyEmailResponse(BaseModel):
    status: Literal["verified", "already_verified", "expired", "invalid"]
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
