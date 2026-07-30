---
name: create-endpoint
description: Use this skill when creating new FastAPI endpoints in app/api/v1/endpoints/. Covers the thin-endpoint pattern, async/await usage, response_model usage, and where business logic should NOT live.
---

## Pattern
Endpoints are thin and async. They only:
1. Receive and validate input via Pydantic schema
2. Await the corresponding service method
3. Return a Pydantic response schema

## Template
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await ProductService(db).create_product(payload)
```

## Rules
- Every endpoint function is `async def`
- Every call into a service or repository is `await`-ed
- Never put if/else business logic here
- Always use `response_model=` on every endpoint
- HTTP 404 → raise in service, catch here only if needed
- Group related endpoints in the same file (products.py, sales.py, etc.)