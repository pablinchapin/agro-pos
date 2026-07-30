from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grain_purchase import GrainPurchase
from app.schemas.grain_purchase import GrainPurchaseCreate


class GrainPurchaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, purchase_id: int) -> Optional[GrainPurchase]:
        result = await self.db.execute(
            select(GrainPurchase).where(GrainPurchase.id == purchase_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[GrainPurchase]:
        result = await self.db.execute(
            select(GrainPurchase).order_by(GrainPurchase.date.desc())
        )
        return list(result.scalars().all())

    async def list_by_person(self, person_id: int) -> List[GrainPurchase]:
        result = await self.db.execute(
            select(GrainPurchase)
            .where(GrainPurchase.person_id == person_id)
            .order_by(GrainPurchase.date.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        data: GrainPurchaseCreate,
        total: Decimal,
        date: datetime,
    ) -> GrainPurchase:
        purchase = GrainPurchase(
            person_id=data.person_id,
            grain_type_id=data.grain_type_id,
            weight=data.weight,
            price_per_unit=data.price_per_unit,
            total=total,
            date=date,
            notes=data.notes,
        )
        self.db.add(purchase)
        await self.db.commit()
        await self.db.refresh(purchase)
        return purchase
