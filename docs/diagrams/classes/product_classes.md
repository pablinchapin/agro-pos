## Product Module — Class Diagram

This diagram shows the three active classes in the products module and how they delegate responsibility downward. Method signatures are taken verbatim from `backend/app/api/v1/endpoints/products.py`, `backend/app/services/product_service.py`, and `backend/app/repositories/product_repository.py`. The `Product` model class is included to show what the repository returns.

```mermaid
classDiagram
    class ProductsRouter {
        +create_product(payload: ProductCreate, db: AsyncSession) ProductResponse
        +list_products(db: AsyncSession) list[ProductResponse]
        +get_product(product_id: int, db: AsyncSession) ProductResponse
        +update_product(product_id: int, payload: ProductUpdate, db: AsyncSession) ProductResponse
        +delete_product(product_id: int, db: AsyncSession) Response
    }
    class ProductService {
        -repo: ProductRepository
        +create_product(data: ProductCreate) Product
        +get_product(product_id: int) Product
        +list_products() list[Product]
        +update_product(product_id: int, data: ProductUpdate) Product
        +delete_product(product_id: int) None
        +reduce_stock(product_id: int, quantity: int) Product
    }
    class ProductRepository {
        -db: AsyncSession
        +get_by_id(product_id: int) Optional[Product]
        +get_by_name(name: str) Optional[Product]
        +list_all() list[Product]
        +create(data: ProductCreate) Product
        +update(product_id: int, data: ProductUpdate) Optional[Product]
        +delete(product_id: int) bool
    }
    class Product {
        +id: int
        +name: str
        +category: str
        +unit: str
        +price: Decimal
        +stock: int
        +min_stock: int
        +created_at: datetime
    }
    ProductsRouter --> ProductService : delegates to
    ProductService --> ProductRepository : queries via
    ProductRepository --> Product : returns
```
