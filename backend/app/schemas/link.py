import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

_DOMAIN_LIKE = re.compile(r"^([\w-]+\.)+[\w-]{2,}(/.*)?$", re.IGNORECASE)
_HAS_PROTOCOL = re.compile(r"^https?://", re.IGNORECASE)


def _normalize_link_url(value: str) -> str:
    v = value.strip()
    if not v:
        return v
    if _HAS_PROTOCOL.match(v):
        return v
    if _DOMAIN_LIKE.match(v) or v.lower().startswith("www."):
        return f"https://{v}"
    return v


class LinkItem(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=2000)

    @field_validator("label", "url")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("url")
    @classmethod
    def _normalize_url(cls, v: str) -> str:
        return _normalize_link_url(v)


def normalize_links(raw: Optional[List[dict]]) -> Optional[List[dict]]:
    """Validate and dedupe links; returns None when empty."""
    if not raw:
        return None
    seen = set()
    out: list[dict] = []
    for item in raw:
        try:
            link = LinkItem.model_validate(item)
        except Exception:
            continue
        key = (link.label.lower(), link.url.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(link.model_dump())
    return out or None
