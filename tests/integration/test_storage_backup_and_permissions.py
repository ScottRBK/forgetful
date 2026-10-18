"""Backup tool lookup, restore strictness, dump permissions and backup location.

The PostgreSQL client tools are replaced by tiny POSIX shell scripts that record how
they were started, so these checks need no database and no network.
"""

import os
import stat
import sys
from pathlib import Path

import pytest
import yaml

from app.bootstrap import create_backup_service
from app.config.settings import settings
from app.repositories.backup_adapter import DatabaseBackupAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell scripts and mode bits")


def fake_tool(
    bin_dir: Path, name: str, log: Path, exit_code: int = 0, stderr: str = "",
    dump: Path | None = None,
) -> None:
    """Install an executable that logs its environment and arguments, then exits.

    A fake pg_dump writes the given dump file (a one-line dump by default) to its -f target.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / name
    write_dump = f'cat "{dump}" > "$out"' if dump else 'echo "-- fake dump" > "$out"'
    script.write_text(
        "#!/bin/sh\n"
        "{\n"
        '  printf "PGPASSWORD=%s\\n" "$PGPASSWORD"\n'
        '  for arg in "$@"; do printf "ARG %s\\n" "$arg"; done\n'
        f'}} > "{log}"\n'
        'out=""\n'
        'prev=""\n'
        'for arg in "$@"; do\n'
        '  if [ "$prev" = "-f" ]; then out="$arg"; fi\n'
        '  prev="$arg"\n'
        "done\n"
        f'if [ "{name}" = "pg_dump" ] && [ -n "$out" ]; then {write_dump}; fi\n'
        f'echo "{stderr}" >&2\n'
        f"exit {exit_code}\n",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def logged_args(log: Path) -> list[str]:
    return [line[4:] for line in log.read_text().splitlines() if line.startswith("ARG ")]


@pytest.fixture
def pg_tools(tmp_path, monkeypatch):
    """Put the fake tools on the caller's PATH only, as on a Homebrew or Nix host."""
    bin_dir = tmp_path / "custom-prefix" / "bin"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(os, "defpath", str(tmp_path / "no-such-default-path"))
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "data" / "forgetful.db"))
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", "s3cret-pw")
    return bin_dir


@posix_only
async def test_postgres_backup_finds_pg_dump_on_the_callers_path(pg_tools, tmp_path):
    log = tmp_path / "pg_dump.log"
    fake_tool(pg_tools, "pg_dump", log)

    backup = await create_backup_service(database_type="Postgres").create_backup()

    assert backup.read_text() == "-- fake dump\n"
    assert "PGPASSWORD=s3cret-pw" in log.read_text()
    args = logged_args(log)
    assert "--clean" in args
    # Without IF EXISTS a restore into a database that lacks an object cannot be strict.
    assert "--if-exists" in args


@posix_only
async def test_postgres_restore_finds_psql_on_the_callers_path(pg_tools, tmp_path):
    log = tmp_path / "psql.log"
    fake_tool(pg_tools, "psql", log)
    dump = tmp_path / "dump.sql"
    dump.write_text("-- dump")

    await create_backup_service(database_type="Postgres").restore_backup(dump)

    assert "PGPASSWORD=s3cret-pw" in log.read_text()


@posix_only
async def test_postgres_restore_stops_at_the_first_error_inside_one_transaction(pg_tools, tmp_path):
    log = tmp_path / "psql.log"
    fake_tool(pg_tools, "psql", log)
    dump = tmp_path / "dump.sql"
    dump.write_text("-- dump")

    await create_backup_service(database_type="Postgres").restore_backup(dump)

    args = logged_args(log)
    assert args[args.index("-v") + 1] == "ON_ERROR_STOP=1"
    assert "--single-transaction" in args
    assert args[args.index("-f") + 1] == str(dump)


@posix_only
async def test_postgres_restore_failure_is_reported_with_the_server_message(pg_tools, tmp_path):
    fake_tool(pg_tools, "psql", tmp_path / "psql.log", exit_code=3, stderr="relation does not exist")
    dump = tmp_path / "dump.sql"
    dump.write_text("-- dump")

    with pytest.raises(RuntimeError, match="relation does not exist"):
        await create_backup_service(database_type="Postgres").restore_backup(dump)


