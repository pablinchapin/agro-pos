from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, InsufficientStockError, NotFoundError
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate

VALID_CATEGORIES = {"seeds", "fertilizers", "herbicides", "fungicides"}
VALID_UNITS = {"lb", "kg", "liter", "unit"}


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)

    async def create_product(self, data: ProductCreate) -> Product:
        if data.category not in VALID_CATEGORIES:
            raise DuplicateError(
                f"Invalid category '{data.category}'. "
                f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        if data.unit not in VALID_UNITS:
            raise DuplicateError(
                f"Invalid unit '{data.unit}'. "
                f"Must be one of: {', '.join(sorted(VALID_UNITS))}"
            )
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise DuplicateError(f"Product '{data.name}' already exists")
        return await self.repo.create(data)

    async def get_product(self, product_id: int) -> Product:
        product = await self.repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return product

    async def list_products(self) -> List[Product]:
        return await self.repo.list_all()

    async def list_inactive_products(self) -> List[Product]:
        return await self.repo.list_inactive()

    async def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        # Ensure the product exists first
        await self.get_product(product_id)

        if data.category is not None and data.category not in VALID_CATEGORIES:
            raise DuplicateError(
                f"Invalid category '{data.category}'. "
                f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        if data.unit is not None and data.unit not in VALID_UNITS:
            raise DuplicateError(
                f"Invalid unit '{data.unit}'. "
                f"Must be one of: {', '.join(sorted(VALID_UNITS))}"
            )
        if data.name is not None:
            existing = await self.repo.get_by_name(data.name)
            if existing and existing.id != product_id:
                raise DuplicateError(f"Product '{data.name}' already exists")

        product = await self.repo.update(product_id, data)
        return product

    async def deactivate_product(self, product_id: int) -> Product:
        # Ensure the product exists first
        await self.get_product(product_id)
        return await self.repo.set_active(product_id, False)

    async def activate_product(self, product_id: int) -> Product:
        # Ensure the product exists first
        await self.get_product(product_id)
        return await self.repo.set_active(product_id, True)

    async def reduce_stock(self, product_id: int, quantity: int) -> Product:
        product = await self.get_product(product_id)
        if product.stock < quantity:
            raise InsufficientStockError(
                f"Not enough stock for '{product.name}': "
                f"has {product.stock}, needs {quantity}"
            )
        update_data = ProductUpdate(stock=product.stock - quantity)
        return await self.repo.update(product_id, update_data)
