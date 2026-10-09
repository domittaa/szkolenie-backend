"""Promo codes (PIZZA-91), behind the PROMO_CODES_ENABLED feature flag."""

from datetime import UTC, datetime

from pizza_core.errors import DomainError, ErrorCode
from sqlalchemy.orm import Session

from app.models import PromoCode


class PromoCodeError(DomainError):
    http_status = 400
    code = ErrorCode.PROMO_CODE_INVALID


def normalize_code(code: str) -> str:
    # PIZZA-91: codes are case-insensitive and stored upper-case
    return code.strip().upper()


def _as_utc(value: datetime) -> datetime:
    # SQLite (tests) returns naive datetimes, PostgreSQL returns aware ones
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def get_valid_promo_code(db: Session, raw_code: str, *, now: datetime | None = None) -> PromoCode:
    now = now or datetime.now(UTC)
    promo = db.get(PromoCode, normalize_code(raw_code))
    if promo is None or not promo.is_active:
        raise PromoCodeError("Promo code is invalid", details={"code": raw_code})
    if now < _as_utc(promo.valid_from):
        raise PromoCodeError("Promo code is not active yet", details={"code": promo.code})
    if now > _as_utc(promo.valid_until):
        raise PromoCodeError(
            "Promo code has expired",
            code=ErrorCode.PROMO_CODE_EXPIRED,
            details={"code": promo.code},
        )
    if promo.max_uses is not None and promo.times_used >= promo.max_uses:
        raise PromoCodeError("Promo code usage limit reached", details={"code": promo.code})
    return promo
