## Sale Creation — Sequence Diagram

This diagram traces the full cross-layer flow for `POST /api/v1/sales/`, sourced from `backend/app/api/v1/endpoints/sales.py` and `backend/app/services/sale_service.py`. `SaleService.create_sale()` first validates the person exists and has a customer-eligible role (`customer` or `both`) via `PersonService`, rejecting `farmer`. It then, for every submitted item, validates the product exists via `ProductService` (caching lookups per `product_id` within the request) while accumulating `subtotal`, `total_amount`, and per-product aggregated quantities — the total is never trusted from the client, it is always recomputed server-side. Only after every product's aggregated quantity is checked against its current stock does the service reduce stock per line item via `ProductService.reduce_stock()`, guaranteeing a sale never partially fails after stock was already reduced. Finally it persists the sale and its line items through `SaleRepository.create()`.

```mermaid
sequenceDiagram
    actor Cashier
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as SaleService
    participant PSVC as PersonService
    participant PRSVC as ProductService
    participant REPO as SaleRepository
    participant DB as PostgreSQL

    Cashier->>UI: Confirms sale with cart items
    UI->>API: POST /api/v1/sales/ {person_id, items[], notes}
    API->>SVC: create_sale(data)

    SVC->>PSVC: get_person(data.person_id)
    PSVC->>DB: SELECT * FROM persons WHERE id = ?
    DB-->>PSVC: row or None

    alt Person not found
        PSVC-->>SVC: raise NotFoundError
        SVC-->>API: NotFoundError
        API-->>UI: 404 Not Found
        UI-->>Cashier: "Persona no encontrada"
    else Person found

        alt person.role not in {customer, both}
            PSVC-->>SVC: Person(role="farmer")
            SVC-->>API: raise DomainError
            API-->>UI: 422 Unprocessable Entity
            UI-->>Cashier: "Esta persona no puede registrar ventas"
        else role is customer or both
            PSVC-->>SVC: Person object

            loop For each item in data.items
                SVC->>PRSVC: get_product(item.product_id)
                PRSVC->>DB: SELECT * FROM products WHERE id = ?
                DB-->>PRSVC: row or None

                alt Product not found
                    PRSVC-->>SVC: raise NotFoundError
                    SVC-->>API: NotFoundError
                    API-->>UI: 404 Not Found
                    UI-->>Cashier: "Producto no encontrado"
                else Product found
                    PRSVC-->>SVC: Product object
                    Note over SVC: subtotal = item.quantity × item.unit_price<br/>total_amount += subtotal<br/>quantities_by_product[product_id] += item.quantity
                end
            end

            Note over SVC: For each product_id in quantities_by_product:<br/>check product.stock < aggregated quantity

            alt Any product has insufficient stock
                SVC-->>API: raise InsufficientStockError
                API-->>UI: 422 Unprocessable Entity
                UI-->>Cashier: "Stock insuficiente"
            else Stock sufficient for all products
                loop For each item in data.items
                    SVC->>PRSVC: reduce_stock(item.product_id, item.quantity)
                    PRSVC->>DB: UPDATE products SET stock = stock - quantity
                    DB-->>PRSVC: updated row
                    PRSVC-->>SVC: Product (updated)
                end

                Note over SVC: sale_date = data.date or now(UTC)

                SVC->>REPO: create(data, items_with_subtotals, total_amount, sale_date)
                REPO->>DB: INSERT INTO sales ...
                REPO->>DB: INSERT INTO sale_items ... (via cascade)
                DB-->>REPO: new sale id
                REPO->>DB: SELECT sale + items (get_by_id)
                DB-->>REPO: Sale with items
                REPO-->>SVC: Sale object
                SVC-->>API: Sale object
                API-->>UI: SaleResponse (201)
                UI-->>Cashier: "Venta registrada"
            end
        end
    end
```
