"""Task due date/time helpers."""

from __future__ import annotations

from datetime import datetime

from app.models.models import Task
from app.services.timezones import now_in_timezone, resolve_timezone


def format_task_due(task: Task, *, tz_name: str | None = None) -> str:
    if not task.due_date:
        return "No due date"
    text = task.due_date.strftime("%d %b %Y")
    if task.due_time:
        text = f"{text} {task.due_time.strftime('%H:%M')}"
    if tz_name:
        from app.services.timezones import format_timezone_label

        text = f"{text} ({format_timezone_label(tz_name)})"
    return text


def is_task_overdue(task: Task, *, tz_name: str | None = None, now: datetime | None = None) -> bool:
    if (task.status or "").lower() in {"completed", "done", "cancelled"}:
        return False
    if task.due_date is None:
        return False

    now = now or now_in_timezone(tz_name)
    today = now.date()
    current_time = now.time().replace(tzinfo=None)

    if task.due_date < today:
        return True
    if task.due_date > today:
        return False
    if task.due_time is None:
        return False
    return task.due_time <= current_time
