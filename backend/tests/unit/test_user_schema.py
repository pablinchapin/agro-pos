"""Unit tests for app.schemas.user: UserResponse must never leak hashed_password."""
from datetime import datetime, timezone

from app.models.user import User
from app.schemas.user import Token, UserResponse


def test_user_response_excludes_hashed_password():
    user = User()
    user.id = 1
    user.username = "admin"
    user.hashed_password = "super-secret-hash"
    user.role = "admin"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)

    response = UserResponse.model_validate(user, from_attributes=True)
    dumped = response.model_dump()

    assert "hashed_password" not in dumped
    assert dumped["username"] == "admin"
    assert dumped["role"] == "admin"


def test_token_schema_default_token_type_is_bearer():
    token = Token(access_token="abc.def.ghi")
    assert token.token_type == "bearer"
    assert token.model_dump() == {"access_token": "abc.def.ghi", "token_type": "bearer"}
