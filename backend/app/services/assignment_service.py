from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Assignment, Training, User


def create_assignments(
    db: Session,
    *,
    training_id: int,
    assignee_emails: list[str],
    assigned_by_id: int,
) -> list[Assignment]:
    """Create assignments for users not already assigned to this training.

    Emails are normalized (lowercase, deduped). Existing (training, user) pairs are skipped.

    If a concurrent request inserts the same row, responds with 409 (IntegrityError).
    """
    if db.get(Training, training_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    emails_unique = list(dict.fromkeys(e.strip().lower() for e in assignee_emails if e and e.strip()))
    if not emails_unique:
        return []

    users = list(
        db.scalars(select(User).where(func.lower(User.email).in_(emails_unique))).all()
    )
    id_by_email = {u.email.lower(): u.id for u in users}
    missing = [e for e in emails_unique if e not in id_by_email]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account for: {', '.join(missing)}",
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
    return created


def list_assignments_for_user(db: Session, *, current_user: User) -> list[Assignment]:
    stmt = (
        select(Assignment)
        .options(
            joinedload(Assignment.training),
            joinedload(Assignment.assignee),
            joinedload(Assignment.assigned_by),
        )
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
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if assignment.assignee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

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
        # Should be prevented by schema validation, but keep the service safe.
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")

    db.commit()
    db.refresh(assignment)
    return assignment
