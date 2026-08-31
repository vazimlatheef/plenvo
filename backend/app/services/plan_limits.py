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
TIER_RANK: dict[str, int] = {"personal": 0, "team": 1, "enterprise": 2}

TRIAL_DOWNGRADE_MESSAGE = (
    "You can upgrade anytime during your trial. To switch to a lower plan, "
    "wait until your trial ends or subscribe."
)


def tier_rank(tier: str | None) -> int:
    return TIER_RANK.get((tier or _DEFAULT_TIER).strip().lower(), 0)


def minimum_tier_for_member_count(count: int) -> str:
    if count <= 1:
        return "personal"
    if count <= 5:
        return "team"
    return "enterprise"


def minimum_tier_label(tier: str) -> str:
    labels = {"personal": "Personal", "team": "Team", "enterprise": "Enterprise"}
    return labels.get(tier, tier)


def trial_peak_member_count(org: Organisation, db: Session) -> int:
    current = count_team_members(db, org.id)
    stored = org.trial_peak_member_count or 1
    return max(stored, current)


def bump_trial_peak_member_count(db: Session, org: Organisation) -> None:
    """Raise stored peak headcount during an active trial after a successful member add."""
    if not is_on_trial(org):
        return
    current = count_team_members(db, org.id)
    peak = org.trial_peak_member_count or 1
    org.trial_peak_member_count = max(peak, current)
    db.add(org)


def assert_trial_plan_upgrade_only(org: Organisation, target_tier: str) -> None:
    if not is_on_trial(org):
        return
    current = (org.plan_tier or _DEFAULT_TIER).strip().lower()
    target = (target_tier or _DEFAULT_TIER).strip().lower()
    if tier_rank(target) < tier_rank(current):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=TRIAL_DOWNGRADE_MESSAGE,
        )


def assert_checkout_meets_minimum_tier(db: Session, org: Organisation, target_tier: str) -> None:
    peak = trial_peak_member_count(org, db)
    min_tier = minimum_tier_for_member_count(peak)
    target = (target_tier or _DEFAULT_TIER).strip().lower()
    if tier_rank(target) < tier_rank(min_tier):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Your trial peaked at {peak} team member{'s' if peak != 1 else ''}. "
                f"Minimum plan: {minimum_tier_label(min_tier)}."
            ),
        )


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
    label = {"personal": "Personal", "team": "Team", "enterprise": "Enterprise"}.get(tier, "this")
    if tier == "personal":
        return "Personal is for one person. Upgrade to Team to add members."
    if limit is None:
        return f"You've reached the member limit for the {label} plan."
    if is_on_trial(org, now=now):
        return (
            f"Your {label} trial includes up to {limit} members. "
            "Upgrade in Account to add more."
        )
    return f"Your {label} plan includes up to {limit} members. Upgrade in Account to add more."


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
        "trial_peak_member_count": trial_peak_member_count(org, db),
        "minimum_subscribable_tier": minimum_tier_for_member_count(trial_peak_member_count(org, db)),
        "member_count": current,
        "member_limit": limit,
        "can_add_members": can_add,
        "limit_message": None
        if can_add or limit is None
        else plan_limit_message(org, limit),
    }
