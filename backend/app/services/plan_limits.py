"""Organisation team-member plan limits.

Enforced when adding members (contacts / users), not at signup.
Headcount = org Users + unlinked Contacts (linked contacts are already counted as users).
Trial uses the selected plan's real limits — not a blanket upgrade.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Contact, Organisation, User

# Max total headcount (Users + unlinked Contacts).
# personal = solo only (1 total member).
_PLAN_MEMBER_LIMITS: dict[str, int | None] = {
    "personal": 1,
    "team": 5,
    "enterprise": None,
}
_DEFAULT_TIER = "team"


def is_on_trial(org: Organisation, *, now: datetime | None = None) -> bool:
    if org.trial_ends_at is None:
        return False
    now = now or datetime.now(timezone.utc)
    ends = org.trial_ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    return ends > now


def member_limit_for_org(org: Organisation, *, now: datetime | None = None) -> int | None:
    """Return max headcount, or None for unlimited (enterprise)."""
    tier = (org.plan_tier or _DEFAULT_TIER).strip().lower()
    if tier not in _PLAN_MEMBER_LIMITS:
        tier = _DEFAULT_TIER
    return _PLAN_MEMBER_LIMITS[tier]


def count_team_members(db: Session, organisation_id: int) -> int:
    """Users in org + contacts not yet linked to a user."""
    users = (
        db.query(User)
        .filter(User.organisation_id == organisation_id)
        .count()
    )
    unlinked = (
        db.query(Contact)
        .filter(
            Contact.organisation_id == organisation_id,
            Contact.user_id.is_(None),
        )
        .count()
    )
    return int(users) + int(unlinked)


def plan_limit_message(org: Organisation, limit: int, *, now: datetime | None = None) -> str:
    tier = (org.plan_tier or _DEFAULT_TIER).strip().lower() or _DEFAULT_TIER
    trial_suffix = " trial" if is_on_trial(org, now=now) else ""
    if tier == "personal":
        shown = "1 member (solo — no additional team members)"
    elif limit is None:
        shown = "unlimited team members"
    else:
        shown = f"up to {limit} team members"
    return (
        f"Your {tier}{trial_suffix} plan allows {shown}. "
        "Upgrade in Account & Subscription to add more."
    )


def can_add_team_members(
    db: Session,
    org: Organisation,
    *,
    adding: int = 1,
    now: datetime | None = None,
) -> tuple[bool, int, int | None, str | None]:
    """Return (allowed, current_count, limit, error_message_if_blocked)."""
    if adding <= 0:
        current = count_team_members(db, org.id)
        limit = member_limit_for_org(org, now=now)
        return True, current, limit, None

    current = count_team_members(db, org.id)
    limit = member_limit_for_org(org, now=now)
    if limit is None:
        return True, current, None, None
    if current + adding > limit:
        return False, current, limit, plan_limit_message(org, limit, now=now)
    return True, current, limit, None


def assert_can_add_team_members(
    db: Session,
    org: Organisation,
    *,
    adding: int = 1,
    now: datetime | None = None,
) -> None:
    allowed, _current, _limit, message = can_add_team_members(
        db, org, adding=adding, now=now
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message or "Team member limit reached.",
        )


def team_limit_snapshot(db: Session, org: Organisation) -> dict:
    current = count_team_members(db, org.id)
    tier = (org.plan_tier or _DEFAULT_TIER).strip().lower()
    limit = member_limit_for_org(org)
    on_trial = is_on_trial(org)
    can_add = limit is None or current < limit
    return {
        "plan_tier": tier,
        "currency": (org.currency or "USD").strip().upper(),
        "on_trial": on_trial,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        "member_count": current,
        "member_limit": limit,
        "can_add_members": can_add,
        "limit_message": None
        if can_add or limit is None
        else plan_limit_message(org, limit),
    }
