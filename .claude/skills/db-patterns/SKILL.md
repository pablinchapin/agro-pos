---
name: db-patterns
description: Use this skill when working with the database layer - creating SQLAlchemy models, writing repository methods, configuring the async engine/session, or setting up Alembic migrations. Covers async SQLAlchemy 2.0 patterns specific to this project.
---

## Core Setup — app/core/database.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

`DATABASE_URL` must use the `asyncpg` driver: `postgresql+asyncpg://user:pass@host/dbname`

## SQLAlchemy Models — app/models/

```python
from sqlalchemy import String, Numeric, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Use SQLAlchemy 2.0 `Mapped[]` / `mapped_column()` style — never the legacy `Column()` declarative style.

## Repository Pattern — app/repositories/

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.schemas.product import ProductCreate

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Product]:
        result = await self.db.execute(select(Product))
        return list(result.scalars().all())

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product
```

## Migrations — Alembic

- Every schema change goes through a migration. Never edit tables manually.
- Generate: `alembic revision --autogenerate -m "create products table"`
- Apply: `alembic upgrade head`
- Always review the auto-generated migration file before applying — autogenerate misses some changes (column renames, certain constraints)
- `alembic/env.py` must be configured for async (uses `run_sync` internally) — do not replace with the sync template


## Seed Data Migrations — Correct Order

When editing an existing seed migration that has already been applied:

1. ALWAYS downgrade first, THEN edit the file, THEN upgrade:
```bash
alembic downgrade -1        # removes the data using the OLD downgrade()
# edit the migration file
alembic upgrade head        # re-inserts using the NEW upgrade()
```

2. NEVER edit the migration file while it is already applied to the DB —
   this creates orphan rows because downgrade() no longer matches what
   upgrade() inserted.

3. After any seed migration change, verify the final state directly in the DB:
```bash
psql -h localhost -p 5432 -U postgres -d agro_pos \
    -c "SELECT * FROM grain_types ORDER BY id;"
```

Note: ids will increment on each downgrade/upgrade cycle — this is expected
and harmless for catalog tables.


## Rules
- Every repository method is `async def` and receives `self.db: AsyncSession` from `__init__`
- Repositories return ORM model instances or `None`/`list` — never Pydantic schemas (that conversion happens in services or via `response_model`)
- Always `await db.commit()` after writes, and `await db.refresh(obj)` if you need DB-generated fields (id, timestamps) back
- Use `select()` + `await db.execute()` — never the legacy `db.query()` style (that's sync-only)
- One repository class per entity, named `<Entity>Repository`
- Repositories never raise HTTP exceptions — that's the service layer's job (repositories return `None`, services decide what `None` means)