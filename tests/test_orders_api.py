from fastapi.testclient import TestClient
from pizza_core.events import InMemoryPublisher
from sqlalchemy.orm import Session

from app.models import MenuItem
from tests.helpers import (
    CUSTOMER,
    OTHER_CUSTOMER,
    STAFF,
    FakeAuth,
    add_promo_code,
    order_payload,
    place_order,
)


def test_place_order_calculates_price_and_publishes_event(
    client: TestClient, margherita: MenuItem, publisher: InMemoryPublisher
) -> None:
    response = client.post("/api/v1/orders", json=order_payload(margherita, quantity=2))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["subtotal"] == {"amount": "59.98", "currency": "PLN"}
    assert body["delivery_fee"] == {"amount": "9.99", "currency": "PLN"}
    assert body["total"] == {"amount": "69.97", "currency": "PLN"}
    assert [event.event_type for event in publisher.events] == ["order.created"]


def test_quantity_is_limited_to_20(client: TestClient, margherita: MenuItem) -> None:
    response = client.post("/api/v1/orders", json=order_payload(margherita, quantity=21))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unavailable_item_cannot_be_ordered(
    client: TestClient, db: Session, margherita: MenuItem
) -> None:
    margherita.is_available = False
    db.commit()

    response = client.post("/api/v1/orders", json=order_payload(margherita))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MENU_ITEM_UNAVAILABLE"


def test_promo_code_is_case_insensitive(
    client: TestClient, db: Session, margherita: MenuItem
) -> None:
    add_promo_code(db, code="PIZZA10", discount_percent=10)

    response = client.post(
        "/api/v1/orders", json=order_payload(margherita, quantity=3, promo_code="pizza10")
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["promo_code"] == "PIZZA10"
    assert body["discount"] == {"amount": "9.00", "currency": "PLN"}  # 10% of 89.97
    assert body["delivery_fee"] == {"amount": "0.00", "currency": "PLN"}  # 80.97 >= 60.00


def test_customer_cannot_change_status(client: TestClient, margherita: MenuItem) -> None:
    order_id = place_order(client, margherita)

    response = client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "confirmed"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_customer_cannot_cancel_order_in_preparation(
    client: TestClient, auth: FakeAuth, margherita: MenuItem
) -> None:
    order_id = place_order(client, margherita)
    auth.principal = STAFF
    for status in ("confirmed", "preparing"):
        response = client.patch(f"/api/v1/orders/{order_id}/status", json={"status": status})
        assert response.status_code == 200, response.text

    auth.principal = CUSTOMER
    response = client.post(f"/api/v1/orders/{order_id}/cancel")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"


def test_invalid_transition_is_rejected(
    client: TestClient, auth: FakeAuth, margherita: MenuItem
) -> None:
    order_id = place_order(client, margherita)
    auth.principal = STAFF

    response = client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "delivered"})

    assert response.status_code == 409
    assert response.json()["error"]["details"]["allowed"] == ["cancelled", "confirmed"]


def test_other_customers_orders_are_hidden(
    client: TestClient, auth: FakeAuth, margherita: MenuItem
) -> None:
    order_id = place_order(client, margherita)
    auth.principal = OTHER_CUSTOMER

    assert client.get(f"/api/v1/orders/{order_id}").status_code == 404
    assert client.get("/api/v1/orders").json()["total"] == 0


def test_list_orders_is_paginated(client: TestClient, margherita: MenuItem) -> None:
    for _ in range(3):
        place_order(client, margherita)

    body = client.get("/api/v1/orders", params={"page": 1, "page_size": 2}).json()

    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["has_next"] is True
    assert body["items"][0]["items_count"] == 1
