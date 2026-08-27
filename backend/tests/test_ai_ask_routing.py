"""Ask-query routing heuristics for Plenvo Brief."""

from app.api.v1.ai import is_ask_query


def test_team_status_queries_are_ask_mode():
    assert is_ask_query("How is my team doing?")
    assert is_ask_query("What's overdue this week?")


def test_focus_queries_are_ask_mode():
    assert is_ask_query("What should I focus on today?")
    assert is_ask_query("What's coming up this week?")


def test_note_dump_is_not_ask_mode():
    assert not is_ask_query(
        "Standup 9am Monday. API docs due Thursday — high priority."
    )
