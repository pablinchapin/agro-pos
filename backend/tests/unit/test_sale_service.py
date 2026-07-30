"""Unit tests for SaleService.

All repository, PersonService, and ProductService calls are mocked — no
database required.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from unittest.mock import AsyncMock

from app.core.exceptions import DomainError, InsufficientStockError, NotFoundError
from app.models.person import Person
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.services.sale_service import SaleService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_person(**kwargs) -> Person:
    defaults = dict(id=1, full_name="Jane Customer", phone="555-1000", role="customer")
    defaults.update(kwargs)
    p = Person()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


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
    for k, v in defaults.items():
        setattr(product, k, v)
    return product


def make_sale_item(**kwargs) -> SaleItem:
    defaults = dict(
        id=1,
        sale_id=1,
        product_id=1,
        quantity=5,
        unit_price=Decimal("10.50"),
        subtotal=Decimal("52.50"),
    )
    defaults.update(kwargs)
    item = SaleItem()
    for k, v in defaults.items():
        setattr(item, k, v)
    return item


def make_sale(**kwargs) -> Sale:
    defaults = dict(
        id=1,
        person_id=1,
        date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        total_amount=Decimal("52.50"),
        notes=None,
        items=[make_sale_item()],
    )
    defaults.update(kwargs)
    sale = Sale()
    for k, v in defaults.items():
        setattr(sale, k, v)
    return sale


def make_service():
    """Return (service, sale_repo_mock, person_service_mock, product_service_mock)."""
    db = AsyncMock()
    service = SaleService(db)

    sale_repo = AsyncMock()
    person_service = AsyncMock()
    product_service = AsyncMock()

    service.sale_repo = sale_repo
    service.person_service = person_service
    service.product_service = product_service

    return service, sale_repo, person_service, product_service


# ---------------------------------------------------------------------------
# create_sale — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_sale_customer_role_succeeds():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(stock=100)
    expected_sale = make_sale()
    sale_repo.create.return_value = expected_sale

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=5, unit_price=Decimal("10.50"))],
    )
    result = await service.create_sale(payload)

    person_service.get_person.assert_awaited_once_with(1)
    assert result is expected_sale


@pytest.mark.asyncio
async def test_create_sale_both_role_succeeds():
    """A person with role 'both' can have a sale registered."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="both")
    product_service.get_product.return_value = make_product(stock=100)
    sale_repo.create.return_value = make_sale()

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=2, unit_price=Decimal("5.00"))],
    )
    result = await service.create_sale(payload)

    assert result is not None


@pytest.mark.asyncio
async def test_create_sale_calculates_total_correctly_single_item():
    """total_amount passed to repo.create must equal quantity x unit_price."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(stock=100)
    sale_repo.create.return_value = make_sale()

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=3, unit_price=Decimal("20.00"))],
    )
    await service.create_sale(payload)

    call_args = sale_repo.create.call_args
    # call signature: create(data, items_with_subtotals, total_amount, date)
    passed_total = call_args[0][2]
    assert passed_total == Decimal("60.00")


@pytest.mark.asyncio
async def test_create_sale_calculates_total_correctly_multi_item():
    """total_amount must be the sum of all line item subtotals."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")

    def get_product_side_effect(product_id):
        if product_id == 1:
            return make_product(id=1, name="Seed", stock=100)
        return make_product(id=2, name="Fertilizer", stock=50)

    product_service.get_product.side_effect = get_product_side_effect
    sale_repo.create.return_value = make_sale()

    payload = SaleCreate(
        person_id=1,
        items=[
            SaleItemCreate(product_id=1, quantity=3, unit_price=Decimal("20.00")),
            SaleItemCreate(product_id=2, quantity=2, unit_price=Decimal("15.00")),
        ],
    )
    await service.create_sale(payload)

    call_args = sale_repo.create.call_args
    passed_items = call_args[0][1]
    passed_total = call_args[0][2]

    assert passed_total == Decimal("90.00")  # 60.00 + 30.00
    assert passed_items[0]["subtotal"] == Decimal("60.00")
    assert passed_items[1]["subtotal"] == Decimal("30.00")


@pytest.mark.asyncio
async def test_create_sale_ignores_any_client_supplied_total():
    """SaleCreate schema has no total field — total is always server-computed."""
    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
    )
    assert not hasattr(payload, "total")
    assert not hasattr(payload, "total_amount")


@pytest.mark.asyncio
async def test_create_sale_reduces_stock_per_item():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(stock=100)
    sale_repo.create.return_value = make_sale()

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=7, unit_price=Decimal("10.00"))],
    )
    await service.create_sale(payload)

    product_service.reduce_stock.assert_awaited_once_with(1, 7)


@pytest.mark.asyncio
async def test_create_sale_reduces_stock_for_each_distinct_line_item():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")

    def get_product_side_effect(product_id):
        return make_product(id=product_id, stock=100)

    product_service.get_product.side_effect = get_product_side_effect
    sale_repo.create.return_value = make_sale()

    payload = SaleCreate(
        person_id=1,
        items=[
            SaleItemCreate(product_id=1, quantity=3, unit_price=Decimal("10.00")),
            SaleItemCreate(product_id=2, quantity=4, unit_price=Decimal("5.00")),
        ],
    )
    await service.create_sale(payload)

    assert product_service.reduce_stock.await_count == 2
    product_service.reduce_stock.assert_any_await(1, 3)
    product_service.reduce_stock.assert_any_await(2, 4)


