"""Trial-ending warning email trigger."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.services.trial_notifications import check_and_send_trial_warning


def _user(*, role: str = "admin", do_not_email: bool = False) -> MagicMock:
    user = MagicMock()
    user.role = role
    user.organisation_id = 1
    user.do_not_email = do_not_email
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.email_unsubscribe_token = "unsub-token"
    return user


def _org(
    *,
    trial_days: float = 2,
    warning_sent: bool = False,
    paid: bool = False,
) -> MagicMock:
    org = MagicMock()
    org.id = 1
    org.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=trial_days)
    org.trial_warning_sent_at = datetime.now(timezone.utc) if warning_sent else None
    org.stripe_subscription_id = "sub_paid" if paid else None
    org.subscription_status = "active" if paid else None
    return org


@patch("app.services.trial_notifications.send_trial_ending_email", return_value=True)
@patch("app.services.trial_notifications.count_org_tasks", return_value=3)
@patch("app.services.trial_notifications.count_org_projects", return_value=1)
def test_trial_warning_sends_within_3_days(mock_projects, mock_tasks, mock_send):
    db = MagicMock()
    org = _org(trial_days=2)
    db.get.return_value = org
    user = _user()

    assert check_and_send_trial_warning(db, user) is True
    mock_send.assert_called_once()
    assert org.trial_warning_sent_at is not None
    kwargs = mock_send.call_args.kwargs
    assert kwargs["days_left"] <= 3
    assert kwargs["unsubscribe_token"] == "unsub-token"


@patch("app.services.trial_notifications.send_trial_ending_email")
def test_trial_warning_skips_when_already_sent(mock_send):
    db = MagicMock()
    db.get.return_value = _org(trial_days=2, warning_sent=True)
    assert check_and_send_trial_warning(db, _user()) is False
    mock_send.assert_not_called()


@patch("app.services.trial_notifications.send_trial_ending_email")
def test_trial_warning_skips_when_more_than_3_days(mock_send):
    db = MagicMock()
    db.get.return_value = _org(trial_days=10)
    assert check_and_send_trial_warning(db, _user()) is False
    mock_send.assert_not_called()


@patch("app.services.trial_notifications.send_trial_ending_email")
def test_trial_warning_skips_paid_subscription(mock_send):
    db = MagicMock()
    db.get.return_value = _org(trial_days=2, paid=True)
    assert check_and_send_trial_warning(db, _user()) is False
    mock_send.assert_not_called()
