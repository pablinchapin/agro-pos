---
name: pydantic-schemas
description: Use this skill when creating or modifying Pydantic schemas in app/schemas/. 
Covers the Create/Update/Response pattern, validation rules, and how schemas relate to SQLAlchemy models in this project.
---

## Pattern
Every domain entity gets its own schema file with up to three variants:
- `<Entity>Create` — input for POST requests, no `id`
- `<Entity>Update` — input for PATCH/PUT, all fields Optional
- `<Entity>Response` — output, includes `id` and any DB-generated fields

## File Location
One file per entity: `app/schemas/product.py`, `app/schemas/sale.py`, `app/schemas/grain_purchase.py`

## Template
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    category: str  # seed, fertilizer, herbicide, fungicide
    unit: str       # lb, kg, liter, unit
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
    created_at: datetime
```

## Rules
- `Base` class holds shared fields; `Create` inherits from it directly
- `Update` never inherits from `Base` — all fields must be individually Optional, so don't reuse required-field definitions
- `Response` always sets `model_config = ConfigDict(from_attributes=True)` so it can read directly from SQLAlchemy ORM objects
- Use `Decimal` for money fields, never `float`
- Use `Field(...)` with constraints (`gt`, `ge`, `min_length`) instead of validating manually in services when the rule is a simple range/length check
- Category and unit fields are plain `str` in v1 (no Enum yet) — keep validation of allowed values in the service layer, not here
- Never import SQLAlchemy models into schema files — schemas must stay framework-agnostic