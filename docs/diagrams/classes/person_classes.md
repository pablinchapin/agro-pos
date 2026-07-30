## Person Classes

This diagram shows the four classes that make up the persons module and how they relate to each other. `PersonsEndpoint` contains the five FastAPI route handler functions and delegates every operation to `PersonService`. `PersonService` holds all business logic — role validation and duplicate-name-plus-phone checks — and queries the database exclusively through `PersonRepository`. `PersonRepository` owns every SQL statement and maps rows to the `Person` SQLAlchemy model. Method signatures are taken verbatim from the source files.

```mermaid
classDiagram
    class Person {
        +int id
        +str full_name
        +str phone
        +str role
        +str notes
        +datetime created_at
    }
    class PersonRepository {
        -db: AsyncSession
        +get_by_id(person_id) Optional~Person~
        +get_by_name_and_phone(full_name, phone) Optional~Person~
        +list_all() List~Person~
        +list_by_roles(roles) List~Person~
        +create(data) Person
        +update(person_id, data) Optional~Person~
        +delete(person_id) None
    }
    class PersonService {
        -repo: PersonRepository
        +create_person(data) Person
        +get_person(person_id) Person
        +list_persons() List~Person~
        +list_persons_by_role(role) List~Person~
        +update_person(person_id, data) Person
        +delete_person(person_id) None
    }
    class PersonsEndpoint {
        +create_person(payload, db) PersonResponse
        +list_persons(role, db) List~PersonResponse~
        +get_person(person_id, db) PersonResponse
        +update_person(person_id, payload, db) PersonResponse
        +delete_person(person_id, db) None
    }
    PersonsEndpoint --> PersonService : delegates to
    PersonService --> PersonRepository : queries via
    PersonRepository --> Person : maps to
```
