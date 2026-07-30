---
name: service-layer
description: Use this skill when writing or modifying business logic in app/services/. Covers how services orchestrate repositories, how to raise business errors, and how stock/inventory rules should be enforced.
---

## Responsibility
Services are where business rules live. They:
1. Receive a Pydantic schema (already validated by FastAPI)
2. Call one or more repository methods
3. Enforce business rules (stock checks, duplicates, cross-entity logic)
4. Raise domain exceptions when a rule is violated
5. Return data (ORM object or Pydantic schema — endpoint's `response_model` handles final shaping)

## Template
```python
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate
from app.core.exceptions import DuplicateError, NotFoundError, InsufficientStockError

class ProductService:
    def __init__(self, db):
        self.repo = ProductRepository(db)

    async def create_product(self, data: ProductCreate):
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise DuplicateError(f"Product '{data.name}' already exists")
        return await self.repo.create(data)

    async def get_product(self, product_id: int):
        product = await self.repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return product

    async def reduce_stock(self, product_id: int, quantity: int):
        product = await self.get_product(product_id)
        if product.stock < quantity:
            raise InsufficientStockError(
                f"Not enough stock for '{product.name}': has {product.stock}, needs {quantity}"
            )
        return await self.repo.update_stock(product_id, product.stock - quantity)
```

## Domain Exceptions — app/core/exceptions.py
```python
class DomainError(Exception):
    """Base class for all business rule violations."""
    pass

class NotFoundError(DomainError):
    pass

class DuplicateError(DomainError):
    pass

class InsufficientStockError(DomainError):
    pass
```

These get mapped to HTTP status codes once, in a global exception handler in `app/main.py` — endpoints never catch these manually:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundError, DuplicateError, InsufficientStockError

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(InsufficientStockError)
async def stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

## Multi-Entity Operations (e.g. creating a Sale)
When a single business operation touches multiple repositories (a sale reduces product stock AND creates sale records), orchestrate them in the service — never split that logic across two service classes.

```python
class SaleService:
    def __init__(self, db):
        self.db = db
        self.sale_repo = SaleRepository(db)
        self.product_service = ProductService(db)

    async def create_sale(self, data: SaleCreate):
        for item in data.items:
            await self.product_service.reduce_stock(item.product_id, item.quantity)
        return await self.sale_repo.create(data)
```

## Rules
- Services receive `db: AsyncSession` (or are constructed with it) and instantiate their own repositories — endpoints never touch repositories directly
- Business rules (stock checks, duplicates, valid ranges beyond what Pydantic already validates) belong here, never in repositories or endpoints
- Always raise domain exceptions (`app/core/exceptions.py`), never raise `HTTPException` from a service — that couples business logic to HTTP, and breaks if the service is ever reused outside FastAPI (e.g. called from a background job)
- One service class per entity (`ProductService`, `SaleService`), named `<Entity>Service`
- A service CAN call another service when an operation spans entities (see Multi-Entity example) — but never call a repository belonging to another entity directly