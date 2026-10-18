"""Migration runner behaviour against a real SQLite file.

- application logging survives the migration step
- a `%` in SQLITE_PATH no longer aborts start-up
- the working directory is never put on sys.path
"""

import io
import logging
import logging.handlers
import os
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import app.services.memory_service  # noqa: F401  (logger created at import time, as in the server)
from app.config import logging_config
from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_LOGGER = "app.services.memory_service"


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    """Point the SQLite adapter at a fresh file."""
    path = tmp_path / "forgetful.db"
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(path))
    return path


@pytest.fixture
def isolated_logging():
    """Snapshot and restore global logging state so the test cannot pollute others."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_disabled = {
        name: logger.disabled
        for name, logger in logging.Logger.manager.loggerDict.items()
        if isinstance(logger, logging.Logger)
    }
    saved_stderr = sys.stderr
    try:
        yield
    finally:
        listener = logging_config._queue_listener
        if listener is not None and getattr(listener, "_thread", None) is not None:
            listener.stop()
        logging_config._queue_listener = None
        sys.stderr = saved_stderr
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)
        for name, logger in logging.Logger.manager.loggerDict.items():
            if isinstance(logger, logging.Logger):
                logger.disabled = saved_disabled.get(name, False)


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


class TestApplicationLoggingSurvivesMigrations:
    async def test_init_db_does_not_clobber_application_logging(self, file_db, isolated_logging):
        stream = io.StringIO()
        sys.stderr = stream  # the console handler binds sys.stderr when configured
        listener = logging_config.configure_logging("INFO", "console")

        app_logger = logging.getLogger(APP_LOGGER)
        app_logger.info("BEFORE init_db marker")

        await init_and_dispose(SqliteDatabaseAdapter())

        root = logging.getLogger()
        state = {
            "app_logger.disabled": app_logger.disabled,
            "root.level": root.level,
            "root_has_queue_handler": any(
                isinstance(handler, logging.handlers.QueueHandler) for handler in root.handlers
            ),
        }
        app_logger.info("AFTER init_db info marker")
        app_logger.error("AFTER init_db error marker")
        listener.stop()  # flush the queue
        output = stream.getvalue()

        assert state["app_logger.disabled"] is False, state
        assert state["root.level"] == logging.INFO, state
        assert state["root_has_queue_handler"], state
        assert "BEFORE init_db marker" in output, f"logging is not working at all: {output!r}"
        assert "AFTER init_db info marker" in output, state
        assert "AFTER init_db error marker" in output, state

    def test_command_line_run_keeps_existing_loggers_enabled(self, file_db, isolated_logging):
        """`alembic upgrade head` applies alembic.ini logging but must not mute app loggers."""
        from alembic.config import Config

        from alembic import command

        app_logger = logging.getLogger(APP_LOGGER)
        assert app_logger.disabled is False

        # No injected connection: env.py builds its own engine, as the CLI does.
        command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")

        assert app_logger.disabled is False
        assert snapshot(file_db)[1], "the command line run should have stamped the database"


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
