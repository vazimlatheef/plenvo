from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env — always relative to this package, not the shell cwd
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    frontend_url: str = "http://localhost:5173"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_product_image_url: str = ""

    # One multi-currency Price ID per plan (currency passed at Checkout time)
    stripe_price_id_personal: str = ""
    stripe_price_id_team: str = ""
    stripe_price_id_enterprise: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: object) -> str:
        if v is None:
            raise RuntimeError(
                "DATABASE_URL is None; DATABASE_URL must be set in the environment."
            )
        if not isinstance(v, str) or not v.strip():
            raise RuntimeError(
                "DATABASE_URL is empty; DATABASE_URL must be set in the environment."
            )
        allowed_prefixes = (
            "postgresql://",
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
        )
        if not v.startswith(allowed_prefixes):
            raise RuntimeError(
                'DATABASE_URL does not start with "postgresql://", '
                '"postgresql+psycopg://", or "postgresql+psycopg2://"; '
                "DATABASE_URL must be set in the environment."
            )
        return v


settings = Settings()
