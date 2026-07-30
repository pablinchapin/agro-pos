## Grain Purchases ERD

This diagram covers the `grain_purchases` and `grain_inventory` tables together with the `persons` and `grain_types` catalog tables they reference. `grain_purchases` records every individual transaction in which the store buys grain from a farmer, storing the weight, price per unit, and the pre-calculated total. `grain_inventory.total_stock` is not entered manually — it is updated automatically on every purchase creation via `GrainInventoryRepository.add_stock()`, which either increments an existing row or inserts a new one.

```mermaid
erDiagram
    PERSONS {
        int id PK
        string full_name
        string phone
        string role
        string notes
        datetime created_at
    }
    GRAIN_TYPES {
        int id PK
        string name
        string unit
        datetime created_at
    }
    GRAIN_PURCHASES {
        int id PK
        int person_id FK
        int grain_type_id FK
        decimal weight
        decimal price_per_unit
        decimal total
        datetime date
        string notes
    }
    GRAIN_INVENTORY {
        int id PK
        int grain_type_id FK
        decimal total_stock
    }
    PERSONS ||--o{ GRAIN_PURCHASES : sells_grains_via
    GRAIN_TYPES ||--o{ GRAIN_PURCHASES : categorises
    GRAIN_TYPES ||--o| GRAIN_INVENTORY : tracked_in
```
