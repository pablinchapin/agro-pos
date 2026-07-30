## Frontend Login & Role-Based Navigation Setup — Sequence Diagram

This diagram traces the Streamlit admin/POS frontend's login flow, sourced from `frontend/app.py`, `frontend/login.py`, and `frontend/shared/api_client.py`. On every script run, `app.py` checks `st.session_state` for `access_token`; if absent it renders `login_page()` and calls `st.stop()`, halting execution before any navigation is built. The login form submits credentials via `api_client.login()`, an OAuth2 form-encoded `POST /auth/token` request with no `Authorization` header (see `sequences/auth_login_flow.md` for the backend's handling of that request). On success, `decode_token()` reads the `role` claim out of the JWT client-side using `jose.jwt.get_unverified_claims()` — **no signature verification happens here**; it exists purely so the frontend knows which navigation sections to render, since the backend independently verifies the token's signature on every subsequent authenticated request. `login_page()` then populates `st.session_state` (`access_token`, `username`, `role`) and calls `st.rerun()`, causing `app.py` to re-execute from the top: this time `access_token` is present, so it skips the login gate, builds the `pages` dict (always including "Punto de Venta", conditionally including "Administración" when `role == "admin"`), and calls `st.navigation(pages).run()`.

**This is frontend UX gating only.** The role-based section visibility here does not enforce anything — it only affects which pages are offered in the sidebar. Actual authorization happens on the backend via `require_admin`/`require_clerk` on every API call, independent of what the frontend renders (see `flows/auth_rbac_check_flow.md` and `sequences/auth_protected_request_flow.md`).

```mermaid
sequenceDiagram
    actor User as Client (browser)
    participant APP as app.py
    participant LOGIN as login.py (login_page)
    participant CLIENT as api_client.py
    participant API as FastAPI (POST /auth/token)

    User->>APP: Load / refresh Streamlit app
    APP->>APP: "access_token" in st.session_state?

    alt No access_token
        APP->>LOGIN: login_page()
        LOGIN-->>User: Render username/password form
        APP->>APP: st.stop() (halt, no navigation built)

        User->>LOGIN: Submit form (username, password)
        LOGIN->>CLIENT: login(username, password)
        CLIENT->>API: POST /auth/token (form-encoded, no auth header)

        alt Invalid credentials
            API-->>CLIENT: 401 Unauthorized
            CLIENT-->>LOGIN: raise httpx.HTTPStatusError
            LOGIN-->>User: st.error("Usuario o contraseña incorrectos")
            Note over LOGIN: st.session_state untouched; form stays on screen
        else Valid credentials
            API-->>CLIENT: 200 OK {access_token, token_type}
            CLIENT-->>LOGIN: dict with access_token
            LOGIN->>CLIENT: decode_token(access_token)
            Note over CLIENT: jose.jwt.get_unverified_claims() — no signature check,\nbackend already verified it when issuing/will verify on every request
            CLIENT-->>LOGIN: claims dict (sub, role, exp)
            LOGIN->>LOGIN: st.session_state.access_token = access_token
            LOGIN->>LOGIN: st.session_state.username = username
            LOGIN->>LOGIN: st.session_state.role = claims["role"]
            LOGIN->>APP: st.rerun()
        end
    else access_token present
        APP->>APP: role = st.session_state.get("role")
        APP->>APP: pages = {"Punto de Venta": [sales.py, buys.py]}
        alt role == "admin"
            APP->>APP: pages["Administración"] = [products.py, inventory.py, reports.py]
        else role == "clerk" (or other)
            APP->>APP: Administración section omitted
        end
        APP->>APP: st.navigation(pages).run()
        APP-->>User: Render sidebar (username/role, "Cerrar sesión") + selected page
    end
```
