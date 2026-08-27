from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Assignment, Contact, Training, TrainingToken, User
from app.services.email import (
    build_training_magic_link_url,
    send_manager_training_complete_email,
    send_training_magic_link_email,
)


@dataclass(frozen=True)
class _AssigneeTarget:
    kind: str  # "user" | "contact"
    id: int


def _require_org_id(organisation_id: int | None) -> int:
    if organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")
    return organisation_id


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "Team", "Member"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _assignment_assignee_name(assignment: Assignment) -> str:
    if assignment.assignee is not None:
        return assignment.assignee.full_name
    if assignment.assignee_contact is not None:
        return assignment.assignee_contact.name
    return "Assignee"


def _assignment_assignee_email(assignment: Assignment) -> str:
    if assignment.assignee is not None:
        return assignment.assignee.email
    if assignment.assignee_contact is not None:
        return assignment.assignee_contact.email
    return ""


def _validate_contact(db: Session, org_id: int, contact_id: int) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None or contact.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact not found: {contact_id}")
    return contact


def _validate_user(db: Session, org_id: int, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found: {user_id}")
    return user


def _resolve_assignee_targets(
    db: Session,
    *,
    org_id: int,
    assignee_emails: list[str],
    assignee_user_ids: list[int],
    assignee_contact_ids: list[int],
) -> list[_AssigneeTarget]:
    targets: list[_AssigneeTarget] = []
    seen_users: set[int] = set()
    seen_contacts: set[int] = set()

    for user_id in assignee_user_ids:
        _validate_user(db, org_id, user_id)
        if user_id not in seen_users:
            seen_users.add(user_id)
            targets.append(_AssigneeTarget("user", user_id))

    for contact_id in assignee_contact_ids:
        contact = _validate_contact(db, org_id, contact_id)
        if contact.user_id is not None and contact.user_id in seen_users:
            continue
        if contact.user_id is not None and contact.user_id not in seen_users:
            seen_users.add(contact.user_id)
            targets.append(_AssigneeTarget("user", contact.user_id))
            continue
        if contact_id not in seen_contacts:
            seen_contacts.add(contact_id)
            targets.append(_AssigneeTarget("contact", contact_id))

    if not assignee_emails:
        return targets

    users = list(
        db.scalars(
            select(User).where(
                func.lower(User.email).in_(assignee_emails),
                User.organisation_id == org_id,
            )
        ).all()
    )
    user_by_email = {u.email.lower(): u for u in users}

    contacts = list(
        db.scalars(
            select(Contact).where(
                func.lower(Contact.email).in_(assignee_emails),
                Contact.organisation_id == org_id,
            )
        ).all()
    )
    contact_by_email = {c.email.lower(): c for c in contacts}

    missing: list[str] = []
    for email in assignee_emails:
        user = user_by_email.get(email)
        if user is not None:
            if user.id not in seen_users:
                seen_users.add(user.id)
                targets.append(_AssigneeTarget("user", user.id))
            continue

        contact = contact_by_email.get(email)
        if contact is not None:
            if contact.user_id is not None:
                if contact.user_id not in seen_users:
                    seen_users.add(contact.user_id)
                    targets.append(_AssigneeTarget("user", contact.user_id))
                continue
            if contact.id not in seen_contacts:
                seen_contacts.add(contact.id)
                targets.append(_AssigneeTarget("contact", contact.id))
            continue

        missing.append(email)

    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No team member or contact in your organisation for: {', '.join(missing)}",
        )

    return targets


