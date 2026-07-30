from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_clerk
from app.schemas.inventory import GrainInventoryResponse, ProductInventoryResponse
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get("/products", response_model=List[ProductInventoryResponse])
async def list_product_inventory(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await InventoryService(db).list_product_inventory()


@router.get("/grains", response_model=List[GrainInventoryResponse])
async def list_grain_inventory(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await InventoryService(db).list_grain_inventory()
