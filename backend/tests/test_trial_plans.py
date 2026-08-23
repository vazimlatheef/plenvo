"""Trial plan limits and signup plan selection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.core.pricing import resolve_signup_plan_tier
from app.services.plan_limits import is_on_trial, member_limit_for_org


def _org(plan_tier: str = "team", *, trial_days: int = 14) -> MagicMock:
    org = MagicMock()
    org.plan_tier = plan_tier
    org.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=trial_days)
    return org


def test_resolve_signup_plan_from_pricing_card():
    assert resolve_signup_plan_tier("personal") == "personal"
    assert resolve_signup_plan_tier("enterprise") == "enterprise"


def test_resolve_signup_plan_generic_defaults_team():
    assert resolve_signup_plan_tier(None) == "team"
    assert resolve_signup_plan_tier("") == "team"
    assert resolve_signup_plan_tier("invalid") == "team"


def test_personal_trial_member_limit_is_one():
    org = _org("personal")
    assert is_on_trial(org)
    assert member_limit_for_org(org) == 1


def test_team_trial_member_limit_is_five():
    org = _org("team")
    assert member_limit_for_org(org) == 5


def test_enterprise_trial_member_limit_unlimited():
    org = _org("enterprise")
    assert member_limit_for_org(org) is None


def test_paid_team_not_on_trial_still_five():
    org = _org("team", trial_days=-1)
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    assert not is_on_trial(org)
    assert member_limit_for_org(org) == 5
