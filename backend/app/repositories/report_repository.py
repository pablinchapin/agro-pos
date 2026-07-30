from datetime import date
from decimal import Decimal
from typing import Sequence, Tuple

from sqlalchemy import Date, Row, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grain_purchase import GrainPurchase
from app.models.grain_type import GrainType
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem


class ReportRepository:
    """Read-only aggregation queries that span multiple entities.

    Unlike other repositories (one per model), this repository is organized
    around report queries rather than a single table, since reporting is
    inherently a cross-entity concern (sales joined to sale_items and
    products, grain_purchases joined to grain_types). It never writes to
    the database.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_sales_totals(self, target_date: date) -> Tuple[Decimal, int]:
        """Sum of sales.total_amount and count of sales for a given date."""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(Sale.total_amount), 0),
                func.count(Sale.id),
            ).where(cast(Sale.date, Date) == target_date)
        )
        total_amount, transaction_count = result.one()
        return Decimal(str(total_amount)), transaction_count

    async def get_top_products_by_date(
        self, target_date: date, limit: int = 5
    ) -> Sequence[Row]:
        """Products ranked by total quantity sold on a given date.

        Joins sale_items -> sales (date filter) -> products, grouped by
        product and ordered by summed quantity descending.
        """
        result = await self.db.execute(
            select(
                Product.id,
                Product.name,
                Product.unit,
                func.sum(SaleItem.quantity).label("total_quantity"),
                func.sum(SaleItem.subtotal).label("total_revenue"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Product, SaleItem.product_id == Product.id)
            .where(cast(Sale.date, Date) == target_date)
            .group_by(Product.id, Product.name, Product.unit)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
        )
        return result.all()

    async def get_daily_grain_purchase_total(self, target_date: date) -> Decimal:
        """Sum of grain_purchases.total for a given date."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(GrainPurchase.total), 0)).where(
                cast(GrainPurchase.date, Date) == target_date
            )
        )
        total_amount = result.scalar_one()
        return Decimal(str(total_amount))

    async def get_grain_purchase_breakdown_by_type(
        self, target_date: date
    ) -> Sequence[Row]:
        """Grain purchases for a given date, broken down by grain type.

        Joins grain_purchases (date filter) -> grain_types, grouped by
        grain type, aggregating total weight and total amount spent.
        """
        result = await self.db.execute(
            select(
                GrainType.id,
                GrainType.name,
                GrainType.unit,
                func.sum(GrainPurchase.weight).label("total_weight"),
                func.sum(GrainPurchase.total).label("total_spent"),
            )
            .join(GrainType, GrainPurchase.grain_type_id == GrainType.id)
            .where(cast(GrainPurchase.date, Date) == target_date)
            .group_by(GrainType.id, GrainType.name, GrainType.unit)
            .order_by(func.sum(GrainPurchase.total).desc())
        )
        return result.all()

    async def get_top_products_by_range(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> Sequence[Row]:
        """Products ranked by total quantity sold within a date range
        (inclusive on both ends).
        """
        result = await self.db.execute(
            select(
                Product.id,
                Product.name,
                Product.unit,
                func.sum(SaleItem.quantity).label("total_quantity"),
                func.sum(SaleItem.subtotal).label("total_revenue"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Product, SaleItem.product_id == Product.id)
            .where(
                cast(Sale.date, Date) >= start_date,
                cast(Sale.date, Date) <= end_date,
            )
            .group_by(Product.id, Product.name, Product.unit)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
        )
        return result.all()
