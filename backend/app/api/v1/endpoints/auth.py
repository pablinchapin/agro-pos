from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import Token
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/token", response_model=Token, status_code=200)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).login(form_data.username, form_data.password)
