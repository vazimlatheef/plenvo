"""Stripe billing helpers for Checkout + subscription lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.pricing import (
    catalogue_for_currency,
    checkout_currency,
    normalize_plan,
    plan_from_price_id,
    plan_label_for_org,
    price_id_for,
    stripe_product_image_url,
)
from app.models.models import Organisation, User
from app.services.email import send_subscription_cancelled_email, send_subscription_thank_you_email
from app.services.plan_access import has_paid_subscription, plan_access_snapshot
from app.services.plan_limits import (
    assert_checkout_meets_minimum_tier,
    assert_trial_plan_upgrade_only,
    is_on_trial,
    team_limit_snapshot,
)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _require_stripe() -> None:
    key = (settings.stripe_secret_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured (missing STRIPE_SECRET_KEY).",
        )
    stripe.api_key = key


def _frontend_base() -> str:
    return (settings.frontend_url or "http://localhost:5173").rstrip("/")


def _ts_to_dt(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def _subscription_period_end(sub: Any) -> datetime | None:
    dt = _ts_to_dt(_get(sub, "current_period_end"))
    if dt:
        return dt
    items = _get(sub, "items") or {}
    data = items.get("data") if isinstance(items, dict) else _get(items, "data")
    if data:
        return _ts_to_dt(_get(data[0], "current_period_end"))
    return None


def _format_access_date(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d %b %Y")


def _org_admin(db: Session, org: Organisation) -> User | None:
    return (
        db.query(User)
        .filter(User.organisation_id == org.id, User.role == "admin")
        .order_by(User.id.asc())
        .first()
    )


def _maybe_send_paid_welcome(db: Session, org: Organisation) -> None:
    if org.paid_welcome_email_sent_at or not has_paid_subscription(org):
        return
    admin = _org_admin(db, org)
    if admin is None or not (admin.email or "").strip():
        return
    sent = send_subscription_thank_you_email(
        admin.email,
        admin.first_name,
        plan_tier=org.plan_tier,
    )
    if not sent:
        return
    org.paid_welcome_email_sent_at = datetime.now(timezone.utc)
    db.add(org)
    db.commit()


def _maybe_send_cancel_notice(db: Session, org: Organisation) -> None:
    if not org.cancel_at_period_end or org.cancel_notice_email_sent_at:
        return
    admin = _org_admin(db, org)
    if admin is None or not (admin.email or "").strip():
        return
    sent = send_subscription_cancelled_email(
        admin.email,
        admin.first_name,
        access_ends_on=_format_access_date(org.subscription_current_period_end),
        plan_tier=org.plan_tier,
    )
    if not sent:
        return
    org.cancel_notice_email_sent_at = datetime.now(timezone.utc)
    db.add(org)
    db.commit()


def ensure_stripe_customer(db: Session, org: Organisation, admin: User) -> str:
    _require_stripe()
    if org.stripe_customer_id:
        return org.stripe_customer_id

    customer = stripe.Customer.create(
        email=admin.email,
        name=org.name,
        metadata={"organisation_id": str(org.id)},
    )
    org.stripe_customer_id = customer.id
    db.add(org)
    db.commit()
    db.refresh(org)
    return customer.id


def _has_active_paid_subscription(org: Organisation) -> bool:
    return has_paid_subscription(org)


def create_checkout_session(
    db: Session,
    *,
    org: Organisation,
    admin: User,
    plan: str,
    subscribe: bool = False,
) -> dict:
    """Start Checkout for a new subscription, or switch price on an existing one.

    During an unpaid trial, ``subscribe=False`` updates the trial plan locally
    (no card). ``subscribe=True`` opens Stripe Checkout immediately.
    Returns ``{"url": "..."}`` for Checkout redirect, or ``{"updated": True}`` when
    an existing subscription was modified in place.
    """
    _require_stripe()
    tier = normalize_plan(plan)
    currency = checkout_currency(org.currency)
    price_id = price_id_for(tier)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No Stripe Price ID configured for {tier}. "
                f"Set STRIPE_PRICE_ID_{tier.upper()} env var."
            ),
        )

    has_paid = _has_active_paid_subscription(org)
    on_trial = is_on_trial(org)

    # Active trial without a paid Stripe sub: upgrade plan locally unless they
    # explicitly chose Subscribe now (card / Checkout).
    if on_trial and not has_paid and not subscribe:
        assert_trial_plan_upgrade_only(org, tier)
        org.plan_tier = tier
        db.add(org)
        db.commit()
        db.refresh(org)
        return {"updated": True, "plan_tier": tier, "on_trial": True}

    if on_trial and not has_paid and subscribe:
        assert_trial_plan_upgrade_only(org, tier)

    assert_checkout_meets_minimum_tier(db, org, tier)

    # Existing paid subscription → change price in place (avoid a second sub).
    if org.stripe_subscription_id and (org.subscription_status or "active") in (
        "active",
        "trialing",
        "past_due",
    ):
        sub = stripe.Subscription.retrieve(org.stripe_subscription_id)
        items = _get(sub, "items") or {}
        data = items.get("data") if isinstance(items, dict) else _get(items, "data")
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read current Stripe subscription items.",
            )
        item_id = _get(data[0], "id")
        updated = stripe.Subscription.modify(
            org.stripe_subscription_id,
            items=[{"id": item_id, "price": price_id}],
            currency=currency,
            cancel_at_period_end=False,
            metadata={
                "organisation_id": str(org.id),
                "plan_tier": tier,
            },
            proration_behavior="create_prorations",
        )
        _apply_subscription_to_org(db, org, updated)
        org.plan_tier = tier
        org.trial_ends_at = None
        org.cancel_at_period_end = False
        db.add(org)
        db.commit()
        return {"updated": True, "plan_tier": tier}

    customer_id = ensure_stripe_customer(db, org, admin)
    base = _frontend_base()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        currency=currency,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base}/app/account?checkout=success",
        cancel_url=f"{base}/app/account?checkout=cancel",
        client_reference_id=str(org.id),
        metadata={
            "organisation_id": str(org.id),
            "plan_tier": tier,
            "currency": currency,
        },
        subscription_data={
            "metadata": {
                "organisation_id": str(org.id),
                "plan_tier": tier,
            },
        },
        allow_promotion_codes=True,
    )
    if not session.url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a Checkout URL.",
        )
    return {"url": session.url}


def cancel_subscription_at_period_end(db: Session, org: Organisation) -> dict:
    """Schedule cancellation at period end; returns access-end date."""
    _require_stripe()
    if not org.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active paid subscription to cancel.",
        )

    sub = stripe.Subscription.modify(
        org.stripe_subscription_id,
        cancel_at_period_end=True,
    )
    period_end = _subscription_period_end(sub)
    if period_end is None:
        retrieved = stripe.Subscription.retrieve(org.stripe_subscription_id)
        period_end = _subscription_period_end(retrieved)
    org.cancel_at_period_end = True
    org.subscription_current_period_end = period_end
    org.subscription_status = _get(sub, "status") or "active"
    db.add(org)
    db.commit()
    db.refresh(org)
    _maybe_send_cancel_notice(db, org)
    db.refresh(org)

    return {
        "cancel_at_period_end": True,
        "access_ends_at": period_end.isoformat() if period_end else None,
        "subscription_status": org.subscription_status,
    }


def _org_by_stripe_customer(db: Session, customer_id: str | None) -> Organisation | None:
    if not customer_id:
        return None
    return (
        db.query(Organisation)
        .filter(Organisation.stripe_customer_id == customer_id)
        .first()
    )


def _org_by_id(db: Session, org_id: str | int | None) -> Organisation | None:
    if org_id is None:
        return None
    try:
        oid = int(org_id)
    except (TypeError, ValueError):
        return None
    return db.get(Organisation, oid)


def _plan_from_subscription(sub: Any) -> str | None:
    meta = _get(sub, "metadata") or {}
    if isinstance(meta, dict):
        plan = (meta.get("plan_tier") or "").strip().lower()
        if plan in ("personal", "team", "enterprise"):
            return plan

    items = _get(sub, "items") or {}
    data = _get(items, "data") if not isinstance(items, list) else items
    if isinstance(items, dict):
        data = items.get("data") or []
    if data:
        first = data[0]
        price = _get(first, "price")
        price_id = _get(price, "id") if price is not None else None
        return plan_from_price_id(price_id)
    return None


def _apply_subscription_to_org(db: Session, org: Organisation, sub: Any) -> None:
    status_val = _get(sub, "status") or "active"
    cancel_at_period_end = bool(_get(sub, "cancel_at_period_end", False))
    period_end = _subscription_period_end(sub)

    sub_id = _get(sub, "id")
    if sub_id:
        org.stripe_subscription_id = sub_id
    org.subscription_status = status_val
    org.cancel_at_period_end = cancel_at_period_end
    org.subscription_current_period_end = period_end

    plan = _plan_from_subscription(sub)

    if status_val in ("canceled", "unpaid", "incomplete_expired"):
        org.plan_tier = "personal"
        org.stripe_subscription_id = None
        org.cancel_at_period_end = False
        org.paid_welcome_email_sent_at = None
        org.cancel_notice_email_sent_at = None
    elif plan in ("personal", "team", "enterprise"):
        org.plan_tier = plan
        if status_val in ("active", "trialing"):
            org.trial_ends_at = None
        if not cancel_at_period_end:
            org.cancel_notice_email_sent_at = None

    db.add(org)
    db.commit()


def handle_checkout_completed(db: Session, session_obj: Any) -> None:
    meta = _get(session_obj, "metadata") or {}
    org_id = meta.get("organisation_id") if isinstance(meta, dict) else None
    org = _org_by_id(db, org_id)
    if org is None:
        org = _org_by_id(db, _get(session_obj, "client_reference_id"))
    if org is None:
        org = _org_by_stripe_customer(db, _get(session_obj, "customer"))
    if org is None:
        return

    customer_id = _get(session_obj, "customer")
    if customer_id and not org.stripe_customer_id:
        org.stripe_customer_id = customer_id

    plan = None
    if isinstance(meta, dict):
        plan = (meta.get("plan_tier") or "").strip().lower() or None

    subscription_id = _get(session_obj, "subscription")
    if subscription_id:
        try:
            _require_stripe()
            sub = stripe.Subscription.retrieve(subscription_id)
            _apply_subscription_to_org(db, org, sub)
            if plan in ("personal", "team", "enterprise"):
                assert_checkout_meets_minimum_tier(db, org, plan)
                org.plan_tier = plan
                org.trial_ends_at = None
                db.add(org)
                db.commit()
            _maybe_send_paid_welcome(db, org)
            return
        except Exception:
            org.stripe_subscription_id = subscription_id

    if plan in ("personal", "team", "enterprise"):
        assert_checkout_meets_minimum_tier(db, org, plan)
        org.plan_tier = plan
        org.trial_ends_at = None
        org.subscription_status = "active"
        org.cancel_at_period_end = False

    db.add(org)
    db.commit()
    _maybe_send_paid_welcome(db, org)


def handle_subscription_updated(db: Session, sub: Any) -> None:
    meta = _get(sub, "metadata") or {}
    org = _org_by_id(db, meta.get("organisation_id") if isinstance(meta, dict) else None)
    if org is None:
        org = (
            db.query(Organisation)
            .filter(Organisation.stripe_subscription_id == _get(sub, "id"))
            .first()
        )
    if org is None:
        org = _org_by_stripe_customer(db, _get(sub, "customer"))
    if org is None:
        return
    _apply_subscription_to_org(db, org, sub)
    db.refresh(org)
    _maybe_send_cancel_notice(db, org)


def handle_subscription_deleted(db: Session, sub: Any) -> None:
    meta = _get(sub, "metadata") or {}
    org = _org_by_id(db, meta.get("organisation_id") if isinstance(meta, dict) else None)
    if org is None:
        org = (
            db.query(Organisation)
            .filter(Organisation.stripe_subscription_id == _get(sub, "id"))
            .first()
        )
    if org is None:
        org = _org_by_stripe_customer(db, _get(sub, "customer"))
    if org is None:
        return

    org.plan_tier = "personal"
    org.stripe_subscription_id = None
    org.subscription_status = "canceled"
    org.cancel_at_period_end = False
    org.subscription_current_period_end = _subscription_period_end(sub)
    org.paid_welcome_email_sent_at = None
    org.cancel_notice_email_sent_at = None
    db.add(org)
    db.commit()


def account_snapshot(db: Session, org: Organisation) -> dict:
    limits = team_limit_snapshot(db, org)
    access = plan_access_snapshot(db, org)
    on_trial = access["on_trial"]
    has_paid = access["has_paid_subscription"]
    tier = limits["plan_tier"]

    return {
        **limits,
        **access,
        "organisation_name": org.name,
        "display_plan": tier,
        "plan_label": plan_label_for_org(tier, on_trial=on_trial, has_paid=has_paid),
        "subscription_status": org.subscription_status,
        "cancel_at_period_end": bool(org.cancel_at_period_end),
        "access_ends_at": (
            org.subscription_current_period_end.isoformat()
            if org.cancel_at_period_end and org.subscription_current_period_end
            else None
        ),
        "subscription_current_period_end": (
            org.subscription_current_period_end.isoformat()
            if org.subscription_current_period_end
            else None
        ),
        "can_cancel": has_paid and not bool(org.cancel_at_period_end),
        "plans": catalogue_for_currency(org.currency),
        "product_image_url": stripe_product_image_url(),
    }
