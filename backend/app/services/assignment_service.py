from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Assignment, Training, TrainingToken, User
from app.services.email import send_manager_training_complete_email, send_training_magic_link_email


def _require_org_id(organisation_id: int | None) -> int:
    if organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")
    return organisation_id


def create_assignments(
    db: Session,
    *,
    training_id: int,
    assignee_emails: list[str],
    assigned_by_id: int,
    organisation_id: int,
) -> list[Assignment]:
    org_id = _require_org_id(organisation_id)

    training = db.get(Training, training_id)
    if training is None or training.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    emails_unique = list(dict.fromkeys(e.strip().lower() for e in assignee_emails if e and e.strip()))
    if not emails_unique:
        return []

    users = list(
        db.scalars(
            select(User).where(
                func.lower(User.email).in_(emails_unique),
                User.organisation_id == org_id,
            )
        ).all()
    )
    id_by_email = {u.email.lower(): u.id for u in users}
    missing = [e for e in emails_unique if e not in id_by_email]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account in your organisation for: {', '.join(missing)}",
        )

    assignee_user_ids = [id_by_email[e] for e in emails_unique]

    existing_assignees = set(
        db.scalars(
            select(Assignment.assignee_user_id).where(
                Assignment.training_id == training_id,
                Assignment.assignee_user_id.in_(assignee_user_ids),
            )
        ).all()
    )

    assigner = db.get(User, assigned_by_id)
    to_create = [uid for uid in assignee_user_ids if uid not in existing_assignees]
    created: list[Assignment] = []
    for uid in to_create:
        row = Assignment(
            training_id=training_id,
            assignee_user_id=uid,
            assigned_by_id=assigned_by_id,
            status="not_started",
        )
        db.add(row)
        created.append(row)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment already exists for one or more users.",
        ) from None

    for row in created:
        db.refresh(row)
        assignee = db.get(User, row.assignee_user_id)
        token_row = _create_magic_token(db, row.id)
        if assignee and assigner:
            magic_url = f"https://plenvo.io/training/{token_row.token}"
            send_training_magic_link_email(
                to_email=assignee.email,
                employee_name=assignee.full_name,
                training_title=training.title,
                assigned_by_name=assigner.full_name,
                magic_url=magic_url,
            )

    return created


def _create_magic_token(db: Session, assignment_id: int) -> TrainingToken:
    import secrets
    from datetime import timedelta

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    row = TrainingToken(token=token, assignment_id=assignment_id, expires_at=expires_at)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_assignments_for_user(db: Session, *, current_user: User) -> list[Assignment]:
    org_id = _require_org_id(current_user.organisation_id)

    stmt = (
        select(Assignment)
        .join(Training, Assignment.training_id == Training.id)
        .options(
            joinedload(Assignment.training),
            joinedload(Assignment.assignee),
            joinedload(Assignment.assigned_by),
        )
        .where(Training.organisation_id == org_id)
        .order_by(Assignment.created_at.desc())
    )
    if current_user.role != "admin":
        stmt = stmt.where(Assignment.assignee_user_id == current_user.id)
    return list(db.scalars(stmt).all())


def update_assignment_progress(
    db: Session,
    *,
    assignment_id: int,
    current_user: User,
    status_value: str,
) -> Assignment:
    org_id = _require_org_id(current_user.organisation_id)
    assignment = (
        db.scalars(
            select(Assignment)
            .join(Training, Assignment.training_id == Training.id)
            .where(Assignment.id == assignment_id, Training.organisation_id == org_id)
        )
        .first()
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if assignment.assignee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    _apply_status(assignment, status_value)
    db.commit()
    db.refresh(assignment)
    return assignment


def _apply_status(assignment: Assignment, status_value: str) -> None:
    now = datetime.now(timezone.utc)

    if status_value == "not_started":
        assignment.status = "not_started"
        assignment.started_at = None
        assignment.completed_at = None
    elif status_value == "in_progress":
        assignment.status = "in_progress"
        assignment.completed_at = None
        if assignment.started_at is None:
            assignment.started_at = now
    elif status_value == "completed":
        assignment.status = "completed"
        assignment.completed_at = now
        if assignment.started_at is None:
            assignment.started_at = now
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")


def get_training_by_token(db: Session, token: str) -> tuple[TrainingToken, Assignment]:
    token_row = db.scalars(
        select(TrainingToken)
        .options(
            joinedload(TrainingToken.assignment).joinedload(Assignment.training),
            joinedload(TrainingToken.assignment).joinedload(Assignment.assignee),
            joinedload(TrainingToken.assignment).joinedload(Assignment.assigned_by),
        )
        .where(TrainingToken.token == token)
    ).first()

    if token_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid training link.")

    now = datetime.now(timezone.utc)
    expires = token_row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This training link has expired.")

    if token_row.used_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This training link has already been used.")

    return token_row, token_row.assignment


def update_assignment_by_token(db: Session, token: str, status_value: str) -> Assignment:
    token_row, assignment = get_training_by_token(db, token)
    _apply_status(assignment, status_value)

    if status_value == "completed":
        token_row.used_at = datetime.now(timezone.utc)
        if assignment.manager_notified_at is None:
            manager = assignment.assigned_by
            assignee = assignment.assignee
            training = assignment.training
            if manager and assignee and training:
                sent = send_manager_training_complete_email(
                    to_email=manager.email,
                    manager_name=manager.full_name,
                    employee_name=assignee.full_name,
                    training_title=training.title,
                )
                if sent:
                    assignment.manager_notified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(assignment)
    return assignment
