"""Unit tests for app.core.security: password hashing and JWT handling.

No database, no FastAPI app — pure function tests.
"""
from datetime import datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------

def test_hash_password_returns_different_string_than_plain():
    hashed = hash_password("Admin1234!")
    assert hashed != "Admin1234!"
    assert len(hashed) > 0


def test_hash_password_generates_different_hash_each_time():
    """bcrypt salts every hash — same password should never hash the same way twice."""
    first = hash_password("Admin1234!")
    second = hash_password("Admin1234!")
    assert first != second


def test_verify_password_success_with_correct_password():
    hashed = hash_password("Admin1234!")
    assert verify_password("Admin1234!", hashed) is True


def test_verify_password_fails_with_wrong_password():
    hashed = hash_password("Admin1234!")
    assert verify_password("WrongPassword", hashed) is False


# ---------------------------------------------------------------------------
# create_access_token / decode_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_returns_valid_jwt_string():
    token = create_access_token(username="admin", role="admin")
    assert isinstance(token, str)
    assert token.count(".") == 2  # header.payload.signature


def test_decode_access_token_round_trips_payload():
    token = create_access_token(username="admin", role="admin")
    payload = decode_access_token(token)

    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_access_token_invalid_token_returns_empty_dict():
    payload = decode_access_token("not-a-valid-token")
    assert payload == {}


def test_decode_access_token_expired_token_returns_empty_dict():
    expired_payload = {
        "sub": "admin",
        "role": "admin",
        "exp": datetime.utcnow() - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    payload = decode_access_token(expired_token)
    assert payload == {}


def test_decode_access_token_wrong_secret_returns_empty_dict():
    token = jwt.encode(
        {"sub": "admin", "role": "admin", "exp": datetime.utcnow() + timedelta(minutes=5)},
        "a-completely-different-secret-key",
        algorithm=settings.ALGORITHM,
    )

    payload = decode_access_token(token)
    assert payload == {}
