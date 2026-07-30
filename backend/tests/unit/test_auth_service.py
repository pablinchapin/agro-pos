"""Unit tests for AuthService.login.

UserService.authenticate is mocked so no database is required.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import Token
from app.services.auth_service import AuthService


def make_user(**kwargs) -> User:
    defaults = dict(id=1, username="admin", hashed_password="x", role="admin", is_active=True)
    defaults.update(kwargs)
    user = User()
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


def make_service(mock_user_service: MagicMock) -> AuthService:
    db = AsyncMock()
    service = AuthService(db)
    service.user_service = mock_user_service
    return service


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success_returns_token():
    mock_user_service = AsyncMock()
    mock_user_service.authenticate.return_value = make_user(username="admin", role="admin")

    service = make_service(mock_user_service)
    result = await service.login("admin", "Admin1234!")

    mock_user_service.authenticate.assert_awaited_once_with("admin", "Admin1234!")
    assert isinstance(result, Token)
    assert result.token_type == "bearer"

    payload = decode_access_token(result.access_token)
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_login_success_response_shape_uses_access_token_field():
    """The Token schema must expose the OAuth2-standard 'access_token' field."""
    mock_user_service = AsyncMock()
    mock_user_service.authenticate.return_value = make_user(username="clerk1", role="clerk")

    service = make_service(mock_user_service)
    result = await service.login("clerk1", "Clerk1234!")

    dumped = result.model_dump()
    assert set(dumped.keys()) == {"access_token", "token_type"}


@pytest.mark.asyncio
async def test_login_invalid_credentials_raises_authentication_error():
    mock_user_service = AsyncMock()
    mock_user_service.authenticate.return_value = None

    service = make_service(mock_user_service)

    with pytest.raises(AuthenticationError, match="Invalid username or password"):
        await service.login("admin", "wrong-password")


@pytest.mark.asyncio
async def test_login_inactive_user_raises_authentication_error():
    """authenticate() already returns None for inactive users — login must surface that as an error."""
    mock_user_service = AsyncMock()
    mock_user_service.authenticate.return_value = None

    service = make_service(mock_user_service)

    with pytest.raises(AuthenticationError):
        await service.login("deactivated_user", "whatever")
