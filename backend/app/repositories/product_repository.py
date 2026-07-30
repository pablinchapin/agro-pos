from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Product]:
        result = await self.db.execute(select(Product))
        return list(result.scalars().all())

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: int, data: ProductUpdate) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if product is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if product is None:
            return False
        await self.db.delete(product)
        await self.db.commit()
        return True
