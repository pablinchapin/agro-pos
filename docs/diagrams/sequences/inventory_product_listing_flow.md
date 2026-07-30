## Product Inventory Listing — Sequence Diagram

This diagram traces `GET /api/v1/inventory/products`, sourced from `backend/app/api/v1/endpoints/inventory.py` and `backend/app/services/inventory_service.py`. `InventoryService.list_product_inventory()` fetches every row from `products` via `ProductRepository.list_all()` (no filters — the module always reports the full catalog) and, for each `Product`, computes the `low_stock` flag as `stock <= min_stock` before mapping it into a `ProductInventoryResponse`. This flow performs no writes: it never calls `reduce_stock` or any other mutating repository method.

```mermaid
sequenceDiagram
    actor Owner
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as InventoryService
    participant REPO as ProductRepository
    participant DB as PostgreSQL

    Owner->>UI: Opens inventory dashboard
    UI->>API: GET /api/v1/inventory/products
    API->>SVC: list_product_inventory()
    SVC->>REPO: list_all()
    REPO->>DB: SELECT * FROM products
    DB-->>REPO: product rows
    REPO-->>SVC: list[Product]

    loop For each product
        Note over SVC: low_stock = product.stock <= product.min_stock
        SVC->>SVC: build ProductInventoryResponse(id, name, category,<br/>unit, stock, min_stock, low_stock)
    end

    SVC-->>API: list[ProductInventoryResponse]
    API-->>UI: 200 OK [ProductInventoryResponse...]
    UI-->>Owner: Renders product stock table with low-stock flags
```
