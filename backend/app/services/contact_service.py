"""Helpers for lightweight Contact records and linking to User accounts."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Contact, Task, User


def link_contact_to_user(db: Session, contact: Contact, user: User, *, mark_invited: bool = True) -> Contact:
    """Attach a User to a Contact and copy contact-assigned tasks onto the user.

    Task history carries over: assignee_contact_id stays; assignee_id is set so
    My Tasks / filters by user continue to work after signup/invite.
    """
    contact.user_id = user.id
    if mark_invited and contact.invited_at is None:
        contact.invited_at = datetime.now(timezone.utc)

    db.query(Task).filter(
        Task.assignee_contact_id == contact.id,
        Task.organisation_id == contact.organisation_id,
    ).update({Task.assignee_id: user.id}, synchronize_session=False)

    return contact


def find_org_contact_by_email(db: Session, organisation_id: int, email: str) -> Contact | None:
    return (
        db.query(Contact)
        .filter(
            Contact.organisation_id == organisation_id,
            Contact.email == email.strip().lower(),
        )
        .first()
    )


def find_unlinked_contact_for_user(db: Session, user: User) -> Contact | None:
    if not user.organisation_id:
        return None
    return (
        db.query(Contact)
        .filter(
            Contact.organisation_id == user.organisation_id,
            Contact.email == user.email.strip().lower(),
            Contact.user_id.is_(None),
        )
        .first()
    )
