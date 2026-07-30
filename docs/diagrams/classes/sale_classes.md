## Sales Module — Class Diagram

This diagram shows the classes that make up the sales module and the supporting classes they depend on. `SalesEndpoint` delegates all logic to `SaleService`, which owns a `SaleRepository` and delegates person and product validation/mutation to `PersonService` and `ProductService` respectively. There is no separate `SaleItemRepository` — `SaleItem` rows are created and deleted entirely through the `Sale.items` relationship (`cascade="all, delete-orphan"`), so `SaleRepository` is the only repository that persists sales and their line items together in `create()`. Method signatures are taken directly from the source files; `Sale` and `SaleItem` are SQLAlchemy ORM models (fields listed, no methods).

```mermaid
classDiagram
    class SalesEndpoint {
        +create_sale(payload: SaleCreate, db: AsyncSession) SaleResponse
        +list_sales(person_id: Optional[int], db: AsyncSession) list[SaleResponse]
        +get_sale(sale_id: int, db: AsyncSession) SaleResponse
    }
    class SaleService {
        -db: AsyncSession
        -sale_repo: SaleRepository
        -person_service: PersonService
        -product_service: ProductService
        +create_sale(data: SaleCreate) Sale
        +get_sale(sale_id: int) Sale
        +list_sales(person_id: Optional[int]) list[Sale]
    }
    class SaleRepository {
        -db: AsyncSession
        +get_by_id(sale_id: int) Optional[Sale]
        +list_all() list[Sale]
        +list_by_person(person_id: int) list[Sale]
        +create(data: SaleCreate, items_with_subtotals: list[Dict], total_amount: Decimal, date: datetime) Sale
    }
    class PersonService {
        -repo: PersonRepository
        +get_person(person_id: int) Person
        +create_person(data: PersonCreate) Person
        +list_persons() list[Person]
        +list_persons_by_role(role: str) list[Person]
        +update_person(person_id: int, data: PersonUpdate) Person
        +delete_person(person_id: int) None
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
    class Sale {
        +id: int
        +person_id: int
        +date: datetime
        +total_amount: Decimal
        +notes: str
        +items: list[SaleItem]
    }
    class SaleItem {
        +id: int
        +sale_id: int
        +product_id: int
        +quantity: int
        +unit_price: Decimal
        +subtotal: Decimal
    }

    SalesEndpoint --> SaleService : delegates to
    SaleService --> SaleRepository : persists via
    SaleService --> PersonService : validates person via
    SaleService --> ProductService : validates product & reduces stock via
    SaleRepository --> Sale : persists
    Sale "1" *-- "many" SaleItem : items (cascade all, delete-orphan)
```

Note: `SaleItem` rows have no dedicated repository — they are created, read, and deleted exclusively through the `Sale.items` ORM relationship inside `SaleRepository`.
