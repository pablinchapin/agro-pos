# Agro POS — Product Specification

## Problem Statement
Agricultural supply stores (agroservicios) in Guatemala operate two parallel
commercial flows: selling agricultural inputs to farmers, and buying raw grains
from those same farmers. Managing both flows manually (paper or spreadsheets)
creates inventory errors, pricing inconsistencies, and no visibility into
margins. This system digitalizes both flows in a single POS with a shared
person registry, so the same individual can be tracked as a customer, a
farmer, or both — without duplicating data.

## Users
- **Store clerk**: operates the POS daily — registers sales and grain purchases
- **Store owner/manager**: manages product catalog, reviews inventory levels,
  and consults reports on sales and grain purchase activity

## Key Domain Concepts
- **Product**: item sold by the store (seed, fertilizer, herbicide, fungicide)
- **Grain**: agricultural product purchased from farmers (coffee, corn, beans)
- **Person**: any individual that interacts with the store. Has one or more roles:
  - `customer` → buys products from the store
  - `farmer` → sells grains to the store
  - `both` → acts as customer and farmer (common in Guatemalan agroservicios)
- **Sale**: outbound transaction — store sells products to a Person (role: customer/both)
- **GrainPurchase**: inbound transaction — store buys grains from a Person (role: farmer/both)
- **Supplier**: company/person that sells inputs TO the store (v2)

## Implementation Order
Modules must be implemented in this order due to data dependencies:

Products          (no dependencies)              ✅ done
Persons           (no dependencies)              ✅ done
Grain Purchases   (depends on Person)            ✅ done
Sales / POS       (depends on Person + Product)  ✅ done
Inventory         (depends on Product + Grain)   ✅ done
Reporting         (depends on Sales + Grain)     ✅ done
Auth / Users      (cross-cutting concern)        ⬜ next
Frontend Admin    (depends on Auth)              ⬜
Frontend POS      (depends on Auth)              ⬜


## Core Modules

### 1. Product Catalog  DONE
Manages the store's sellable inventory of agricultural inputs.
- Full CRUD for products
- Categories: `seed`, `fertilizer`, `herbicide`, `fungicide`
- Units of measure: `lb`, `kg`, `liter`, `unit`
- Fields: name, category, unit, price (Decimal), stock quantity, minimum stock threshold
- Stock decreases automatically on each sale
- Low stock alert when `stock <= min_stock`

### 2. Persons  DONE
Central registry of all individuals that interact with the store.
Avoids data duplication when the same person is both a customer and a farmer
(common in Guatemalan agroservicios).
- Full CRUD for persons
- Role field: `customer`, `farmer`, or `both`
- Fields: full_name, phone, role, notes, created_at
- A Person with role `farmer` or `both` can be referenced in grain purchases
- A Person with role `customer` or `both` can be referenced in sales
- Role validation enforced at the service layer:
  - Cannot register a grain purchase for a Person with role `customer`
  - Cannot register a sale for a Person with role `farmer`

### 3. Grain Purchasing (Inbound) DONE
Registers the store's purchases of raw grains from farmers.
Each purchase references a Person (role: farmer/both) and updates grain inventory.
- Register grain purchases linked to a Person
- Grain types: `coffee`, `corn`, `beans` (extensible via grain_types table)
- Units: `lb` (pounds), `qq` (quintales — 100 lb, common in Guatemala)
- Fields: person_id (FK→persons), grain_type_id (FK→grain_types),
  weight, price_per_unit, total (auto-calculated), date, notes
- Each purchase increases grain inventory automatically
- Cannot register a purchase for a Person with role `customer`

### 4. Sales / POS (Outbound) DONE
Registers the store's sales of agricultural inputs to customers.
Each sale references a Person (role: customer/both) and reduces product stock.
- Create sales transactions linked to a Person
- Multi-item sales: one sale can include multiple products
- Total calculated automatically from line items (quantity × unit_price)
- Each confirmed sale reduces stock for each product in the sale
- Stock validation enforced before confirming: cannot sell more than available stock
- Basic receipt data available (no printer integration in v1)
- Cannot register a sale for a Person with role `farmer`

### 5. Inventory  DONE
Provides real-time visibility into stock levels for both products and grains.
- Current stock per product (inputs) with low-stock flag
- Current stock per grain type (from accumulated purchases)
- Low stock alerts when `stock <= min_stock` (products only in v1)
- Read-only module — stock is modified only through sales and grain purchases

### 6. Reporting (v1 — basic) DONE
Provides basic operational summaries for the store owner/manager.
- Daily sales summary (total amount, number of transactions, top products)
- Daily grain purchases summary (total spent, breakdown by grain type)
- Top 10 sold products by quantity (configurable date range)
- All reports are read-only queries — no data modification

## Authentication & Authorization (RBAC — v1)

### Design
Role-Based Access Control with two fixed roles:
- `admin` — full access: product catalog, reports, sales, grain purchases, inventory, user management
- `clerk` — operational access: register sales, register grain purchases, view inventory, view products

### Users
- Managed from the admin panel (create, deactivate — no delete)
- Stored in `users` table with hashed passwords (bcrypt)
- A user has exactly one role: `admin` or `clerk`

### Auth Flow
1. User submits username + password to `POST /api/v1/auth/token`
2. Server verifies credentials, returns a signed JWT
3. JWT payload: `{ sub: username, role: admin|clerk, exp: timestamp }`
4. All protected endpoints verify the JWT via `Depends(get_current_user)`

### Endpoint Permission Matrix
| Endpoint group                       | admin | clerk |
|--------------------------------------|-------|-------|
| POST/PATCH/DELETE /products/         | ALLOW | DENY  |
| GET /products/                       | ALLOW | ALLOW |
| ALL /persons/                        | ALLOW | ALLOW |
| POST /sales/                         | ALLOW | ALLOW |
| GET /sales/                          | ALLOW | ALLOW |
| POST /grain-purchases/               | ALLOW | ALLOW |
| GET /grain-purchases/                | ALLOW | ALLOW |
| ALL /inventory/                      | ALLOW | DENY  |
| ALL /reports/                        | ALLOW | DENY  |
| ALL /users/                          | ALLOW | DENY  |
| POST /auth/token                     | public | public |

## Out of Scope (v1)
- Printer/receipt hardware integration
- Multi-store / multi-branch support
- Password reset and email verification (auth v2)
- Token refresh mechanism (auth v2)
- Credit / accounts receivable
- Supplier management (v2)
- Grain inventory minimum thresholds and alerts (v2)

## API Design
- Base URL: `/api/v1/`
- Response format: JSON
- Error format: `{ "detail": "message" }`
- HTTP status codes: 200 (ok), 201 (created), 404 (not found),
  409 (duplicate/conflict), 422 (business rule violation)

## Database
- PostgreSQL (single schema, no multi-tenancy in v1)
- All schema changes via Alembic migrations — never manual ALTER TABLE
- Async connection via SQLAlchemy 2.0 + asyncpg driver