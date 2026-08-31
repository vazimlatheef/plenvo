from datetime import date

from app.services.recurrence import add_months, expand_series, infer_recurrence, occurrence_dates


def test_weekly_occurrences_start_on_given_monday():
    start = date(2026, 8, 31)  # Monday
    dates = occurrence_dates(start, "weekly", count=4)
    assert dates == [
        date(2026, 8, 31),
        date(2026, 9, 7),
        date(2026, 9, 14),
        date(2026, 9, 21),
    ]


def test_monthly_clamps_end_of_month():
    start = date(2026, 1, 31)
    assert add_months(start, 1) == date(2026, 2, 28)
    dates = occurrence_dates(start, "monthly", count=3)
    assert dates[0] == start
    assert dates[1] == date(2026, 2, 28)
    assert dates[2] == date(2026, 3, 31)


def test_expand_series_none_without_due_date():
    rec, series_id, dates = expand_series(None, "weekly")
    assert rec == "none"
    assert series_id is None
    assert dates == [None]


def test_infer_weekly_from_title():
    assert infer_recurrence(
        recurrence=None,
        title="Schedule weekly meeting on Monday at 9am for SKAO with Alex",
        description=None,
    ) == "weekly"
