"""Conservative name/title matching for AI-extracted mentions.

Only returns a match when exactly one candidate is a clear hit.
Ambiguous first names (or close ties) yield None — never guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

# Exact full-name / title always wins. Fuzzy needs a high ratio.
_FUZZY_FULL_MIN = 0.88
_FUZZY_FIRST_MIN = 0.94  # first-name-only fuzzy is stricter
_FUZZY_PROJECT_MIN = 0.88


def _norm(text: str | None) -> str:
    if not text:
        return ""
    # Collapse whitespace, lowercase, strip punctuation noise around tokens.
    cleaned = re.sub(r"[^\w\s'@.+-]", " ", text.strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokens(text: str) -> list[str]:
    return [t for t in _norm(text).split() if t]


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


@dataclass(frozen=True)
class PersonCandidate:
    kind: Literal["user", "contact"]
    id: int
    full_name: str
    first_name: str
    # When a contact is linked to a user, prefer the user id downstream.
    linked_user_id: int | None = None


@dataclass(frozen=True)
class PersonMatch:
    kind: Literal["user", "contact"]
    id: int
    display_name: str  # Canonical casing from User/Contact, never the raw query.


@dataclass(frozen=True)
class _Scored:
    candidate: PersonCandidate
    score: float
    tier: int  # lower = better (0 exact full, 1 exact first, 2 fuzzy full, 3 fuzzy first)


def _score_person(query: str, query_tokens: list[str], person: PersonCandidate) -> _Scored | None:
    full = _norm(person.full_name)
    first = _norm(person.first_name) or (_tokens(full)[0] if full else "")
    if not full and not first:
        return None

    if query == full and full:
        return _Scored(person, 1.0, 0)

    # Full query equals first name only (e.g. "Sarah")
    if len(query_tokens) == 1 and first and query == first:
        return _Scored(person, 1.0, 1)

    # Multi-token query: first token matches first name and remaining matches last
    if len(query_tokens) >= 2 and first and query_tokens[0] == first:
        last = _norm(" ".join(_tokens(full)[1:])) if full else ""
        rest = " ".join(query_tokens[1:])
        if last and (rest == last or _ratio(rest, last) >= _FUZZY_FULL_MIN):
            return _Scored(person, 1.0 if rest == last else _ratio(rest, last), 0 if rest == last else 2)

    full_r = _ratio(query, full) if full else 0.0
    if full_r >= _FUZZY_FULL_MIN:
        return _Scored(person, full_r, 2)

    # Only allow first-name fuzzy when the query itself is a single token
    if len(query_tokens) == 1 and first:
        first_r = _ratio(query, first)
        if first_r >= _FUZZY_FIRST_MIN:
            return _Scored(person, first_r, 3)

    return None


def match_person(name: str | None, people: list[PersonCandidate]) -> PersonMatch | None:
    """Return a unique person match, or None if missing / ambiguous."""
    query = _norm(name)
    if not query or not people:
        return None

    query_tokens = _tokens(query)
    scored: list[_Scored] = []
    for person in people:
        hit = _score_person(query, query_tokens, person)
        if hit:
            scored.append(hit)

    if not scored:
        return None

    best_tier = min(s.tier for s in scored)
    top = [s for s in scored if s.tier == best_tier]
    # Within the best tier, require a clear unique winner (no near-ties of distinct people).
    top.sort(key=lambda s: s.score, reverse=True)
    best = top[0]
    distinct_ids: set[tuple[str, int]] = set()
    for s in top:
        # Collapse linked contact+user to the same identity when possible
        if s.candidate.kind == "contact" and s.candidate.linked_user_id is not None:
            distinct_ids.add(("user", s.candidate.linked_user_id))
        else:
            distinct_ids.add((s.candidate.kind, s.candidate.id))

    if len(distinct_ids) != 1:
        return None

    # Prefer user when the unique identity is a linked contact
    chosen = best.candidate
    if chosen.kind == "contact" and chosen.linked_user_id is not None:
        user_cand = next(
            (p for p in people if p.kind == "user" and p.id == chosen.linked_user_id),
            None,
        )
        display = (user_cand.full_name if user_cand else chosen.full_name).strip()
        return PersonMatch(kind="user", id=chosen.linked_user_id, display_name=display)

    return PersonMatch(kind=chosen.kind, id=chosen.id, display_name=chosen.full_name.strip())


def match_project(name: str | None, projects: list[tuple[int, str]]) -> tuple[int, str] | None:
    """Return (project id, canonical title) if exactly one clear match, else None."""
    query = _norm(name)
    if not query or not projects:
        return None

    exact: list[tuple[int, str]] = []
    fuzzy: list[tuple[float, int, str]] = []
    for pid, title in projects:
        t = _norm(title)
        if not t:
            continue
        if query == t:
            exact.append((pid, title))
            continue
        # Containment: query is full title or title contains query as whole phrase
        if query in t or t in query:
            fuzzy.append((0.95, pid, title))
            continue
        r = _ratio(query, t)
        if r >= _FUZZY_PROJECT_MIN:
            fuzzy.append((r, pid, title))

    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None

    if not fuzzy:
        return None
    fuzzy.sort(key=lambda x: x[0], reverse=True)
    best_score, best_id, best_title = fuzzy[0]
    # Ambiguous if another candidate is within 0.03
    rivals = [(pid, title) for score, pid, title in fuzzy if score >= best_score - 0.03]
    distinct = {(pid, _norm(title)) for pid, title in rivals}
    if len(distinct) != 1:
        return None
    return best_id, best_title


def build_person_candidates(*, users, contacts) -> list[PersonCandidate]:
    people: list[PersonCandidate] = []
    for u in users:
        first = (getattr(u, "first_name", None) or "").strip()
        last = (getattr(u, "last_name", None) or "").strip()
        full = f"{first} {last}".strip() or (getattr(u, "full_name", None) or "")
        if not full and not first:
            continue
        people.append(
            PersonCandidate(
                kind="user",
                id=u.id,
                full_name=full,
                first_name=first or (_tokens(full)[0] if full else ""),
            )
        )
    for c in contacts:
        name = (getattr(c, "name", None) or "").strip()
        if not name:
            continue
        parts = name.split(None, 1)
        people.append(
            PersonCandidate(
                kind="contact",
                id=c.id,
                full_name=name,
                first_name=parts[0],
                linked_user_id=getattr(c, "user_id", None),
            )
        )
    return people
