from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.grain_inventory_repository import GrainInventoryRepository
from app.repositories.grain_type_repository import GrainTypeRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import GrainInventoryResponse, ProductInventoryResponse


class InventoryService:
    """Read-only orchestration of stock visibility for products and grains.

    This module never writes to the database — stock is only ever modified
    through the sales and grain purchase flows. It only reads existing
    tables (`products`, `grain_types`, `grain_inventory`) and computes the
    `low_stock` flag for products.
    """

    def __init__(self, db: AsyncSession):
        self.product_repo = ProductRepository(db)
        self.grain_inventory_repo = GrainInventoryRepository(db)
        self.grain_type_repo = GrainTypeRepository(db)

    async def list_product_inventory(self) -> List[ProductInventoryResponse]:
        products = await self.product_repo.list_all()
        return [
            ProductInventoryResponse(
                id=product.id,
                name=product.name,
                category=product.category,
                unit=product.unit,
                stock=product.stock,
                min_stock=product.min_stock,
                low_stock=product.stock <= product.min_stock,
            )
            for product in products
        ]

    async def list_grain_inventory(self) -> List[GrainInventoryResponse]:
        # Every grain type is listed even if it has no purchases yet
        # (defaults to 0 stock), so the inventory view always reflects
        # the full catalog of grain types.
        grain_types = await self.grain_type_repo.get_all()
        inventories = await self.grain_inventory_repo.list_all()
        stock_by_grain_type = {
            inventory.grain_type_id: inventory.total_stock
            for inventory in inventories
        }
        return [
            GrainInventoryResponse(
                grain_type_id=grain_type.id,
                grain_type_name=grain_type.name,
                unit=grain_type.unit,
                total_stock=stock_by_grain_type.get(grain_type.id, Decimal("0")),
            )
            for grain_type in grain_types
        ]
