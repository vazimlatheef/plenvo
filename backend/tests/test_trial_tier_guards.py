"""Trial tier guards: block downgrades during trial, enforce minimum tier at checkout."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.models import Contact, Organisation, User
from app.services.plan_limits import (
    TRIAL_DOWNGRADE_MESSAGE,
    bump_trial_peak_member_count,
    minimum_tier_for_member_count,
)
from app.services.stripe_billing import create_checkout_session


def _seed_trial_org(
    db,
    *,
    plan_tier: str = "enterprise",
    trial_days: int = 7,
    peak: int = 1,
    extra_contacts: int = 0,
) -> dict:
    org = Organisation(
        id=1,
        name="Acme",
        slug="acme",
        plan_tier=plan_tier,
        currency="USD",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=trial_days),
        trial_peak_member_count=peak,
    )
    db.add(org)
    db.flush()

    admin = User(
        id=1,
        organisation_id=org.id,
        email="admin@acme.com",
        password_hash="hashed",
        first_name="Admin",
        last_name="User",
        role="admin",
    )
    db.add(admin)
    db.flush()

    contacts = []
    for i in range(extra_contacts):
        contact = Contact(
            id=i + 1,
            organisation_id=org.id,
            name=f"Contact {i}",
            email=f"contact{i}@acme.com",
        )
        db.add(contact)
        contacts.append(contact)
    db.commit()
    for obj in (org, admin, *contacts):
        db.refresh(obj)
    return {"org": org, "admin": admin, "contacts": contacts}


def test_minimum_tier_for_member_count():
    assert minimum_tier_for_member_count(1) == "personal"
    assert minimum_tier_for_member_count(2) == "team"
    assert minimum_tier_for_member_count(5) == "team"
    assert minimum_tier_for_member_count(6) == "enterprise"


def test_bump_trial_peak_member_count(db):
    data = _seed_trial_org(db, plan_tier="team", peak=1, extra_contacts=2)
    org = data["org"]
    bump_trial_peak_member_count(db, org)
    db.commit()
    db.refresh(org)
    assert org.trial_peak_member_count == 3


def test_active_trial_downgrade_blocked_with_six_members(db, stripe_test_env):
    data = _seed_trial_org(db, plan_tier="enterprise", peak=6, extra_contacts=5)
    org = data["org"]
    admin = data["admin"]

    with pytest.raises(HTTPException) as exc:
        create_checkout_session(db, org=org, admin=admin, plan="team")
    assert exc.value.status_code == 403
    assert exc.value.detail == TRIAL_DOWNGRADE_MESSAGE
    db.refresh(org)
    assert org.plan_tier == "enterprise"


def test_active_trial_upgrade_allowed(db, stripe_test_env):
    data = _seed_trial_org(db, plan_tier="personal", peak=1)
    org = data["org"]
    admin = data["admin"]

    result = create_checkout_session(db, org=org, admin=admin, plan="team")
    assert result["updated"] is True
    assert result["plan_tier"] == "team"
    db.refresh(org)
    assert org.plan_tier == "team"


@patch("app.services.stripe_billing.stripe.checkout.Session.create")
def test_expired_trial_personal_checkout_blocked_peak_four(mock_session_create, db, stripe_test_env):
    data = _seed_trial_org(db, plan_tier="team", trial_days=-1, peak=4, extra_contacts=3)
    org = data["org"]
    admin = data["admin"]
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    org.stripe_customer_id = "cus_test"
    db.add(org)
    db.commit()
    db.refresh(org)

    with pytest.raises(HTTPException) as exc:
        create_checkout_session(db, org=org, admin=admin, plan="personal")
    assert exc.value.status_code == 400
    assert "4" in exc.value.detail
    assert "Team" in exc.value.detail
    mock_session_create.assert_not_called()


@patch("app.services.stripe_billing.stripe.checkout.Session.create")
def test_expired_trial_team_checkout_allowed_peak_four(mock_session_create, db, stripe_test_env):
    data = _seed_trial_org(db, plan_tier="team", trial_days=-1, peak=4, extra_contacts=3)
    org = data["org"]
    admin = data["admin"]
    org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    org.stripe_customer_id = "cus_test"
    db.add(org)
    db.commit()
    db.refresh(org)

    mock_session_create.return_value = MagicMock(url="https://checkout.stripe.test/team")
    result = create_checkout_session(db, org=org, admin=admin, plan="team")
    assert result["url"] == "https://checkout.stripe.test/team"
    mock_session_create.assert_called_once()
