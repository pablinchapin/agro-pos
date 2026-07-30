"""Unit tests for ProductService.

All repository calls are mocked so no database is required.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import DuplicateError, InsufficientStockError, NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_product(**kwargs) -> Product:
    """Return a Product ORM instance with sensible defaults."""
    defaults = dict(
        id=1,
        name="Maize Seed",
        category="seeds",
        unit="lb",
        price=Decimal("10.50"),
        stock=100,
        min_stock=10,
    )
    defaults.update(kwargs)
    product = Product()
    for key, value in defaults.items():
        setattr(product, key, value)
    return product


def make_service(mock_repo: MagicMock) -> ProductService:
    """Return a ProductService with its repository replaced by a mock."""
    db = AsyncMock()
    service = ProductService(db)
    service.repo = mock_repo
    return service


# ---------------------------------------------------------------------------
# create_product
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_product_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_name.return_value = None
    expected = make_product()
    mock_repo.create.return_value = expected

    service = make_service(mock_repo)
    payload = ProductCreate(
        name="Maize Seed",
        category="seeds",
        unit="lb",
        price=Decimal("10.50"),
        stock=100,
        min_stock=10,
    )
    result = await service.create_product(payload)

    mock_repo.get_by_name.assert_awaited_once_with("Maize Seed")
    mock_repo.create.assert_awaited_once_with(payload)
    assert result is expected


@pytest.mark.asyncio
async def test_create_product_duplicate_name_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_name.return_value = make_product()

    service = make_service(mock_repo)
    payload = ProductCreate(
        name="Maize Seed",
        category="seeds",
        unit="lb",
        price=Decimal("10.50"),
        stock=100,
    )

    with pytest.raises(DuplicateError, match="already exists"):
        await service.create_product(payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_product_invalid_category_raises():
    mock_repo = AsyncMock()
    service = make_service(mock_repo)

    payload = ProductCreate(
        name="Unknown",
        category="chemicals",  # invalid
        unit="kg",
        price=Decimal("5.00"),
        stock=0,
    )

    with pytest.raises(DuplicateError, match="category"):
        await service.create_product(payload)


@pytest.mark.asyncio
async def test_create_product_invalid_unit_raises():
    mock_repo = AsyncMock()
    service = make_service(mock_repo)

    payload = ProductCreate(
        name="Valid Name",
        category="seeds",
        unit="gallon",  # invalid
        price=Decimal("5.00"),
        stock=0,
    )

    with pytest.raises(DuplicateError, match="unit"):
        await service.create_product(payload)


# ---------------------------------------------------------------------------
# get_product
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_product_returns_product():
    mock_repo = AsyncMock()
    expected = make_product(id=42)
    mock_repo.get_by_id.return_value = expected

    service = make_service(mock_repo)
    result = await service.get_product(42)

    mock_repo.get_by_id.assert_awaited_once_with(42)
    assert result is expected


@pytest.mark.asyncio
async def test_get_product_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError, match="99"):
        await service.get_product(99)


# ---------------------------------------------------------------------------
# list_products
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_products_returns_all():
    mock_repo = AsyncMock()
    products = [make_product(id=1), make_product(id=2, name="Fertilizer A")]
    mock_repo.list_all.return_value = products

    service = make_service(mock_repo)
    result = await service.list_products()

    mock_repo.list_all.assert_awaited_once()
    assert result == products


@pytest.mark.asyncio
async def test_list_products_empty():
    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = []

    service = make_service(mock_repo)
    result = await service.list_products()

    assert result == []


# ---------------------------------------------------------------------------
# update_product
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_product_success():
    mock_repo = AsyncMock()
    existing = make_product(id=1)
    updated = make_product(id=1, stock=50)
    mock_repo.get_by_id.return_value = existing
    mock_repo.get_by_name.return_value = None
    mock_repo.update.return_value = updated

    service = make_service(mock_repo)
    payload = ProductUpdate(stock=50)
    result = await service.update_product(1, payload)

    mock_repo.update.assert_awaited_once_with(1, payload)
    assert result is updated


@pytest.mark.asyncio
async def test_update_product_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.update_product(999, ProductUpdate(stock=10))


@pytest.mark.asyncio
async def test_update_product_duplicate_name_raises():
    mock_repo = AsyncMock()
    current = make_product(id=1, name="Old Name")
    other = make_product(id=2, name="Other Product")
    mock_repo.get_by_id.return_value = current
    mock_repo.get_by_name.return_value = other  # different product has that name

    service = make_service(mock_repo)
    payload = ProductUpdate(name="Other Product")

    with pytest.raises(DuplicateError, match="already exists"):
        await service.update_product(1, payload)


@pytest.mark.asyncio
async def test_update_product_same_name_allowed():
    """A product may be updated with its own existing name (no rename, no collision)."""
    mock_repo = AsyncMock()
    product = make_product(id=1, name="Maize Seed")
    mock_repo.get_by_id.return_value = product
    mock_repo.get_by_name.return_value = product  # same object — same id
    mock_repo.update.return_value = product

    service = make_service(mock_repo)
    payload = ProductUpdate(name="Maize Seed", stock=200)
    result = await service.update_product(1, payload)

    mock_repo.update.assert_awaited_once_with(1, payload)
    assert result is product


# ---------------------------------------------------------------------------
# delete_product
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_product_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_product(id=1)
    mock_repo.delete.return_value = True

    service = make_service(mock_repo)
    await service.delete_product(1)

    mock_repo.delete.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_delete_product_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.delete_product(999)


# ---------------------------------------------------------------------------
# reduce_stock
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reduce_stock_success():
    mock_repo = AsyncMock()
    product = make_product(id=1, stock=100)
    updated = make_product(id=1, stock=75)
    mock_repo.get_by_id.return_value = product
    mock_repo.update.return_value = updated

    service = make_service(mock_repo)
    result = await service.reduce_stock(1, 25)

    assert result is updated
    call_args = mock_repo.update.call_args
    assert call_args[0][1].stock == 75


@pytest.mark.asyncio
async def test_reduce_stock_insufficient_raises():
    mock_repo = AsyncMock()
    product = make_product(id=1, stock=10)
    mock_repo.get_by_id.return_value = product

    service = make_service(mock_repo)

    with pytest.raises(InsufficientStockError, match="Not enough stock"):
        await service.reduce_stock(1, 50)
