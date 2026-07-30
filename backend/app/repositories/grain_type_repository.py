from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grain_type import GrainType


class GrainTypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[GrainType]:
        result = await self.db.execute(select(GrainType).order_by(GrainType.name))
        return list(result.scalars().all())

    async def get_by_id(self, grain_type_id: int) -> Optional[GrainType]:
        result = await self.db.execute(
            select(GrainType).where(GrainType.id == grain_type_id)
        )
        return result.scalar_one_or_none()
