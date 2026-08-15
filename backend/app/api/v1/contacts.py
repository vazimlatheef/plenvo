from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.security import hash_password
from app.models.models import Contact, Organisation, User
from app.schemas.contact import ContactCreate, ContactInviteRequest, ContactResponse, ContactUpdate
from app.services.contact_service import link_contact_to_user
from app.services.email import generate_temp_password, generate_unsubscribe_token, send_invite_email

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    if not parts:
        return "Team", "Member"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _require_org(user: User) -> int:
    if user.organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")
    return user.organisation_id


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = _require_org(current_user)
    return (
        db.query(Contact)
        .filter(Contact.organisation_id == org_id)
        .order_by(Contact.name.asc())
        .all()
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    org_id = _require_org(current_user)
    email = str(payload.email).strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.organisation_id == org_id, User.email == email)
        .first()
    )

    contact = Contact(
        organisation_id=org_id,
        name=payload.name.strip(),
        email=email,
        role=payload.role,
        user_id=existing_user.id if existing_user else None,
    )
    db.add(contact)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists in your organisation.",
        ) from None

    db.refresh(contact)
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    org_id = _require_org(current_user)
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact or contact.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.name is not None:
        contact.name = payload.name.strip()
    if payload.role is not None:
        contact.role = payload.role
    if payload.email is not None:
        contact.email = str(payload.email).strip().lower()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists in your organisation.",
        ) from None

    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    org_id = _require_org(current_user)
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact or contact.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return None


@router.post("/{contact_id}/invite", response_model=ContactResponse)
def invite_contact(
    contact_id: int,
    payload: ContactInviteRequest = ContactInviteRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a Plenvo account for this contact (if needed) and email login credentials."""
    org_id = _require_org(current_user)
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact or contact.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if not current_user.team_size:
        if not payload.team_size:
            raise HTTPException(
                status_code=400,
                detail="team_size is required on your first invite.",
            )
        current_user.team_size = payload.team_size.strip()

    user = contact.user
    temp_password: str | None = None

    if user is None:
        existing = db.query(User).filter(User.email == contact.email).first()
        if existing:
            if existing.organisation_id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email already belongs to another Plenvo account.",
                )
            user = existing
            link_contact_to_user(db, contact, user)
            temp_password = generate_temp_password()
            user.password_hash = hash_password(temp_password)
            db.commit()
            db.refresh(user)
            db.refresh(contact)
        else:
            first_name, last_name = _split_name(contact.name)
            temp_password = generate_temp_password()
            user = User(
                organisation_id=org_id,
                email=contact.email,
                password_hash=hash_password(temp_password),
                first_name=first_name,
                last_name=last_name or "Member",
                role="employee",
                position=contact.role,
                company_name=current_user.company_name,
                email_unsubscribe_token=generate_unsubscribe_token(),
            )
            db.add(user)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists.",
                ) from None
            link_contact_to_user(db, contact, user)
            db.commit()
            db.refresh(user)
            db.refresh(contact)
    else:
        # Re-invite linked user with a fresh temporary password.
        temp_password = generate_temp_password()
        user.password_hash = hash_password(temp_password)
        contact.invited_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        db.refresh(contact)

    org = db.query(Organisation).filter_by(id=org_id).first()
    email_sent = send_invite_email(
        to_email=user.email,
        employee_name=contact.name or user.full_name,
        temp_password=temp_password,
        organisation_name=org.name if org else None,
    )
    if not email_sent:
        print(f"⚠️ Warning: Failed to send invite email to {user.email}")

    db.refresh(current_user)
    db.refresh(contact)
    return contact
