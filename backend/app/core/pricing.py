"""Display / Stripe pricing catalogue.

Keep in sync with frontend/src/composables/useCurrency.js.
Stripe Price IDs are loaded from environment (see Settings / .env.example).
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
        "enterprise": "39.99",
    },
    "EUR": {
        "symbol": "€",
        "personal": "4.99",
        "team": "19.99",
        "enterprise": "39.99",
    },
    "USD": {
        "symbol": "$",
        "personal": "4.99",
        "team": "19.99",
        "enterprise": "39.99",
    },
    "INR": {
        "symbol": "₹",
        "personal": "499",
        "team": "1,999",
        "enterprise": "3,999",
    },
}

# Minor units for Stripe Price / Checkout (integer, no separators).
PRICE_MINOR_UNITS: dict[str, dict[str, int]] = {
    "GBP": {"personal": 499, "team": 1999, "enterprise": 3999},
    "EUR": {"personal": 499, "team": 1999, "enterprise": 3999},
    "USD": {"personal": 499, "team": 1999, "enterprise": 3999},
    "INR": {"personal": 49900, "team": 199900, "enterprise": 399900},
}


def _env_price(currency: str, plan: str) -> str | None:
    attr = f"stripe_price_{currency.lower()}_{plan}"
    value = (getattr(settings, attr, "") or "").strip()
    return value or None


def stripe_price_ids() -> dict[str, dict[str, str | None]]:
    """Live map of currency → plan → Stripe Price ID (from env)."""
    out: dict[str, dict[str, str | None]] = {}
    for currency in ("GBP", "EUR", "USD", "INR"):
        out[currency] = {
            "personal": _env_price(currency, "personal"),
            "team": _env_price(currency, "team"),
            "enterprise": _env_price(currency, "enterprise"),
        }
    return out


# Backwards-compatible name used elsewhere
STRIPE_PRICE_IDS = stripe_price_ids()


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


def normalize_plan(plan: str | None) -> str:
    key = (plan or "").strip().lower()
    if key in PLAN_TIERS:
        return key
    raise ValueError(f"Invalid plan: {plan}")


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


def price_id_for(currency: str | None, plan: str) -> str | None:
    cur = normalize_currency(currency)
    tier = normalize_plan(plan)
    return stripe_price_ids().get(cur, {}).get(tier)


def plan_from_price_id(price_id: str | None) -> str | None:
    if not price_id:
        return None
    for _currency, plans in stripe_price_ids().items():
        for plan, pid in plans.items():
            if pid and pid == price_id:
                return plan
    return None


def catalogue_for_currency(currency: str | None) -> list[dict]:
    """Plans with display amounts + whether a Stripe Price ID is configured."""
    cur = normalize_currency(currency)
    cfg = PRICE_DISPLAY[cur]
    ids = stripe_price_ids()[cur]
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
