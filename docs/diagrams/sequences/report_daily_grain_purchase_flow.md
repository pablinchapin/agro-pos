## Daily Grain Purchase Report — Sequence Diagram

This diagram traces `GET /api/v1/reports/grain-purchases/daily`, sourced from `backend/app/api/v1/endpoints/reports.py`, `backend/app/services/report_service.py`, and `backend/app/repositories/report_repository.py`. The optional `date` query parameter defaults to `ReportService._today()` (`datetime.now(timezone.utc).date()`) when omitted. `ReportService.get_daily_grain_purchase_report()` calls `ReportRepository.get_daily_grain_purchase_total()` for the summed `total_amount`, then `ReportRepository.get_grain_purchase_breakdown_by_type()` to aggregate `total_weight` and `total_spent` per grain type. Results are assembled into a `DailyGrainPurchaseReport`. This flow is entirely read-only — no rows in `grain_purchases` or `grain_types` are written.

```mermaid
sequenceDiagram
    actor Owner
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as ReportService
    participant REPO as ReportRepository
    participant DB as PostgreSQL

    Owner->>UI: Opens daily grain purchase report
    UI->>API: GET /api/v1/reports/grain-purchases/daily?date=
    API->>SVC: get_daily_grain_purchase_report(target_date=date)

    alt date query param omitted
        Note over SVC: target_date = _today() (UTC)
    else date provided
        Note over SVC: target_date = date
    end

    SVC->>REPO: get_daily_grain_purchase_total(target_date)
    REPO->>DB: SELECT SUM(total)<br/>FROM grain_purchases WHERE CAST(date AS DATE) = target_date
    DB-->>REPO: total_amount
    REPO-->>SVC: Decimal total_amount

    SVC->>REPO: get_grain_purchase_breakdown_by_type(target_date)
    REPO->>DB: SELECT grain_type, SUM(weight), SUM(total)<br/>FROM grain_purchases JOIN grain_types<br/>WHERE CAST(date AS DATE) = target_date<br/>GROUP BY grain_type ORDER BY total_spent DESC
    DB-->>REPO: breakdown rows
    REPO-->>SVC: list[Row]

    loop For each row
        SVC->>SVC: build GrainTypeBreakdownItem(grain_type_id,<br/>grain_type_name, unit, total_weight, total_spent)
    end

    SVC->>SVC: build DailyGrainPurchaseReport(date, total_amount, breakdown)
    SVC-->>API: DailyGrainPurchaseReport
    API-->>UI: 200 OK DailyGrainPurchaseReport
    UI-->>Owner: Renders daily grain purchase total and breakdown by type
```
