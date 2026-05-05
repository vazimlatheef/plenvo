from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.trainings import router as trainings_router
from app.api.v1.ai import router as ai_router
from app.db.session import init_db
from app.api.v1.organisations import router as organisations_router
app.include_router(organisations_router)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except OperationalError as e:
        raise RuntimeError(
            "PostgreSQL connection failed. Fix DATABASE_URL: user, password, host, port, and database "
            "must match your server. URL-encode special characters in the password. "
            "Example: postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/Plenvo"
        ) from e
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(trainings_router)
app.include_router(assignments_router)
app.include_router(ai_router)