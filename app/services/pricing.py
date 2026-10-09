"""Order pricing rules (Confluence: PIZZA / Pricing & Delivery).

The frontend shows a cart preview with the same rules (frontend src/utils/pricing.ts),
the values calculated here are the source of truth.
"""

from dataclasses import dataclass

from pizza_core.money import Money

DELIVERY_FEE = Money.of("9.99")
# PIZZA-58: free delivery from 60 PLN, checked AFTER the promo code discount
FREE_DELIVERY_THRESHOLD = Money.of("60.00")


@dataclass(frozen=True)
class PricedLine:
    unit_price: Money
    quantity: int

    @property
    def line_total(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class PriceBreakdown:
    subtotal: Money
    discount: Money
    delivery_fee: Money
    total: Money


def calculate_price(lines: list[PricedLine], discount_percent: int = 0) -> PriceBreakdown:
    subtotal = sum((line.line_total for line in lines), Money.zero())
    discount = subtotal.percent_of(discount_percent) if discount_percent else Money.zero()
    after_discount = subtotal - discount
    delivery_fee = Money.zero() if after_discount >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE
    return PriceBreakdown(
        subtotal=subtotal,
        discount=discount,
        delivery_fee=delivery_fee,
        total=after_discount + delivery_fee,
    )
