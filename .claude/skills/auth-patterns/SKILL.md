---
name: auth-patterns
description: Use this skill when implementing authentication, JWT handling, password hashing, or RBAC dependencies in this project. Covers the auth module structure, JWT payload, bcrypt hashing, and the three FastAPI dependency functions (get_current_user, require_admin, require_clerk).
---

## Dependencies Required

python-jose[cryptography] → JWT signing and verification
passlib[bcrypt] → password hashing

## JWT Configuration — app/core/config.py additions
```python
SECRET_KEY: str                    # loaded from .env — never hardcoded
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours (full work day)
```

Add to .env:
```
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## Password Hashing — app/core/security.py
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

## JWT Handling — app/core/security.py (continued)
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return {}
```

## FastAPI Dependencies — app/core/dependencies.py
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload  # {"sub": username, "role": role}

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_clerk(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("admin", "clerk"):
        raise HTTPException(status_code=403, detail="Clerk or admin access required")
    return user
```

## Applying to Endpoints
```python
# Admin only
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)  # underscore = not used in body
):
    return await ProductService(db).create_product(payload)

# Admin + clerk
@router.post("/", response_model=SaleResponse, status_code=201)
async def create_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_clerk)
):
    return await SaleService(db).create_sale(payload)

# Public (no dependency)
@router.post("/token")
async def login(...):
    ...
```

## Rules
- Never store plain passwords — always hash with `hash_password()` before saving to DB
- Never put SECRET_KEY in source code — always from .env via settings
- `get_current_user` returns the JWT payload dict, not a DB User object —
  avoid an extra DB query on every request
- Apply `require_admin` or `require_clerk` as `_: dict = Depends(...)` when
  the user payload is not needed in the endpoint body
- The `/auth/token` endpoint is the only public endpoint — all others require auth
- User management endpoints (create user, deactivate) are admin-only
- Never print, log, or expose tokens, passwords, or SECRET_KEY values —
  not in test output, not in error messages, not in API responses