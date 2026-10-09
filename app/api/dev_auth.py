"""Local development login without Identity Platform.

Enabled with ``DEV_AUTH_ENABLED=true``, which ``Settings`` refuses outside ``APP_ENV=local``.
The frontend (``VITE_AUTH_MODE=dev``, src/auth/devAuth.ts) sends
``Authorization: Bearer dev:<user_id>:<role>``, e.g. ``dev:kuchnia:staff``.
"""

from pizza_core.auth import Principal, principal_from_claims
from pizza_core.errors import UnauthenticatedError

DEV_TOKEN_PREFIX = "dev:"


def is_dev_token(token: str) -> bool:
    return token.startswith(DEV_TOKEN_PREFIX)


def principal_from_dev_token(token: str) -> Principal:
    try:
        _, user_id, role = token.split(":")
    except ValueError:
        raise UnauthenticatedError("Malformed dev token, expected dev:<user_id>:<role>") from None
    return principal_from_claims({"sub": user_id, "role": role, "email": f"{user_id}@local.test"})
