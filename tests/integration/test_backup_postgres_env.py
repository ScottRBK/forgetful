"""The Postgres backup path must hand pg_dump/psql a usable environment.

Passing only {"PGPASSWORD": ...} replaces the child environment, so the commands
lose PATH and are never found: execvp falls back to the compiled-in
/bin:/usr/bin, which is empty in a Nix deployment. The failure surfaces as
FileNotFoundError for pg_dump even when pg_dump is on the caller's PATH.
"""
from pathlib import Path

import pytest

from app.config.settings import settings
from app.repositories import backup_adapter
from app.repositories.backup_adapter import DatabaseBackupAdapter


class _Result:
    returncode = 0
    stderr = ""


@pytest.fixture
def captured(monkeypatch, tmp_path):
    """Record the subprocess call instead of running pg_dump or psql."""
    calls: list[dict] = []

    def fake_run(cmd, env=None, capture_output=True, text=True):
        calls.append({"cmd": cmd, "env": env})
        return _Result()

    monkeypatch.setattr(backup_adapter.subprocess, "run", fake_run)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "forgetful.db"))
    monkeypatch.setenv("PATH", "/nix/store/example-bin")
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", "secret-value")
    return calls


def test_postgres_backup_keeps_the_caller_path(captured):
    DatabaseBackupAdapter(database_type="Postgres")._backup_postgres("20260101T000000")

    assert len(captured) == 1
    env = captured[0]["env"]
    assert env["PATH"] == "/nix/store/example-bin", (
        "the child environment must keep PATH or pg_dump cannot be found"
    )
    assert captured[0]["cmd"][0] == "pg_dump"


def test_postgres_restore_keeps_the_caller_path(captured, tmp_path):
    dump = Path(tmp_path) / "dump.sql"
    dump.write_text("SELECT 1;", encoding="utf-8")

    DatabaseBackupAdapter(database_type="Postgres")._restore_postgres(dump)

    env = captured[0]["env"]
    assert env["PATH"] == "/nix/store/example-bin"
    assert captured[0]["cmd"][0] == "psql"


def test_postgres_commands_receive_the_password(captured, tmp_path):
    adapter = DatabaseBackupAdapter(database_type="Postgres")
    adapter._backup_postgres("20260101T000001")
    dump = Path(tmp_path) / "dump.sql"
    dump.write_text("SELECT 1;", encoding="utf-8")
    adapter._restore_postgres(dump)

    assert [call["env"]["PGPASSWORD"] for call in captured] == [
        "secret-value", "secret-value",
    ]
