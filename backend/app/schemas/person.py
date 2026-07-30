from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

VALID_ROLES = {"customer", "farmer", "both"}


class PersonBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = None
    role: str  # validated in service layer
    notes: Optional[str] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
