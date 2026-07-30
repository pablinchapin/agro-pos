from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await UserService(db).create_user(payload)


@router.get("/", response_model=List[UserResponse], status_code=200)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await UserService(db).list_users()


@router.get("/{user_id}", response_model=UserResponse, status_code=200)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse, status_code=200)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await UserService(db).update_user(user_id, payload)


@router.patch("/{user_id}/deactivate", response_model=UserResponse, status_code=200)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await UserService(db).deactivate_user(user_id)
