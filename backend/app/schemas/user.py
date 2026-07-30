from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

VALID_ROLES = {"admin", "clerk"}


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str  # admin, clerk


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
