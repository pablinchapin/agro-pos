# Agro POS — Mermaid Diagrams

This directory contains all technical diagrams for the agro-pos project, organized by diagram type. Every diagram is generated from the actual source code — no fields or relationships are invented.

## Directory Structure

```
docs/diagrams/
├── erd/          Entity-relationship diagrams (SQLAlchemy models)
├── sequences/    Sequence diagrams (cross-layer business flows)
├── classes/      Class diagrams (service / repository / model relationships)
└── flows/        Flowcharts (business rules with branching logic)
```

---

## Products Module

| Type | File | Description |
|---|---|---|
| ERD | [erd/product_erd.md](erd/product_erd.md) | `products` table — all columns and types from `Product` model |
| Sequence | [sequences/product_sale_flow.md](sequences/product_sale_flow.md) | Full sale flow: Streamlit UI → FastAPI → ProductService → ProductRepository → PostgreSQL |
| Class | [classes/product_classes.md](classes/product_classes.md) | `ProductsRouter`, `ProductService`, `ProductRepository`, and `Product` model with method signatures |
| Flowchart | [flows/product_stock_validation_flow.md](flows/product_stock_validation_flow.md) | Branching logic inside `ProductService.reduce_stock()` |

---

## Persons Module

| Type | File | Description |
|---|---|---|
| ERD | [erd/person_erd.md](erd/person_erd.md) | `persons` table — all columns and types from `Person` model; future FK references to `sales` and `grain_purchases` noted in description only |
| Sequence | [sequences/person_creation_flow.md](sequences/person_creation_flow.md) | Full `POST /api/v1/persons/` flow: Streamlit UI → FastAPI → PersonService → PersonRepository → PostgreSQL, with invalid-role and duplicate-name+phone failure branches |
| Class | [classes/person_classes.md](classes/person_classes.md) | `PersonsEndpoint`, `PersonService`, `PersonRepository`, and `Person` model with exact method signatures |
| Flowchart | [flows/person_role_validation_flow.md](flows/person_role_validation_flow.md) | Role validation and duplicate name+phone check logic for `create_person` and `update_person`, including the phone=None bypass and the id-exclusion guard |

---

## Grain Types (Catalog)

| Type | File | Description |
|---|---|---|
| ERD | [erd/grain_type_erd.md](erd/grain_type_erd.md) | `grain_types` catalog table — all columns and types from `GrainType` model; managed via Alembic seed migrations, no API endpoints |

---

## Grain Purchases Module

| Type | File | Description |
|---|---|---|
| ERD | [erd/grain_purchase_erd.md](erd/grain_purchase_erd.md) | `grain_purchases` and `grain_inventory` tables with all columns and FK links to `persons` and `grain_types`; notes that `total_stock` is auto-updated on every purchase |
| Sequence | [sequences/grain_purchase_creation_flow.md](sequences/grain_purchase_creation_flow.md) | Full `POST /api/v1/grain-purchases/` flow across all layers, including person-not-found (404), invalid-role (422), and grain-type-not-found (404) failure branches, plus the inventory upsert step |
| Class | [classes/grain_purchase_classes.md](classes/grain_purchase_classes.md) | `GrainPurchasesEndpoint`, `GrainPurchaseService`, `GrainPurchaseRepository`, `GrainInventoryRepository`, `GrainTypeRepository`, `PersonService`, and both ORM models with exact method signatures |
| Flowchart | [flows/grain_purchase_business_rules_flow.md](flows/grain_purchase_business_rules_flow.md) | Two subgraphs: person role validation (farmer/both vs customer) and inventory upsert logic (increment existing row vs insert new row) |

---

## Sales Module

| Type | File | Description |
|---|---|---|
| ERD | [erd/sale_erd.md](erd/sale_erd.md) | `sales` and `sale_items` tables with all columns and FK links to `persons` and `products`; notes that `total_amount`/`subtotal` are server-calculated and that `SaleItem` rows cascade with their parent `Sale` |
| Sequence | [sequences/sale_creation_flow.md](sequences/sale_creation_flow.md) | Full `POST /api/v1/sales/` flow across all layers, including person-not-found (404), invalid-role/farmer-rejected (422), product-not-found (404), and insufficient-stock (422) failure branches, plus the per-item stock reduction and persistence steps |
| Class | [classes/sale_classes.md](classes/sale_classes.md) | `SalesEndpoint`, `SaleService`, `SaleRepository`, `PersonService`, `ProductService`, and both `Sale`/`SaleItem` ORM models with exact method signatures; notes there is no separate `SaleItemRepository` |
| Flowchart | [flows/sale_validation_flow.md](flows/sale_validation_flow.md) | Person role validation (customer/both vs farmer), per-item product existence check with subtotal/total accumulation, aggregated stock validation before any reduction, and per-item stock reduction |

