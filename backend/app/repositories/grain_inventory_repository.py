from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grain_inventory import GrainInventory


class GrainInventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_grain_type(self, grain_type_id: int) -> Optional[GrainInventory]:
        result = await self.db.execute(
            select(GrainInventory).where(
                GrainInventory.grain_type_id == grain_type_id
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[GrainInventory]:
        result = await self.db.execute(select(GrainInventory))
        return list(result.scalars().all())

    async def add_stock(self, grain_type_id: int, amount: Decimal) -> GrainInventory:
        inventory = await self.get_by_grain_type(grain_type_id)
        if inventory is not None:
            inventory.total_stock = Decimal(str(inventory.total_stock)) + amount
            await self.db.commit()
            await self.db.refresh(inventory)
            return inventory
        inventory = GrainInventory(
            grain_type_id=grain_type_id,
            total_stock=amount,
        )
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory
