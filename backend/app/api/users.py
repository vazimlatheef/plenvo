from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db, require_admin_full_write_access
from app.core.security import hash_password
from app.models import User
from app.models.models import Organisation
from app.schemas.user import UserCreate, UserPublic, UserUpdate
from app.services.overdue_notifications import check_and_send_overdue_notifications
from app.services.plan_limits import assert_can_add_team_members, bump_trial_peak_member_count
from app.services.trial_notifications import check_and_send_trial_warning

router = APIRouter(tags=["users"])


class OverdueCheckResponse(BaseModel):
    notified: int


class TrialWarningCheckResponse(BaseModel):
    sent: bool


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    data = payload.model_dump(exclude_unset=True)

    if "first_name" in data and data["first_name"] is not None:
        current_user.first_name = data["first_name"].strip()
    if "last_name" in data and data["last_name"] is not None:
        current_user.last_name = data["last_name"].strip()
    if "position" in data:
        current_user.position = data["position"]
    if "job_title" in data:
        current_user.job_title = data["job_title"]
    if "team_division" in data:
        current_user.team_division = data["team_division"]
    if "address" in data:
        current_user.address = data["address"]
    if "company_name" in data:
        current_user.company_name = data["company_name"]
    if "linkedin_url" in data:
        current_user.linkedin_url = data["linkedin_url"]
    if "phone" in data:
        current_user.phone_number = data["phone"]
    elif "phone_number" in data:
        current_user.phone_number = data["phone_number"]
    if "phone_country" in data:
        current_user.phone_country = data["phone_country"]
    if "country" in data:
        current_user.country = data["country"]
    if "team_size" in data:
        current_user.team_size = data["team_size"]
    if "timezone" in data:
        current_user.timezone = data["timezone"]
    if "overdue_email_enabled" in data and data["overdue_email_enabled"] is not None:
        current_user.overdue_email_enabled = bool(data["overdue_email_enabled"])

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/check-overdue-tasks", response_model=OverdueCheckResponse)
def check_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverdueCheckResponse:
    """Check for newly overdue assigned tasks and email once per task (non-blocking for client)."""
    notified = check_and_send_overdue_notifications(db, current_user)
    return OverdueCheckResponse(notified=notified)


@router.post("/me/check-trial-warning", response_model=TrialWarningCheckResponse)
def check_trial_warning(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TrialWarningCheckResponse:
    """Email admin once when trial ends within 3 days (non-blocking for client)."""
    sent = check_and_send_trial_warning(db, current_user)
    return TrialWarningCheckResponse(sent=sent)


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_full_write_access),
) -> User:
    if not current_user.organisation_id:
        raise HTTPException(status_code=400, detail="No organisation on account.")

    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")
    assert_can_add_team_members(db, org, adding=1)

    user = User(
        organisation_id=current_user.organisation_id,
        email=str(payload.email).strip().lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        role=payload.role,
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
    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first()
    if org:
        bump_trial_peak_member_count(db, org)
        db.commit()
        db.refresh(org)
    return user


@router.get("/", response_model=list[UserPublic])
def list_users(
    role: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organisation_id is None:
        return []
    query = db.query(User).filter(User.organisation_id == current_user.organisation_id)
    if role:
        query = query.filter(User.role == role)
    return query.all()
