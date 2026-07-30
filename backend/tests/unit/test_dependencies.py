"""Unit tests for app.core.dependencies: get_current_user, require_admin, require_clerk.

These are plain async functions — called directly (not through FastAPI's DI
container) with the same arguments FastAPI would inject.
"""
import pytest
from fastapi import HTTPException

from app.core.dependencies import get_current_user, require_admin, require_clerk
from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_valid_token_returns_payload():
    token = create_access_token(username="admin", role="admin")
    payload = await get_current_user(token)

    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("garbage-token")

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# require_admin
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_admin_allows_admin_role():
    user = {"sub": "admin", "role": "admin"}
    result = await require_admin(user)
    assert result == user


@pytest.mark.asyncio
async def test_require_admin_denies_clerk_role():
    user = {"sub": "clerk1", "role": "clerk"}

    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_denies_unknown_role():
    user = {"sub": "ghost", "role": "unknown"}

    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user)

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# require_clerk
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_clerk_allows_clerk_role():
    user = {"sub": "clerk1", "role": "clerk"}
    result = await require_clerk(user)
    assert result == user


@pytest.mark.asyncio
async def test_require_clerk_allows_admin_role():
    """Admin is a superset of clerk — admins can hit clerk-only endpoints."""
    user = {"sub": "admin", "role": "admin"}
    result = await require_clerk(user)
    assert result == user


@pytest.mark.asyncio
async def test_require_clerk_denies_unknown_role():
    user = {"sub": "ghost", "role": "unknown"}

    with pytest.raises(HTTPException) as exc_info:
        await require_clerk(user)

    assert exc_info.value.status_code == 403
