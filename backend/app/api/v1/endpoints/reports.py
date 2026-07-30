from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas.report import (
    DailyGrainPurchaseReport,
    DailySalesReport,
    TopSoldProductsReport,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/sales/daily", response_model=DailySalesReport)
async def get_daily_sales_report(
    date: Optional[date_type] = Query(
        None, description="Date to report on, defaults to today (UTC)"
    ),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await ReportService(db).get_daily_sales_report(target_date=date)


@router.get("/grain-purchases/daily", response_model=DailyGrainPurchaseReport)
async def get_daily_grain_purchase_report(
    date: Optional[date_type] = Query(
        None, description="Date to report on, defaults to today (UTC)"
    ),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await ReportService(db).get_daily_grain_purchase_report(target_date=date)


@router.get("/products/top-sold", response_model=TopSoldProductsReport)
async def get_top_sold_products(
    start_date: Optional[date_type] = Query(
        None, description="Range start date, defaults to today (UTC)"
    ),
    end_date: Optional[date_type] = Query(
        None, description="Range end date, defaults to today (UTC)"
    ),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await ReportService(db).get_top_sold_products(
        start_date=start_date, end_date=end_date
    )
