from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate


class PersonRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, person_id: int) -> Optional[Person]:
        result = await self.db.execute(
            select(Person).where(Person.id == person_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_phone(
        self, full_name: str, phone: Optional[str]
    ) -> Optional[Person]:
        # Two persons with the same name and no phone are NOT duplicates.
        # Only check when phone is provided.
        if phone is None:
            return None
        result = await self.db.execute(
            select(Person).where(
                Person.full_name == full_name,
                Person.phone == phone,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Person]:
        result = await self.db.execute(select(Person))
        return list(result.scalars().all())

    async def list_by_roles(self, roles: List[str]) -> List[Person]:
        result = await self.db.execute(
            select(Person).where(Person.role.in_(roles))
        )
        return list(result.scalars().all())

    async def create(self, data: PersonCreate) -> Person:
        person = Person(**data.model_dump())
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def update(self, person_id: int, data: PersonUpdate) -> Optional[Person]:
        person = await self.get_by_id(person_id)
        if person is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def delete(self, person_id: int) -> None:
        person = await self.get_by_id(person_id)
        if person is None:
            return
        await self.db.delete(person)
        await self.db.commit()
