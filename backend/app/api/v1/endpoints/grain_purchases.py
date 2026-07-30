from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_clerk
from app.schemas.grain_purchase import GrainPurchaseCreate, GrainPurchaseResponse
from app.services.grain_purchase_service import GrainPurchaseService

router = APIRouter()


@router.post("/", response_model=GrainPurchaseResponse, status_code=201)
async def create_grain_purchase(
    payload: GrainPurchaseCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await GrainPurchaseService(db).create_purchase(payload)


@router.get("/", response_model=List[GrainPurchaseResponse])
async def list_grain_purchases(
    person_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await GrainPurchaseService(db).list_purchases(person_id=person_id)


@router.get("/{purchase_id}", response_model=GrainPurchaseResponse)
async def get_grain_purchase(
    purchase_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await GrainPurchaseService(db).get_purchase(purchase_id)
