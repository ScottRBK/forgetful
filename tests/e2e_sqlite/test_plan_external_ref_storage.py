"""Plan migrations and concurrent writes using file-backed SQLite."""

import pytest

from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from tests.plan_external_ref_cases import (
    TestPlanExternalRefStorage as TestPlanExternalRefStorage,
)
from tests.plan_external_ref_cases import reference_store as reference_store


@pytest.fixture
async def reference_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "plan-references.db"))
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    try:
        yield adapter
    finally:
        await adapter.dispose()
