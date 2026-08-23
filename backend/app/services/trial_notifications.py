from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Organisation, User
from app.services.email import send_trial_ending_email
from app.services.plan_access import (
    count_org_projects,
    count_org_tasks,
    has_paid_subscription,
    trial_days_remaining,
)
from app.services.plan_limits import is_on_trial


def check_and_send_trial_warning(db: Session, user: User) -> bool:
    """Email org admin once when trial ends within 3 days. Returns True if sent."""
    if user.role != "admin" or not user.organisation_id or user.do_not_email:
        return False

    org = db.get(Organisation, user.organisation_id)
    if org is None:
        return False
    if not is_on_trial(org) or has_paid_subscription(org):
        return False
    if org.trial_warning_sent_at is not None:
        return False

    days_left = trial_days_remaining(org)
    if days_left is None or days_left > 3 or days_left < 0:
        return False

    project_count = count_org_projects(db, org.id)
    task_count = count_org_tasks(db, org.id)

    sent = send_trial_ending_email(
        to_email=user.email,
        user_name=user.full_name,
        days_left=days_left,
        project_count=project_count,
        task_count=task_count,
    )
    if not sent:
        return False

    org.trial_warning_sent_at = datetime.now(timezone.utc)
    db.add(org)
    db.commit()
    return True
