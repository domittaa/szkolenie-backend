"""Database wiring. The engine is created lazily on first use."""

from collections.abc import Iterator
from functools import lru_cache

from pizza_core.db import create_db_engine, make_session_factory
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().sqlalchemy_url
    if url.startswith("sqlite"):
        # local development without PostgreSQL (.env.example), requests run in a thread pool
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_db_engine(url)


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
