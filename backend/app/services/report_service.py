from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.repositories.report_repository import ReportRepository
from app.schemas.report import (
    DailyGrainPurchaseReport,
    DailySalesReport,
    GrainTypeBreakdownItem,
    ProductQuantitySold,
    TopSoldProductsReport,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


class ReportService:
    """Read-only orchestration of operational reports.

    This module never writes to the database — it only reads from the
    existing `sales`, `sale_items`, `products`, `grain_purchases` and
    `grain_types` tables via `ReportRepository` and shapes the results
    into report response schemas.
    """

    def __init__(self, db: AsyncSession):
        self.repo = ReportRepository(db)

    async def get_daily_sales_report(
        self, target_date: Optional[date] = None
    ) -> DailySalesReport:
        target_date = target_date or _today()

        total_amount, transaction_count = await self.repo.get_daily_sales_totals(
            target_date
        )
        top_rows = await self.repo.get_top_products_by_date(target_date, limit=5)
        top_products = [
            ProductQuantitySold(
                product_id=row.id,
                product_name=row.name,
                unit=row.unit,
                quantity_sold=row.total_quantity,
                total_revenue=row.total_revenue,
            )
            for row in top_rows
        ]

        return DailySalesReport(
            date=target_date,
            total_amount=total_amount,
            transaction_count=transaction_count,
            top_products=top_products,
        )

    async def get_daily_grain_purchase_report(
        self, target_date: Optional[date] = None
    ) -> DailyGrainPurchaseReport:
        target_date = target_date or _today()

        total_amount = await self.repo.get_daily_grain_purchase_total(target_date)
        breakdown_rows = await self.repo.get_grain_purchase_breakdown_by_type(
            target_date
        )
        breakdown = [
            GrainTypeBreakdownItem(
                grain_type_id=row.id,
                grain_type_name=row.name,
                unit=row.unit,
                total_weight=row.total_weight,
                total_spent=row.total_spent,
            )
            for row in breakdown_rows
        ]

        return DailyGrainPurchaseReport(
            date=target_date,
            total_amount=total_amount,
            breakdown=breakdown,
        )

    async def get_top_sold_products(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> TopSoldProductsReport:
        today = _today()
        start_date = start_date or today
        end_date = end_date or today

        if start_date > end_date:
            raise DomainError(
                f"start_date ({start_date}) cannot be after end_date ({end_date})"
            )

        rows = await self.repo.get_top_products_by_range(
            start_date, end_date, limit=10
        )
        products = [
            ProductQuantitySold(
                product_id=row.id,
                product_name=row.name,
                unit=row.unit,
                quantity_sold=row.total_quantity,
                total_revenue=row.total_revenue,
            )
            for row in rows
        ]

        return TopSoldProductsReport(
            start_date=start_date,
            end_date=end_date,
            products=products,
        )