@pytest.mark.asyncio
async def test_create_sale_uses_provided_date():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(stock=100)
    sale_repo.create.return_value = make_sale()

    fixed_date = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
        date=fixed_date,
    )
    await service.create_sale(payload)

    call_args = sale_repo.create.call_args
    passed_date = call_args[0][3]
    assert passed_date == fixed_date


@pytest.mark.asyncio
async def test_create_sale_defaults_date_to_now_when_not_provided():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(stock=100)
    sale_repo.create.return_value = make_sale()

    before = datetime.now(timezone.utc)
    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
    )
    await service.create_sale(payload)
    after = datetime.now(timezone.utc)

    call_args = sale_repo.create.call_args
    passed_date = call_args[0][3]
    assert before <= passed_date <= after


# ---------------------------------------------------------------------------
# create_sale — role validation failures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_sale_farmer_role_raises_domain_error():
    """Person with role 'farmer' cannot have a sale registered — DomainError."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
    )

    with pytest.raises(DomainError, match="farmer"):
        await service.create_sale(payload)

    sale_repo.create.assert_not_awaited()
    product_service.reduce_stock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_sale_error_message_contains_person_id():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(id=42, role="farmer")

    payload = SaleCreate(
        person_id=42,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
    )

    with pytest.raises(DomainError, match="42"):
        await service.create_sale(payload)


# ---------------------------------------------------------------------------
# create_sale — person / product not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_sale_person_not_found_raises():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.side_effect = NotFoundError("Person 99 not found")

    payload = SaleCreate(
        person_id=99,
        items=[SaleItemCreate(product_id=1, quantity=1, unit_price=Decimal("10.00"))],
    )

    with pytest.raises(NotFoundError, match="99"):
        await service.create_sale(payload)

    sale_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_sale_product_not_found_raises():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.side_effect = NotFoundError("Product 999 not found")

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=999, quantity=1, unit_price=Decimal("10.00"))],
    )

    with pytest.raises(NotFoundError, match="999"):
        await service.create_sale(payload)

    sale_repo.create.assert_not_awaited()
    product_service.reduce_stock.assert_not_awaited()


# ---------------------------------------------------------------------------
# create_sale — stock validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_sale_insufficient_stock_raises():
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(name="Maize Seed", stock=5)

    payload = SaleCreate(
        person_id=1,
        items=[SaleItemCreate(product_id=1, quantity=10, unit_price=Decimal("10.00"))],
    )

    with pytest.raises(InsufficientStockError, match="Not enough stock"):
        await service.create_sale(payload)

    sale_repo.create.assert_not_awaited()
    product_service.reduce_stock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_sale_insufficient_stock_aggregates_same_product_across_items():
    """Two line items for the same product must be summed before the stock check."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")
    product_service.get_product.return_value = make_product(id=1, name="Maize Seed", stock=8)

    payload = SaleCreate(
        person_id=1,
        items=[
            SaleItemCreate(product_id=1, quantity=5, unit_price=Decimal("10.00")),
            SaleItemCreate(product_id=1, quantity=5, unit_price=Decimal("10.00")),
        ],
    )

    with pytest.raises(InsufficientStockError):
        await service.create_sale(payload)

    sale_repo.create.assert_not_awaited()
    product_service.reduce_stock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_sale_no_partial_stock_reduction_on_failure():
    """If any product fails the stock check, no stock reduction happens at all."""
    service, sale_repo, person_service, product_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")

    def get_product_side_effect(product_id):
        if product_id == 1:
            return make_product(id=1, name="Seed", stock=100)
        return make_product(id=2, name="Fertilizer", stock=1)

    product_service.get_product.side_effect = get_product_side_effect

    payload = SaleCreate(
        person_id=1,
        items=[
            SaleItemCreate(product_id=1, quantity=5, unit_price=Decimal("10.00")),
            SaleItemCreate(product_id=2, quantity=10, unit_price=Decimal("5.00")),
        ],
    )

    with pytest.raises(InsufficientStockError):
        await service.create_sale(payload)

    product_service.reduce_stock.assert_not_awaited()
    sale_repo.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_sale
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_sale_returns_sale():
    service, sale_repo, *_ = make_service()
    expected = make_sale(id=7)
    sale_repo.get_by_id.return_value = expected

    result = await service.get_sale(7)

    sale_repo.get_by_id.assert_awaited_once_with(7)
    assert result is expected


@pytest.mark.asyncio
async def test_get_sale_not_found_raises():
    service, sale_repo, *_ = make_service()
    sale_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_sale(404)


# ---------------------------------------------------------------------------
# list_sales
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_sales_no_filter_calls_list_all():
    service, sale_repo, *_ = make_service()
    sales = [make_sale(id=1), make_sale(id=2)]
    sale_repo.list_all.return_value = sales

    result = await service.list_sales()

    sale_repo.list_all.assert_awaited_once()
    sale_repo.list_by_person.assert_not_awaited()
    assert result == sales


@pytest.mark.asyncio
async def test_list_sales_with_person_id_calls_list_by_person():
    service, sale_repo, *_ = make_service()
    sales = [make_sale(id=1, person_id=3)]
    sale_repo.list_by_person.return_value = sales

    result = await service.list_sales(person_id=3)

    sale_repo.list_by_person.assert_awaited_once_with(3)
    sale_repo.list_all.assert_not_awaited()
    assert result == sales


@pytest.mark.asyncio
async def test_list_sales_empty_returns_empty_list():
    service, sale_repo, *_ = make_service()
    sale_repo.list_all.return_value = []

    result = await service.list_sales()

    assert result == []
