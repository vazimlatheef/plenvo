from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Assignment, Contact, Note, Project, Task, Training, User


def _reassign_owned_records(db: Session, *, from_user_id: int, to_user_id: int) -> None:
    db.query(Task).filter(Task.created_by_id == from_user_id).update(
        {Task.created_by_id: to_user_id}, synchronize_session=False
    )
    db.query(Task).filter(Task.assignee_id == from_user_id).update(
        {Task.assignee_id: None}, synchronize_session=False
    )
    db.query(Note).filter(Note.created_by_id == from_user_id).update(
        {Note.created_by_id: to_user_id}, synchronize_session=False
    )
    db.query(Project).filter(Project.manager_id == from_user_id).update(
        {Project.manager_id: to_user_id}, synchronize_session=False
    )
    db.query(Training).filter(Training.created_by_id == from_user_id).update(
        {Training.created_by_id: to_user_id}, synchronize_session=False
    )
    db.query(Assignment).filter(Assignment.assigned_by_id == from_user_id).update(
        {Assignment.assigned_by_id: to_user_id}, synchronize_session=False
    )


def remove_team_member(
    db: Session,
    *,
    org_id: int,
    admin: User,
    contact_id: int | None = None,
    user_id: int | None = None,
) -> None:
    """Remove a contact and/or employee account from the organisation."""
    if admin.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed.")

    contact = None
    target_user = None

    if contact_id is not None:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or contact.organisation_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found.")
        if contact.user_id:
            target_user = db.get(User, contact.user_id)

    if user_id is not None:
        target_user = db.get(User, user_id)
        if not target_user or target_user.organisation_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found.")
        if contact is None:
            contact = (
                db.query(Contact)
                .filter(Contact.organisation_id == org_id, Contact.user_id == target_user.id)
                .first()
            )

    if target_user is not None:
        if target_user.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own account.",
            )
        if target_user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin accounts cannot be removed from the team.",
            )
        _reassign_owned_records(db, from_user_id=target_user.id, to_user_id=admin.id)

    if contact is not None:
        db.delete(contact)
        db.flush()

    if target_user is not None:
        db.delete(target_user)

    db.commit()
