## RBAC Permission Check — Flowchart

This flowchart traces the branching logic across `get_current_user`, `require_admin`, and `require_clerk` in `backend/app/core/dependencies.py`, backed by `decode_access_token()` in `backend/app/core/security.py`. FastAPI resolves the `Authorization: Bearer <token>` header via `OAuth2PasswordBearer` before `get_current_user` ever runs (a missing header is rejected by that scheme itself). `decode_access_token()` returns `{}` for any decoding failure — expired, malformed, or bad-signature JWTs are indistinguishable at this layer, all resulting in a `401`. Which role-check dependency runs next (`require_admin` vs `require_clerk`) depends entirely on which route declared it: `require_admin` is used by `users.py`, `reports.py`, and the write operations (`POST`/`PATCH`/`DELETE`) of `products.py`; `require_clerk` is used by `sales.py`, `grain_purchases.py`, `persons.py`, `inventory.py`, and the read (`GET`) operations of `products.py`. An `admin` token satisfies both checks since `require_clerk` accepts `role in (admin, clerk)`.

```mermaid
flowchart TD
    A([Incoming request to a protected route]) --> B{Authorization: Bearer header present?}
    B -- No --> C[FastAPI OAuth2PasswordBearer rejects: 401 Unauthorized]
    B -- Yes --> D[get_current_user: decode_access_token token]
    D --> E{JWT valid, signature OK, not expired?}
    E -- No, JWTError caught --> F[decode_access_token returns empty dict]
    F --> G[Raise HTTPException 401 'Invalid or expired token']
    E -- Yes --> H[payload = sub: username, role: role, exp: ...]
    H --> I{Which dependency does the route declare?}
    I -- require_admin --> J{payload.role == 'admin'?}
    J -- No --> K[Raise HTTPException 403 'Admin access required']
    J -- Yes --> L[Proceed: user dict passed to endpoint handler]
    I -- require_clerk --> M{payload.role in admin, clerk?}
    M -- No --> N[Raise HTTPException 403 'Clerk or admin access required']
    M -- Yes --> L
    L --> O([Endpoint handler executes business logic])
```
