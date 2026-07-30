## Grain Inventory Listing — Sequence Diagram

This diagram traces `GET /api/v1/inventory/grains`, sourced from `backend/app/api/v1/endpoints/inventory.py` and `backend/app/services/inventory_service.py`. `InventoryService.list_grain_inventory()` reads the full grain type catalog via `GrainTypeRepository.get_all()` and all existing stock rows via the newly added `GrainInventoryRepository.list_all()`, builds an in-memory `{grain_type_id: total_stock}` lookup from the latter, then iterates every `GrainType` and defaults to `Decimal("0")` when no matching `grain_inventory` row exists — guaranteeing every catalog grain type appears in the response even if it has never been purchased. This flow performs no writes: `add_stock()` is never called here.

```mermaid
sequenceDiagram
    actor Owner
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as InventoryService
    participant GTREPO as GrainTypeRepository
    participant GIREPO as GrainInventoryRepository
    participant DB as PostgreSQL

    Owner->>UI: Opens grain inventory dashboard
    UI->>API: GET /api/v1/inventory/grains
    API->>SVC: list_grain_inventory()

    SVC->>GTREPO: get_all()
    GTREPO->>DB: SELECT * FROM grain_types ORDER BY name
    DB-->>GTREPO: grain type rows
    GTREPO-->>SVC: list[GrainType]

    SVC->>GIREPO: list_all()
    GIREPO->>DB: SELECT * FROM grain_inventory
    DB-->>GIREPO: grain_inventory rows
    GIREPO-->>SVC: list[GrainInventory]

    Note over SVC: stock_by_grain_type = {inv.grain_type_id: inv.total_stock<br/>for inv in inventories}

    loop For each grain_type in grain_types
        alt grain_type.id in stock_by_grain_type
            Note over SVC: total_stock = stock_by_grain_type[grain_type.id]
        else No grain_inventory row for this grain type
            Note over SVC: total_stock = Decimal("0")
        end
        SVC->>SVC: build GrainInventoryResponse(grain_type_id, grain_type_name,<br/>unit, total_stock)
    end

    SVC-->>API: list[GrainInventoryResponse]
    API-->>UI: 200 OK [GrainInventoryResponse...]
    UI-->>Owner: Renders grain stock table
```
