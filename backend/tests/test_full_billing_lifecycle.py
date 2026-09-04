"""End-to-end billing / subscription / tier-transition pipeline audit.

Covers signup→trial, paid upgrades/downgrades, payment failure, cancellation,
seat recovery, webhook edge cases (idempotency, missing refs, currency safety).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.organisations import TRIAL_DAYS
from app.core.pricing import resolve_currency_from_country
from app.models.models import Contact, Organisation, User
from app.services.plan_access import (
    assert_full_write_access,
    has_full_write_access,
    has_paid_subscription,
    is_restricted,
)
from app.services.plan_limits import count_team_members, team_limit_snapshot
from app.services.stripe_billing import (
    create_checkout_session,
    handle_checkout_completed,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
    handle_subscription_updated,
)
from app.services.team_members import remove_team_member


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sub(
    *,
    sub_id: str,
    org_id: int,
    plan_tier: str,
    price_id: str,
    status: str = "active",
    customer: str | None = "cus_full",
    cancel_at_period_end: bool = False,
) -> dict:
    return {
        "id": sub_id,
        "status": status,
        "customer": customer,
        "cancel_at_period_end": cancel_at_period_end,
        "current_period_end": int(_now().timestamp()) + 86400 * 30,
        "metadata": {"organisation_id": str(org_id), "plan_tier": plan_tier},
        "items": {"data": [{"id": "si_full", "price": {"id": price_id}}]},
    }


def _seed_trial(
    db,
    *,
    org_id: int = 100,
    plan: str = "team",
    currency: str = "GBP",
    country: str | None = None,
) -> dict:
    if country:
        currency = resolve_currency_from_country(country)
    trial_ends = _now() + timedelta(days=TRIAL_DAYS)
    org = Organisation(
        id=org_id,
        name=f"Org {org_id}",
        slug=f"org-{org_id}",
        plan_tier=plan,
        currency=currency,
        trial_ends_at=trial_ends,
        trial_peak_member_count=1,
    )
    db.add(org)
    db.flush()
    admin = User(
        id=org_id,
        organisation_id=org.id,
        email=f"admin{org_id}@plenvo.test",
        password_hash="hashed",
        first_name="Admin",
        last_name="User",
        role="admin",
        country=(country or None),
    )
    db.add(admin)
    db.commit()
    db.refresh(org)
    db.refresh(admin)
    return {"org": org, "admin": admin, "trial_ends": trial_ends}


def _seed_paid(
    db,
    *,
    org_id: int = 200,
    plan: str = "enterprise",
    currency: str = "USD",
    extra_contacts: int = 0,
    sub_id: str = "sub_paid",
    customer: str = "cus_paid",
) -> dict:
    org = Organisation(
        id=org_id,
        name=f"Paid {org_id}",
        slug=f"paid-{org_id}",
        plan_tier=plan,
        currency=currency,
        stripe_customer_id=customer,
        stripe_subscription_id=sub_id,
        subscription_status="active",
        trial_ends_at=None,
        trial_peak_member_count=max(1, 1 + extra_contacts),
    )
    db.add(org)
    db.flush()
    admin = User(
        id=org_id,
        organisation_id=org.id,
        email=f"paid{org_id}@plenvo.test",
        password_hash="hashed",
        first_name="Paid",
        last_name="Admin",
        role="admin",
    )
    db.add(admin)
    contacts = []
    for i in range(extra_contacts):
        c = Contact(
            id=org_id * 100 + i,
            organisation_id=org.id,
            name=f"Member {i}",
            email=f"m{i}.{org_id}@plenvo.test",
        )
        db.add(c)
        contacts.append(c)
    db.commit()
    db.refresh(org)
    db.refresh(admin)
    return {"org": org, "admin": admin, "contacts": contacts}


# ---------------------------------------------------------------------------
# 1. Signup → Trial
# ---------------------------------------------------------------------------


def test_signup_trial_locks_currency_and_grants_write_access(db):
    data = _seed_trial(db, country="GB", plan="team")
    org = data["org"]

    assert org.currency == "GBP"
    assert org.plan_tier == "team"
    assert org.stripe_subscription_id is None
    assert org.trial_ends_at is not None
    ends = org.trial_ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    remaining = (ends - _now()).total_seconds()
    assert 13 * 86400 < remaining <= 14 * 86400
    assert has_full_write_access(org, db=db) is True
    assert is_restricted(org, db=db) is False
    assert_full_write_access(org, db=db)

    snap = team_limit_snapshot(db, org)
    assert snap["on_trial"] is True
    assert snap["currency"] == "GBP"
    assert snap["member_limit"] == 5


def test_signup_eurozone_locks_eur(db):
    data = _seed_trial(db, org_id=101, country="DE", plan="personal")
    assert data["org"].currency == "EUR"
    assert has_full_write_access(data["org"], db=db) is True


# ---------------------------------------------------------------------------
# 2. Trial → Paid via Checkout webhook
# ---------------------------------------------------------------------------


@patch("app.services.stripe_billing.send_subscription_thank_you_email", return_value=True)
@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
@patch("app.services.stripe_billing.stripe.checkout.Session.create")
def test_trial_to_paid_checkout_webhook(
    mock_session_create,
    mock_sub_retrieve,
    _mock_email,
    db,
    stripe_test_env,
):
    data = _seed_trial(db, org_id=110, plan="personal", currency="GBP")
    org, admin = data["org"], data["admin"]
    org.stripe_customer_id = "cus_trial_pay"
    db.add(org)
    db.commit()

    mock_session_create.return_value = MagicMock(url="https://checkout.stripe.test/pay")
    result = create_checkout_session(db, org=org, admin=admin, plan="team", subscribe=True)
    assert result["url"]
    kwargs = mock_session_create.call_args.kwargs
    assert kwargs["currency"] == "gbp"
    assert kwargs["client_reference_id"] == str(org.id)
    assert kwargs["metadata"]["currency"] == "gbp"

    mock_sub_retrieve.return_value = _sub(
        sub_id="sub_from_trial",
        org_id=org.id,
        plan_tier="team",
        price_id="price_team_test",
        customer="cus_trial_pay",
    )
    handle_checkout_completed(
        db,
        {
            "metadata": {"organisation_id": str(org.id), "plan_tier": "team", "currency": "gbp"},
            "subscription": "sub_from_trial",
            "customer": "cus_trial_pay",
            "client_reference_id": str(org.id),
        },
    )
    db.refresh(org)

    assert org.stripe_subscription_id == "sub_from_trial"
    assert org.subscription_status == "active"
    assert org.plan_tier == "team"
    assert org.trial_ends_at is None
    assert org.currency == "GBP"  # locked; webhook currency ignored
    assert has_paid_subscription(org) is True
    assert has_full_write_access(org, db=db) is True


# ---------------------------------------------------------------------------
# 3. Mid-cycle upgrades Personal → Team → Enterprise
# ---------------------------------------------------------------------------


@patch("app.services.stripe_billing.stripe.Subscription.modify")
@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
def test_midcycle_plan_upgrades_increase_seat_limits(
    mock_retrieve,
    mock_modify,
    db,
    stripe_test_env,
):
    data = _seed_paid(db, org_id=210, plan="personal", extra_contacts=0, sub_id="sub_up")
    org, admin = data["org"], data["admin"]

    for target, price, limit in (
        ("team", "price_team_test", 5),
        ("enterprise", "price_enterprise_test", None),
    ):
        mock_retrieve.return_value = _sub(
            sub_id="sub_up",
            org_id=org.id,
            plan_tier=org.plan_tier,
            price_id=f"price_{org.plan_tier}_test",
        )
        mock_modify.return_value = _sub(
            sub_id="sub_up",
            org_id=org.id,
            plan_tier=target,
            price_id=price,
        )
        result = create_checkout_session(db, org=org, admin=admin, plan=target)
        assert result["updated"] is True
        kwargs = mock_modify.call_args.kwargs
        assert kwargs["proration_behavior"] == "create_prorations"
        assert "currency" not in kwargs
        db.refresh(org)
        assert org.plan_tier == target
        snap = team_limit_snapshot(db, org)
        assert snap["member_limit"] == limit
        assert has_full_write_access(org, db=db) is True


# ---------------------------------------------------------------------------
# 4–5. Downgrade over-capacity reject / under-capacity success
# ---------------------------------------------------------------------------


@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
def test_downgrade_over_capacity_rejects_http_400(mock_retrieve, db, stripe_test_env):
    # 1 admin + 5 contacts = 6 → Team limit 5
    data = _seed_paid(db, org_id=220, plan="enterprise", extra_contacts=5, sub_id="sub_ent")
    org, admin = data["org"], data["admin"]
    mock_retrieve.return_value = _sub(
        sub_id="sub_ent",
        org_id=org.id,
        plan_tier="enterprise",
        price_id="price_enterprise_test",
    )

    with pytest.raises(HTTPException) as exc:
        create_checkout_session(db, org=org, admin=admin, plan="team")
    assert exc.value.status_code == 400
    assert "Remove" in str(exc.value.detail)
    db.refresh(org)
    assert org.plan_tier == "enterprise"
    mock_retrieve.assert_not_called()


@patch("app.services.stripe_billing.stripe.Subscription.modify")
@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
def test_downgrade_under_capacity_updates_plan_and_limits(
    mock_retrieve,
    mock_modify,
    db,
    stripe_test_env,
):
    # 1 admin + 4 contacts = 5 → Team OK
    data = _seed_paid(db, org_id=221, plan="enterprise", extra_contacts=4, sub_id="sub_ent2")
    org, admin = data["org"], data["admin"]
    mock_retrieve.return_value = _sub(
        sub_id="sub_ent2",
        org_id=org.id,
        plan_tier="enterprise",
        price_id="price_enterprise_test",
    )
    mock_modify.return_value = _sub(
        sub_id="sub_ent2",
        org_id=org.id,
        plan_tier="team",
        price_id="price_team_test",
    )

    result = create_checkout_session(db, org=org, admin=admin, plan="team")
    assert result["updated"] is True
    db.refresh(org)
    assert org.plan_tier == "team"
    snap = team_limit_snapshot(db, org)
    assert snap["member_count"] == 5
    assert snap["member_limit"] == 5
    assert snap["over_member_limit"] is False
    assert has_full_write_access(org, db=db) is True


# ---------------------------------------------------------------------------
# 6. Payment failure / incomplete → 402
# ---------------------------------------------------------------------------


def test_subscription_updated_past_due_restricts_writes(db):
    data = _seed_paid(db, org_id=230, plan="team", extra_contacts=1, sub_id="sub_fail")
    org = data["org"]
    assert has_full_write_access(org, db=db) is True

    handle_subscription_updated(
        db,
        _sub(
            sub_id="sub_fail",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
            status="past_due",
            customer=org.stripe_customer_id,
        ),
    )
    db.refresh(org)
    assert org.subscription_status == "past_due"
    assert org.plan_tier == "team"  # plan retained during recovery window
    assert has_paid_subscription(org) is False
    assert is_restricted(org, db=db) is True
    with pytest.raises(HTTPException) as exc:
        assert_full_write_access(org, db=db)
    assert exc.value.status_code == 402


def test_invoice_payment_failed_marks_past_due(db):
    data = _seed_paid(db, org_id=231, plan="personal", sub_id="sub_inv", customer="cus_inv")
    org = data["org"]

    handle_invoice_payment_failed(
        db,
        {"subscription": "sub_inv", "customer": "cus_inv"},
    )
    db.refresh(org)
    assert org.subscription_status == "past_due"
    assert org.stripe_subscription_id == "sub_inv"
    assert org.plan_tier == "personal"
    with pytest.raises(HTTPException) as exc:
        assert_full_write_access(org, db=db)
    assert exc.value.status_code == 402


def test_subscription_updated_unpaid_downgrades_and_restricts(db):
    data = _seed_paid(db, org_id=232, plan="team", extra_contacts=2, sub_id="sub_unpaid")
    org = data["org"]

    handle_subscription_updated(
        db,
        _sub(
            sub_id="sub_unpaid",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
            status="unpaid",
            customer=org.stripe_customer_id,
        ),
    )
    db.refresh(org)
    assert org.subscription_status == "unpaid"
    assert org.stripe_subscription_id is None
    assert org.plan_tier == "personal"
    assert is_restricted(org, db=db) is True


def test_subscription_updated_incomplete_restricts(db):
    data = _seed_paid(db, org_id=233, plan="team", sub_id="sub_inc")
    org = data["org"]
    handle_subscription_updated(
        db,
        _sub(
            sub_id="sub_inc",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
            status="incomplete",
            customer=org.stripe_customer_id,
        ),
    )
    db.refresh(org)
    assert org.subscription_status == "incomplete"
    assert has_paid_subscription(org) is False
    assert is_restricted(org, db=db) is True


# ---------------------------------------------------------------------------
# 7. Cancellation → Personal + seat enforcement
# ---------------------------------------------------------------------------


def test_subscription_deleted_resets_to_personal_and_enforces_seats(db):
    data = _seed_paid(db, org_id=240, plan="enterprise", extra_contacts=3, sub_id="sub_del")
    org = data["org"]

    handle_subscription_deleted(
        db,
        {
            "id": "sub_del",
            "metadata": {"organisation_id": str(org.id)},
            "current_period_end": int(_now().timestamp()),
        },
    )
    db.refresh(org)
    assert org.plan_tier == "personal"
    assert org.stripe_subscription_id is None
    assert org.subscription_status == "canceled"
    snap = team_limit_snapshot(db, org)
    assert snap["member_limit"] == 1
    assert snap["member_count"] == 4
    assert snap["over_member_limit"] is True
    assert is_restricted(org, db=db) is True


# ---------------------------------------------------------------------------
# 8. Restricted → delete members → unblock
# ---------------------------------------------------------------------------


def test_delete_excess_members_unblocks_over_capacity_workspace(db, stripe_test_env):
    data = _seed_paid(db, org_id=250, plan="personal", extra_contacts=3, sub_id="sub_cap")
    org, admin = data["org"], data["admin"]
    contacts = data["contacts"]

    assert count_team_members(db, org.id) == 4
    assert is_restricted(org, db=db) is True

    for c in contacts:
        remove_team_member(db, org_id=org.id, admin=admin, contact_id=c.id)

    db.refresh(org)
    assert count_team_members(db, org.id) == 1
    assert is_restricted(org, db=db) is False
    assert_full_write_access(org, db=db)

    # Peak headcount still requires Team+ for checkout; upgrade unblocks billing path.
    with patch("app.services.stripe_billing.stripe.Subscription.retrieve") as mock_ret, patch(
        "app.services.stripe_billing.stripe.Subscription.modify"
    ) as mock_mod:
        mock_ret.return_value = _sub(
            sub_id="sub_cap",
            org_id=org.id,
            plan_tier="personal",
            price_id="price_personal_test",
        )
        mock_mod.return_value = _sub(
            sub_id="sub_cap",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
        )
        result = create_checkout_session(db, org=org, admin=admin, plan="team")
        assert result["updated"] is True
    db.refresh(org)
    assert org.plan_tier == "team"


def test_expired_trial_delete_members_then_subscribe(db, stripe_test_env):
    data = _seed_trial(db, org_id=251, plan="team", currency="USD")
    org, admin = data["org"], data["admin"]
    org.trial_ends_at = _now() - timedelta(days=1)
    db.add(org)
    for i in range(3):
        db.add(
            Contact(
                id=2510 + i,
                organisation_id=org.id,
                name=f"Extra {i}",
                email=f"extra{i}@plenvo.test",
            )
        )
    db.commit()
    db.refresh(org)

    assert is_restricted(org, db=db) is True
    contacts = db.query(Contact).filter(Contact.organisation_id == org.id).all()
    for c in contacts:
        remove_team_member(db, org_id=org.id, admin=admin, contact_id=c.id)
    assert count_team_members(db, org.id) == 1

    with patch("app.services.stripe_billing.stripe.checkout.Session.create") as mock_create, patch(
        "app.services.stripe_billing.stripe.Customer.create"
    ) as mock_cust, patch(
        "app.services.stripe_billing.stripe.Subscription.retrieve"
    ) as mock_sub:
        mock_cust.return_value = MagicMock(id="cus_expired")
        mock_create.return_value = MagicMock(url="https://checkout.stripe.test/expired")
        checkout = create_checkout_session(db, org=org, admin=admin, plan="personal", subscribe=True)
        assert checkout["url"]

        mock_sub.return_value = _sub(
            sub_id="sub_expired_fix",
            org_id=org.id,
            plan_tier="personal",
            price_id="price_personal_test",
            customer="cus_expired",
        )
        handle_checkout_completed(
            db,
            {
                "metadata": {"organisation_id": str(org.id), "plan_tier": "personal"},
                "subscription": "sub_expired_fix",
                "customer": "cus_expired",
                "client_reference_id": str(org.id),
            },
        )
    db.refresh(org)
    assert org.subscription_status == "active"
    assert has_full_write_access(org, db=db) is True


# ---------------------------------------------------------------------------
# Webhook resilience
# ---------------------------------------------------------------------------


@patch("app.services.stripe_billing.send_subscription_thank_you_email", return_value=True)
@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
def test_duplicate_checkout_webhook_is_idempotent(mock_sub_retrieve, mock_email, db, stripe_test_env):
    data = _seed_trial(db, org_id=300, plan="personal")
    org = data["org"]
    org.stripe_customer_id = "cus_idem"
    db.add(org)
    db.commit()

    payload = _sub(
        sub_id="sub_idem",
        org_id=org.id,
        plan_tier="personal",
        price_id="price_personal_test",
        customer="cus_idem",
    )
    mock_sub_retrieve.return_value = payload
    session = {
        "metadata": {"organisation_id": str(org.id), "plan_tier": "personal"},
        "subscription": "sub_idem",
        "customer": "cus_idem",
        "client_reference_id": str(org.id),
    }
    handle_checkout_completed(db, session)
    handle_checkout_completed(db, session)
    db.refresh(org)

    assert org.stripe_subscription_id == "sub_idem"
    assert org.subscription_status == "active"
    assert mock_email.call_count == 1  # welcome email not double-sent


def test_duplicate_subscription_updated_safe(db):
    data = _seed_paid(db, org_id=301, plan="team", sub_id="sub_dup")
    org = data["org"]
    payload = _sub(
        sub_id="sub_dup",
        org_id=org.id,
        plan_tier="enterprise",
        price_id="price_enterprise_test",
        customer=org.stripe_customer_id,
    )
    handle_subscription_updated(db, payload)
    handle_subscription_updated(db, payload)
    db.refresh(org)
    assert org.plan_tier == "enterprise"
    assert org.subscription_status == "active"


def test_webhook_missing_org_refs_is_noop(db):
    """No matching organisation_id / client_reference_id / customer → no crash."""
    before = db.query(Organisation).count()
    handle_checkout_completed(
        db,
        {
            "metadata": {},
            "subscription": "sub_orphan",
            "customer": "cus_unknown",
            "client_reference_id": "not-an-int",
        },
    )
    handle_subscription_updated(
        db,
        {
            "id": "sub_orphan",
            "status": "active",
            "metadata": {},
            "customer": "cus_unknown",
            "items": {"data": []},
        },
    )
    handle_subscription_deleted(db, {"id": "sub_orphan", "metadata": {}, "customer": "cus_unknown"})
    handle_invoice_payment_failed(db, {"subscription": "sub_orphan", "customer": "cus_unknown"})
    assert db.query(Organisation).count() == before


def test_webhook_resolves_org_via_client_reference_id_only(db, stripe_test_env):
    data = _seed_trial(db, org_id=302, plan="team")
    org = data["org"]

    with patch("app.services.stripe_billing.stripe.Subscription.retrieve") as mock_sub:
        mock_sub.return_value = _sub(
            sub_id="sub_cref",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
            customer="cus_cref_new",
        )
        handle_checkout_completed(
            db,
            {
                "metadata": {},  # no organisation_id
                "subscription": "sub_cref",
                "customer": "cus_cref_new",
                "client_reference_id": str(org.id),
            },
        )
    db.refresh(org)
    assert org.stripe_subscription_id == "sub_cref"
    assert org.stripe_customer_id == "cus_cref_new"
    assert org.subscription_status == "active"


def test_webhook_currency_mismatch_does_not_corrupt_org_currency(db, stripe_test_env):
    data = _seed_trial(db, org_id=303, plan="personal", currency="GBP")
    org = data["org"]
    org.stripe_customer_id = "cus_cur"
    db.add(org)
    db.commit()

    with patch("app.services.stripe_billing.stripe.Subscription.retrieve") as mock_sub:
        mock_sub.return_value = _sub(
            sub_id="sub_cur",
            org_id=org.id,
            plan_tier="personal",
            price_id="price_personal_test",
            customer="cus_cur",
        )
        handle_checkout_completed(
            db,
            {
                "metadata": {
                    "organisation_id": str(org.id),
                    "plan_tier": "personal",
                    "currency": "eur",  # mismatched vs locked GBP
                },
                "subscription": "sub_cur",
                "customer": "cus_cur",
                "client_reference_id": str(org.id),
            },
        )
    db.refresh(org)
    assert org.currency == "GBP"
    assert org.subscription_status == "active"


def test_past_due_recovery_via_subscription_updated_restores_writes(db):
    data = _seed_paid(db, org_id=304, plan="team", sub_id="sub_rec")
    org = data["org"]
    org.subscription_status = "past_due"
    db.add(org)
    db.commit()
    assert is_restricted(org, db=db) is True

    handle_subscription_updated(
        db,
        _sub(
            sub_id="sub_rec",
            org_id=org.id,
            plan_tier="team",
            price_id="price_team_test",
            status="active",
            customer=org.stripe_customer_id,
        ),
    )
    db.refresh(org)
    assert org.subscription_status == "active"
    assert has_full_write_access(org, db=db) is True
