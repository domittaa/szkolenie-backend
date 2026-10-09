"""Promo code schemas (frontend: ``PromoCodeValidation`` in src/api/types.ts)."""

from pizza_core.money import Money
from pydantic import BaseModel, Field

from app.schemas.common import UtcDatetime


class PromoCodeValidateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=32)
    subtotal: Money


class PromoCodeValidateResponse(BaseModel):
    code: str
    discount_percent: int
    discount: Money
    valid_until: UtcDatetime
