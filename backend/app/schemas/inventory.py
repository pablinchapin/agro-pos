from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    unit: str
    stock: int
    min_stock: int
    low_stock: bool


class GrainInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grain_type_id: int
    grain_type_name: str
    unit: str
    total_stock: Decimal
