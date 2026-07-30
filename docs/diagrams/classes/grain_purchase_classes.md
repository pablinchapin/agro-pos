## Grain Purchases — Class Diagram

This diagram shows the classes that make up the grain purchases module and the supporting classes they depend on. The three route handlers in `GrainPurchasesEndpoint` delegate all logic to `GrainPurchaseService`. The service owns instances of `GrainPurchaseRepository`, `GrainInventoryRepository`, and `GrainTypeRepository`, and delegates person lookup and role validation to `PersonService`. Method signatures are taken directly from the source files; `GrainPurchase` and `GrainInventory` are SQLAlchemy ORM models (fields listed, no methods).

```mermaid
classDiagram
    class GrainPurchasesEndpoint {
        +create_grain_purchase(payload, db) GrainPurchaseResponse
        +list_grain_purchases(person_id, db) list[GrainPurchaseResponse]
        +get_grain_purchase(purchase_id, db) GrainPurchaseResponse
    }
    class GrainPurchaseService {
        -db: AsyncSession
        -purchase_repo: GrainPurchaseRepository
        -inventory_repo: GrainInventoryRepository
        -grain_type_repo: GrainTypeRepository
        -person_service: PersonService
        +create_purchase(data) GrainPurchase
        +get_purchase(purchase_id) GrainPurchase
        +list_purchases(person_id) list[GrainPurchase]
    }
    class GrainPurchaseRepository {
        -db: AsyncSession
        +get_by_id(purchase_id) GrainPurchase
        +list_all() list[GrainPurchase]
        +list_by_person(person_id) list[GrainPurchase]
        +create(data, total, date) GrainPurchase
    }
    class GrainInventoryRepository {
        -db: AsyncSession
        +get_by_grain_type(grain_type_id) GrainInventory
        +add_stock(grain_type_id, amount) GrainInventory
    }
    class GrainTypeRepository {
        -db: AsyncSession
        +get_all() list[GrainType]
        +get_by_id(grain_type_id) GrainType
    }
    class PersonService {
        -repo: PersonRepository
        +get_person(person_id) Person
        +create_person(data) Person
        +list_persons() list[Person]
        +list_persons_by_role(role) list[Person]
        +update_person(person_id, data) Person
        +delete_person(person_id) None
    }
    class GrainPurchase {
        +id: int
        +person_id: int
        +grain_type_id: int
        +weight: Decimal
        +price_per_unit: Decimal
        +total: Decimal
        +date: datetime
        +notes: str
    }
    class GrainInventory {
        +id: int
        +grain_type_id: int
        +total_stock: Decimal
    }
    GrainPurchasesEndpoint --> GrainPurchaseService : delegates to
    GrainPurchaseService --> GrainPurchaseRepository : queries via
    GrainPurchaseService --> GrainInventoryRepository : updates inventory via
    GrainPurchaseService --> GrainTypeRepository : validates grain type via
    GrainPurchaseService --> PersonService : validates person via
    GrainPurchaseRepository --> GrainPurchase : persists
    GrainInventoryRepository --> GrainInventory : persists
```
