---
name: write-tests
description: Use this skill when writing pytest tests for this project, whether unit tests for services/repositories or integration tests for API endpoints. Covers test location, naming, async fixtures, and the difference between unit and integration tests here.
---

## Test Types in This Project

- **Unit tests** (`tests/unit/`): test a single async function/method in isolation. No real DB, no HTTP. Mock repositories when testing services.
- **Integration tests** (`tests/integration/`): test the full flow through an async HTTP client against a real test database.

## File Naming
- Mirror the source file: `app/services/product_service.py` → `tests/unit/test_product_service.py`
- Test functions: `test_<method_name>_<scenario>`, e.g. `test_create_product_raises_on_duplicate_name`
- Every async test is marked `@pytest.mark.asyncio`

## Unit Test Template
```python
import pytest
from unittest.mock import AsyncMock
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate

@pytest.mark.asyncio
async def test_create_product_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_name.return_value = None
    service = ProductService(repo=mock_repo)

    payload = ProductCreate(name="Urea 46%", category="fertilizer", unit="lb", price=15.50, stock=100)
    result = await service.create_product(payload)

    mock_repo.create.assert_awaited_once()
    assert result.name == "Urea 46%"
```

## Integration Test Template
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_product_endpoint_returns_201():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/products/", json={
            "name": "Urea 46%",
            "category": "fertilizer",
            "unit": "lb",
            "price": 15.50,
            "stock": 100
        })
    assert response.status_code == 201
    assert response.json()["name"] == "Urea 46%"
```

## Rules
- One assertion focus per test (can be multiple `assert` lines, but one behavior)
- Always test the failure path too (duplicate, not found, invalid input)
- Use `AsyncMock` (not `MagicMock`) for mocking repository/service calls
- Use pytest fixtures from `tests/conftest.py` for shared setup (async test DB session, async test client) — never duplicate setup code across files
- Integration tests must clean up created data (use a transaction rollback fixture, never leave test data in the DB)
- Never hit the real/production database in tests