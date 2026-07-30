from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict


class ProductQuantitySold(BaseModel):
    """A product aggregated by quantity sold within some date scope."""

    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    unit: str
    quantity_sold: int
    total_revenue: Decimal


class GrainTypeBreakdownItem(BaseModel):
    """A grain type aggregated by weight and amount spent within a day."""

    model_config = ConfigDict(from_attributes=True)

    grain_type_id: int
    grain_type_name: str
    unit: str
    total_weight: Decimal
    total_spent: Decimal


class DailySalesReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_amount: Decimal
    transaction_count: int
    top_products: List[ProductQuantitySold]


class DailyGrainPurchaseReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_amount: Decimal
    breakdown: List[GrainTypeBreakdownItem]


class TopSoldProductsReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    products: List[ProductQuantitySold]
