## Grain Purchase Business Rules — Flowchart

This diagram combines the two core business rules enforced by the grain purchases module. Subgraph A covers person role validation as implemented in `GrainPurchaseService.create_purchase()`: the service calls `PersonService.get_person()` which raises `NotFoundError` if the person does not exist, and then the service itself raises `DomainError` if the person's role is `customer`. Subgraph B covers the inventory upsert logic inside `GrainInventoryRepository.add_stock()`: the repository checks whether a `grain_inventory` row already exists for the grain type — if it does, it increments `total_stock` by the purchased weight; if it does not, it inserts a new row with `total_stock` set to that weight.

```mermaid
flowchart TD
    subgraph A [Person Role Validation]
        A1([create_purchase called]) --> A2[Call PersonService.get_person]
        A2 --> A3{Person found?}
        A3 -- No --> A4[Raise NotFoundError\n404 response]
        A3 -- Yes --> A5{role in farmer or both?}
        A5 -- No, role is customer --> A6[Raise DomainError\n422 response]
        A5 -- Yes --> A7([Proceed to grain type check])
    end

    subgraph B [Inventory Upsert]
        B1([add_stock called]) --> B2[Query grain_inventory\nWHERE grain_type_id = ?]
        B2 --> B3{Row exists?}
        B3 -- Yes --> B4[total_stock = total_stock + weight\nUPDATE row]
        B3 -- No --> B5[INSERT new row\ntotal_stock = weight]
        B4 --> B6([Return GrainInventory])
        B5 --> B6
    end
```