---

## Inventory Module

Read-only module — introduces no new tables/migrations and performs no writes. It reports live stock data owned by the Products and Grain Purchases modules.

| Type | File | Description |
|---|---|---|
| ERD | [erd/inventory_erd.md](erd/inventory_erd.md) | `products`, `grain_types`, and `grain_inventory` tables (all pre-existing, no new tables) limited to the columns `InventoryService` actually consumes; notes that stock values are still written exclusively by the sales and grain purchase flows |
| Sequence | [sequences/inventory_product_listing_flow.md](sequences/inventory_product_listing_flow.md) | Full `GET /api/v1/inventory/products` flow: FastAPI → `InventoryService.list_product_inventory()` → `ProductRepository.list_all()` → PostgreSQL, including the per-product `low_stock` computation |
| Sequence | [sequences/inventory_grain_listing_flow.md](sequences/inventory_grain_listing_flow.md) | Full `GET /api/v1/inventory/grains` flow: FastAPI → `InventoryService.list_grain_inventory()` → `GrainTypeRepository.get_all()` + `GrainInventoryRepository.list_all()` → PostgreSQL, including the `{grain_type_id: total_stock}` lookup and `Decimal("0")` defaulting for grain types with no purchases |
| Flowchart | [flows/inventory_low_stock_detection_flow.md](flows/inventory_low_stock_detection_flow.md) | Two subgraphs: product `low_stock` detection (`stock <= min_stock`) and grain inventory defaulting (existing `grain_inventory` row vs `Decimal("0")` default) |

---

## Reporting Module

Read-only aggregation/reporting layer over the `sales`, `sale_items`, `products`, `grain_purchases`, and `grain_types` tables (all pre-existing — no new tables or migrations). Exposes three `GET` endpoints under `/api/v1/reports`: a daily sales report, a daily grain purchase report, and a top-sold-products report over an arbitrary date range. `ReportService` never writes to the database and never raises anything other than `DomainError` (for an invalid `start_date > end_date` range, surfaced as HTTP 422); `ReportRepository` is organized around report queries rather than a single table, since reporting is inherently a cross-entity concern.

| Type | File | Description |
|---|---|---|
| Sequence | [sequences/report_daily_sales_flow.md](sequences/report_daily_sales_flow.md) | Full `GET /api/v1/reports/sales/daily` flow: FastAPI → `ReportService.get_daily_sales_report()` → `ReportRepository.get_daily_sales_totals()` + `get_top_products_by_date()` (limit 5) → PostgreSQL, including the `date` defaulting to `_today()` (UTC) when omitted |
| Sequence | [sequences/report_daily_grain_purchase_flow.md](sequences/report_daily_grain_purchase_flow.md) | Full `GET /api/v1/reports/grain-purchases/daily` flow: FastAPI → `ReportService.get_daily_grain_purchase_report()` → `ReportRepository.get_daily_grain_purchase_total()` + `get_grain_purchase_breakdown_by_type()` → PostgreSQL, including the `date` defaulting to `_today()` (UTC) when omitted |
| Sequence | [sequences/report_top_sold_products_flow.md](sequences/report_top_sold_products_flow.md) | Full `GET /api/v1/reports/products/top-sold` flow: FastAPI → `ReportService.get_top_sold_products()` → `ReportRepository.get_top_products_by_range()` (limit 10) → PostgreSQL, including independent `start_date`/`end_date` defaulting to `_today()` and the `start_date > end_date` → `DomainError` (422) failure branch that short-circuits before any query runs |
| Flowchart | [flows/report_date_defaulting_flow.md](flows/report_date_defaulting_flow.md) | Two subgraphs: single-date defaulting shared by `sales/daily` and `grain-purchases/daily`, and range defaulting + `start_date <= end_date` validation for `products/top-sold` |

---

## Auth Module

