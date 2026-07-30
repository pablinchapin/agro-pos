## Product Stock Validation — Flowchart

This flowchart traces every branch inside `ProductService.reduce_stock()` as it exists in `backend/app/services/product_service.py`. The method first delegates product lookup to `get_product()`, which itself raises `NotFoundError` when the product does not exist. It then compares current stock against the requested quantity and raises `InsufficientStockError` when stock is insufficient. Only when both guards pass does it compute the new stock value and persist the update via the repository.

```mermaid
flowchart TD
    A([reduce_stock called\nproduct_id, quantity]) --> B[get_product product_id]
    B --> C[repo.get_by_id product_id]
    C --> D{Product found?}
    D -- No --> E[raise NotFoundError]
    D -- Yes --> F{product.stock < quantity?}
    F -- Yes --> G[raise InsufficientStockError]
    F -- No --> H[new_stock = product.stock - quantity]
    H --> I[ProductUpdate stock=new_stock]
    I --> J[repo.update product_id, update_data]
    J --> K[DB: UPDATE products SET stock = new_stock]
    K --> L([Return updated Product])
```
