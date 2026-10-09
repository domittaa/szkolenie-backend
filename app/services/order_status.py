"""Order lifecycle state machine (Confluence: PIZZA / Order Lifecycle).

    pending -> confirmed -> preparing -> out_for_delivery -> delivered
       |           |
       +-----------+-> cancelled

Mirrored in the frontend kitchen panel: src/utils/orderStatus.ts (NEXT_STATUSES).
"""

from pizza_core.errors import DomainError, ErrorCode

from app.schemas.order import OrderStatus

ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.PREPARING, OrderStatus.CANCELLED}),
    OrderStatus.PREPARING: frozenset({OrderStatus.OUT_FOR_DELIVERY}),
    OrderStatus.OUT_FOR_DELIVERY: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}

# PIZZA-73: customers can cancel only before the kitchen starts preparing the order
CUSTOMER_CANCELLABLE = frozenset({OrderStatus.PENDING, OrderStatus.CONFIRMED})


class InvalidStatusTransitionError(DomainError):
    http_status = 409
    code = ErrorCode.INVALID_STATUS_TRANSITION


class OrderNotCancellableError(DomainError):
    http_status = 409
    code = ErrorCode.ORDER_NOT_CANCELLABLE


def ensure_transition_allowed(current: OrderStatus, target: OrderStatus) -> None:
    allowed = ALLOWED_TRANSITIONS[current]
    if target not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot change order status from '{current}' to '{target}'",
            details={
                "from": current.value,
                "to": target.value,
                "allowed": sorted(status.value for status in allowed),
            },
        )


def ensure_customer_can_cancel(current: OrderStatus) -> None:
    if current not in CUSTOMER_CANCELLABLE:
        raise OrderNotCancellableError(
            f"Order in status '{current}' cannot be cancelled", details={"status": current.value}
        )
