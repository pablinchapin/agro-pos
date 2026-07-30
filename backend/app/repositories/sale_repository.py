from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.sale import SaleCreate


class SaleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, sale_id: int) -> Optional[Sale]:
        result = await self.db.execute(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.id == sale_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Sale]:
        result = await self.db.execute(
            select(Sale).options(selectinload(Sale.items)).order_by(Sale.date.desc())
        )
        return list(result.scalars().all())

    async def list_by_person(self, person_id: int) -> List[Sale]:
        result = await self.db.execute(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.person_id == person_id)
            .order_by(Sale.date.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        data: SaleCreate,
        items_with_subtotals: List[Dict],
        total_amount: Decimal,
        date: datetime,
    ) -> Sale:
        sale = Sale(
            person_id=data.person_id,
            date=date,
            total_amount=total_amount,
            notes=data.notes,
            items=[
                SaleItem(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"],
                )
                for item in items_with_subtotals
            ],
        )
        self.db.add(sale)
        await self.db.commit()
        return await self.get_by_id(sale.id)
