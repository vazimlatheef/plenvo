from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate, UserPublic

router = APIRouter(tags=["users"])


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
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


@router.get("/", response_model=list[UserPublic])
def list_users(
    role: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users, optionally filtered by role (e.g., ?role=employee)"""
    query = db.query(User).filter(User.organisation_id == current_user.organisation_id)
    if role:
        query = query.filter(User.role == role)
    return query.all()