"""Migration runner behaviour against a real SQLite file.

- a `%` in SQLITE_PATH no longer aborts start-up
- the working directory is never put on sys.path
"""

import os
import sqlite3
import subprocess
import sys
import textwrap
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


class TestStartupNeverImportsFromWorkingDirectory:
    def test_hostile_working_directory_is_not_imported(self, tmp_path):
        """A `pgvector/` package in the cwd must not be picked up while migrating."""
        hostile = tmp_path / "hostile_project"
        (hostile / "pgvector").mkdir(parents=True)
        marker = hostile / "PWNED"
        (hostile / "pgvector" / "__init__.py").write_text(
            f"open({str(marker)!r}, 'w').write('x')\nraise ImportError('hijacked')\n",
        )
        runner_dir = tmp_path / "runner"
        runner_dir.mkdir()
        runner = runner_dir / "run_init_db.py"
        runner.write_text(textwrap.dedent(f"""
            import asyncio
            import sys

            # Mirror `python main.py`: the script directory, not the cwd, leads sys.path.
            sys.path.insert(0, {str(PROJECT_ROOT)!r})
            from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter


            async def main():
                adapter = SqliteDatabaseAdapter()
                try:
                    await adapter.init_db()
                finally:
                    await adapter.dispose()


            asyncio.run(main())
            print("INIT_DB_OK")
        """))
        env = {
            key: value for key, value in os.environ.items()
            if key not in ("PYTHONPATH", "PYTHONSAFEPATH")
        }
        env.update(
            DATABASE="SQLite",
            SQLITE_PATH=str(tmp_path / "forgetful.db"),
            SQLITE_MEMORY="false",
        )

        proc = subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
            [sys.executable, str(runner)],
            cwd=hostile, env=env, capture_output=True, text=True, timeout=120,
        )

        output = proc.stdout + proc.stderr
        assert not marker.exists(), f"code from the working directory ran:\n{output[-1500:]}"
        assert "INIT_DB_OK" in proc.stdout, output[-1500:]
