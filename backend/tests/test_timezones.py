"""Timezone helpers and overdue checks."""

from datetime import date, time

from app.services.task_due import is_task_overdue
from app.services.timezones import normalize_timezone, now_in_timezone, today_in_timezone


def test_normalize_timezone_accepts_iana():
    assert normalize_timezone("Europe/London") == "Europe/London"
    assert normalize_timezone("Not/AZone") is None


def test_today_in_london():
    # Smoke: returns a date without raising.
    assert isinstance(today_in_timezone("Europe/London"), date)


def test_timed_task_overdue_in_user_timezone():
    class Task:
        status = "pending"
        due_date = date(2026, 1, 15)
        due_time = time(9, 0)

    tz = "Europe/London"
    # 2026-01-15 10:00 in London
    now = now_in_timezone(tz).replace(year=2026, month=1, day=15, hour=10, minute=0, second=0, microsecond=0)
    assert is_task_overdue(Task(), tz_name=tz, now=now) is True

    early = now.replace(hour=8, minute=30)
    assert is_task_overdue(Task(), tz_name=tz, now=early) is False


def test_date_only_not_overdue_on_due_day():
    class Task:
        status = "pending"
        due_date = date(2026, 1, 15)
        due_time = None

    tz = "Europe/London"
    now = now_in_timezone(tz).replace(year=2026, month=1, day=15, hour=23, minute=0, second=0, microsecond=0)
    assert is_task_overdue(Task(), tz_name=tz, now=now) is False
