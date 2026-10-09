"""Orders API schemas (frontend: ``Order``, ``OrderSummary`` in src/api/types.ts)."""

import uuid
from datetime import datetime
from enum import StrEnum

from pizza_core.money import Money
from pizza_core.pagination import PageParams
from pydantic import BaseModel, Field

from app.models import Order, OrderItem

# PIZZA-64: max 20 pieces of one item per order (mirrored in frontend src/cart/CartContext.tsx)
MAX_QUANTITY_PER_ITEM = 20
PHONE_PATTERN = r"^\+?[0-9 ]{9,15}$"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemIn(BaseModel):
    menu_item_id: uuid.UUID
    quantity: int = Field(ge=1, le=MAX_QUANTITY_PER_ITEM)
    notes: str | None = Field(default=None, max_length=200)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=30)
    promo_code: str | None = Field(default=None, max_length=32)
    delivery_address: str = Field(min_length=5, max_length=300)
    phone: str = Field(pattern=PHONE_PATTERN)


class OrderItemOut(BaseModel):
    menu_item_id: uuid.UUID
    name: str
    quantity: int
    unit_price: Money
    line_total: Money
    notes: str | None = None

    @classmethod
    def from_model(cls, item: OrderItem, currency: str) -> "OrderItemOut":
        unit_price = Money.of(item.unit_price_amount, currency)
        return cls(
            menu_item_id=item.menu_item_id,
            name=item.name,
            quantity=item.quantity,
            unit_price=unit_price,
            line_total=unit_price * item.quantity,
            notes=item.notes,
        )


class OrderOut(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    items: list[OrderItemOut]
    subtotal: Money
    discount: Money
    delivery_fee: Money
    total: Money
    promo_code: str | None = None
    delivery_address: str
    phone: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, order: Order) -> "OrderOut":
        currency = order.currency
        return cls(
            id=order.id,
            status=OrderStatus(order.status),
            items=[OrderItemOut.from_model(item, currency) for item in order.items],
            subtotal=Money.of(order.subtotal_amount, currency),
            discount=Money.of(order.discount_amount, currency),
            delivery_fee=Money.of(order.delivery_fee_amount, currency),
            total=Money.of(order.total_amount, currency),
            promo_code=order.promo_code,
            delivery_address=order.delivery_address,
            phone=order.phone,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderSummaryOut(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total: Money
    items_count: int  # number of pieces, not order lines
    created_at: datetime

    @classmethod
    def from_model(cls, order: Order) -> "OrderSummaryOut":
        return cls(
            id=order.id,
            status=OrderStatus(order.status),
            total=Money.of(order.total_amount, order.currency),
            items_count=sum(item.quantity for item in order.items),
            created_at=order.created_at,
        )


class OrderListParams(PageParams):
    """Query params of GET /orders: ``?page=1&page_size=20&status=pending``."""

    status: OrderStatus | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
