"""Seat-limit downgrade guards and over-capacity write access."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.models import Contact, Organisation, User
from app.services.plan_access import assert_full_write_access, has_full_write_access, is_restricted
from app.services.plan_limits import (
    assert_checkout_meets_minimum_tier,
    assert_target_plan_fits_members,
    is_over_member_limit,
)


def _seed_over_capacity_paid(db) -> Organisation:
    org = Organisation(
        id=50,
        name="Busy Co",
        slug="busy-co",
        plan_tier="personal",
        currency="GBP",
        stripe_customer_id="cus_busy",
        stripe_subscription_id="sub_busy",
        subscription_status="active",
        trial_ends_at=None,
    )
    db.add(org)
    db.flush()

    admin = User(
        id=50,
        organisation_id=org.id,
        email="admin@busy.com",
        password_hash="hashed",
        first_name="Admin",
        last_name="Busy",
        role="admin",
    )
    db.add(admin)
    for i in range(4):
        db.add(
            Contact(
                id=i + 1,
                organisation_id=org.id,
                name=f"Member {i}",
                email=f"m{i}@busy.com",
                role="Team Member",
            )
        )
    db.commit()
    db.refresh(org)
    return org


def test_downgrade_blocked_when_over_target_seat_limit(db):
    org = _seed_over_capacity_paid(db)
    # 1 admin + 4 contacts = 5 → Team ok, Personal not
    assert_target_plan_fits_members(db, org, "team")
    with pytest.raises(HTTPException) as exc:
        assert_target_plan_fits_members(db, org, "personal")
    assert exc.value.status_code == 400
    assert "Remove" in str(exc.value.detail)


def test_checkout_minimum_tier_uses_current_headcount(db):
    org = _seed_over_capacity_paid(db)
    with pytest.raises(HTTPException) as exc:
        assert_checkout_meets_minimum_tier(db, org, "personal")
    assert exc.value.status_code == 400


def test_paid_over_limit_blocks_write_access(db):
    org = _seed_over_capacity_paid(db)
    assert is_over_member_limit(db, org) is True
    assert has_full_write_access(org) is True  # without db: paid still looks open
    assert has_full_write_access(org, db=db) is False
    assert is_restricted(org, db=db) is True
    with pytest.raises(HTTPException) as exc:
        assert_full_write_access(org, db=db)
    assert exc.value.status_code == 402
    assert "Remove" in str(exc.value.detail)
