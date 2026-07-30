from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GrainPurchaseCreate(BaseModel):
    person_id: int
    grain_type_id: int
    weight: Decimal = Field(..., gt=0)
    price_per_unit: Decimal = Field(..., gt=0)
    date: Optional[datetime] = None
    notes: Optional[str] = None


class GrainPurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    grain_type_id: int
    weight: Decimal
    price_per_unit: Decimal
    total: Decimal
    date: datetime
    notes: Optional[str]
