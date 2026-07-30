## Daily Sales Report — Sequence Diagram

This diagram traces `GET /api/v1/reports/sales/daily`, sourced from `backend/app/api/v1/endpoints/reports.py`, `backend/app/services/report_service.py`, and `backend/app/repositories/report_repository.py`. The optional `date` query parameter defaults to `ReportService._today()` (`datetime.now(timezone.utc).date()`) when omitted. `ReportService.get_daily_sales_report()` then calls `ReportRepository.get_daily_sales_totals()` for the summed `total_amount` and `transaction_count`, followed by `ReportRepository.get_top_products_by_date()` (limit 5) to rank products by quantity sold on that date. Results are assembled into a `DailySalesReport`. This flow is entirely read-only — no rows in `sales`, `sale_items`, or `products` are written.

```mermaid
sequenceDiagram
    actor Owner
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as ReportService
    participant REPO as ReportRepository
    participant DB as PostgreSQL

    Owner->>UI: Opens daily sales report
    UI->>API: GET /api/v1/reports/sales/daily?date=
    API->>SVC: get_daily_sales_report(target_date=date)

    alt date query param omitted
        Note over SVC: target_date = _today() (UTC)
    else date provided
        Note over SVC: target_date = date
    end

    SVC->>REPO: get_daily_sales_totals(target_date)
    REPO->>DB: SELECT SUM(total_amount), COUNT(id)<br/>FROM sales WHERE CAST(date AS DATE) = target_date
    DB-->>REPO: (total_amount, transaction_count)
    REPO-->>SVC: (Decimal total_amount, int transaction_count)

    SVC->>REPO: get_top_products_by_date(target_date, limit=5)
    REPO->>DB: SELECT product, SUM(quantity), SUM(subtotal)<br/>FROM sale_items JOIN sales JOIN products<br/>WHERE CAST(sales.date AS DATE) = target_date<br/>GROUP BY product ORDER BY quantity DESC LIMIT 5
    DB-->>REPO: ranked product rows
    REPO-->>SVC: list[Row]

    loop For each row
        SVC->>SVC: build ProductQuantitySold(product_id, product_name,<br/>unit, quantity_sold, total_revenue)
    end

    SVC->>SVC: build DailySalesReport(date, total_amount,<br/>transaction_count, top_products)
    SVC-->>API: DailySalesReport
    API-->>UI: 200 OK DailySalesReport
    UI-->>Owner: Renders daily sales summary and top products
```
