"""Promo code validation, called by the cart page before placing an order (PIZZA-91)."""

from fastapi import APIRouter
from pizza_core.errors import FeatureDisabledError

from app.api.deps import CurrentPrincipal, DbSession, SettingsDep
from app.schemas.promo_code import PromoCodeValidateRequest, PromoCodeValidateResponse
from app.services.promo_codes import get_valid_promo_code

router = APIRouter(prefix="/promo-codes", tags=["promo-codes"])


@router.post("/validate", response_model=PromoCodeValidateResponse)
def validate_promo_code(
    data: PromoCodeValidateRequest,
    db: DbSession,
    settings: SettingsDep,
    _: CurrentPrincipal,
) -> PromoCodeValidateResponse:
    if not settings.promo_codes_enabled:
        raise FeatureDisabledError("Promo codes are disabled")
    promo = get_valid_promo_code(db, data.code)
    return PromoCodeValidateResponse(
        code=promo.code,
        discount_percent=promo.discount_percent,
        discount=data.subtotal.percent_of(promo.discount_percent),
        valid_until=promo.valid_until,
    )
