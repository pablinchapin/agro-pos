## Protected Request (RBAC) — Sequence Diagram

This diagram traces a protected request end-to-end using `POST /api/v1/sales/` as the concrete example, sourced from `backend/app/api/v1/endpoints/sales.py`, `backend/app/core/dependencies.py`, and `backend/app/core/security.py`. Every route except `POST /api/v1/auth/token` depends on `require_admin` or `require_clerk`, both of which depend on `get_current_user`. `get_current_user` extracts the bearer token via FastAPI's `OAuth2PasswordBearer`, calls `decode_access_token()` (which swallows any `JWTError` — expired, malformed, or bad signature — and returns `{}`), and raises `401` if the payload is empty. `require_clerk` (used by `sales.py`, `grain_purchases.py`, `persons.py`, `inventory.py`) then checks `role in ("admin", "clerk")`; `require_admin` (used by `users.py`, `reports.py`, and the write endpoints of `products.py`) checks `role == "admin"` — so an admin token satisfies both. Only once these dependencies resolve does the endpoint handler run and delegate to the normal service/repository/DB chain.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI (sales.py)
    participant DEP as get_current_user
    participant RBAC as require_clerk
    participant SEC as security.py
    participant SVC as SaleService
    participant REPO as SaleRepository
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/sales/ {..} <br/>Authorization: Bearer <token>
    API->>DEP: get_current_user(token)
    DEP->>SEC: decode_access_token(token)

    alt Token missing, malformed, or expired
        SEC-->>DEP: {} (JWTError caught)
        DEP-->>API: raise HTTPException 401 "Invalid or expired token"
        API-->>Client: 401 Unauthorized
    else Token valid
        SEC-->>DEP: payload {sub, role, exp}
        DEP-->>RBAC: user dict {sub, role}
        RBAC->>RBAC: check role in (admin, clerk)

        alt role not in (admin, clerk)
            RBAC-->>API: raise HTTPException 403 "Clerk or admin access required"
            API-->>Client: 403 Forbidden
        else role is admin or clerk
            RBAC-->>API: user dict (authorized)
            API->>SVC: create_sale(payload)
            SVC->>REPO: create(data, items, total_amount, sale_date)
            REPO->>DB: INSERT INTO sales / sale_items ...
            DB-->>REPO: new sale id
            REPO-->>SVC: Sale object
            SVC-->>API: Sale object
            API-->>Client: 201 Created (SaleResponse)
        end
    end
```
