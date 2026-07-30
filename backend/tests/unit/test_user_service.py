"""Unit tests for UserService.

All repository calls are mocked so no database is required.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import DuplicateError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(**kwargs) -> User:
    """Return a User ORM instance with sensible defaults."""
    defaults = dict(
        id=1,
        username="admin",
        hashed_password=hash_password("Admin1234!"),
        role="admin",
        is_active=True,
    )
    defaults.update(kwargs)
    user = User()
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


def make_service(mock_repo: MagicMock) -> UserService:
    """Return a UserService with its repository replaced by a mock."""
    db = AsyncMock()
    service = UserService(db)
    service.repo = mock_repo
    return service


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_user_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_username.return_value = None
    expected = make_user()
    mock_repo.create.return_value = expected

    service = make_service(mock_repo)
    payload = UserCreate(username="admin", password="Admin1234!", role="admin")
    result = await service.create_user(payload)

    mock_repo.get_by_username.assert_awaited_once_with("admin")
    mock_repo.create.assert_awaited_once()
    call_kwargs = mock_repo.create.call_args.kwargs
    assert call_kwargs["username"] == "admin"
    assert call_kwargs["role"] == "admin"
    # never store the plain password
    assert call_kwargs["hashed_password"] != "Admin1234!"
    assert result is expected


@pytest.mark.asyncio
async def test_create_user_duplicate_username_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_username.return_value = make_user()

    service = make_service(mock_repo)
    payload = UserCreate(username="admin", password="Admin1234!", role="admin")

    with pytest.raises(DuplicateError, match="already exists"):
        await service.create_user(payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_user_invalid_role_raises():
    mock_repo = AsyncMock()
    service = make_service(mock_repo)

    payload = UserCreate(username="newuser", password="Password1!", role="manager")

    with pytest.raises(DuplicateError, match="role"):
        await service.create_user(payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_user_valid_roles():
    """Both valid roles (admin, clerk) should succeed."""
    for role in ("admin", "clerk"):
        mock_repo = AsyncMock()
        mock_repo.get_by_username.return_value = None
        expected = make_user(role=role)
        mock_repo.create.return_value = expected

        service = make_service(mock_repo)
        payload = UserCreate(username=f"user_{role}", password="Password1!", role=role)
        result = await service.create_user(payload)

        assert result is expected


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_user_returns_user():
    mock_repo = AsyncMock()
    expected = make_user(id=5)
    mock_repo.get_by_id.return_value = expected

    service = make_service(mock_repo)
    result = await service.get_user(5)

    mock_repo.get_by_id.assert_awaited_once_with(5)
    assert result is expected


@pytest.mark.asyncio
async def test_get_user_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError, match="99"):
        await service.get_user(99)


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_users_returns_all():
    mock_repo = AsyncMock()
    users = [make_user(id=1), make_user(id=2, username="clerk1", role="clerk")]
    mock_repo.list_all.return_value = users

    service = make_service(mock_repo)
    result = await service.list_users()

    mock_repo.list_all.assert_awaited_once()
    assert result == users


@pytest.mark.asyncio
async def test_list_users_empty():
    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = []

    service = make_service(mock_repo)
    result = await service.list_users()

    assert result == []


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_user_success_role_change():
    mock_repo = AsyncMock()
    existing = make_user(id=1, role="clerk")
    updated = make_user(id=1, role="admin")
    mock_repo.get_by_id.return_value = existing
    mock_repo.update.return_value = updated

    service = make_service(mock_repo)
    payload = UserUpdate(role="admin")
    result = await service.update_user(1, payload)

    mock_repo.update.assert_awaited_once_with(1, role="admin")
    assert result is updated


@pytest.mark.asyncio
async def test_update_user_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.update_user(999, UserUpdate(role="admin"))


@pytest.mark.asyncio
async def test_update_user_invalid_role_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_user(id=1)

    service = make_service(mock_repo)
    payload = UserUpdate(role="superadmin")

    with pytest.raises(DuplicateError, match="role"):
        await service.update_user(1, payload)

    mock_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_password_gets_rehashed():
    mock_repo = AsyncMock()
    existing = make_user(id=1)
    mock_repo.get_by_id.return_value = existing
    mock_repo.update.return_value = existing

    service = make_service(mock_repo)
    payload = UserUpdate(password="NewPassword1!")
    await service.update_user(1, payload)

    call_kwargs = mock_repo.update.call_args.kwargs
    assert "hashed_password" in call_kwargs
    assert call_kwargs["hashed_password"] != "NewPassword1!"
    assert "password" not in call_kwargs


# ---------------------------------------------------------------------------
# deactivate_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deactivate_user_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_user(id=1, is_active=True)
    deactivated = make_user(id=1, is_active=False)
    mock_repo.deactivate.return_value = deactivated

    service = make_service(mock_repo)
    result = await service.deactivate_user(1)

    mock_repo.deactivate.assert_awaited_once_with(1)
    assert result.is_active is False


@pytest.mark.asyncio
async def test_deactivate_user_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.deactivate_user(999)

    mock_repo.deactivate.assert_not_awaited()


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_success_returns_user():
    mock_repo = AsyncMock()
    plain_password = "Admin1234!"
    user = make_user(hashed_password=hash_password(plain_password))
    mock_repo.get_by_username.return_value = user

    service = make_service(mock_repo)
    result = await service.authenticate("admin", plain_password)

    assert result is user


@pytest.mark.asyncio
async def test_authenticate_wrong_password_returns_none():
    mock_repo = AsyncMock()
    user = make_user(hashed_password=hash_password("Admin1234!"))
    mock_repo.get_by_username.return_value = user

    service = make_service(mock_repo)
    result = await service.authenticate("admin", "WrongPassword")

    assert result is None


@pytest.mark.asyncio
async def test_authenticate_unknown_username_returns_none():
    mock_repo = AsyncMock()
    mock_repo.get_by_username.return_value = None

    service = make_service(mock_repo)
    result = await service.authenticate("ghost", "whatever")

    assert result is None


@pytest.mark.asyncio
async def test_authenticate_inactive_user_returns_none():
    mock_repo = AsyncMock()
    plain_password = "Admin1234!"
    user = make_user(hashed_password=hash_password(plain_password), is_active=False)
    mock_repo.get_by_username.return_value = user

    service = make_service(mock_repo)
    result = await service.authenticate("admin", plain_password)

    assert result is None
