from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.person import Person
from app.repositories.person_repository import PersonRepository
from app.schemas.person import VALID_ROLES, PersonCreate, PersonUpdate


class PersonService:
    def __init__(self, db: AsyncSession):
        self.repo = PersonRepository(db)

    async def create_person(self, data: PersonCreate) -> Person:
        if data.role not in VALID_ROLES:
            raise DuplicateError(
                f"Invalid role '{data.role}'. "
                f"Must be one of: {', '.join(sorted(VALID_ROLES))}"
            )
        existing = await self.repo.get_by_name_and_phone(data.full_name, data.phone)
        if existing:
            raise DuplicateError(
                f"Person with name '{data.full_name}' and phone '{data.phone}' already exists"
            )
        return await self.repo.create(data)

    async def get_person(self, person_id: int) -> Person:
        person = await self.repo.get_by_id(person_id)
        if person is None:
            raise NotFoundError(f"Person {person_id} not found")
        return person

    async def list_persons(self) -> List[Person]:
        return await self.repo.list_all()

    async def list_persons_by_role(self, role: str) -> List[Person]:
        # When caller asks for role=farmer, return persons where role is farmer OR both.
        # When caller asks for role=customer, return persons where role is customer OR both.
        # When caller asks for role=both, return only exact "both" matches.
        if role == "farmer":
            roles = ["farmer", "both"]
        elif role == "customer":
            roles = ["customer", "both"]
        else:
            roles = ["both"]
        return await self.repo.list_by_roles(roles)

    async def update_person(self, person_id: int, data: PersonUpdate) -> Person:
        # Ensure the person exists first
        await self.get_person(person_id)

        if data.role is not None and data.role not in VALID_ROLES:
            raise DuplicateError(
                f"Invalid role '{data.role}'. "
                f"Must be one of: {', '.join(sorted(VALID_ROLES))}"
            )

        # TODO: When Sales and GrainPurchases modules exist, enforce that a
        # person's role cannot be changed if existing transactions conflict
        # with the new role. For example:
        #   - Cannot change from "farmer" to "customer" if grain purchases exist.
        #   - Cannot change from "customer" to "farmer" if sales exist.
        # Role change is allowed for now because those tables don't exist yet.

        # Check duplicate name+phone if either field is being updated
        if data.full_name is not None or data.phone is not None:
            current = await self.repo.get_by_id(person_id)
            effective_name = data.full_name if data.full_name is not None else current.full_name
            effective_phone = data.phone if data.phone is not None else current.phone
            existing = await self.repo.get_by_name_and_phone(effective_name, effective_phone)
            if existing and existing.id != person_id:
                raise DuplicateError(
                    f"Person with name '{effective_name}' and phone '{effective_phone}' already exists"
                )

        return await self.repo.update(person_id, data)

    async def delete_person(self, person_id: int) -> None:
        # Ensure the person exists first
        await self.get_person(person_id)
        await self.repo.delete(person_id)
