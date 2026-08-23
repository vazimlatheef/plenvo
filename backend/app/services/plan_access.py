"""Organisation write access: active trial or paid subscription required."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.models import Organisation, Project, Task
from app.services.plan_limits import is_on_trial

PAYMENT_REQUIRED_STATUS = status.HTTP_402_PAYMENT_REQUIRED


def has_paid_subscription(org: Organisation) -> bool:
    if not org.stripe_subscription_id:
        return False
    status = (org.subscription_status or "active").strip().lower()
    return status not in ("canceled", "incomplete_expired", "unpaid")


def has_full_write_access(org: Organisation, *, now: datetime | None = None) -> bool:
    return has_paid_subscription(org) or is_on_trial(org, now=now)


def is_restricted(org: Organisation, *, now: datetime | None = None) -> bool:
    return not has_full_write_access(org, now=now)


def restriction_message(
    org: Organisation,
    *,
    project_count: int,
    task_count: int,
    on_trial: bool,
    has_paid: bool,
) -> str:
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
    restricted = is_restricted(org, now=now)
    project_count = count_org_projects(db, org.id)
    task_count = count_org_tasks(db, org.id)
    paid = has_paid_subscription(org)
    on_trial = is_on_trial(org, now=now)
    return {
        "has_full_write_access": not restricted,
        "restricted": restricted,
        "has_paid_subscription": paid,
        "on_trial": on_trial,
        "project_count": project_count,
        "task_count": task_count,
        "restriction_message": restriction_message(
            org,
            project_count=project_count,
            task_count=task_count,
            on_trial=on_trial,
            has_paid=paid,
        )
        if restricted
        else None,
    }


def assert_full_write_access(org: Organisation, *, now: datetime | None = None) -> None:
    if not is_restricted(org, now=now):
        return
    now = now or datetime.now(timezone.utc)
    # Counts are not available without db — use generic detail for API errors.
    raise HTTPException(
        status_code=PAYMENT_REQUIRED_STATUS,
        detail="Your trial has ended. Upgrade in Account & Subscription to keep creating and editing.",
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
