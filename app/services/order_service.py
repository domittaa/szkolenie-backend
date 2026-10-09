"""Order use cases: place, list, read, cancel and move through the lifecycle."""

import logging
import uuid

from pizza_core.auth import Principal, Role
from pizza_core.errors import DomainError, ErrorCode, FeatureDisabledError, NotFoundError
from pizza_core.events import EventPublisher, OrderEvent, OrderEventType
from pizza_core.money import Money
from pizza_core.pagination import Page
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MenuItem, Order, OrderItem
from app.schemas.order import OrderCreate, OrderListParams, OrderOut, OrderStatus, OrderSummaryOut
from app.services.order_status import ensure_customer_can_cancel, ensure_transition_allowed
from app.services.pricing import PricedLine, calculate_price
from app.services.promo_codes import get_valid_promo_code

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self, db: Session, publisher: EventPublisher, *, promo_codes_enabled: bool
    ) -> None:
        self.db = db
        self.publisher = publisher
        self.promo_codes_enabled = promo_codes_enabled

    def place_order(self, principal: Principal, data: OrderCreate) -> OrderOut:
        menu_ids = {line.menu_item_id for line in data.items}
        menu = {m.id: m for m in self.db.scalars(select(MenuItem).where(MenuItem.id.in_(menu_ids)))}

        lines: list[PricedLine] = []
        order_items: list[OrderItem] = []
        for line in data.items:
            menu_item = menu.get(line.menu_item_id)
            if menu_item is None:
                raise NotFoundError(
                    "Menu item not found", details={"menu_item_id": str(line.menu_item_id)}
                )
            if not menu_item.is_available:
                raise DomainError(
                    f"'{menu_item.name}' is currently unavailable",
                    code=ErrorCode.MENU_ITEM_UNAVAILABLE,
                    details={"menu_item_id": str(menu_item.id)},
                )
            unit_price = Money.of(menu_item.price_amount, menu_item.currency)
            lines.append(PricedLine(unit_price=unit_price, quantity=line.quantity))
            order_items.append(
                OrderItem(
                    menu_item_id=menu_item.id,
                    name=menu_item.name,
                    unit_price_amount=unit_price.amount,
                    quantity=line.quantity,
                    notes=line.notes,
                )
            )

        discount_percent = 0
        promo_code: str | None = None
        if data.promo_code:
            if not self.promo_codes_enabled:
                raise FeatureDisabledError("Promo codes are disabled")
            promo = get_valid_promo_code(self.db, data.promo_code)
            promo.times_used += 1
            discount_percent = promo.discount_percent
            promo_code = promo.code

        price = calculate_price(lines, discount_percent)
        order = Order(
            customer_id=principal.user_id,
            status=OrderStatus.PENDING.value,
            subtotal_amount=price.subtotal.amount,
            discount_amount=price.discount.amount,
            delivery_fee_amount=price.delivery_fee.amount,
            total_amount=price.total.amount,
            promo_code=promo_code,
            delivery_address=data.delivery_address,
            phone=data.phone,
            items=order_items,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        self.publisher.publish(
            OrderEvent(
                event_type=OrderEventType.ORDER_CREATED,
                order_id=str(order.id),
                payload={
                    "customer_id": order.customer_id,
                    "total": price.total.model_dump(mode="json"),
                },
            )
        )
        logger.info("Order placed", extra={"order_id": str(order.id), "total": str(price.total)})
        return OrderOut.from_model(order)

    def list_orders(self, principal: Principal, params: OrderListParams) -> Page[OrderSummaryOut]:
        """Customers see their own orders, staff see all of them."""
        query = select(Order)
        if not principal.has_any_role(Role.STAFF):
            query = query.where(Order.customer_id == principal.user_id)
        if params.status is not None:
            query = query.where(Order.status == params.status.value)

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        orders = self.db.scalars(
            query.order_by(Order.created_at.desc()).offset(params.offset).limit(params.limit)
        )
        return Page[OrderSummaryOut].create(
            [OrderSummaryOut.from_model(order) for order in orders], total=total, params=params
        )

    def get_order(self, principal: Principal, order_id: uuid.UUID) -> OrderOut:
        return OrderOut.from_model(self._get_visible_order(principal, order_id))

    def cancel_order(self, principal: Principal, order_id: uuid.UUID) -> OrderOut:
        order = self._get_visible_order(principal, order_id)
        current = OrderStatus(order.status)
        if principal.has_any_role(Role.STAFF):
            ensure_transition_allowed(current, OrderStatus.CANCELLED)
        else:
            ensure_customer_can_cancel(current)
        return self._set_status(order, OrderStatus.CANCELLED, changed_by=principal)

    def change_status(
        self, principal: Principal, order_id: uuid.UUID, target: OrderStatus
    ) -> OrderOut:
        """Staff only, the role is checked by the route dependency."""
        order = self._get_visible_order(principal, order_id)
        ensure_transition_allowed(OrderStatus(order.status), target)
        return self._set_status(order, target, changed_by=principal)

    def _get_visible_order(self, principal: Principal, order_id: uuid.UUID) -> Order:
        order = self.db.get(Order, order_id)
        is_owner = order is not None and order.customer_id == principal.user_id
        if order is None or not (is_owner or principal.has_any_role(Role.STAFF)):
            # 404 instead of 403: do not reveal that other customers' orders exist
            raise NotFoundError("Order not found", details={"order_id": str(order_id)})
        return order

    def _set_status(self, order: Order, target: OrderStatus, *, changed_by: Principal) -> OrderOut:
        previous = order.status
        order.status = target.value
        self.db.commit()
        self.db.refresh(order)

        event_type = (
            OrderEventType.ORDER_CANCELLED
            if target is OrderStatus.CANCELLED
            else OrderEventType.ORDER_STATUS_CHANGED
        )
        self.publisher.publish(
            OrderEvent(
                event_type=event_type,
                order_id=str(order.id),
                payload={"from": previous, "to": target.value, "changed_by": changed_by.user_id},
            )
        )
        return OrderOut.from_model(order)
