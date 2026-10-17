"""User creation and duplicate recovery against real SQLite."""

import pytest

from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from tests.user_creation_cases import UserCreationCases


@pytest.fixture
async def user_repository(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    adapter = SqliteDatabaseAdapter()
    try:
        await adapter.init_db()
        yield SqliteUserRepository(adapter)
    finally:
        await adapter.dispose()


class TestSqliteUserCreation(UserCreationCases):
    pass
