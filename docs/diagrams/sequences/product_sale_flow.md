## Product Sale Flow — Sequence Diagram

This diagram traces how a sale triggers stock reduction across every layer of the architecture: the Streamlit POS UI calls FastAPI, which delegates to `ProductService`, which validates stock and then persists the change via `ProductRepository` to PostgreSQL. The `reduce_stock` logic is sourced directly from `backend/app/services/product_service.py`. The Sales endpoint that orchestrates this call will be added in the Sales module; the product-side sequence shown here is complete and final.

```mermaid
sequenceDiagram
    actor Cashier
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as ProductService
    participant REPO as ProductRepository
    participant DB as PostgreSQL

    Cashier->>UI: Confirms cart with selected products
    UI->>API: POST /api/v1/sales/ {items}
    loop For each cart item
        API->>SVC: reduce_stock(product_id, quantity)
        SVC->>REPO: get_by_id(product_id)
        REPO->>DB: SELECT * FROM products WHERE id = ?
        DB-->>REPO: row or None
        REPO-->>SVC: Product or None
        alt Product not found
            SVC-->>API: raise NotFoundError
            API-->>UI: 404 Not Found
            UI-->>Cashier: "Producto no encontrado"
        else Product found, stock < quantity
            SVC-->>API: raise InsufficientStockError
            API-->>UI: 422 Unprocessable Entity
            UI-->>Cashier: "Stock insuficiente"
        else Stock sufficient
            SVC->>REPO: update(product_id, ProductUpdate(stock=new_stock))
            REPO->>DB: UPDATE products SET stock = new_stock WHERE id = ?
            DB-->>REPO: updated row
            REPO-->>SVC: Product (updated)
            SVC-->>API: Product (updated)
        end
    end
    API-->>UI: SaleResponse (201)
    UI-->>Cashier: "Venta registrada"
```