JWT-based authentication and role-based access control (RBAC) that gates every other module. `POST /api/v1/auth/token` is the sole public endpoint (no auth dependency) — it accepts an OAuth2 password-grant form and returns a signed JWT embedding `sub` (username) and `role` (`admin` or `clerk`) as an OAuth2-standard `Token` schema field named `access_token`. Every other route in the API depends on `require_admin` or `require_clerk` (both built on `get_current_user`, which decodes and validates the bearer token), including RBAC wiring retrofitted onto the pre-existing `products`, `sales`, `grain_purchases`, `persons`, `inventory`, and `reports` endpoints. The `users` table has no foreign key relationships to any domain table — auth is orthogonal to the domain model. User management (`/api/v1/users`) is admin-only CRUD with no delete, only deactivate.

| Type | File | Description |
|---|---|---|
| ERD | [erd/user_erd.md](erd/user_erd.md) | `users` table — all columns and types from `User` model; notes it has no FK relationships to any domain table |
| Sequence | [sequences/auth_login_flow.md](sequences/auth_login_flow.md) | Full `POST /api/v1/auth/token` flow: FastAPI → `AuthService.login()` → `UserService.authenticate()` → `UserRepository.get_by_username()` → PostgreSQL → `verify_password()` → `create_access_token()`, including the unknown-user, inactive-user, and wrong-password failure branches (all collapsing to a generic 401) |
| Sequence | [sequences/auth_protected_request_flow.md](sequences/auth_protected_request_flow.md) | End-to-end protected request using `POST /api/v1/sales/` as the concrete example: bearer token → `get_current_user` (401 on invalid/expired) → `require_clerk` (403 on role mismatch) → normal service/repository/DB chain, with both the success and 403-denied paths shown |
| Flowchart | [flows/auth_rbac_check_flow.md](flows/auth_rbac_check_flow.md) | Full RBAC decision tree: missing header → 401, invalid/expired JWT → 401, then branching on which dependency the route declares (`require_admin` → role == admin, `require_clerk` → role in admin/clerk) → 403 on mismatch or proceed to the endpoint handler |

---

## Frontend (Admin) Module

The Streamlit frontend (`frontend/app.py`, `frontend/login.py`, `frontend/admin/*`, `frontend/pos/*`, `frontend/shared/api_client.py`) — login gate, role-based navigation, and the admin-facing pages built on top of it: product catalog CRUD (`admin/products.py`), a read-only inventory view (`admin/inventory.py`), and reports with date pickers (`admin/reports.py`). On every script run, `app.py` checks `st.session_state` for an `access_token`; if absent, it renders `login_page()` and halts via `st.stop()`. `login_page()` (`frontend/login.py`) authenticates against the backend's `POST /auth/token` (see the Auth Module above, `sequences/auth_login_flow.md`) via `shared/api_client.py`'s `login()` helper, then decodes the returned JWT client-side with `jose.jwt.get_unverified_claims()` purely to read the `role` claim for UI purposes — the backend independently verifies the token's signature on every subsequent request. Once `access_token` is present, `app.py` always registers the "Punto de Venta" pages and additionally registers the "Administración" pages only when `role == "admin"`. This role check is **frontend UX gating only, not an authorization boundary**: real enforcement happens on the backend via `require_admin`/`require_clerk` on every request, as already documented in `sequences/auth_protected_request_flow.md` and `flows/auth_rbac_check_flow.md`. A separate `_handle_response()` helper in `api_client.py` clears `st.session_state` and reruns the app whenever the backend returns a 401 on any authenticated call, routing the user back through the same login gate.

| Type | File | Description |
|---|---|---|
| Sequence | [sequences/frontend_login_navigation_flow.md](sequences/frontend_login_navigation_flow.md) | Full login flow: `app.py`'s no-token gate → `login_page()` form submit → `api_client.login()` → `POST /auth/token` → `decode_token()` (unverified, client-side, role-only) → `st.session_state` population → `st.rerun()` → `app.py` re-executes and builds role-conditioned navigation, including the bad-credentials failure branch (`httpx.HTTPStatusError` → `st.error`, no session state set) |
| Flowchart | [flows/frontend_nav_gate_flow.md](flows/frontend_nav_gate_flow.md) | Navigation gate decision tree: `access_token` present? → login page + `st.stop()` vs role-conditioned page registration (`Punto de Venta` always, `Administración` only when `role == "admin"`) → `st.navigation(pages).run()`; includes the separate 401-triggered `_handle_response()` path that clears session state and re-enters the same gate |
