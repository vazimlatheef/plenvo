"""Plan write-access enforcement after trial expiry."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.plan_access import (
    assert_full_write_access,
    has_full_write_access,
    is_restricted,
    plan_access_snapshot,
)


def _org(
    *,
    plan_tier: str = "team",
    trial_days: int = 14,
    stripe_subscription_id: str | None = None,
    subscription_status: str | None = None,
) -> MagicMock:
    org = MagicMock()
    org.id = 1
    org.plan_tier = plan_tier
    now = datetime.now(timezone.utc)
    org.trial_ends_at = now + timedelta(days=trial_days)
    org.stripe_subscription_id = stripe_subscription_id
    org.subscription_status = subscription_status
    return org


def test_active_trial_has_full_write_access():
    org = _org(trial_days=10)
    assert has_full_write_access(org) is True
    assert is_restricted(org) is False
    assert_full_write_access(org)


def test_expired_trial_without_payment_is_restricted():
    org = _org(trial_days=-1)
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    assert has_full_write_access(org) is False
    assert is_restricted(org) is True
    with pytest.raises(HTTPException) as exc:
        assert_full_write_access(org)
    assert exc.value.status_code == 402


def test_expired_trial_with_paid_subscription_has_full_access():
    org = _org(trial_days=-1, stripe_subscription_id="sub_123", subscription_status="active")
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    assert has_full_write_access(org) is True
    assert is_restricted(org) is False
    assert_full_write_access(org)


def test_plan_access_snapshot_marks_restricted_with_counts():
    org = _org(trial_days=-1)
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=2)
    db = MagicMock()
    db.scalar.side_effect = [3, 12]

    snap = plan_access_snapshot(db, org)
    assert snap["restricted"] is True
    assert snap["has_full_write_access"] is False
    assert snap["project_count"] == 3
    assert snap["task_count"] == 12
    assert "3 projects" in snap["restriction_message"]
    assert "12 tasks" in snap["restriction_message"]
