## Auth Login — Sequence Diagram

This diagram traces the full cross-layer flow for `POST /api/v1/auth/token`, sourced from `backend/app/api/v1/endpoints/auth.py`, `backend/app/services/auth_service.py`, `backend/app/services/user_service.py`, `backend/app/repositories/user_repository.py`, and `backend/app/core/security.py`. This is the only endpoint in the entire API with no auth dependency — it is how a client obtains a token in the first place. The client submits `username`/`password` as an OAuth2 password-grant form (`OAuth2PasswordRequestForm`, not JSON). `AuthService.login()` delegates credential verification to `UserService.authenticate()`, which looks up the user by username, rejects a missing or inactive user, and verifies the bcrypt hash via `verify_password()` — all three failure cases collapse to the same `None` result so the client cannot distinguish "unknown user" from "wrong password" from "inactive account". On success, `create_access_token()` signs a JWT with `{"sub": username, "role": role, "exp": ...}` and the endpoint returns a `Token` schema whose field is named `access_token`, per the OAuth2 standard.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI (auth.py)
    participant ASVC as AuthService
    participant USVC as UserService
    participant REPO as UserRepository
    participant DB as PostgreSQL
    participant SEC as security.py

    Client->>API: POST /api/v1/auth/token (form: username, password)
    API->>ASVC: login(username, password)
    ASVC->>USVC: authenticate(username, password)
    USVC->>REPO: get_by_username(username)
    REPO->>DB: SELECT * FROM users WHERE username = ?
    DB-->>REPO: row or None

    alt User not found
        REPO-->>USVC: None
        USVC-->>ASVC: None
        ASVC-->>API: raise AuthenticationError("Invalid username or password")
        API-->>Client: 401 Unauthorized
    else User found but inactive
        REPO-->>USVC: User(is_active=False)
        USVC-->>ASVC: None
        ASVC-->>API: raise AuthenticationError("Invalid username or password")
        API-->>Client: 401 Unauthorized
    else User found and active
        REPO-->>USVC: User object
        USVC->>SEC: verify_password(password, user.hashed_password)

        alt Password does not match
            SEC-->>USVC: False
            USVC-->>ASVC: None
            ASVC-->>API: raise AuthenticationError("Invalid username or password")
            API-->>Client: 401 Unauthorized
        else Password matches
            SEC-->>USVC: True
            USVC-->>ASVC: User object
            ASVC->>SEC: create_access_token(username=user.username, role=user.role)
            SEC-->>ASVC: signed JWT (sub, role, exp)
            ASVC-->>API: Token(access_token=jwt, token_type="bearer")
            API-->>Client: 200 OK {"access_token": "...", "token_type": "bearer"}
        end
    end
```
