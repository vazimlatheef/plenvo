"""Logged-in password change."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.users import ChangePasswordRequest, change_password
from app.core.security import hash_password, verify_password
from app.models.models import Organisation, User


def _seed_user(db, password: str = "old-secret") -> User:
    org = Organisation(id=1, name="Solo Co", slug="solo-co", plan_tier="personal", currency="GBP")
    db.add(org)
    db.flush()
    user = User(
        id=1,
        organisation_id=org.id,
        email="admin@solo.com",
        password_hash=hash_password(password),
        first_name="Solo",
        last_name="Admin",
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_change_password_success(db):
    user = _seed_user(db)
    result = change_password(
        ChangePasswordRequest(current_password="old-secret", new_password="new-secret1"),
        db,
        user,
    )
    db.refresh(user)
    assert result.message == "Your password has been updated."
    assert verify_password("new-secret1", user.password_hash)
    assert not verify_password("old-secret", user.password_hash)


def test_change_password_rejects_wrong_current(db):
    user = _seed_user(db)
    with pytest.raises(HTTPException) as exc:
        change_password(
            ChangePasswordRequest(current_password="wrong-pass", new_password="new-secret1"),
            db,
            user,
        )
    assert exc.value.status_code == 400
    assert "incorrect" in exc.value.detail.lower()
    db.refresh(user)
    assert verify_password("old-secret", user.password_hash)


def test_change_password_rejects_same_password(db):
    user = _seed_user(db)
    with pytest.raises(HTTPException) as exc:
        change_password(
            ChangePasswordRequest(current_password="old-secret", new_password="old-secret"),
            db,
            user,
        )
    assert exc.value.status_code == 400
