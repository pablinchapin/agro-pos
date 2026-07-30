from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_clerk
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate
from app.services.person_service import PersonService

router = APIRouter()


@router.post("/", response_model=PersonResponse, status_code=201)
async def create_person(
    payload: PersonCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await PersonService(db).create_person(payload)


@router.get("/", response_model=List[PersonResponse], status_code=200)
async def list_persons(
    role: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    service = PersonService(db)
    if role is not None:
        return await service.list_persons_by_role(role)
    return await service.list_persons()


@router.get("/{person_id}", response_model=PersonResponse, status_code=200)
async def get_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await PersonService(db).get_person(person_id)


@router.patch("/{person_id}", response_model=PersonResponse, status_code=200)
async def update_person(
    person_id: int,
    payload: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    return await PersonService(db).update_person(person_id, payload)


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk),
):
    await PersonService(db).delete_person(person_id)
    return Response(status_code=204)
