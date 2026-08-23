"""Display / Stripe pricing catalogue.

Keep in sync with frontend/src/composables/useCurrency.js.
Stripe Price IDs are loaded from environment (see Settings / .env.example).
Each plan uses one multi-currency Price ID; org.currency is passed at Checkout time.
"""

from __future__ import annotations

from typing import Literal

from app.core.config import settings

CurrencyCode = Literal["GBP", "EUR", "USD", "INR"]
PlanTier = Literal["personal", "team", "enterprise"]

DEFAULT_CURRENCY: CurrencyCode = "USD"
PLAN_TIERS: tuple[str, ...] = ("personal", "team", "enterprise")

SUPPORTED_CURRENCIES: frozenset[str] = frozenset({"GBP", "EUR", "USD", "INR"})

# Official Eurozone ISO country codes (2026).
EUROZONE: frozenset[str] = frozenset(
    {
        "AT",
        "BE",
        "HR",
        "CY",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PT",
        "SK",
        "SI",
        "ES",
    }
)

# Human-readable amounts (same strings as marketing UI).
PRICE_DISPLAY: dict[str, dict[str, str]] = {
    "GBP": {
        "symbol": "£",
        "personal": "4.99",
        "team": "19.99",
        "enterprise": "49.99",
    },
    "EUR": {
        "symbol": "€",
        "personal": "4.99",
        "team": "19.99",
        "enterprise": "49.99",
    },
    "USD": {
        "symbol": "$",
        "personal": "4.99",
        "team": "19.99",
        "enterprise": "49.99",
    },
    "INR": {
        "symbol": "₹",
        "personal": "499",
        "team": "1,999",
        "enterprise": "4,999",
    },
}

# Minor units for Stripe Price / Checkout (integer, no separators).
PRICE_MINOR_UNITS: dict[str, dict[str, int]] = {
    "GBP": {"personal": 499, "team": 1999, "enterprise": 4999},
    "EUR": {"personal": 499, "team": 1999, "enterprise": 4999},
    "USD": {"personal": 499, "team": 1999, "enterprise": 4999},
    "INR": {"personal": 49900, "team": 199900, "enterprise": 499900},
}


def _env_price_id(plan: str) -> str | None:
    attr = f"stripe_price_id_{plan}"
    value = (getattr(settings, attr, "") or "").strip()
    return value or None


def stripe_price_ids_by_plan() -> dict[str, str | None]:
    """Plan tier → multi-currency Stripe Price ID (from env)."""
    return {plan: _env_price_id(plan) for plan in PLAN_TIERS}


# Backwards-compatible alias (plan → price id; no longer keyed by currency).
STRIPE_PRICE_IDS = stripe_price_ids_by_plan()


def stripe_product_image_url() -> str:
    custom = (settings.stripe_product_image_url or "").strip()
    if custom:
        return custom
    base = (settings.frontend_url or "https://plenvo.io").rstrip("/")
    return f"{base}/plenvo-icon-512.png"


def normalize_currency(code: str | None) -> CurrencyCode:
    key = (code or "").strip().upper()
    if key in SUPPORTED_CURRENCIES:
        return key  # type: ignore[return-value]
    return DEFAULT_CURRENCY


def checkout_currency(code: str | None) -> str:
    """Lowercase ISO currency for Stripe Checkout / Subscription APIs."""
    return normalize_currency(code).lower()


def normalize_plan(plan: str | None) -> str:
    key = (plan or "").strip().lower()
    if key in PLAN_TIERS:
        return key
    raise ValueError(f"Invalid plan: {plan}")


def resolve_signup_plan_tier(plan: str | None) -> str:
    """Plan chosen at signup; generic CTA defaults to team."""
    if not plan or not str(plan).strip():
        return "team"
    key = str(plan).strip().lower()
    if key in PLAN_TIERS:
        return key
    return "team"


def plan_display_name(tier: str | None) -> str:
    key = (tier or "personal").strip().lower()
    return {
        "personal": "Personal",
        "team": "Team",
        "enterprise": "Enterprise",
    }.get(key, key.capitalize())


def plan_label_for_org(tier: str | None, *, on_trial: bool, has_paid: bool) -> str:
    label = plan_display_name(tier)
    if on_trial and not has_paid:
        return f"{label} (Trial)"
    return label


def resolve_currency_from_country(country_code: str | None) -> CurrencyCode:
    cc = (country_code or "").strip().upper()
    if cc == "GB":
        return "GBP"
    if cc == "IN":
        return "INR"
    if cc in EUROZONE:
        return "EUR"
    return DEFAULT_CURRENCY


def currency_symbol(code: str | None) -> str:
    cfg = PRICE_DISPLAY[normalize_currency(code)]
    return cfg["symbol"]


def display_price(code: str | None, plan: str) -> str:
    cfg = PRICE_DISPLAY[normalize_currency(code)]
    amount = cfg.get(plan, "")
    return f"{cfg['symbol']}{amount}"


def price_id_for(plan: str) -> str | None:
    tier = normalize_plan(plan)
    return stripe_price_ids_by_plan().get(tier)


def plan_from_price_id(price_id: str | None) -> str | None:
    if not price_id:
        return None
    for plan, pid in stripe_price_ids_by_plan().items():
        if pid and pid == price_id:
            return plan
    return None


def catalogue_for_currency(currency: str | None) -> list[dict]:
    """Plans with display amounts + whether a Stripe Price ID is configured."""
    cur = normalize_currency(currency)
    cfg = PRICE_DISPLAY[cur]
    ids = stripe_price_ids_by_plan()
    return [
        {
            "id": plan,
            "name": plan.capitalize(),
            "price_display": f"{cfg['symbol']}{cfg[plan]}",
            "amount": cfg[plan],
            "currency": cur,
            "interval": "month",
            "stripe_price_id": ids.get(plan),
            "checkout_ready": bool(ids.get(plan)),
        }
        for plan in PLAN_TIERS
    ]
