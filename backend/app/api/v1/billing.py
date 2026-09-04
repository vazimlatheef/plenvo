"""Billing: Checkout Session, cancel-at-period-end, Stripe webhooks."""

from __future__ import annotations

from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.config import settings
from app.models.models import Organisation, User
from app.services.stripe_billing import (
    account_snapshot,
    cancel_subscription_at_period_end,
    create_checkout_session,
    handle_checkout_completed,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
    handle_subscription_updated,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: str = Field(..., min_length=3, max_length=32)
    subscribe: bool = False


def _org_for_user(db: Session, user: User) -> Organisation:
    if not user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organisation.",
        )
    org = db.get(Organisation, user.organisation_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found.",
        )
    return org


@router.get("/account")
def get_billing_account(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Current plan, trial, team usage, and upgrade catalogue (org currency)."""
    org = _org_for_user(db, current_user)
    snap = account_snapshot(db, org)
    snap["can_manage_billing"] = current_user.role == "admin"
    return snap


@router.post("/create-checkout-session")
def post_create_checkout_session(
    payload: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db),
):
    org = _org_for_user(db, current_user)
    return create_checkout_session(
        db, org=org, admin=current_user, plan=payload.plan, subscribe=payload.subscribe
    )


@router.post("/cancel-subscription")
def post_cancel_subscription(
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db),
):
    org = _org_for_user(db, current_user)
    return cancel_subscription_at_period_end(db, org)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    secret = (settings.stripe_webhook_secret or "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STRIPE_WEBHOOK_SECRET is not configured.",
        )

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload") from exc
    except Exception as exc:
        # stripe.error.SignatureVerificationError (SDK version variance)
        name = type(exc).__name__
        if "SignatureVerification" not in name:
            raise
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    etype = event["type"]
    data_object = event["data"]["object"]

    if etype == "checkout.session.completed":
        handle_checkout_completed(db, data_object)
    elif etype == "customer.subscription.updated":
        handle_subscription_updated(db, data_object)
    elif etype == "customer.subscription.deleted":
        handle_subscription_deleted(db, data_object)
    elif etype == "invoice.payment_failed":
        handle_invoice_payment_failed(db, data_object)

    return {"received": True}
