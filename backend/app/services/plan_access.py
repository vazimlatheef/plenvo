"""Organisation write access: active trial or paid subscription required.

Also blocks general writes when the org is over its plan seat limit
(member removal remains allowed so admins can recover).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.models import Organisation, Project, Task
from app.services.plan_limits import (
    is_on_trial,
    is_over_member_limit,
    over_member_limit_message,
)

PAYMENT_REQUIRED_STATUS = status.HTTP_402_PAYMENT_REQUIRED


# Statuses that mean the card/subscription is not in good standing.
_PAID_BLOCKED_STATUSES = frozenset(
    {
        "canceled",
        "incomplete",
        "incomplete_expired",
        "past_due",
        "unpaid",
        "paused",
    }
)


def has_paid_subscription(org: Organisation) -> bool:
    """True when Stripe sub exists and is billable (active/trialing).

    ``past_due`` / ``incomplete`` / ``unpaid`` are not treated as paid so
    write access restricts until payment recovers (HTTP 402).
    """
    if not org.stripe_subscription_id:
        return False
    status = (org.subscription_status or "active").strip().lower()
    return status not in _PAID_BLOCKED_STATUSES


def has_full_write_access(
    org: Organisation,
    *,
    db: Session | None = None,
    now: datetime | None = None,
) -> bool:
    if not (has_paid_subscription(org) or is_on_trial(org, now=now)):
        return False
    if db is not None and is_over_member_limit(db, org):
        return False
    return True


def is_restricted(
    org: Organisation,
    *,
    db: Session | None = None,
    now: datetime | None = None,
) -> bool:
    return not has_full_write_access(org, db=db, now=now)


def restriction_message(
    org: Organisation,
    *,
    project_count: int,
    task_count: int,
    on_trial: bool,
    has_paid: bool,
    over_member_limit: bool = False,
    over_member_detail: str | None = None,
) -> str:
    if over_member_limit and over_member_detail:
        return over_member_detail
    if org.trial_ends_at is not None and not on_trial and not has_paid:
        lead = "Your trial ended"
    else:
        lead = "Your subscription ended"
    return (
        f"{lead} — you have {project_count} projects and {task_count} tasks waiting. "
        "Upgrade to keep creating and editing."
    )


def count_org_projects(db: Session, organisation_id: int) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(Project).where(Project.organisation_id == organisation_id)
        )
        or 0
    )


def count_org_tasks(db: Session, organisation_id: int) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(Task).where(Task.organisation_id == organisation_id)
        )
        or 0
    )


def plan_access_snapshot(db: Session, org: Organisation, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    paid = has_paid_subscription(org)
    on_trial = is_on_trial(org, now=now)
    over_limit = is_over_member_limit(db, org)
    # Seat message only when billing is otherwise OK (paid/trial); expired/canceled
    # should keep the subscription/trial-ended copy.
    seat_blocked = over_limit and (paid or on_trial)
    restricted = is_restricted(org, db=db, now=now)
    project_count = count_org_projects(db, org.id)
    task_count = count_org_tasks(db, org.id)
    over_detail = over_member_limit_message(db, org) if seat_blocked else None
    return {
        "has_full_write_access": not restricted,
        "restricted": restricted,
        "has_paid_subscription": paid,
        "on_trial": on_trial,
        "over_member_limit": over_limit,
        "project_count": project_count,
        "task_count": task_count,
        "restriction_message": restriction_message(
            org,
            project_count=project_count,
            task_count=task_count,
            on_trial=on_trial,
            has_paid=paid,
            over_member_limit=seat_blocked,
            over_member_detail=over_detail,
        )
        if restricted
        else None,
    }


def assert_full_write_access(
    org: Organisation,
    *,
    db: Session | None = None,
    now: datetime | None = None,
) -> None:
    if not (has_paid_subscription(org) or is_on_trial(org, now=now)):
        raise HTTPException(
            status_code=PAYMENT_REQUIRED_STATUS,
            detail="Your trial has ended. Upgrade in Account & Subscription to keep creating and editing.",
        )
    if db is not None and is_over_member_limit(db, org):
        raise HTTPException(
            status_code=PAYMENT_REQUIRED_STATUS,
            detail=over_member_limit_message(db, org),
        )


def trial_days_remaining(org: Organisation, *, now: datetime | None = None) -> int | None:
    if org.trial_ends_at is None:
        return None
    now = now or datetime.now(timezone.utc)
    ends = org.trial_ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    if ends <= now:
        return 0
    return max(0, math.ceil((ends - now).total_seconds() / 86400))
