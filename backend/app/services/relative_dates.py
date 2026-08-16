"""Resolve relative due-date phrases to concrete calendar dates.

Used after AI extraction so "by Thursday", "tomorrow", "in 2 weeks", etc.
become ISO dates relative to extraction time — not left blank.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_ORDINAL_RE = re.compile(r"\b(\d{1,2})(st|nd|rd|th)\b", re.I)

# Leading noise often glued to date phrases in notes / model output.
_PREFIX_RE = re.compile(
    r"^(?:due|by|before|on|until|till|for|at|around|approx(?:imately)?)\s+",
    re.I,
)

_RELATIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:day\s+after\s+tomorrow)\b", re.I), "day_after_tomorrow"),
    (re.compile(r"\b(?:today)\b", re.I), "today"),
    (re.compile(r"\b(?:tomorrow|tmrw|tmr)\b", re.I), "tomorrow"),
    (re.compile(r"\b(?:yesterday)\b", re.I), "yesterday"),
    (re.compile(r"\b(?:end\s+of\s+(?:the\s+)?week|eow)\b", re.I), "end_of_week"),
    (re.compile(r"\b(?:end\s+of\s+(?:the\s+)?month|eom)\b", re.I), "end_of_month"),
    (re.compile(r"\b(?:in\s+a\s+week|next\s+week)\b", re.I), "in_one_week"),
    (re.compile(r"\b(?:in\s+two\s+weeks|in\s+2\s+weeks)\b", re.I), "in_two_weeks"),
    (
        re.compile(
            r"\b(?:in\s+(\d+)\s+(days?|weeks?|months?))\b",
            re.I,
        ),
        "in_n_units",
    ),
    (
        re.compile(
            r"\b(?:next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun))\b",
            re.I,
        ),
        "next_weekday",
    ),
    (
        re.compile(
            r"\b(?:this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun))\b",
            re.I,
        ),
        "this_weekday",
    ),
    (
        re.compile(
            r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b",
            re.I,
        ),
        "weekday",
    ),
]


def _next_weekday(today: date, target: int, *, force_next: bool = False) -> date:
    """Upcoming weekday. Includes today unless force_next."""
    delta = (target - today.weekday()) % 7
    if delta == 0 and force_next:
        delta = 7
    return today + timedelta(days=delta)


def _parse_iso(text: str) -> date | None:
    m = _ISO_RE.match(text.strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _resolve_token(kind: str, match: re.Match[str], today: date) -> date | None:
    if kind == "today":
        return today
    if kind == "tomorrow":
        return today + timedelta(days=1)
    if kind == "day_after_tomorrow":
        return today + timedelta(days=2)
    if kind == "yesterday":
        return today - timedelta(days=1)
    if kind == "end_of_week":
        # Friday of the current ISO week (Mon–Sun), or today if already weekend.
        days_to_fri = (4 - today.weekday()) % 7
        return today + timedelta(days=days_to_fri)
    if kind == "end_of_month":
        last = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, last)
    if kind == "in_one_week":
        return today + timedelta(days=7)
    if kind == "in_two_weeks":
        return today + timedelta(days=14)
    if kind == "in_n_units":
        n = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("day"):
            return today + timedelta(days=n)
        if unit.startswith("week"):
            return today + timedelta(weeks=n)
        if unit.startswith("month"):
            month = today.month - 1 + n
            year = today.year + month // 12
            month = month % 12 + 1
            day = min(today.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        return None
    if kind in {"next_weekday", "this_weekday", "weekday"}:
        name = match.group(1).lower()
        target = _WEEKDAYS.get(name)
        if target is None:
            return None
        force_next = kind == "next_weekday"
        return _next_weekday(today, target, force_next=force_next)
    return None


def resolve_relative_date(text: str | None, *, today: date | None = None) -> date | None:
    """Parse a due-date string that may be ISO or a relative phrase."""
    if not text:
        return None
    today = today or date.today()
    raw = str(text).strip()
    if not raw:
        return None

    iso = _parse_iso(raw)
    if iso:
        return iso

    cleaned = _PREFIX_RE.sub("", raw)
    cleaned = _ORDINAL_RE.sub(r"\1", cleaned)
    cleaned = cleaned.strip(" .,;:!?\"'")

    iso = _parse_iso(cleaned)
    if iso:
        return iso

    for pattern, kind in _RELATIVE_PATTERNS:
        m = pattern.search(cleaned)
        if not m:
            continue
        resolved = _resolve_token(kind, m, today)
        if resolved:
            return resolved
    return None


def resolve_task_due_date(
    *,
    due_date: str | None,
    title: str | None = None,
    description: str | None = None,
    today: date | None = None,
) -> str | None:
    """Return YYYY-MM-DD or None. Prefer explicit due_date, else scan title/description."""
    today = today or date.today()

    from_field = resolve_relative_date(due_date, today=today)
    if from_field:
        return from_field.isoformat()

    # Model sometimes leaves due_date null but embeds "by Friday" in the title.
    for blob in (title, description):
        if not blob:
            continue
        found = resolve_relative_date(blob, today=today)
        if found:
            return found.isoformat()
        # Also try after stripping common task verbs noise by scanning for known phrases only
        for pattern, kind in _RELATIVE_PATTERNS:
            m = pattern.search(str(blob))
            if not m:
                continue
            resolved = _resolve_token(kind, m, today)
            if resolved:
                return resolved.isoformat()

    return None
