"""Billing lifecycle: downgrade data survival, over-limit grace, re-subscribe via webhook."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.models import Contact, Organisation, Project, Task, Training, User
from app.services.plan_access import assert_full_write_access, has_full_write_access, is_restricted
from app.services.plan_limits import assert_can_add_team_members, can_add_team_members, team_limit_snapshot
from app.services.stripe_billing import (
    create_checkout_session,
    handle_checkout_completed,
    handle_subscription_deleted,
)


def _seed_solo_org(db) -> dict:
    """Solo org: admin only (1 headcount)."""
    org = Organisation(
        id=1,
        name="Solo Co",
        slug="solo-co",
        plan_tier="personal",
        currency="USD",
        stripe_customer_id="cus_solo",
        stripe_subscription_id="sub_personal",
        subscription_status="active",
        trial_ends_at=None,
        trial_peak_member_count=1,
    )
    db.add(org)
    db.flush()
    admin = User(
        id=1,
        organisation_id=org.id,
        email="admin@solo.com",
        password_hash="hashed",
        first_name="Solo",
        last_name="Admin",
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(org)
    db.refresh(admin)
    return {"org": org, "admin": admin}


def _seed_team_org_with_data(db) -> dict:
    """Team org: 1 admin + 5 contacts (6 headcount), project, task, training."""
    org = Organisation(
        id=1,
        name="Acme",
        slug="acme",
        plan_tier="team",
        currency="USD",
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_team",
        subscription_status="active",
        trial_ends_at=None,
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
    for i in range(5):
        contact = Contact(
            id=i + 1,
            organisation_id=org.id,
            name=f"Contact {i}",
            email=f"contact{i}@acme.com",
        )
        db.add(contact)
        contacts.append(contact)
    db.flush()

    project = Project(
        id=1,
        organisation_id=org.id,
        title="Launch",
        description="Keep",
        manager_id=admin.id,
    )
    db.add(project)
    db.flush()

    task = Task(
        id=1,
        organisation_id=org.id,
        title="Ship feature",
        project_id=project.id,
        assignee_contact_id=contacts[0].id,
        created_by_id=admin.id,
        status="pending",
    )
    db.add(task)

    training = Training(
        id=1,
        organisation_id=org.id,
        title="Onboarding",
        content_type="link",
        external_url="https://example.com/training",
        created_by_id=admin.id,
        project_id=project.id,
    )
    db.add(training)
    db.commit()

    for obj in (org, admin, project, task, training, *contacts):
        db.refresh(obj)

    return {
        "org": org,
        "admin": admin,
        "contacts": contacts,
        "project": project,
        "task": task,
        "training": training,
    }


def _subscription_payload(*, sub_id: str, org_id: int, plan_tier: str, price_id: str) -> dict:
    return {
        "id": sub_id,
        "status": "active",
        "cancel_at_period_end": False,
        "current_period_end": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30,
        "metadata": {"organisation_id": str(org_id), "plan_tier": plan_tier},
        "items": {"data": [{"id": "si_test", "price": {"id": price_id}}]},
    }


def test_team_cancel_period_end_preserves_data_and_restricts_writes(db):
    """Subscription deleted → personal tier + restricted; all existing data intact."""
    data = _seed_team_org_with_data(db)
    org = data["org"]
    task_id = data["task"].id
    assignee_contact_id = data["task"].assignee_contact_id
    project_id = data["project"].id
    training_id = data["training"].id
    contact_count = len(data["contacts"])

    handle_subscription_deleted(
        db,
        {
            "id": "sub_team",
            "metadata": {"organisation_id": str(org.id)},
            "current_period_end": int(datetime.now(timezone.utc).timestamp()),
        },
    )
    db.refresh(org)

    assert org.plan_tier == "personal"
    assert org.stripe_subscription_id is None
    assert org.subscription_status == "canceled"
    assert is_restricted(org) is True

    assert db.query(Contact).filter(Contact.organisation_id == org.id).count() == contact_count
    assert db.query(User).filter(User.organisation_id == org.id).count() == 1
    assert db.query(Project).filter(Project.organisation_id == org.id).count() == 1
    assert db.query(Task).filter(Task.organisation_id == org.id).count() == 1
    assert db.query(Training).filter(Training.organisation_id == org.id).count() == 1

    task = db.get(Task, task_id)
    assert task is not None
    assert task.assignee_contact_id == assignee_contact_id
    assert task.project_id == project_id
    assert db.get(Project, project_id) is not None
    assert db.get(Training, training_id) is not None

    limits = team_limit_snapshot(db, org)
    assert limits["member_count"] == 6
    assert limits["member_limit"] == 1
    assert limits["can_add_members"] is False
    assert limits["limit_message"] is not None

    with pytest.raises(HTTPException) as exc:
        assert_full_write_access(org)
    assert exc.value.status_code == 402

    with pytest.raises(HTTPException) as exc_add:
        assert_can_add_team_members(db, org, adding=1)
    assert exc_add.value.status_code == 403


def test_over_limit_after_downgrade_does_not_crash(db):
    """6 members on Personal (limit 1): data preserved; new adds blocked; writes blocked when restricted."""
    data = _seed_team_org_with_data(db)
    org = data["org"]
    org.plan_tier = "personal"
    org.stripe_subscription_id = None
    org.subscription_status = "canceled"
    db.add(org)
    db.commit()
    db.refresh(org)

    assert is_restricted(org) is True
    with pytest.raises(HTTPException) as exc_write:
        assert_full_write_access(org)
    assert exc_write.value.status_code == 402

    allowed, current, limit, message = can_add_team_members(db, org, adding=0)
    assert allowed is True
    assert current == 6
    assert limit == 1

    allowed_add, _, _, msg = can_add_team_members(db, org, adding=1)
    assert allowed_add is False
    assert msg is not None

    snap = team_limit_snapshot(db, org)
    assert snap["member_count"] == 6
    assert snap["member_limit"] == 1
    assert snap["can_add_members"] is False

    tasks = db.query(Task).filter(Task.organisation_id == org.id).all()
    assert len(tasks) == 1
    assert tasks[0].assignee_contact_id is not None


@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
@patch("app.services.stripe_billing.stripe.checkout.Session.create")
def test_personal_resubscribe_checkout_to_webhook_restores_access(
    mock_session_create,
    mock_sub_retrieve,
    db,
    stripe_test_env,
):
    """Restricted Personal org (solo) → Checkout session → webhook → write access restored."""
    data = _seed_solo_org(db)
    org = data["org"]
    admin = data["admin"]

    handle_subscription_deleted(db, {"id": "sub_team", "metadata": {"organisation_id": str(org.id)}})
    db.refresh(org)
    assert is_restricted(org) is True

    mock_session_create.return_value = MagicMock(url="https://checkout.stripe.test/session")
    checkout = create_checkout_session(db, org=org, admin=admin, plan="personal")
    assert checkout["url"] == "https://checkout.stripe.test/session"
    mock_session_create.assert_called_once()

    mock_sub_retrieve.return_value = _subscription_payload(
        sub_id="sub_personal_new",
        org_id=org.id,
        plan_tier="personal",
        price_id="price_personal_test",
    )
    handle_checkout_completed(
        db,
        {
            "metadata": {"organisation_id": str(org.id), "plan_tier": "personal"},
            "subscription": "sub_personal_new",
            "customer": org.stripe_customer_id,
            "client_reference_id": str(org.id),
        },
    )
    db.refresh(org)

    assert org.stripe_subscription_id == "sub_personal_new"
    assert org.subscription_status == "active"
    assert org.plan_tier == "personal"
    assert has_full_write_access(org) is True
    assert is_restricted(org) is False
    assert_full_write_access(org)


@patch("app.services.stripe_billing.stripe.Subscription.retrieve")
@patch("app.services.stripe_billing.stripe.checkout.Session.create")
def test_team_resubscribe_checkout_to_webhook_restores_access_and_tier(
    mock_session_create,
    mock_sub_retrieve,
    db,
    stripe_test_env,
):
    """Restricted downgraded org (4 members) → Checkout Team → webhook → Team tier + write access."""
    org = Organisation(
        id=2,
        name="Mid Co",
        slug="mid-co",
        plan_tier="team",
        currency="USD",
        stripe_customer_id="cus_mid",
        stripe_subscription_id="sub_team",
        subscription_status="active",
        trial_ends_at=None,
        trial_peak_member_count=4,
    )
    db.add(org)
    db.flush()
    admin = User(
        id=2,
        organisation_id=org.id,
        email="admin@mid.com",
        password_hash="hashed",
        first_name="Mid",
        last_name="Admin",
        role="admin",
    )
    db.add(admin)
    db.flush()
    for i in range(3):
        db.add(
            Contact(
                id=i + 10,
                organisation_id=org.id,
                name=f"Contact {i}",
                email=f"mid{i}@mid.com",
            )
        )
    db.commit()
    db.refresh(org)
    db.refresh(admin)

    handle_subscription_deleted(db, {"id": "sub_team", "metadata": {"organisation_id": str(org.id)}})
    db.refresh(org)
    assert org.plan_tier == "personal"
    assert is_restricted(org) is True

    mock_session_create.return_value = MagicMock(url="https://checkout.stripe.test/team")
    checkout = create_checkout_session(db, org=org, admin=admin, plan="team")
    assert "url" in checkout

    mock_sub_retrieve.return_value = _subscription_payload(
        sub_id="sub_team_new",
        org_id=org.id,
        plan_tier="team",
        price_id="price_team_test",
    )
    handle_checkout_completed(
        db,
        {
            "metadata": {"organisation_id": str(org.id), "plan_tier": "team"},
            "subscription": "sub_team_new",
            "customer": org.stripe_customer_id,
        },
    )
    db.refresh(org)

    assert org.plan_tier == "team"
    assert org.stripe_subscription_id == "sub_team_new"
    assert has_full_write_access(org) is True
    assert is_restricted(org) is False

    limits = team_limit_snapshot(db, org)
    assert limits["member_limit"] == 5
    assert limits["member_count"] == 4
    assert limits["can_add_members"] is True
