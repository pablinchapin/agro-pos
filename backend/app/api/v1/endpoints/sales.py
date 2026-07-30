from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_clerk
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sale_service import SaleService

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=201)
async def create_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await SaleService(db).create_sale(payload)


@router.get("/", response_model=List[SaleResponse])
async def list_sales(
    person_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await SaleService(db).list_sales(person_id=person_id)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await SaleService(db).get_sale(sale_id)
