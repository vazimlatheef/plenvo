from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base  # noqa: F401 — package import registers User, Training, Assignment

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create missing tables only. Never drops or resets existing data.

    Schema changes go through Alembic migrations under backend/alembic/.
    """
    Base.metadata.create_all(bind=engine)
