"""Database wiring. The engine is created lazily on first use."""

from collections.abc import Iterator
from functools import lru_cache

from pizza_core.db import create_db_engine, make_session_factory
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_db_engine(settings.sqlalchemy_url, echo=settings.app_env == "local")


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return make_session_factory(get_engine())


def get_db() -> Iterator[Session]:
    """FastAPI dependency. Services commit explicitly, anything uncommitted is rolled back."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
