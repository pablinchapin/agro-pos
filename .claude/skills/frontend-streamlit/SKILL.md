---
name: frontend-streamlit
description: Use this skill when creating or modifying Streamlit pages in frontend/pos/ or frontend/admin/, the shared API client, or navigation in app.py. Covers page structure, session state, and how the frontend talks to the backend API.
---

## Audience Separation
- `frontend/pos/` — cashier-facing pages, daily operations (sales, grain purchases)
- `frontend/admin/` — owner/manager-facing pages (catalog management, inventory, reports)
- Never mix concerns: a page in `pos/` should not contain product-editing or report logic, and vice versa

## Navigation — frontend/app.py
All pages are registered explicitly via `st.Page()`, grouped by audience:

```python
import streamlit as st

pos_ventas = st.Page("pos/ventas.py", title="Ventas", icon="🛒")
pos_compra = st.Page("pos/compra_grano.py", title="Compra de Grano", icon="🌾")
admin_catalogo = st.Page("admin/catalogo_productos.py", title="Catálogo de Productos", icon="📦")

pg = st.navigation({
    "Punto de Venta": [pos_ventas, pos_compra],
    "Administración": [admin_catalogo],
})
pg.run()
```

No numeric filename prefixes. Title, icon, and order are always set explicitly in `st.Page()`.

## Shared API Client — frontend/shared/api_client.py
One shared httpx client, reused across all pages, never instantiated per-page:

```python
import httpx
import streamlit as st

BASE_URL = "http://localhost:8000/api/v1"

@st.cache_resource
def get_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=10.0)

def get_products() -> list[dict]:
    response = get_client().get("/products/", headers=get_headers())
    response.raise_for_status()
    return response.json()

def create_sale(payload: dict) -> dict:
    response = get_client().post("/sales/", json=payload,
                                  headers=get_headers())
    response.raise_for_status()
    return response.json()
```

Use sync `httpx.Client` here, NOT `httpx.AsyncClient` — Streamlit's execution model is synchronous per script run, async clients add complexity with no benefit in this context.

## Page Template
```python
import streamlit as st
from shared.api_client import get_products, create_sale

st.title("Ventas")

if "cart" not in st.session_state:
    st.session_state.cart = []

products = get_products()
selected = st.selectbox("Producto", options=products, format_func=lambda p: p["name"])
qty = st.number_input("Cantidad", min_value=1, value=1)

if st.button("Agregar al carrito"):
    st.session_state.cart.append({"product_id": selected["id"], "quantity": qty})
    st.rerun()

st.write(st.session_state.cart)

if st.button("Confirmar venta") and st.session_state.cart:
    create_sale({"items": st.session_state.cart})
    st.session_state.cart = []
    st.success("Venta registrada")
    st.rerun()
```

## Session State Rules
- Streamlit re-runs the entire script top-to-bottom on every interaction — never assume variables persist outside `st.session_state`
- Initialize every session_state key with an `if "key" not in st.session_state:` guard before using it
- Cart/transaction-in-progress data belongs in `st.session_state`, scoped with a clear key name (e.g. `cart`, not `data`)
- Call `st.rerun()` after mutating state that should immediately reflect in the UI (e.g. after adding to cart)

## Error Handling
- Wrap API calls in `try/except httpx.HTTPStatusError` and show `st.error(...)` with the backend's `detail` message — never let raw exceptions surface to the user
- Backend errors already come with proper status codes and `{"detail": "..."}" bodies (see service-layer skill) — just display `e.response.json()["detail"]`

## Authentication — Token Handling

The shared api_client must include the Bearer token in every request.
Token is stored in st.session_state after login.

```python
# frontend/shared/api_client.py

def get_headers() -> dict:
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
```

## Login Flow

```python
# frontend/login.py
import streamlit as st
from shared.api_client import get_client

def login_page():
    st.title("Agro POS — Iniciar Sesión")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        try:
            response = get_client().post(
                "/auth/token",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.username = username
            st.rerun()
        except httpx.HTTPStatusError:
            st.error("Usuario o contraseña incorrectos")
```

## Rules
- All HTTP calls to the backend go through `shared/api_client.py` — never call `httpx` directly inside a page file
- No business logic in pages (no stock validation, no price calculation) — that already happened in the backend; the frontend only displays and collects input
- Reusable rendering logic (e.g. a product picker used in both `ventas.py` and `catalogo_productos.py`) goes in `shared/components.py` as a plain function — remember these share global session state, they are not isolated like React components
- Use `st.cache_data` for read-heavy, rarely-changing data (e.g. product list) to avoid hitting the API on every rerun unnecessarily — but invalidate/clear cache after writes (e.g. after creating a product)