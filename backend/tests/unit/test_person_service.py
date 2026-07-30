"""Unit tests for PersonService.

All repository calls are mocked so no database is required.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate
from app.services.person_service import PersonService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_person(**kwargs) -> Person:
    """Return a Person ORM instance with sensible defaults."""
    defaults = dict(
        id=1,
        full_name="Juan Perez",
        phone="555-1234",
        role="customer",
        notes=None,
    )
    defaults.update(kwargs)
    person = Person()
    for key, value in defaults.items():
        setattr(person, key, value)
    return person


def make_service(mock_repo: MagicMock) -> PersonService:
    """Return a PersonService with its repository replaced by a mock."""
    db = AsyncMock()
    service = PersonService(db)
    service.repo = mock_repo
    return service


# ---------------------------------------------------------------------------
# create_person
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_person_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_name_and_phone.return_value = None
    expected = make_person()
    mock_repo.create.return_value = expected

    service = make_service(mock_repo)
    payload = PersonCreate(full_name="Juan Perez", phone="555-1234", role="customer")
    result = await service.create_person(payload)

    mock_repo.get_by_name_and_phone.assert_awaited_once_with("Juan Perez", "555-1234")
    mock_repo.create.assert_awaited_once_with(payload)
    assert result is expected


@pytest.mark.asyncio
async def test_create_person_invalid_role_raises():
    mock_repo = AsyncMock()
    service = make_service(mock_repo)

    payload = PersonCreate(full_name="Juan Perez", phone="555-1234", role="manager")

    with pytest.raises(DuplicateError, match="role"):
        await service.create_person(payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_person_duplicate_name_and_phone_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_name_and_phone.return_value = make_person()

    service = make_service(mock_repo)
    payload = PersonCreate(full_name="Juan Perez", phone="555-1234", role="farmer")

    with pytest.raises(DuplicateError, match="already exists"):
        await service.create_person(payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_person_no_phone_skips_duplicate_check():
    """Two persons with the same name and no phone are NOT duplicates."""
    mock_repo = AsyncMock()
    # Repository returns None when phone is None (by design)
    mock_repo.get_by_name_and_phone.return_value = None
    expected = make_person(phone=None)
    mock_repo.create.return_value = expected

    service = make_service(mock_repo)
    payload = PersonCreate(full_name="Juan Perez", phone=None, role="customer")
    result = await service.create_person(payload)

    mock_repo.get_by_name_and_phone.assert_awaited_once_with("Juan Perez", None)
    mock_repo.create.assert_awaited_once_with(payload)
    assert result is expected


@pytest.mark.asyncio
async def test_create_person_valid_roles():
    """All three valid roles (customer, farmer, both) should succeed."""
    for role in ("customer", "farmer", "both"):
        mock_repo = AsyncMock()
        mock_repo.get_by_name_and_phone.return_value = None
        expected = make_person(role=role)
        mock_repo.create.return_value = expected

        service = make_service(mock_repo)
        payload = PersonCreate(full_name="Test Person", phone="555-0000", role=role)
        result = await service.create_person(payload)

        assert result is expected


# ---------------------------------------------------------------------------
# get_person
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_person_returns_person():
    mock_repo = AsyncMock()
    expected = make_person(id=5)
    mock_repo.get_by_id.return_value = expected

    service = make_service(mock_repo)
    result = await service.get_person(5)

    mock_repo.get_by_id.assert_awaited_once_with(5)
    assert result is expected


@pytest.mark.asyncio
async def test_get_person_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError, match="99"):
        await service.get_person(99)


# ---------------------------------------------------------------------------
# list_persons
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_persons_returns_all():
    mock_repo = AsyncMock()
    persons = [make_person(id=1), make_person(id=2, full_name="Maria Lopez")]
    mock_repo.list_all.return_value = persons

    service = make_service(mock_repo)
    result = await service.list_persons()

    mock_repo.list_all.assert_awaited_once()
    assert result == persons


@pytest.mark.asyncio
async def test_list_persons_empty():
    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = []

    service = make_service(mock_repo)
    result = await service.list_persons()

    assert result == []


# ---------------------------------------------------------------------------
# list_persons_by_role
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_persons_by_role_farmer_includes_both():
    """Querying for farmer must include persons with role 'both'."""
    mock_repo = AsyncMock()
    persons = [make_person(role="farmer"), make_person(id=2, role="both")]
    mock_repo.list_by_roles.return_value = persons

    service = make_service(mock_repo)
    result = await service.list_persons_by_role("farmer")

    mock_repo.list_by_roles.assert_awaited_once_with(["farmer", "both"])
    assert result == persons


@pytest.mark.asyncio
async def test_list_persons_by_role_customer_includes_both():
    """Querying for customer must include persons with role 'both'."""
    mock_repo = AsyncMock()
    persons = [make_person(role="customer"), make_person(id=2, role="both")]
    mock_repo.list_by_roles.return_value = persons

    service = make_service(mock_repo)
    result = await service.list_persons_by_role("customer")

    mock_repo.list_by_roles.assert_awaited_once_with(["customer", "both"])
    assert result == persons


@pytest.mark.asyncio
async def test_list_persons_by_role_both_exact_match_only():
    """Querying for 'both' returns only persons with role exactly 'both'."""
    mock_repo = AsyncMock()
    persons = [make_person(role="both")]
    mock_repo.list_by_roles.return_value = persons

    service = make_service(mock_repo)
    result = await service.list_persons_by_role("both")

    mock_repo.list_by_roles.assert_awaited_once_with(["both"])
    assert result == persons


# ---------------------------------------------------------------------------
# update_person
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_person_success():
    mock_repo = AsyncMock()
    existing = make_person(id=1)
    updated = make_person(id=1, notes="Updated note")
    mock_repo.get_by_id.return_value = existing
    mock_repo.update.return_value = updated

    service = make_service(mock_repo)
    payload = PersonUpdate(notes="Updated note")
    result = await service.update_person(1, payload)

    mock_repo.update.assert_awaited_once_with(1, payload)
    assert result is updated


@pytest.mark.asyncio
async def test_update_person_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.update_person(999, PersonUpdate(notes="x"))


@pytest.mark.asyncio
async def test_update_person_invalid_role_raises():
    mock_repo = AsyncMock()
    existing = make_person(id=1)
    mock_repo.get_by_id.return_value = existing

    service = make_service(mock_repo)
    payload = PersonUpdate(role="admin")  # invalid

    with pytest.raises(DuplicateError, match="role"):
        await service.update_person(1, payload)

    mock_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_person_duplicate_name_phone_raises():
    """Cannot update to a name+phone combination that belongs to another person."""
    mock_repo = AsyncMock()
    current = make_person(id=1, full_name="Old Name", phone="111-1111")
    other = make_person(id=2, full_name="Juan Perez", phone="555-1234")
    mock_repo.get_by_id.return_value = current
    mock_repo.get_by_name_and_phone.return_value = other  # collision with another person

    service = make_service(mock_repo)
    payload = PersonUpdate(full_name="Juan Perez", phone="555-1234")

    with pytest.raises(DuplicateError, match="already exists"):
        await service.update_person(1, payload)

    mock_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_person_same_name_phone_allowed():
    """Person can be updated with its own existing name+phone (no collision)."""
    mock_repo = AsyncMock()
    person = make_person(id=1, full_name="Juan Perez", phone="555-1234")
    mock_repo.get_by_id.return_value = person
    mock_repo.get_by_name_and_phone.return_value = person  # same id — allowed
    mock_repo.update.return_value = person

    service = make_service(mock_repo)
    payload = PersonUpdate(full_name="Juan Perez", phone="555-1234", notes="hi")
    result = await service.update_person(1, payload)

    mock_repo.update.assert_awaited_once_with(1, payload)
    assert result is person


@pytest.mark.asyncio
async def test_update_person_role_change_allowed_without_transactions():
    """Role change should succeed when no transactions exist (stub state)."""
    mock_repo = AsyncMock()
    existing = make_person(id=1, role="customer")
    updated = make_person(id=1, role="farmer")
    mock_repo.get_by_id.return_value = existing
    mock_repo.update.return_value = updated

    service = make_service(mock_repo)
    payload = PersonUpdate(role="farmer")
    result = await service.update_person(1, payload)

    mock_repo.update.assert_awaited_once_with(1, payload)
    assert result.role == "farmer"


# ---------------------------------------------------------------------------
# delete_person
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_person_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_person(id=1)

    service = make_service(mock_repo)
    await service.delete_person(1)

    mock_repo.delete.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_delete_person_not_found_raises():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    service = make_service(mock_repo)

    with pytest.raises(NotFoundError):
        await service.delete_person(999)
