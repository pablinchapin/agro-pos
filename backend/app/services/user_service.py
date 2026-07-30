from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate

VALID_ROLES = {"admin", "clerk"}


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        if data.role not in VALID_ROLES:
            raise DuplicateError(
                f"Invalid role '{data.role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
            )
        existing = await self.repo.get_by_username(data.username)
        if existing:
            raise DuplicateError(f"Username '{data.username}' already exists")

        hashed_password = hash_password(data.password)
        return await self.repo.create(
            username=data.username, hashed_password=hashed_password, role=data.role
        )

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def list_users(self) -> List[User]:
        return await self.repo.list_all()

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        # Ensure the user exists first
        await self.get_user(user_id)

        if data.role is not None and data.role not in VALID_ROLES:
            raise DuplicateError(
                f"Invalid role '{data.role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
            )

        update_data = data.model_dump(exclude_unset=True, exclude={"password"})
        if data.password is not None:
            update_data["hashed_password"] = hash_password(data.password)

        return await self.repo.update(user_id, **update_data)

    async def deactivate_user(self, user_id: int) -> User:
        # Ensure the user exists first
        await self.get_user(user_id)
        return await self.repo.deactivate(user_id)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.repo.get_by_username(username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
