import pytest

from app.schemas.order import OrderStatus
from app.services.order_status import (
    InvalidStatusTransitionError,
    OrderNotCancellableError,
    ensure_customer_can_cancel,
    ensure_transition_allowed,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OrderStatus.PENDING, OrderStatus.CONFIRMED),
        (OrderStatus.PENDING, OrderStatus.CANCELLED),
        (OrderStatus.CONFIRMED, OrderStatus.PREPARING),
        (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
        (OrderStatus.PREPARING, OrderStatus.OUT_FOR_DELIVERY),
        (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED),
    ],
)
def test_allowed_transitions(current: OrderStatus, target: OrderStatus) -> None:
    ensure_transition_allowed(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OrderStatus.PENDING, OrderStatus.DELIVERED),
        (OrderStatus.PREPARING, OrderStatus.CANCELLED),
        (OrderStatus.DELIVERED, OrderStatus.PENDING),
        (OrderStatus.CANCELLED, OrderStatus.CONFIRMED),
    ],
)
def test_forbidden_transitions(current: OrderStatus, target: OrderStatus) -> None:
    with pytest.raises(InvalidStatusTransitionError):
        ensure_transition_allowed(current, target)


def test_customer_cannot_cancel_after_preparation_started() -> None:
    ensure_customer_can_cancel(OrderStatus.CONFIRMED)
    with pytest.raises(OrderNotCancellableError):
        ensure_customer_can_cancel(OrderStatus.PREPARING)
