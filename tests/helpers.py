from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from pizza_core.auth import Principal, Role
from sqlalchemy.orm import Session

from app.models import MenuItem, PromoCode

CUSTOMER = Principal(user_id="customer-1", email="jan@example.com", role=Role.CUSTOMER)
OTHER_CUSTOMER = Principal(user_id="customer-2", email="ola@example.com", role=Role.CUSTOMER)
STAFF = Principal(user_id="staff-1", email="kuchnia@example.com", role=Role.STAFF)
ADMIN = Principal(user_id="admin-1", email="admin@example.com", role=Role.ADMIN)


class FakeAuth:
    """Replaces token verification. Tests switch users with ``auth.principal = STAFF``."""

    def __init__(self) -> None:
        self.principal = CUSTOMER

    def __call__(self) -> Principal:
        return self.principal


def order_payload(item: MenuItem, quantity: int = 1, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "items": [{"menu_item_id": str(item.id), "quantity": quantity}],
        "delivery_address": "ul. Prosta 1, Warszawa",
        "phone": "+48 600 100 200",
    }
    payload.update(overrides)
    return payload


def place_order(client: TestClient, item: MenuItem, quantity: int = 1) -> str:
    response = client.post("/api/v1/orders", json=order_payload(item, quantity))
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def add_promo_code(
    db: Session,
    code: str = "PIZZA10",
    discount_percent: int = 10,
    valid_from: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    valid_until: datetime = datetime(2099, 1, 1, tzinfo=UTC),
) -> PromoCode:
    promo = PromoCode(
        code=code,
        discount_percent=discount_percent,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    db.add(promo)
    db.commit()
    return promo
