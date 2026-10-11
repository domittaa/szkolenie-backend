"""Menu API schemas (frontend: ``MenuItem`` in src/api/types.ts)."""

import uuid
from enum import StrEnum

from pizza_core.money import Money
from pydantic import BaseModel, Field

from app.models import MenuItem


class MenuCategory(StrEnum):
    PIZZA = "pizza"
    SIDE = "side"
    DRINK = "drink"
    DESSERT = "dessert"


class MenuItemOut(BaseModel):
    id: uuid.UUID
    name: str
    english_name: str
    description: str
    category: MenuCategory
    price: Money
    is_available: bool
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)


    @classmethod
    def from_model(cls, item: MenuItem) -> "MenuItemOut":
        return cls(
            id=item.id,
            name=item.name,
            english_name=item.english_name,
            description=item.description,
            category=MenuCategory(item.category),
            price=Money.of(item.price_amount, item.currency),
            is_available=item.is_available,
            image_url=item.image_url,
            tags=list(item.tags or []),
        )


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    category: MenuCategory
    price: Money
    is_available: bool = True
    image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=10)


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: Money | None = None
    is_available: bool | None = None
    image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=10)
