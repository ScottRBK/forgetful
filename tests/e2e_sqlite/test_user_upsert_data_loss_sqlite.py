"""User upsert on login against the real SQLite stack (no stubs).

Regression coverage for notes/idp_metadata being wiped when the IdP name or
email changes.
"""

import pytest

from app.config.settings import settings
from app.models.user_models import UserCreate, UserUpdate
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.user_service import UserService


@pytest.fixture
async def user_service(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    adapter = SqliteDatabaseAdapter()
    try:
        await adapter.init_db()
        yield UserService(SqliteUserRepository(adapter))
    finally:
        await adapter.dispose()


async def test_name_change_on_login_keeps_notes(user_service):
    await user_service.get_or_create_user(
        UserCreate(external_id="sub1", name="Old Name", email="a@example.com"),
    )
    await user_service.update_user(UserUpdate(external_id="sub1", notes="I prefer tabs"))

    # The auth middleware builds UserCreate(external_id, name, email) on every request.
    after = await user_service.get_or_create_user(
        UserCreate(external_id="sub1", name="New Name", email="a@example.com"),
    )

    assert after.name == "New Name"
    assert after.notes == "I prefer tabs"
    persisted = await user_service.user_repo.get_user_by_external_id("sub1")
    assert persisted.name == "New Name"
    assert persisted.notes == "I prefer tabs"


async def test_email_change_on_login_keeps_idp_metadata(user_service):
    await user_service.get_or_create_user(
        UserCreate(
            external_id="sub2",
            name="Name",
            email="a@example.com",
            idp_metadata={"groups": ["admin"]},
        ),
    )

    after = await user_service.get_or_create_user(
        UserCreate(external_id="sub2", name="Name", email="b@example.com"),
    )

    assert after.email == "b@example.com"
    assert after.idp_metadata == {"groups": ["admin"]}
    persisted = await user_service.user_repo.get_user_by_external_id("sub2")
    assert persisted.idp_metadata == {"groups": ["admin"]}
