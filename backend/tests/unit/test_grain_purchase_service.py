"""Unit tests for GrainPurchaseService.

All repository and PersonService calls are mocked — no database required.
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import DomainError, NotFoundError
from app.models.grain_inventory import GrainInventory
from app.models.grain_purchase import GrainPurchase
from app.models.grain_type import GrainType
from app.models.person import Person
from app.schemas.grain_purchase import GrainPurchaseCreate
from app.services.grain_purchase_service import GrainPurchaseService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_person(**kwargs) -> Person:
    defaults = dict(id=1, full_name="Farmer Joe", phone="555-0001", role="farmer")
    defaults.update(kwargs)
    p = Person()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def make_grain_type(**kwargs) -> GrainType:
    defaults = dict(id=1, name="coffee", unit="qq")
    defaults.update(kwargs)
    gt = GrainType()
    for k, v in defaults.items():
        setattr(gt, k, v)
    return gt


def make_grain_purchase(**kwargs) -> GrainPurchase:
    defaults = dict(
        id=1,
        person_id=1,
        grain_type_id=1,
        weight=Decimal("10.00"),
        price_per_unit=Decimal("500.00"),
        total=Decimal("5000.00"),
        date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        notes=None,
    )
    defaults.update(kwargs)
    gp = GrainPurchase()
    for k, v in defaults.items():
        setattr(gp, k, v)
    return gp


def make_grain_inventory(**kwargs) -> GrainInventory:
    defaults = dict(id=1, grain_type_id=1, total_stock=Decimal("10.00"))
    defaults.update(kwargs)
    gi = GrainInventory()
    for k, v in defaults.items():
        setattr(gi, k, v)
    return gi


def make_service():
    """Return (service, purchase_repo_mock, inventory_repo_mock, grain_type_repo_mock, person_service_mock)."""
    db = AsyncMock()
    service = GrainPurchaseService(db)

    purchase_repo = AsyncMock()
    inventory_repo = AsyncMock()
    grain_type_repo = AsyncMock()
    person_service = AsyncMock()

    service.purchase_repo = purchase_repo
    service.inventory_repo = inventory_repo
    service.grain_type_repo = grain_type_repo
    service.person_service = person_service

    return service, purchase_repo, inventory_repo, grain_type_repo, person_service


# ---------------------------------------------------------------------------
# create_purchase — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_purchase_farmer_role_succeeds():
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person = make_person(role="farmer")
    grain_type = make_grain_type()
    expected_purchase = make_grain_purchase()

    person_service.get_person.return_value = person
    grain_type_repo.get_by_id.return_value = grain_type
    purchase_repo.create.return_value = expected_purchase
    inventory_repo.add_stock.return_value = make_grain_inventory()

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("10.00"),
        price_per_unit=Decimal("500.00"),
    )
    result = await service.create_purchase(payload)

    person_service.get_person.assert_awaited_once_with(1)
    grain_type_repo.get_by_id.assert_awaited_once_with(1)
    assert result is expected_purchase


@pytest.mark.asyncio
async def test_create_purchase_both_role_succeeds():
    """A person with role 'both' can sell grains."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person = make_person(role="both")
    grain_type = make_grain_type()
    expected_purchase = make_grain_purchase()

    person_service.get_person.return_value = person
    grain_type_repo.get_by_id.return_value = grain_type
    purchase_repo.create.return_value = expected_purchase
    inventory_repo.add_stock.return_value = make_grain_inventory()

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("5.00"),
        price_per_unit=Decimal("200.00"),
    )
    result = await service.create_purchase(payload)

    assert result is expected_purchase


@pytest.mark.asyncio
async def test_create_purchase_calculates_total_correctly():
    """total must equal weight x price_per_unit passed to repo.create."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")
    grain_type_repo.get_by_id.return_value = make_grain_type()
    purchase_repo.create.return_value = make_grain_purchase(total=Decimal("750.00"))
    inventory_repo.add_stock.return_value = make_grain_inventory()

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("3.00"),
        price_per_unit=Decimal("250.00"),
    )
    await service.create_purchase(payload)

    call_args = purchase_repo.create.call_args
    # call signature: create(data, total, date)
    passed_total = call_args[0][1]
    assert passed_total == Decimal("750.00")


@pytest.mark.asyncio
async def test_create_purchase_uses_provided_date():
    """If date is provided in payload it must be forwarded to repo.create."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")
    grain_type_repo.get_by_id.return_value = make_grain_type()
    purchase_repo.create.return_value = make_grain_purchase()
    inventory_repo.add_stock.return_value = make_grain_inventory()

    fixed_date = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("1.00"),
        price_per_unit=Decimal("100.00"),
        date=fixed_date,
    )
    await service.create_purchase(payload)

    call_args = purchase_repo.create.call_args
    passed_date = call_args[0][2]
    assert passed_date == fixed_date


