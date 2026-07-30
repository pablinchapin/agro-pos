from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    DomainError,
    DuplicateError,
    InsufficientStockError,
    NotFoundError,
)
from app.api.v1.endpoints import (
    auth,
    inventory,
    persons,
    products,
    grain_purchases,
    reports,
    sales,
    users,
)

app = FastAPI(title="Agro POS API", version="1.0.0")


# ---------------------------------------------------------------------------
# Global exception handlers — domain errors mapped to HTTP status codes once.
# Endpoints never catch these manually.
# DomainError handler comes first so it serves as the catch-all for any
# future subclasses that don't have their own handler. FastAPI registers
# handlers in declaration order and matches the most specific (last-registered)
# for known subclasses when multiple handlers share the same exception type.
# ---------------------------------------------------------------------------

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InsufficientStockError)
async def stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(
    grain_purchases.router,
    prefix="/api/v1/grain-purchases",
    tags=["grain-purchases"],
)
app.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
