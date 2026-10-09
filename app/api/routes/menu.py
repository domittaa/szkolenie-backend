"""Menu API. Reading is public, changes require the admin role."""

import uuid

from fastapi import APIRouter, status
from pizza_core.errors import NotFoundError
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.api.deps import AdminPrincipal, DbSession
from app.models import MenuItem
from app.schemas.menu import MenuCategory, MenuItemCreate, MenuItemOut, MenuItemUpdate

router = APIRouter(prefix="/menu", tags=["menu"])

# categories in the order of the MenuCategory enum: pizza, side, drink, dessert
_CATEGORY_ORDER = case(
    {category.value: rank for rank, category in enumerate(MenuCategory)},
    value=MenuItem.category,
    else_=len(MenuCategory),
)


@router.get("", response_model=list[MenuItemOut])
def list_menu(
    db: DbSession, category: MenuCategory | None = None, available_only: bool = True
) -> list[MenuItemOut]:
    query = select(MenuItem).order_by(_CATEGORY_ORDER, MenuItem.name)
    if category is not None:
        query = query.where(MenuItem.category == category.value)
    if available_only:
        query = query.where(MenuItem.is_available.is_(True))
    return [MenuItemOut.from_model(item) for item in db.scalars(query)]


@router.get("/{item_id}", response_model=MenuItemOut)
def get_menu_item(item_id: uuid.UUID, db: DbSession) -> MenuItemOut:
    return MenuItemOut.from_model(_get_or_404(db, item_id))


@router.post("", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def create_menu_item(data: MenuItemCreate, db: DbSession, _: AdminPrincipal) -> MenuItemOut:
    item = MenuItem(
        name=data.name,
        description=data.description,
        category=data.category.value,
        price_amount=data.price.amount,
        currency=data.price.currency,
        is_available=data.is_available,
        image_url=data.image_url,
        tags=data.tags,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MenuItemOut.from_model(item)


@router.patch("/{item_id}", response_model=MenuItemOut)
def update_menu_item(
    item_id: uuid.UUID, data: MenuItemUpdate, db: DbSession, _: AdminPrincipal
) -> MenuItemOut:
    item = _get_or_404(db, item_id)
    if data.price is not None:
        item.price_amount = data.price.amount
        item.currency = data.price.currency
    for field in ("name", "description", "is_available", "image_url", "tags"):
        if field in data.model_fields_set:
            setattr(item, field, getattr(data, field))
    db.commit()
    db.refresh(item)
    return MenuItemOut.from_model(item)


def _get_or_404(db: Session, item_id: uuid.UUID) -> MenuItem:
    item = db.get(MenuItem, item_id)
    if item is None:
        raise NotFoundError("Menu item not found", details={"menu_item_id": str(item_id)})
    return item
