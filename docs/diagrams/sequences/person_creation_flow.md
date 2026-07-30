## Person Creation Sequence

This diagram traces the full cross-layer flow for `POST /api/v1/persons/`, from the Streamlit UI through FastAPI, `PersonService`, `PersonRepository`, and PostgreSQL. Two failure branches are shown: the first occurs when the submitted `role` is not one of the accepted values (`customer`, `farmer`, `both`), and the second occurs when a person with the same `full_name` and `phone` already exists in the database. Both failures result in a `DuplicateError` that FastAPI translates to a `409 Conflict` response.

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant SVC as PersonService
    participant REPO as PersonRepository
    participant DB as PostgreSQL

    User->>UI: Fills person form and submits
    UI->>API: POST /api/v1/persons/ {full_name, phone, role, notes}
    API->>SVC: create_person(data)

    SVC->>SVC: Check role in VALID_ROLES

    alt role not in {customer, farmer, both}
        SVC-->>API: DuplicateError (invalid role)
        API-->>UI: 409 Conflict
        UI-->>User: "Rol inválido"
    else role is valid
        SVC->>REPO: get_by_name_and_phone(full_name, phone)

        alt phone is None
            REPO-->>SVC: None (bypass — no phone means no duplicate check)
        else phone provided
            REPO->>DB: SELECT FROM persons WHERE full_name = ? AND phone = ?
            DB-->>REPO: row or empty
            REPO-->>SVC: Person or None
        end

        alt existing person found
            SVC-->>API: DuplicateError (duplicate full_name + phone)
            API-->>UI: 409 Conflict
            UI-->>User: "La persona ya existe"
        else no duplicate
            SVC->>REPO: create(data)
            REPO->>DB: INSERT INTO persons ...
            DB-->>REPO: new person row
            REPO-->>SVC: Person object
            SVC-->>API: Person object
            API-->>UI: PersonResponse (201)
            UI-->>User: "Persona creada"
        end
    end
```
