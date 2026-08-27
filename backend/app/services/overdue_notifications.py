from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, User
from app.services.email import send_overdue_tasks_email
from app.services.task_due import is_task_overdue


def check_and_send_overdue_notifications(db: Session, user: User) -> int:
    """Email newly overdue tasks once per task. Returns count notified."""
    if not user.overdue_email_enabled or user.do_not_email:
        return 0

    today = date.today()
    tasks = list(
        db.scalars(
            select(Task).where(
                Task.assignee_id == user.id,
                Task.overdue_notified_at.is_(None),
                Task.due_date.isnot(None),
                Task.status != "completed",
            )
        ).all()
    )
    newly_overdue = [t for t in tasks if is_task_overdue(t, tz_name=user.timezone)]
    if not newly_overdue:
        return 0

    sent = send_overdue_tasks_email(
        to_email=user.email,
        user_name=user.full_name,
        tasks=newly_overdue,
    )
    if not sent:
        return 0

    now = datetime.now(timezone.utc)
    for task in newly_overdue:
        task.overdue_notified_at = now
    db.commit()
    return len(newly_overdue)
