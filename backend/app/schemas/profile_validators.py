"""Shared validation for optional professional profile fields."""

from __future__ import annotations

import re

# International-friendly: optional +, digits, spaces, (), ., - ; 7–24 meaningful chars.
_PHONE_RE = re.compile(r"^\+?[\d\s().\-]{7,32}$")
# Accepts https://linkedin.com/in/handle or www.linkedin.com/in/handle (optional trailing slash).
_LINKEDIN_RE = re.compile(
    r"^(https?://)?(www\.)?linkedin\.com/in/[\w\-.%]+/?$",
    re.IGNORECASE,
)


def normalize_optional_str(value: str | None, *, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if max_len is not None and len(text) > max_len:
        raise ValueError(f"Must be at most {max_len} characters.")
    return text


def validate_phone(value: str | None) -> str | None:
    text = normalize_optional_str(value, max_len=64)
    if text is None:
        return None
    if not _PHONE_RE.match(text):
        raise ValueError("Enter a valid phone number (international formats accepted).")
    return text


def validate_linkedin_url(value: str | None) -> str | None:
    text = normalize_optional_str(value, max_len=2048)
    if text is None:
        return None
    if not _LINKEDIN_RE.match(text):
        raise ValueError("LinkedIn URL must look like https://linkedin.com/in/your-profile")
    # Normalize to https://www.linkedin.com/in/...
    handle = text.split("/in/", 1)[1].rstrip("/")
    return f"https://www.linkedin.com/in/{handle}"