def create_assignments(
    db: Session,
    *,
    training_id: int,
    assignee_emails: list[str] | None = None,
    assignee_user_ids: list[int] | None = None,
    assignee_contact_ids: list[int] | None = None,
    assigned_by_id: int,
    organisation_id: int,
) -> list[Assignment]:
    org_id = _require_org_id(organisation_id)

    training = db.get(Training, training_id)
    if training is None or training.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    targets = _resolve_assignee_targets(
        db,
        org_id=org_id,
        assignee_emails=assignee_emails or [],
        assignee_user_ids=assignee_user_ids or [],
        assignee_contact_ids=assignee_contact_ids or [],
    )
    if not targets:
        return []

    user_ids = [t.id for t in targets if t.kind == "user"]
    contact_ids = [t.id for t in targets if t.kind == "contact"]

    existing_users = set()
    if user_ids:
        existing_users = set(
            db.scalars(
                select(Assignment.assignee_user_id).where(
                    Assignment.training_id == training_id,
                    Assignment.assignee_user_id.in_(user_ids),
                )
            ).all()
        )

    existing_contacts = set()
    if contact_ids:
        existing_contacts = set(
            db.scalars(
                select(Assignment.assignee_contact_id).where(
                    Assignment.training_id == training_id,
                    Assignment.assignee_contact_id.in_(contact_ids),
                )
            ).all()
        )

    assigner = db.get(User, assigned_by_id)
    created: list[Assignment] = []
    for target in targets:
        if target.kind == "user":
            if target.id in existing_users:
                continue
            row = Assignment(
                training_id=training_id,
                assignee_user_id=target.id,
                assignee_contact_id=None,
                assigned_by_id=assigned_by_id,
                status="not_started",
            )
        else:
            if target.id in existing_contacts:
                continue
            row = Assignment(
                training_id=training_id,
                assignee_user_id=None,
                assignee_contact_id=target.id,
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
            detail="Assignment already exists for one or more assignees.",
        ) from None

    for row in created:
        db.refresh(row)
        _send_assignment_email(db, row, training, assigner)

    return created


def _send_assignment_email(db: Session, row: Assignment, training: Training, assigner: User | None) -> None:
    token_row = _create_magic_token(db, row.id)
    if not assigner:
        return

    if row.assignee_user_id is not None:
        assignee = db.get(User, row.assignee_user_id)
        if not assignee:
            return
        to_email = assignee.email
        employee_name = assignee.full_name
    elif row.assignee_contact_id is not None:
        contact = db.get(Contact, row.assignee_contact_id)
        if not contact:
            return
        to_email = contact.email
        employee_name = contact.name
    else:
        return

    magic_url = build_training_magic_link_url(token_row.token)
    due_label = None
    if row.due_date:
        due_label = row.due_date.strftime("%d %b %Y")
    send_training_magic_link_email(
        to_email=to_email,
        employee_name=employee_name or "there",
        training_title=training.title,
        assigned_by_name=assigner.full_name,
        magic_url=magic_url,
        due_date=due_label,
        link_valid_days=7,
    )


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
            joinedload(Assignment.assignee_contact),
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
    if status_value == "completed":
        _notify_manager_if_needed(db, assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def _notify_manager_if_needed(db: Session, assignment: Assignment) -> None:
    if assignment.manager_notified_at is not None:
        return
    manager = assignment.assigned_by or db.get(User, assignment.assigned_by_id)
    if assignment.assignee_user_id is not None:
        assignee = assignment.assignee or db.get(User, assignment.assignee_user_id)
        employee_name = assignee.full_name if assignee else "Assignee"
    elif assignment.assignee_contact_id is not None:
        contact = assignment.assignee_contact or db.get(Contact, assignment.assignee_contact_id)
        employee_name = contact.name if contact else "Assignee"
    else:
        employee_name = "Assignee"
    training = assignment.training or db.get(Training, assignment.training_id)
    if not (manager and training):
        return
    sent = send_manager_training_complete_email(
        to_email=manager.email,
        manager_name=manager.full_name,
        employee_name=employee_name,
        training_title=training.title,
    )
    if sent:
        assignment.manager_notified_at = datetime.now(timezone.utc)


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
            joinedload(TrainingToken.assignment).joinedload(Assignment.assignee_contact),
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
        _notify_manager_if_needed(db, assignment)

    db.commit()
    db.refresh(assignment)
    return assignment


def assignment_list_item_fields(assignment: Assignment) -> dict:
    return {
        "id": assignment.id,
        "training_id": assignment.training_id,
        "training_title": assignment.training.title,
        "training_description": assignment.training.description,
        "content_type": assignment.training.content_type,
        "youtube_video_id": assignment.training.youtube_video_id,
        "external_url": assignment.training.external_url,
        "storage_key": assignment.training.storage_key,
        "status": assignment.status,
        "started_at": assignment.started_at,
        "completed_at": assignment.completed_at,
        "due_date": assignment.due_date,
        "assignee_email": _assignment_assignee_email(assignment),
        "assignee_full_name": _assignment_assignee_name(assignment),
        "assignee_contact_id": assignment.assignee_contact_id,
        "assigned_by_full_name": assignment.assigned_by.full_name,
        "created_at": assignment.created_at,
    }