@posix_only
async def test_failed_postgres_dump_leaves_no_partial_file(pg_tools, tmp_path):
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log", exit_code=1, stderr="connection refused")

    with pytest.raises(RuntimeError, match="connection refused"):
        await create_backup_service(database_type="Postgres").create_backup()

    assert list((tmp_path / "data").glob("forgetful-pg-*.sql")) == []


@posix_only
async def test_postgres_dump_and_new_backup_directory_are_owner_only(pg_tools, tmp_path):
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log")
    old_umask = os.umask(0o022)  # the common default, which used to yield 0644 dumps
    try:
        backup = await create_backup_service(database_type="Postgres").create_backup()
    finally:
        os.umask(old_umask)

    assert stat.S_IMODE(backup.stat().st_mode) == 0o600
    assert stat.S_IMODE(backup.parent.stat().st_mode) == 0o700


@posix_only
def test_postgres_dump_tightens_a_pre_existing_loose_file(pg_tools, tmp_path):
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log")
    leftover = tmp_path / "data" / "forgetful-pg-20260101-000000.sql"
    leftover.parent.mkdir()
    leftover.write_text("older dump taken within the same second")
    leftover.chmod(0o644)

    backup = DatabaseBackupAdapter("Postgres").create_backup("20260101-000000")

    assert backup == leftover
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600
    assert backup.read_text() == "-- fake dump\n"


DUMP_HEADER = (
    "--\n-- PostgreSQL database dump\n--\n\n"
    "-- Dumped from database version {server}\n"
    "-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg13+2)\n\n"
    "SET statement_timeout = 0;\nSET lock_timeout = 0;\n"
    "SET idle_in_transaction_session_timeout = 0;\nSET transaction_timeout = 0;\n"
    "SET client_encoding = 'UTF8';\n"
)


@posix_only
@pytest.mark.parametrize(
    ("server", "keeps_setting"),
    [("16.15 (Debian 16.15-1.pgdg12+2)", False), ("9.6.24", False), ("17.2", True), ("18.0", True)],
)
async def test_dump_from_a_server_without_transaction_timeout_can_be_restored_strictly(
    pg_tools, tmp_path, server, keeps_setting,
):
    """pg_dump 17+ emits SET transaction_timeout even for older servers, which reject it."""
    source = tmp_path / "pg_dump_output.sql"
    source.write_text(DUMP_HEADER.format(server=server))
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log", dump=source)

    backup = await create_backup_service(database_type="Postgres").create_backup()

    dumped = backup.read_text()
    assert ("\nSET transaction_timeout = 0;" in dumped) is keeps_setting
    assert "SET lock_timeout = 0;" in dumped
    assert len(dumped) == len(source.read_text())


@posix_only
async def test_backup_dir_setting_redirects_the_postgres_dump(pg_tools, tmp_path, monkeypatch):
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log")
    target = tmp_path / "persistent" / "backups"
    monkeypatch.setattr(settings, "BACKUP_DIR", str(target))

    backup = await create_backup_service(database_type="Postgres").create_backup()

    assert backup.parent == target
    assert not (tmp_path / "data").exists()


@posix_only
async def test_backup_dir_defaults_to_the_sqlite_data_directory(pg_tools, tmp_path):
    fake_tool(pg_tools, "pg_dump", tmp_path / "pg_dump.log")

    backup = await create_backup_service(database_type="Postgres").create_backup()

    assert settings.BACKUP_DIR == ""
    assert backup.parent == tmp_path / "data"


@pytest.mark.parametrize("compose_name", ["docker-compose.yml", "docker-compose.postgres.yml"])
def test_postgres_compose_files_persist_the_backup_directory(compose_name):
    compose = yaml.safe_load((REPO_ROOT / "docker" / compose_name).read_text())
    service = compose["services"]["forgetful-service"]

    environment = service["environment"]
    configured = dict(item.split("=", 1) for item in environment) if isinstance(
        environment, list,
    ) else environment
    backup_dir = configured["BACKUP_DIR"]
    mounts = {volume.split(":")[1]: volume.split(":")[0] for volume in service["volumes"]}

    assert backup_dir in mounts
    # A named volume survives `docker compose up --force-recreate` and image upgrades.
    assert mounts[backup_dir] in compose["volumes"]
