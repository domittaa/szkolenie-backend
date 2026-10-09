from pizza_core.money import Money

from app.services.pricing import DELIVERY_FEE, PricedLine, calculate_price


def test_delivery_fee_below_threshold() -> None:
    price = calculate_price([PricedLine(Money.of("29.99"), 1)])

    assert price.subtotal == Money.of("29.99")
    assert price.delivery_fee == DELIVERY_FEE
    assert price.total == Money.of("39.98")


def test_free_delivery_from_threshold() -> None:
    price = calculate_price([PricedLine(Money.of("30.00"), 2)])

    assert price.delivery_fee == Money.zero()
    assert price.total == Money.of("60.00")


def test_threshold_is_checked_after_discount() -> None:
    # 64.00 - 10% = 57.60, below 60 PLN, so delivery is paid (PIZZA-58)
    price = calculate_price([PricedLine(Money.of("32.00"), 2)], discount_percent=10)

    assert price.discount == Money.of("6.40")
    assert price.delivery_fee == DELIVERY_FEE
    assert price.total == Money.of("67.59")
