from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class SaleCreate(BaseModel):
    person_id: int
    items: List[SaleItemCreate] = Field(..., min_length=1)
    date: Optional[datetime] = None
    notes: Optional[str] = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    date: datetime
    total_amount: Decimal
    notes: Optional[str]
    items: List[SaleItemResponse]
