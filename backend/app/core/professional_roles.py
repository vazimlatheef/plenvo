"""Shared professional role labels for user profiles and contacts."""

from __future__ import annotations

PROFESSIONAL_ROLES: tuple[str, ...] = (
    "CEO",
    "CFO",
    "COO",
    "Division Head",
    "Manager",
    "Project Manager",
    "Team Member",
    "Individual Contributor",
    "Other",
)

OTHER_ROLE = "Other"
DEFAULT_ROLE = "Team Member"

LEGACY_CONTACT_ROLE_MAP: dict[str, str] = {
    "Member": "Team Member",
    "Manager": "Manager",
    "Contractor": "Individual Contributor",
    "Client": "Other",
    "Other": "Other",
}


def is_professional_role(value: str | None) -> bool:
    return value in PROFESSIONAL_ROLES


def resolve_professional_role(role: str | None, role_other: str | None = None) -> str | None:
    """Return the label shown in UI and stored on user.job_title when saved."""
    if not role:
        return None
    if role == OTHER_ROLE:
        custom = (role_other or "").strip()
        return custom or OTHER_ROLE
    return role


def normalise_contact_role(role: str | None, role_other: str | None = None) -> tuple[str, str | None]:
    """Validate role + optional other text for contacts."""
    value = (role or DEFAULT_ROLE).strip()
    if value in LEGACY_CONTACT_ROLE_MAP:
        value = LEGACY_CONTACT_ROLE_MAP[value]
    if value not in PROFESSIONAL_ROLES:
        raise ValueError(f"Invalid role. Choose one of: {', '.join(PROFESSIONAL_ROLES)}")
    other = (role_other or "").strip() or None
    if value == OTHER_ROLE and not other:
        return value, None
    if value != OTHER_ROLE:
        other = None
    return value, other
