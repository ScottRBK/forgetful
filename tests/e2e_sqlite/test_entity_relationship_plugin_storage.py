"""Entity Relationship Plugin contracts on real file-backed SQLite."""

import pytest

from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from tests.entity_relationship_plugin_cases import (
    TestEntityRelationshipPluginPersistence as TestEntityRelationshipPluginPersistence,
)
from tests.entity_relationship_plugin_cases import (
    relationship_store as relationship_store,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def reference_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "relationship-policy.db"))
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    try:
        yield adapter
    finally:
        await adapter.dispose()
