from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError, NotFoundError
from app.models.grain_purchase import GrainPurchase
from app.repositories.grain_inventory_repository import GrainInventoryRepository
from app.repositories.grain_purchase_repository import GrainPurchaseRepository
from app.repositories.grain_type_repository import GrainTypeRepository
from app.schemas.grain_purchase import GrainPurchaseCreate
from app.services.person_service import PersonService


class GrainPurchaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.purchase_repo = GrainPurchaseRepository(db)
        self.inventory_repo = GrainInventoryRepository(db)
        self.grain_type_repo = GrainTypeRepository(db)
        self.person_service = PersonService(db)

    async def create_purchase(self, data: GrainPurchaseCreate) -> GrainPurchase:
        # 1. Validate person exists and has farmer-eligible role
        person = await self.person_service.get_person(data.person_id)
        if person.role not in ("farmer", "both"):
            raise DomainError(
                f"Person {data.person_id} has role '{person.role}' and cannot sell grains. "
                "Only persons with role 'farmer' or 'both' are allowed."
            )

        # 2. Validate grain type exists
        grain_type = await self.grain_type_repo.get_by_id(data.grain_type_id)
        if grain_type is None:
            raise NotFoundError(f"Grain type {data.grain_type_id} not found")

        # 3. Auto-calculate total
        total = data.weight * data.price_per_unit

        # 4. Resolve date
        purchase_date = data.date or datetime.now(timezone.utc)

        # 5. Create purchase record
        purchase = await self.purchase_repo.create(data, total, purchase_date)

        # 6. Update grain inventory
        await self.inventory_repo.add_stock(data.grain_type_id, data.weight)

        return purchase

    async def get_purchase(self, purchase_id: int) -> GrainPurchase:
        purchase = await self.purchase_repo.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Grain purchase {purchase_id} not found")
        return purchase

    async def list_purchases(
        self, person_id: Optional[int] = None
    ) -> List[GrainPurchase]:
        if person_id is not None:
            return await self.purchase_repo.list_by_person(person_id)
        return await self.purchase_repo.list_all()
