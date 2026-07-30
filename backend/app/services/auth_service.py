from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token
from app.schemas.user import Token
from app.services.user_service import UserService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)

    async def login(self, username: str, password: str) -> Token:
        user = await self.user_service.authenticate(username, password)
        if user is None:
            raise AuthenticationError("Invalid username or password")

        token = create_access_token(username=user.username, role=user.role)
        return Token(access_token=token, token_type="bearer")
