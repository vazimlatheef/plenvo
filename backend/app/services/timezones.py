"""IANA timezone helpers for user-local dates and overdue checks."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "UTC"


def normalize_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    name = str(value).strip()
    if not name or len(name) > 64:
        return None
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return None
    return name


def resolve_timezone(value: str | None) -> str:
    return normalize_timezone(value) or DEFAULT_TIMEZONE


def now_in_timezone(tz_name: str | None) -> datetime:
    tz = ZoneInfo(resolve_timezone(tz_name))
    return datetime.now(tz)


def today_in_timezone(tz_name: str | None) -> date:
    return now_in_timezone(tz_name).date()


def format_timezone_label(tz_name: str | None) -> str:
    tz = resolve_timezone(tz_name)
    now = now_in_timezone(tz)
    offset = now.strftime("%z")
    if len(offset) == 5:
        offset = f"{offset[:3]}:{offset[3:]}"
    return f"{tz} (UTC{offset})"
