from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

VALID_CATEGORIES = {"seeds", "fertilizers", "herbicides", "fungicides"}
VALID_UNITS = {"lb", "kg", "liter", "unit"}


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    category: str  # seeds, fertilizers, herbicides, fungicides
    unit: str  # lb, kg, liter, unit
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    min_stock: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    category: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
