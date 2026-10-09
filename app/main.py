"""Pizza Platform REST API."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pizza_core.fastapi import RequestIdMiddleware, install_exception_handlers
from pizza_core.observability import configure_logging

from app import __version__
from app.api.routes import health, menu, orders, promo_codes
from app.settings import get_settings

API_PREFIX = "/api/v1"

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(
        service_name="pizza-backend",
        level=settings.log_level,
        json_output=settings.app_env not in ("local", "test"),
    )

    app = FastAPI(
        title="Pizza Platform API",
        version=__version__,
        # OpenAPI docs are disabled in prod
        docs_url=None if settings.app_env == "prod" else "/docs",
        redoc_url=None,
    )

    app.add_middleware(RequestIdMiddleware)
    # Allowed origins come from CORS_ALLOWED_ORIGINS (gcp repo: frontend URL + extra_cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    install_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(menu.router, prefix=API_PREFIX)
    app.include_router(orders.router, prefix=API_PREFIX)
    app.include_router(promo_codes.router, prefix=API_PREFIX)

    logger.info("Application configured", extra={"env": settings.app_env})
    return app


app = create_app()
