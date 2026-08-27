"""Due time parsing helpers."""

from app.services.due_times import parse_time_string, resolve_task_due_time


def test_parse_24h_time():
    assert parse_time_string("14:30").strftime("%H:%M") == "14:30"


def test_parse_ampm_time():
    assert parse_time_string("9am").strftime("%H:%M") == "09:00"
    assert parse_time_string("6:30 pm").strftime("%H:%M") == "18:30"


def test_resolve_from_title():
    assert resolve_task_due_time(due_time=None, title="Team standup at 9am Monday") == "09:00"
    assert resolve_task_due_time(due_time="15:00", title="Ignore this 6pm") == "15:00"
