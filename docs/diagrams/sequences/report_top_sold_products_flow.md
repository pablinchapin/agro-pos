## Top Sold Products Report — Sequence Diagram

This diagram traces `GET /api/v1/reports/products/top-sold`, sourced from `backend/app/api/v1/endpoints/reports.py`, `backend/app/services/report_service.py`, and `backend/app/repositories/report_repository.py`. Both `start_date` and `end_date` query parameters independently default to `ReportService._today()` (`datetime.now(timezone.utc).date()`) when omitted. Before querying, `ReportService.get_top_sold_products()` validates `start_date <= end_date`; if violated it raises `DomainError`, which `main.py`'s exception handler converts to `422` and the query never reaches `ReportRepository`. When valid, `ReportRepository.get_top_products_by_range()` returns the top 10 products by quantity sold within the inclusive date range, assembled into a `TopSoldProductsReport`. This flow is entirely read-only.

```mermaid
sequenceDiagram
    actor Owner
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as ReportService
    participant REPO as ReportRepository
    participant DB as PostgreSQL

    Owner->>UI: Requests top sold products for a date range
    UI->>API: GET /api/v1/reports/products/top-sold?start_date=&end_date=
    API->>SVC: get_top_sold_products(start_date, end_date)

    Note over SVC: today = _today() (UTC)
    alt start_date query param omitted
        Note over SVC: start_date = today
    else start_date provided
        Note over SVC: start_date = start_date
    end
    alt end_date query param omitted
        Note over SVC: end_date = today
    else end_date provided
        Note over SVC: end_date = end_date
    end

    alt start_date > end_date
        SVC-->>API: raise DomainError("start_date cannot be after end_date")
        API-->>UI: 422 Unprocessable Entity {detail}
        UI-->>Owner: Shows validation error
    else start_date <= end_date
        SVC->>REPO: get_top_products_by_range(start_date, end_date, limit=10)
        REPO->>DB: SELECT product, SUM(quantity), SUM(subtotal)<br/>FROM sale_items JOIN sales JOIN products<br/>WHERE CAST(sales.date AS DATE) BETWEEN start_date AND end_date<br/>GROUP BY product ORDER BY quantity DESC LIMIT 10
        DB-->>REPO: ranked product rows
        REPO-->>SVC: list[Row]

        loop For each row
            SVC->>SVC: build ProductQuantitySold(product_id, product_name,<br/>unit, quantity_sold, total_revenue)
        end

        SVC->>SVC: build TopSoldProductsReport(start_date, end_date, products)
        SVC-->>API: TopSoldProductsReport
        API-->>UI: 200 OK TopSoldProductsReport
        UI-->>Owner: Renders top 10 products for the range
    end
```
