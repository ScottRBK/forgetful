"""Migration runner behaviour against a real SQLite file.

- a `%` in SQLITE_PATH no longer aborts start-up
"""

import sqlite3
from pathlib import Path

import app.services.memory_service  # noqa: F401  (logger created at import time, as in the server)
from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_LOGGER = "app.services.memory_service"


def snapshot(path):
    """Return (user tables, stamped revisions) of a SQLite file."""
    connection = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type='table' "
                "and name not like 'sqlite_%'",
            )
        }
        versions = (
            [row[0] for row in connection.execute("select version_num from alembic_version")]
            if "alembic_version" in tables
            else []
        )
    finally:
        connection.close()
    return tables, versions


async def init_and_dispose(adapter):
    try:
        await adapter.init_db()
    finally:
        await adapter.dispose()


class TestPercentSignInDatabasePath:
    async def test_init_db_accepts_percent_in_sqlite_path(self, tmp_path, monkeypatch):
        path = tmp_path / "50%" / "100%25 done" / "forgetful.db"
        monkeypatch.setattr(settings, "DATABASE", "SQLite")
        monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
        monkeypatch.setattr(settings, "SQLITE_PATH", str(path))

        await init_and_dispose(SqliteDatabaseAdapter())

        assert snapshot(path)[1], "the database should be migrated and stamped"
