from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pizza_core.events import InMemoryPublisher
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_principal
from app.db import get_db
from app.main import app
from app.models import Base, MenuItem
from app.services.events import get_publisher
from app.settings import Settings, get_settings
from tests.helpers import FakeAuth


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def publisher() -> InMemoryPublisher:
    return InMemoryPublisher()


@pytest.fixture
def auth() -> FakeAuth:
    return FakeAuth()


@pytest.fixture
def settings() -> Settings:
    return Settings(app_env="test", promo_codes_enabled=True, use_inmemory_events=True)


@pytest.fixture
def client(
    db: Session, publisher: InMemoryPublisher, auth: FakeAuth, settings: Settings
) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_publisher] = lambda: publisher
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_principal] = auth
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def margherita(db: Session) -> MenuItem:
    item = MenuItem(
        name="Margherita",
        description="Sos pomidorowy, mozzarella, bazylia",
        category="pizza",
        price_amount=Decimal("29.99"),
        tags=["vegetarian"],
    )
    db.add(item)
    db.commit()
    return item
