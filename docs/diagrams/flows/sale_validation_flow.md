## Sale Validation — Flowchart

This flowchart traces every branch inside `SaleService.create_sale()` as it exists in `backend/app/services/sale_service.py`. The method first validates the person exists and has a customer-eligible role (`customer` or `both`), rejecting `farmer` with a `DomainError`. It then validates that every product referenced in the submitted items exists (raising `NotFoundError` on the first missing one), while accumulating each line item's `subtotal`, the running `total_amount`, and quantities aggregated per `product_id`. Only after all items have been validated does it check aggregated stock availability for every distinct product — before reducing any stock — so a sale never partially fails after stock was already reduced. If stock is sufficient for all products, it reduces stock per line item and persists the sale.

```mermaid
flowchart TD
    A([create_sale called with SaleCreate]) --> B[person_service.get_person person_id]
    B --> C{Person found?}
    C -- No --> D[Raise NotFoundError]
    C -- Yes --> E{role in customer or both?}
    E -- No, role is farmer --> F[Raise DomainError]
    E -- Yes --> G[For each item in data.items]
    G --> H{Product already looked up this request?}
    H -- Yes --> J[Use cached Product]
    H -- No --> I[product_service.get_product item.product_id]
    I --> K{Product found?}
    K -- No --> L[Raise NotFoundError]
    K -- Yes --> J
    J --> M[subtotal = quantity x unit_price]
    M --> N[total_amount += subtotal]
    N --> O[quantities_by_product product_id += quantity]
    O --> P{More items?}
    P -- Yes --> G
    P -- No --> Q[For each distinct product_id in quantities_by_product]
    Q --> R{product.stock less than aggregated quantity?}
    R -- Yes --> S[Raise InsufficientStockError]
    R -- No --> T{More products to check?}
    T -- Yes --> Q
    T -- No --> U[For each item in data.items]
    U --> V[product_service.reduce_stock product_id, quantity]
    V --> W{More items?}
    W -- Yes --> U
    W -- No --> X[sale_date = data.date or now UTC]
    X --> Y[sale_repo.create data, items_with_subtotals, total_amount, sale_date]
    Y --> Z([Return persisted Sale with items])
```
