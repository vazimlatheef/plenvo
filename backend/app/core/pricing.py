"""Display / Stripe pricing catalogue.

Keep in sync with frontend/src/composables/useCurrency.js.
Actual Stripe Price IDs will be wired later — this module is config + helpers only.
"""

from __future__ import annotations

from typing import Literal

CurrencyCode = Literal["GBP", "EUR", "USD", "INR"]

DEFAULT_CURRENCY: CurrencyCode = "USD"

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

# Minor units for future Stripe Price / Checkout (integer, no separators).
PRICE_MINOR_UNITS: dict[str, dict[str, int]] = {
    "GBP": {"personal": 499, "team": 1999, "enterprise": 3999},
    "EUR": {"personal": 499, "team": 1999, "enterprise": 3999},
    "USD": {"personal": 499, "team": 1999, "enterprise": 3999},
    "INR": {"personal": 49900, "team": 199900, "enterprise": 399900},
}

# Placeholders for Stripe Price IDs — fill when integrating Checkout.
STRIPE_PRICE_IDS: dict[str, dict[str, str | None]] = {
    "GBP": {"personal": None, "team": None, "enterprise": None},
    "EUR": {"personal": None, "team": None, "enterprise": None},
    "USD": {"personal": None, "team": None, "enterprise": None},
    "INR": {"personal": None, "team": None, "enterprise": None},
}


def normalize_currency(code: str | None) -> CurrencyCode:
    key = (code or "").strip().upper()
    if key in SUPPORTED_CURRENCIES:
        return key  # type: ignore[return-value]
    return DEFAULT_CURRENCY


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
