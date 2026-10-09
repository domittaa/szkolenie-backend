"""Runtime configuration read from environment variables.

On Cloud Run the variables are set by Terraform in the gcp repo
(``modules/app-environment/services.tf``, ``local.backend_env``).
For local development see ``.env.example`` (SQLite and dev login, no GCP needed).
"""

from functools import lru_cache
from typing import Self

from pizza_core.auth import FIREBASE_JWKS_URL
from pizza_core.db import build_database_url
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"  # local | test | dev | prod
    log_level: str = "INFO"
    gcp_project_id: str = "pizza-local"

    # Database: DATABASE_URL wins (local SQLite or PostgreSQL), otherwise the Cloud SQL socket
    database_url: str | None = None
    db_instance_connection_name: str | None = None
    db_name: str = "pizza"
    db_user: str = "pizza_app"
    db_password: str = ""

    # Auth: Identity Platform ID tokens
    auth_issuer: str = "https://securetoken.google.com/pizza-local"
    auth_audience: str = "pizza-local"
    auth_jwks_url: str = FIREBASE_JWKS_URL
    # Local login without Identity Platform: accepts "dev:<user_id>:<role>" bearer tokens
    # (app/api/dev_auth.py). Refused outside APP_ENV=local/test.
    dev_auth_enabled: bool = False

    # Messaging
    orders_topic: str = "order-events"
    use_inmemory_events: bool = False  # local development and tests only

    # HTTP
    cors_allowed_origins: str = "http://localhost:5173"  # comma separated

    # Feature flags
    promo_codes_enabled: bool = False  # PIZZA-91

    @model_validator(mode="after")
    def _dev_auth_only_locally(self) -> Self:
        if self.dev_auth_enabled and self.app_env not in ("local", "test"):
            raise ValueError("DEV_AUTH_ENABLED is allowed only with APP_ENV=local or APP_ENV=test")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return build_database_url(
            user=self.db_user,
            password=self.db_password,
            database=self.db_name,
            instance_connection_name=self.db_instance_connection_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
