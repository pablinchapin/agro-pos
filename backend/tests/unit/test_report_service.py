"""Unit tests for ReportService.

The underlying `ReportRepository` is mocked so no database is required.
This module is entirely read-only — there is no create/update/delete
behavior to test, only read orchestration, date-defaulting, and the
mapping from raw aggregation rows into report response schemas.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import DomainError
from app.services.report_service import ReportService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_service():
    """Return (service, repo_mock)."""
    db = AsyncMock()
    service = ReportService(db)

    repo = AsyncMock()
    service.repo = repo

    return service, repo


def make_product_row(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=1,
        name="Maize Seed",
        unit="lb",
        total_quantity=10,
        total_revenue=Decimal("100.00"),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_grain_breakdown_row(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=1,
        name="Coffee",
        unit="qq",
        total_weight=Decimal("50.00"),
        total_spent=Decimal("2500.00"),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


FIXED_TODAY = date(2026, 7, 21)


def _patch_today():
    """Patch datetime.now() inside the service module to a fixed UTC date."""
    fixed_dt = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)
    return patch("app.services.report_service.datetime", wraps=datetime, **{
        "now.return_value": fixed_dt,
    })


# ---------------------------------------------------------------------------
# get_daily_sales_report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_daily_sales_report_uses_provided_date():
    service, repo = make_service()
    target_date = date(2026, 7, 1)
    repo.get_daily_sales_totals.return_value = (Decimal("500.00"), 5)
    repo.get_top_products_by_date.return_value = [
        make_product_row(id=1, name="Maize Seed", total_quantity=10),
        make_product_row(id=2, name="Urea 46%", total_quantity=7),
    ]

    result = await service.get_daily_sales_report(target_date=target_date)

    repo.get_daily_sales_totals.assert_awaited_once_with(target_date)
    repo.get_top_products_by_date.assert_awaited_once_with(target_date, limit=5)
    assert result.date == target_date
    assert result.total_amount == Decimal("500.00")
    assert result.transaction_count == 5
    assert len(result.top_products) == 2
    assert result.top_products[0].product_id == 1
    assert result.top_products[0].product_name == "Maize Seed"
    assert result.top_products[0].quantity_sold == 10
    assert result.top_products[0].total_revenue == Decimal("100.00")


@pytest.mark.asyncio
async def test_get_daily_sales_report_defaults_to_today_when_no_date_given():
    service, repo = make_service()
    repo.get_daily_sales_totals.return_value = (Decimal("0"), 0)
    repo.get_top_products_by_date.return_value = []

    with _patch_today():
        result = await service.get_daily_sales_report(target_date=None)

    assert result.date == FIXED_TODAY
    repo.get_daily_sales_totals.assert_awaited_once_with(FIXED_TODAY)
    repo.get_top_products_by_date.assert_awaited_once_with(FIXED_TODAY, limit=5)


@pytest.mark.asyncio
async def test_get_daily_sales_report_no_sales_that_day():
    service, repo = make_service()
    target_date = date(2026, 7, 2)
    repo.get_daily_sales_totals.return_value = (Decimal("0"), 0)
    repo.get_top_products_by_date.return_value = []

    result = await service.get_daily_sales_report(target_date=target_date)

    assert result.total_amount == Decimal("0")
    assert result.transaction_count == 0
    assert result.top_products == []


@pytest.mark.asyncio
async def test_get_daily_sales_report_limits_top_products_query_to_five():
    service, repo = make_service()
    target_date = date(2026, 7, 3)
    repo.get_daily_sales_totals.return_value = (Decimal("1000.00"), 20)
    repo.get_top_products_by_date.return_value = [
        make_product_row(id=i, name=f"Product {i}", total_quantity=10 - i)
        for i in range(1, 6)
    ]

    result = await service.get_daily_sales_report(target_date=target_date)

    repo.get_top_products_by_date.assert_awaited_once_with(target_date, limit=5)
    assert len(result.top_products) == 5


# ---------------------------------------------------------------------------
# get_daily_grain_purchase_report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_daily_grain_purchase_report_uses_provided_date():
    service, repo = make_service()
    target_date = date(2026, 7, 1)
    repo.get_daily_grain_purchase_total.return_value = Decimal("3000.00")
    repo.get_grain_purchase_breakdown_by_type.return_value = [
        make_grain_breakdown_row(id=1, name="Coffee", total_weight=Decimal("20.00"), total_spent=Decimal("2000.00")),
        make_grain_breakdown_row(id=2, name="Corn", total_weight=Decimal("30.00"), total_spent=Decimal("1000.00")),
    ]

    result = await service.get_daily_grain_purchase_report(target_date=target_date)

    repo.get_daily_grain_purchase_total.assert_awaited_once_with(target_date)
    repo.get_grain_purchase_breakdown_by_type.assert_awaited_once_with(target_date)
    assert result.date == target_date
    assert result.total_amount == Decimal("3000.00")
    assert len(result.breakdown) == 2
    assert result.breakdown[0].grain_type_id == 1
    assert result.breakdown[0].grain_type_name == "Coffee"
    assert result.breakdown[0].unit == "qq"
    assert result.breakdown[0].total_weight == Decimal("20.00")
    assert result.breakdown[0].total_spent == Decimal("2000.00")


@pytest.mark.asyncio
async def test_get_daily_grain_purchase_report_defaults_to_today_when_no_date_given():
    service, repo = make_service()
    repo.get_daily_grain_purchase_total.return_value = Decimal("0")
    repo.get_grain_purchase_breakdown_by_type.return_value = []

    with _patch_today():
        result = await service.get_daily_grain_purchase_report(target_date=None)

    assert result.date == FIXED_TODAY
    repo.get_daily_grain_purchase_total.assert_awaited_once_with(FIXED_TODAY)
    repo.get_grain_purchase_breakdown_by_type.assert_awaited_once_with(FIXED_TODAY)


@pytest.mark.asyncio
async def test_get_daily_grain_purchase_report_no_purchases_that_day():
    service, repo = make_service()
    target_date = date(2026, 7, 4)
    repo.get_daily_grain_purchase_total.return_value = Decimal("0")
    repo.get_grain_purchase_breakdown_by_type.return_value = []

    result = await service.get_daily_grain_purchase_report(target_date=target_date)

    assert result.total_amount == Decimal("0")
    assert result.breakdown == []


# ---------------------------------------------------------------------------
# get_top_sold_products
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_top_sold_products_uses_provided_range():
    service, repo = make_service()
    start_date = date(2026, 7, 1)
    end_date = date(2026, 7, 15)
    repo.get_top_products_by_range.return_value = [
        make_product_row(id=1, name="Maize Seed", total_quantity=50, total_revenue=Decimal("500.00")),
        make_product_row(id=2, name="Urea 46%", total_quantity=30, total_revenue=Decimal("300.00")),
    ]

    result = await service.get_top_sold_products(start_date=start_date, end_date=end_date)

    repo.get_top_products_by_range.assert_awaited_once_with(start_date, end_date, limit=10)
    assert result.start_date == start_date
    assert result.end_date == end_date
    assert len(result.products) == 2
    assert result.products[0].product_id == 1
    assert result.products[0].quantity_sold == 50
    assert result.products[0].total_revenue == Decimal("500.00")


@pytest.mark.asyncio
async def test_get_top_sold_products_defaults_both_bounds_to_today():
    service, repo = make_service()
    repo.get_top_products_by_range.return_value = []

    with _patch_today():
        result = await service.get_top_sold_products(start_date=None, end_date=None)

    assert result.start_date == FIXED_TODAY
    assert result.end_date == FIXED_TODAY
    repo.get_top_products_by_range.assert_awaited_once_with(FIXED_TODAY, FIXED_TODAY, limit=10)


@pytest.mark.asyncio
async def test_get_top_sold_products_defaults_only_missing_bound():
    service, repo = make_service()
    start_date = date(2026, 6, 1)
    repo.get_top_products_by_range.return_value = []

    with _patch_today():
        result = await service.get_top_sold_products(start_date=start_date, end_date=None)

    assert result.start_date == start_date
    assert result.end_date == FIXED_TODAY
    repo.get_top_products_by_range.assert_awaited_once_with(start_date, FIXED_TODAY, limit=10)


@pytest.mark.asyncio
async def test_get_top_sold_products_raises_when_start_after_end():
    service, repo = make_service()
    start_date = date(2026, 7, 20)
    end_date = date(2026, 7, 10)

    with pytest.raises(DomainError):
        await service.get_top_sold_products(start_date=start_date, end_date=end_date)

    repo.get_top_products_by_range.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_top_sold_products_empty_range_returns_empty_list():
    service, repo = make_service()
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 31)
    repo.get_top_products_by_range.return_value = []

    result = await service.get_top_sold_products(start_date=start_date, end_date=end_date)

    assert result.products == []


@pytest.mark.asyncio
async def test_get_top_sold_products_limits_query_to_ten():
    service, repo = make_service()
    start_date = date(2026, 7, 1)
    end_date = date(2026, 7, 31)
    repo.get_top_products_by_range.return_value = [
        make_product_row(id=i, name=f"Product {i}", total_quantity=100 - i)
        for i in range(1, 11)
    ]

    result = await service.get_top_sold_products(start_date=start_date, end_date=end_date)

    repo.get_top_products_by_range.assert_awaited_once_with(start_date, end_date, limit=10)
    assert len(result.products) == 10
