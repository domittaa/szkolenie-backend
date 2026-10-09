"""Seed a local database with a sample menu and a promo code: ``python -m scripts.seed``."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db import get_session_factory
from app.models import MenuItem, PromoCode

MENU = [
    ("Margherita", "Sos pomidorowy, mozzarella, bazylia", "pizza", "29.99", ["vegetarian"]),
    ("Pepperoni", "Sos pomidorowy, mozzarella, pikantne salami", "pizza", "34.99", ["spicy"]),
    ("Quattro Formaggi", "Mozzarella, gorgonzola, parmezan, ricotta", "pizza", "37.99", []),
    ("Wegańska", "Sos pomidorowy, ser roślinny, papryka, cukinia", "pizza", "33.99", ["vegan"]),
    ("Pieczywo czosnkowe", "4 kawałki, masło czosnkowe", "side", "12.99", ["vegetarian"]),
    ("Lemoniada", "0,5 l, domowa", "drink", "11.99", ["vegan"]),
    ("Tiramisu", "Porcja 150 g", "dessert", "16.99", ["vegetarian"]),
]


def main() -> None:
    with get_session_factory()() as db:
        if db.scalar(select(MenuItem).limit(1)) is not None:
            print("Menu already seeded, nothing to do")
            return
        for name, description, category, price, tags in MENU:
            db.add(
                MenuItem(
                    name=name,
                    description=description,
                    category=category,
                    price_amount=Decimal(price),
                    tags=tags,
                )
            )
        now = datetime.now(UTC)
        db.add(
            PromoCode(
                code="PIZZA10",
                discount_percent=10,
                valid_from=now,
                valid_until=now + timedelta(days=90),
            )
        )
        db.commit()
        print(f"Seeded {len(MENU)} menu items and promo code PIZZA10")


if __name__ == "__main__":
    main()
