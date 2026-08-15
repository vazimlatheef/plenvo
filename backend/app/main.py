from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.trainings import router as trainings_router
from app.api.v1.ai import router as ai_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.organisations import router as organisations_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router
from app.db.session import init_db


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://plenvo.io",
        "https://www.plenvo.io",
        "https://plenvo-two.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(trainings_router)
app.include_router(assignments_router)
app.include_router(ai_router)
app.include_router(organisations_router, prefix="/api/v1")
app.include_router(contacts_router)
app.include_router(projects_router)
app.include_router(tasks_router)