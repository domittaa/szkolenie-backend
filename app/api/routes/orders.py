"""Orders API, used by the customer app and the kitchen panel (frontend src/api/orders.ts)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status
from pizza_core.pagination import Page

from app.api.deps import CurrentPrincipal, OrderServiceDep, StaffPrincipal
from app.schemas.order import (
    OrderCreate,
    OrderListParams,
    OrderOut,
    OrderStatusUpdate,
    OrderSummaryOut,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    data: OrderCreate, principal: CurrentPrincipal, service: OrderServiceDep
) -> OrderOut:
    return service.place_order(principal, data)


@router.get("", response_model=Page[OrderSummaryOut])
def list_orders(
    params: Annotated[OrderListParams, Query()],
    principal: CurrentPrincipal,
    service: OrderServiceDep,
) -> Page[OrderSummaryOut]:
    """Customers get their own orders, staff get all orders."""
    return service.list_orders(principal, params)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: uuid.UUID, principal: CurrentPrincipal, service: OrderServiceDep
) -> OrderOut:
    return service.get_order(principal, order_id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: uuid.UUID, principal: CurrentPrincipal, service: OrderServiceDep
) -> OrderOut:
    return service.cancel_order(principal, order_id)


@router.patch("/{order_id}/status", response_model=OrderOut)
def change_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    principal: StaffPrincipal,
    service: OrderServiceDep,
) -> OrderOut:
    return service.change_status(principal, order_id, data.status)
