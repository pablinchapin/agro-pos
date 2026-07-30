from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[User]:
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    async def create(self, username: str, hashed_password: str, role: str) -> User:
        user = User(username=username, hashed_password=hashed_password, role=role)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, **fields) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for field, value in fields.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate(self, user_id: int) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
