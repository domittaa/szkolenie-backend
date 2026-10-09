from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import MenuItem
from tests.helpers import ADMIN, STAFF, FakeAuth


def test_menu_is_public_and_hides_unavailable_items(
    client: TestClient, db: Session, margherita: MenuItem
) -> None:
    db.add(
        MenuItem(
            name="Hawajska", category="pizza", price_amount=Decimal("31.99"), is_available=False
        )
    )
    db.commit()

    response = client.get("/api/v1/menu")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Margherita"]
    assert response.json()[0]["price"] == {"amount": "29.99", "currency": "PLN"}


def test_menu_is_sorted_by_category_then_name(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            MenuItem(name="Tiramisu", category="dessert", price_amount=Decimal("16.99")),
            MenuItem(name="Lemoniada", category="drink", price_amount=Decimal("11.99")),
            MenuItem(name="Pepperoni", category="pizza", price_amount=Decimal("34.99")),
            MenuItem(name="Margherita", category="pizza", price_amount=Decimal("29.99")),
        ]
    )
    db.commit()

    names = [item["name"] for item in client.get("/api/v1/menu").json()]

    assert names == ["Margherita", "Pepperoni", "Lemoniada", "Tiramisu"]


def test_only_admin_can_create_menu_items(client: TestClient, auth: FakeAuth) -> None:
    payload = {
        "name": "Capricciosa",
        "category": "pizza",
        "price": {"amount": "36.99", "currency": "PLN"},
    }

    auth.principal = STAFF
    assert client.post("/api/v1/menu", json=payload).status_code == 403

    auth.principal = ADMIN
    response = client.post("/api/v1/menu", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["price"] == {"amount": "36.99", "currency": "PLN"}


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