@pytest.mark.asyncio
async def test_create_purchase_defaults_date_to_now_when_not_provided():
    """If date is None, service must pass a current UTC datetime to repo.create."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")
    grain_type_repo.get_by_id.return_value = make_grain_type()
    purchase_repo.create.return_value = make_grain_purchase()
    inventory_repo.add_stock.return_value = make_grain_inventory()

    before = datetime.now(timezone.utc)
    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("1.00"),
        price_per_unit=Decimal("100.00"),
    )
    await service.create_purchase(payload)
    after = datetime.now(timezone.utc)

    call_args = purchase_repo.create.call_args
    passed_date = call_args[0][2]
    assert before <= passed_date <= after


@pytest.mark.asyncio
async def test_create_purchase_updates_inventory():
    """After creating the purchase, inventory.add_stock must be called with grain_type_id and weight."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")
    grain_type_repo.get_by_id.return_value = make_grain_type()
    purchase_repo.create.return_value = make_grain_purchase()
    inventory_repo.add_stock.return_value = make_grain_inventory()

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("7.50"),
        price_per_unit=Decimal("400.00"),
    )
    await service.create_purchase(payload)

    inventory_repo.add_stock.assert_awaited_once_with(1, Decimal("7.50"))


# ---------------------------------------------------------------------------
# create_purchase — role validation failures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_purchase_customer_role_raises_domain_error():
    """Person with role 'customer' cannot sell grains — must raise DomainError."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="customer")

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=1,
        weight=Decimal("5.00"),
        price_per_unit=Decimal("200.00"),
    )

    with pytest.raises(DomainError, match="customer"):
        await service.create_purchase(payload)

    purchase_repo.create.assert_not_awaited()
    inventory_repo.add_stock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_purchase_error_message_contains_person_id():
    """DomainError message must reference the offending person's id."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(id=42, role="customer")

    payload = GrainPurchaseCreate(
        person_id=42,
        grain_type_id=1,
        weight=Decimal("1.00"),
        price_per_unit=Decimal("100.00"),
    )

    with pytest.raises(DomainError, match="42"):
        await service.create_purchase(payload)


# ---------------------------------------------------------------------------
# create_purchase — person not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_purchase_person_not_found_raises():
    """If PersonService.get_person raises NotFoundError, it propagates."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.side_effect = NotFoundError("Person 99 not found")

    payload = GrainPurchaseCreate(
        person_id=99,
        grain_type_id=1,
        weight=Decimal("1.00"),
        price_per_unit=Decimal("100.00"),
    )

    with pytest.raises(NotFoundError, match="99"):
        await service.create_purchase(payload)

    purchase_repo.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# create_purchase — grain type not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_purchase_grain_type_not_found_raises():
    """If grain_type is None the service must raise NotFoundError."""
    service, purchase_repo, inventory_repo, grain_type_repo, person_service = make_service()

    person_service.get_person.return_value = make_person(role="farmer")
    grain_type_repo.get_by_id.return_value = None

    payload = GrainPurchaseCreate(
        person_id=1,
        grain_type_id=99,
        weight=Decimal("5.00"),
        price_per_unit=Decimal("300.00"),
    )

    with pytest.raises(NotFoundError, match="99"):
        await service.create_purchase(payload)

    purchase_repo.create.assert_not_awaited()
    inventory_repo.add_stock.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_purchase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_purchase_returns_purchase():
    service, purchase_repo, *_ = make_service()
    expected = make_grain_purchase(id=7)
    purchase_repo.get_by_id.return_value = expected

    result = await service.get_purchase(7)

    purchase_repo.get_by_id.assert_awaited_once_with(7)
    assert result is expected


@pytest.mark.asyncio
async def test_get_purchase_not_found_raises():
    service, purchase_repo, *_ = make_service()
    purchase_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_purchase(404)


# ---------------------------------------------------------------------------
# list_purchases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_purchases_no_filter_calls_list_all():
    service, purchase_repo, *_ = make_service()
    purchases = [make_grain_purchase(id=1), make_grain_purchase(id=2)]
    purchase_repo.list_all.return_value = purchases

    result = await service.list_purchases()

    purchase_repo.list_all.assert_awaited_once()
    purchase_repo.list_by_person.assert_not_awaited()
    assert result == purchases


@pytest.mark.asyncio
async def test_list_purchases_with_person_id_calls_list_by_person():
    service, purchase_repo, *_ = make_service()
    purchases = [make_grain_purchase(id=1, person_id=3)]
    purchase_repo.list_by_person.return_value = purchases

    result = await service.list_purchases(person_id=3)

    purchase_repo.list_by_person.assert_awaited_once_with(3)
    purchase_repo.list_all.assert_not_awaited()
    assert result == purchases


@pytest.mark.asyncio
async def test_list_purchases_empty_returns_empty_list():
    service, purchase_repo, *_ = make_service()
    purchase_repo.list_all.return_value = []

    result = await service.list_purchases()

    assert result == []
