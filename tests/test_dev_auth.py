import pytest
from fastapi.testclient import TestClient
from pizza_core.auth import Role
from pizza_core.errors import PermissionDeniedError, UnauthenticatedError
from pydantic import ValidationError

from app.api.deps import get_current_principal
from app.api.dev_auth import principal_from_dev_token
from app.main import app
from app.settings import Settings


def test_dev_token_is_parsed() -> None:
    principal = principal_from_dev_token("dev:kuchnia:staff")

    assert principal.user_id == "kuchnia"
    assert principal.role is Role.STAFF


@pytest.mark.parametrize("token", ["dev:", "dev:jan", "dev::customer", "dev:jan:customer:x"])
def test_malformed_dev_token_is_rejected(token: str) -> None:
    with pytest.raises(UnauthenticatedError):
        principal_from_dev_token(token)


def test_unknown_role_is_rejected() -> None:
    with pytest.raises(PermissionDeniedError):
        principal_from_dev_token("dev:jan:superuser")


@pytest.mark.parametrize("app_env", ["dev", "prod"])
def test_dev_auth_cannot_be_enabled_on_gcp(app_env: str) -> None:
    with pytest.raises(ValidationError):
        Settings(app_env=app_env, dev_auth_enabled=True)


def test_dev_tokens_work_only_when_enabled(client: TestClient, settings: Settings) -> None:
    app.dependency_overrides.pop(get_current_principal)
    headers = {"Authorization": "Bearer dev:jan:customer"}

    settings.dev_auth_enabled = False
    assert client.get("/api/v1/orders", headers=headers).status_code == 401

    settings.dev_auth_enabled = True
    assert client.get("/api/v1/orders", headers=headers).status_code == 200
