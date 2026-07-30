"""Unit tests for InventoryService.

All repository calls are mocked so no database is required. This module is
read-only — there is no create/update/delete behavior to test, only read
orchestration and the `low_stock` computation.
"""
from decimal import Decimal

import pytest
from unittest.mock import AsyncMock

from app.models.grain_inventory import GrainInventory
from app.models.grain_type import GrainType
from app.models.product import Product
from app.services.inventory_service import InventoryService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_product(**kwargs) -> Product:
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


def make_grain_type(**kwargs) -> GrainType:
    defaults = dict(id=1, name="Coffee", unit="qq")
    defaults.update(kwargs)
    grain_type = GrainType()
    for key, value in defaults.items():
        setattr(grain_type, key, value)
    return grain_type


def make_grain_inventory(**kwargs) -> GrainInventory:
    defaults = dict(id=1, grain_type_id=1, total_stock=Decimal("50.00"))
    defaults.update(kwargs)
    inventory = GrainInventory()
    for key, value in defaults.items():
        setattr(inventory, key, value)
    return inventory


def make_service():
    """Return (service, product_repo_mock, grain_inventory_repo_mock, grain_type_repo_mock)."""
    db = AsyncMock()
    service = InventoryService(db)

    product_repo = AsyncMock()
    grain_inventory_repo = AsyncMock()
    grain_type_repo = AsyncMock()

    service.product_repo = product_repo
    service.grain_inventory_repo = grain_inventory_repo
    service.grain_type_repo = grain_type_repo

    return service, product_repo, grain_inventory_repo, grain_type_repo


# ---------------------------------------------------------------------------
# list_product_inventory
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_product_inventory_flags_low_stock_when_equal():
    service, product_repo, _, _ = make_service()
    product_repo.list_all.return_value = [make_product(stock=10, min_stock=10)]

    result = await service.list_product_inventory()

    product_repo.list_all.assert_awaited_once()
    assert result[0].low_stock is True


@pytest.mark.asyncio
async def test_list_product_inventory_flags_low_stock_when_below():
    service, product_repo, _, _ = make_service()
    product_repo.list_all.return_value = [make_product(stock=5, min_stock=10)]

    result = await service.list_product_inventory()

    assert result[0].low_stock is True


@pytest.mark.asyncio
async def test_list_product_inventory_not_low_stock_when_above():
    service, product_repo, _, _ = make_service()
    product_repo.list_all.return_value = [make_product(stock=100, min_stock=10)]

    result = await service.list_product_inventory()

    assert result[0].low_stock is False


@pytest.mark.asyncio
async def test_list_product_inventory_returns_all_fields():
    service, product_repo, _, _ = make_service()
    product_repo.list_all.return_value = [
        make_product(id=7, name="Urea 46%", category="fertilizers", unit="lb", stock=30, min_stock=5)
    ]

    result = await service.list_product_inventory()

    item = result[0]
    assert item.id == 7
    assert item.name == "Urea 46%"
    assert item.category == "fertilizers"
    assert item.unit == "lb"
    assert item.stock == 30
    assert item.min_stock == 5
    assert item.low_stock is False


@pytest.mark.asyncio
async def test_list_product_inventory_empty():
    service, product_repo, _, _ = make_service()
    product_repo.list_all.return_value = []

    result = await service.list_product_inventory()

    assert result == []


# ---------------------------------------------------------------------------
# list_grain_inventory
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_grain_inventory_returns_stock_for_existing_inventory():
    service, _, grain_inventory_repo, grain_type_repo = make_service()
    grain_type_repo.get_all.return_value = [make_grain_type(id=1, name="Coffee", unit="qq")]
    grain_inventory_repo.list_all.return_value = [
        make_grain_inventory(grain_type_id=1, total_stock=Decimal("120.50"))
    ]

    result = await service.list_grain_inventory()

    grain_type_repo.get_all.assert_awaited_once()
    grain_inventory_repo.list_all.assert_awaited_once()
    assert len(result) == 1
    assert result[0].grain_type_id == 1
    assert result[0].grain_type_name == "Coffee"
    assert result[0].unit == "qq"
    assert result[0].total_stock == Decimal("120.50")


@pytest.mark.asyncio
async def test_list_grain_inventory_defaults_to_zero_when_no_inventory_row():
    """A grain type with no purchases yet has no grain_inventory row —
    it must still appear in the listing with total_stock of 0."""
    service, _, grain_inventory_repo, grain_type_repo = make_service()
    grain_type_repo.get_all.return_value = [make_grain_type(id=2, name="Corn", unit="lb")]
    grain_inventory_repo.list_all.return_value = []

    result = await service.list_grain_inventory()

    assert len(result) == 1
    assert result[0].grain_type_id == 2
    assert result[0].grain_type_name == "Corn"
    assert result[0].total_stock == Decimal("0")


@pytest.mark.asyncio
async def test_list_grain_inventory_multiple_types():
    service, _, grain_inventory_repo, grain_type_repo = make_service()
    grain_type_repo.get_all.return_value = [
        make_grain_type(id=1, name="Coffee", unit="qq"),
        make_grain_type(id=2, name="Corn", unit="lb"),
        make_grain_type(id=3, name="Beans", unit="lb"),
    ]
    grain_inventory_repo.list_all.return_value = [
        make_grain_inventory(grain_type_id=1, total_stock=Decimal("10.00")),
        make_grain_inventory(id=2, grain_type_id=3, total_stock=Decimal("5.00")),
    ]

    result = await service.list_grain_inventory()

    by_id = {item.grain_type_id: item for item in result}
    assert by_id[1].total_stock == Decimal("10.00")
    assert by_id[2].total_stock == Decimal("0")
    assert by_id[3].total_stock == Decimal("5.00")


@pytest.mark.asyncio
async def test_list_grain_inventory_empty_when_no_grain_types():
    service, _, grain_inventory_repo, grain_type_repo = make_service()
    grain_type_repo.get_all.return_value = []
    grain_inventory_repo.list_all.return_value = []

    result = await service.list_grain_inventory()

    assert result == []
