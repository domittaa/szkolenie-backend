"""FastAPI dependencies shared by the routers."""

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pizza_core.auth import Principal, Role, TokenVerifier, ensure_role
from pizza_core.errors import UnauthenticatedError
from pizza_core.events import EventPublisher
from sqlalchemy.orm import Session

from app.api.dev_auth import is_dev_token, principal_from_dev_token
from app.db import get_db
from app.services.events import get_publisher
from app.services.order_service import OrderService
from app.settings import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_token_verifier() -> TokenVerifier:
    settings = get_settings()
    return TokenVerifier(
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        jwks_url=settings.auth_jwks_url,
    )


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    settings: SettingsDep,
) -> Principal:
    if credentials is None:
        raise UnauthenticatedError("Missing bearer token")
    token = credentials.credentials
    if settings.dev_auth_enabled and is_dev_token(token):
        return principal_from_dev_token(token)
    return verifier.verify(token)


def require_roles(*roles: Role) -> Callable[..., Principal]:
    def dependency(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        ensure_role(principal, *roles)
        return principal

    return dependency


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
StaffPrincipal = Annotated[Principal, Depends(require_roles(Role.STAFF))]
AdminPrincipal = Annotated[Principal, Depends(require_roles(Role.ADMIN))]


def get_order_service(
    db: DbSession,
    publisher: Annotated[EventPublisher, Depends(get_publisher)],
    settings: SettingsDep,
) -> OrderService:
    return OrderService(db, publisher, promo_codes_enabled=settings.promo_codes_enabled)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
