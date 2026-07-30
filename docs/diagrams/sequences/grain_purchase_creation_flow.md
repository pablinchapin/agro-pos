## Grain Purchase Creation — Sequence Diagram

This diagram shows the full cross-layer flow for `POST /api/v1/grain-purchases/`. The happy path runs left-to-right through the Streamlit UI, the FastAPI endpoint, `GrainPurchaseService`, and three repositories before writing to PostgreSQL. Two failure branches short-circuit the flow early: if the person is not found `PersonService.get_person()` raises `NotFoundError` (→ 404), and if the person's role is `customer` the service raises `DomainError` (→ 422). A third failure branch fires if the grain type is not found. On the happy path the service auto-calculates `total = weight × price_per_unit`, persists the purchase record, and then performs an inventory upsert as a distinct final step.

```mermaid
sequenceDiagram
    actor Operator
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as GrainPurchaseService
    participant PSVC as PersonService
    participant GTYPE as GrainTypeRepository
    participant PREPO as GrainPurchaseRepository
    participant IREPO as GrainInventoryRepository
    participant DB as PostgreSQL

    Operator->>UI: Submits grain purchase form
    UI->>API: POST /api/v1/grain-purchases/ {person_id, grain_type_id, weight, price_per_unit, ...}
    API->>SVC: create_purchase(data)

    SVC->>PSVC: get_person(data.person_id)
    PSVC->>DB: SELECT * FROM persons WHERE id = ?
    DB-->>PSVC: row or None

    alt Person not found
        PSVC-->>SVC: raise NotFoundError
        SVC-->>API: NotFoundError
        API-->>UI: 404 Not Found
        UI-->>Operator: "Persona no encontrada"
    else Person found
        PSVC-->>SVC: Person object

        alt person.role == "customer"
            SVC-->>API: raise DomainError
            API-->>UI: 422 Unprocessable Entity
            UI-->>Operator: "Rol inválido para venta de granos"
        else role in farmer or both
            SVC->>GTYPE: get_by_id(data.grain_type_id)
            GTYPE->>DB: SELECT * FROM grain_types WHERE id = ?
            DB-->>GTYPE: row or None

            alt Grain type not found
                GTYPE-->>SVC: None
                SVC-->>API: raise NotFoundError
                API-->>UI: 404 Not Found
                UI-->>Operator: "Tipo de grano no encontrado"
            else Grain type found
                GTYPE-->>SVC: GrainType object
                Note over SVC: total = data.weight × data.price_per_unit
                Note over SVC: purchase_date = data.date or now(UTC)

                SVC->>PREPO: create(data, total, purchase_date)
                PREPO->>DB: INSERT INTO grain_purchases ...
                DB-->>PREPO: purchase record
                PREPO-->>SVC: GrainPurchase object

                SVC->>IREPO: add_stock(data.grain_type_id, data.weight)
                IREPO->>DB: SELECT * FROM grain_inventory WHERE grain_type_id = ?
                DB-->>IREPO: row or None

                alt Inventory row exists
                    IREPO->>DB: UPDATE grain_inventory SET total_stock = total_stock + weight
                else No inventory row yet
                    IREPO->>DB: INSERT INTO grain_inventory (grain_type_id, total_stock)
                end

                DB-->>IREPO: updated/created inventory row
                IREPO-->>SVC: GrainInventory object
                SVC-->>API: GrainPurchase object
                API-->>UI: GrainPurchaseResponse (201)
                UI-->>Operator: "Compra registrada"
            end
        end
    end
```
