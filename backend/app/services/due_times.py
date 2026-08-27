"""Parse optional due-time phrases from AI output and note text."""

from __future__ import annotations

import re
from datetime import time

_TIME_24H = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
_TIME_HMM_AMPM = re.compile(r"\b(1[0-2]|0?[1-9]):([0-5]\d)\s*([ap]\.?m\.?)\b", re.I)
_TIME_H_AMPM = re.compile(r"\b(1[0-2]|0?[1-9])\s*([ap]\.?m\.?)\b", re.I)
_AT_TIME = re.compile(
    r"\b(?:at|@)\s*((?:1[0-2]|0?[1-9])(?::[0-5]\d)?\s*[ap]\.?m\.?|(?:[01]?\d|2[0-3]):[0-5]\d)\b",
    re.I,
)


def _to_time(hour: int, minute: int) -> time | None:
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return time(hour=hour, minute=minute)


def _ampm_hour(hour: int, meridiem: str) -> int:
    m = meridiem.lower().replace(".", "")
    if m.startswith("p"):
        return 12 if hour == 12 else hour + 12
    return 0 if hour == 12 else hour


def parse_time_string(value: str | None) -> time | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", raw)
    if m:
        return _to_time(int(m.group(1)), int(m.group(2)))

    m = _TIME_HMM_AMPM.search(raw)
    if m:
        return _to_time(_ampm_hour(int(m.group(1)), m.group(3)), int(m.group(2)))

    m = _TIME_H_AMPM.search(raw)
    if m:
        return _to_time(_ampm_hour(int(m.group(1)), m.group(2)), 0)

    m = _TIME_24H.search(raw)
    if m:
        return _to_time(int(m.group(1)), int(m.group(2)))

    return None


def resolve_task_due_time(
    *,
    due_time: str | None,
    title: str | None = None,
    description: str | None = None,
) -> str | None:
    """Return HH:MM or None. Prefer explicit due_time, else scan title/description."""
    parsed = parse_time_string(due_time)
    if parsed:
        return parsed.strftime("%H:%M")

    for blob in (title, description):
        if not blob:
            continue
        at = _AT_TIME.search(str(blob))
        if at:
            parsed = parse_time_string(at.group(1))
            if parsed:
                return parsed.strftime("%H:%M")
        parsed = parse_time_string(str(blob))
        if parsed:
            return parsed.strftime("%H:%M")

    return None
