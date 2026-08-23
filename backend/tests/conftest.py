"""Shared pytest fixtures (in-memory SQLite — independent of app DATABASE_URL)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def stripe_test_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.core.config.settings.stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.stripe_price_id_personal", "price_personal_test")
    monkeypatch.setattr("app.core.config.settings.stripe_price_id_team", "price_team_test")
    monkeypatch.setattr("app.core.config.settings.stripe_price_id_enterprise", "price_enterprise_test")
