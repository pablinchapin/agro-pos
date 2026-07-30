from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, require_clerk
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await ProductService(db).create_product(payload)


@router.get("/", response_model=list[ProductResponse], status_code=200)
async def list_products(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await ProductService(db).list_products()


@router.get("/{product_id}", response_model=ProductResponse, status_code=200)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await ProductService(db).get_product(product_id)


@router.patch("/{product_id}", response_model=ProductResponse, status_code=200)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await ProductService(db).update_product(product_id, payload)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    await ProductService(db).delete_product(product_id)
    return Response(status_code=204)
