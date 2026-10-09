"""Runtime configuration read from environment variables.

On Cloud Run the variables are set by Terraform in the gcp repo
(``modules/app-environment/services.tf``, ``local.backend_env``).
For local development see ``.env.example``.
"""

from functools import lru_cache

from pizza_core.auth import FIREBASE_JWKS_URL
from pizza_core.db import build_database_url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"  # local | test | dev | prod
    log_level: str = "INFO"
    gcp_project_id: str = "pizza-local"

    # Database: DATABASE_URL wins (local development), otherwise the Cloud SQL socket is used
    database_url: str | None = None
    db_instance_connection_name: str | None = None
    db_name: str = "pizza"
    db_user: str = "pizza_app"
    db_password: str = ""

    # Auth: Identity Platform ID tokens
    auth_issuer: str = "https://securetoken.google.com/pizza-local"
    auth_audience: str = "pizza-local"
    auth_jwks_url: str = FIREBASE_JWKS_URL

    # Messaging
    orders_topic: str = "order-events"
    use_inmemory_events: bool = False  # local development and tests only

    # HTTP
    cors_allowed_origins: str = "http://localhost:5173"  # comma separated

    # Feature flags
    promo_codes_enabled: bool = False  # PIZZA-91

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
