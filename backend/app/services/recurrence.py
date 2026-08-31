from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta
from uuid import uuid4

ALLOWED_RECURRENCE = frozenset({"none", "weekly", "monthly"})
SERIES_LENGTH = 12

_WEEKLY_RE = re.compile(
    r"\b(every week|weekly|each week|every monday|every tuesday|every wednesday|"
    r"every thursday|every friday|every saturday|every sunday)\b",
    re.I,
)
_MONTHLY_RE = re.compile(r"\b(every month|monthly|each month)\b", re.I)


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def normalize_recurrence(value: str | None) -> str:
    key = (value or "none").strip().lower()
    if key not in ALLOWED_RECURRENCE:
        raise ValueError("Repeat must be none, weekly, or monthly.")
    return key


def occurrence_dates(start: date, recurrence: str, *, count: int = SERIES_LENGTH) -> list[date]:
    rec = normalize_recurrence(recurrence)
    if rec == "none":
        return [start]
    dates = [start]
    for i in range(1, count):
        if rec == "weekly":
            dates.append(start + timedelta(weeks=i))
        else:
            dates.append(add_months(start, i))
    return dates


def expand_series(due_date: date | None, recurrence: str | None) -> tuple[str, str | None, list[date | None]]:
    rec = normalize_recurrence(recurrence)
    if due_date is None or rec == "none":
        return "none", None, [due_date]
    return rec, str(uuid4()), occurrence_dates(due_date, rec)


def infer_recurrence(*, recurrence: str | None, title: str | None, description: str | None) -> str:
    try:
        rec = normalize_recurrence(recurrence) if recurrence else "none"
    except ValueError:
        rec = "none"
    if rec != "none":
        return rec
    text = f"{title or ''} {description or ''}"
    if _MONTHLY_RE.search(text):
        return "monthly"
    if _WEEKLY_RE.search(text):
        return "weekly"
    return "none"
