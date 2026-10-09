from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.settings import Settings
from tests.helpers import add_promo_code

SUBTOTAL = {"amount": "59.98", "currency": "PLN"}


def test_validate_promo_code(client: TestClient, db: Session) -> None:
    add_promo_code(db, code="PIZZA10", discount_percent=10)

    response = client.post(
        "/api/v1/promo-codes/validate", json={"code": "pizza10", "subtotal": SUBTOTAL}
    )

    assert response.status_code == 200, response.text
    assert response.json()["discount"] == {"amount": "6.00", "currency": "PLN"}


def test_expired_promo_code(client: TestClient, db: Session) -> None:
    add_promo_code(
        db,
        code="SUMMER20",
        discount_percent=20,
        valid_from=datetime(2026, 6, 1, tzinfo=UTC),
        valid_until=datetime(2026, 8, 31, tzinfo=UTC),
    )

    response = client.post(
        "/api/v1/promo-codes/validate", json={"code": "SUMMER20", "subtotal": SUBTOTAL}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PROMO_CODE_EXPIRED"


def test_promo_codes_behind_feature_flag(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.promo_codes_enabled = False
    add_promo_code(db)

    response = client.post(
        "/api/v1/promo-codes/validate", json={"code": "PIZZA10", "subtotal": SUBTOTAL}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FEATURE_DISABLED"
