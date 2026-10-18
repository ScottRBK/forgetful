"""PostgreSQL backups with the real pg_dump and psql: strict restores and private dumps."""

import os
import stat
import sys
from uuid import uuid4

import psycopg2
import pytest
from sqlalchemy import text

from app.bootstrap import create_backup_service
from app.config.settings import settings

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
    pytest.mark.usefixtures("postgres_backup_tools"),
]

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")


@pytest.fixture
def backup_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "backups" / "forgetful.db"))
    return tmp_path / "backups"


async def scalar(db_adapter, sql, params=None):
    async with db_adapter.system_session() as session:
        return (await session.execute(text(sql), params or {})).scalar()


async def test_failed_restore_raises_and_rolls_back_every_statement(
    db_adapter, backup_directory, tmp_path,
):
    dump = tmp_path / "failing-dump.sql"
    dump.write_text(
        "CREATE TABLE fg_restore_probe (id integer);\n"
        "INSERT INTO fg_restore_probe VALUES (1);\n"
        "INSERT INTO fg_table_that_does_not_exist VALUES (1);\n",
    )
    try:
        with pytest.raises(RuntimeError, match="fg_table_that_does_not_exist"):
            await create_backup_service(database_type="Postgres").restore_backup(dump)

        assert await scalar(db_adapter, "SELECT to_regclass('public.fg_restore_probe')") is None
    finally:
        async with db_adapter.system_session() as session:
            await session.execute(text("DROP TABLE IF EXISTS fg_restore_probe"))


async def test_restore_blocked_by_a_dependent_object_is_reported_and_changes_nothing(
    db_adapter, backup_directory,
):
    """The re-embed failure this guards: the database must not be called restored when it is not."""
    service = create_backup_service(database_type="Postgres")
    backup = await service.create_backup()
    marker = str(uuid4())
    async with db_adapter.system_session() as session:
        # Created after the backup: makes DROP TABLE memories fail during the restore.
        await session.execute(text("CREATE VIEW fg_restore_blocker AS SELECT id FROM memories"))
        await session.execute(text(
            "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
            "VALUES (:id, 'fg-restore-marker', 'Marker', 'marker@example.test', now(), now())",
        ), {"id": marker})
    try:
        await db_adapter.dispose()
        with pytest.raises(RuntimeError, match="fg_restore_blocker|depend"):
            await service.restore_backup(backup)

        # Everything after the failure point was rolled back, not half applied.
        assert await scalar(
            db_adapter, "SELECT count(*) FROM users WHERE id = :id", {"id": marker},
        ) == 1
    finally:
        async with db_adapter.system_session() as session:
            await session.execute(text("DROP VIEW IF EXISTS fg_restore_blocker"))
            await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": marker})


@pytest.fixture
def scratch_database(db_adapter):
    """An empty database on the same server, with the extension the dump expects to create."""
    name = "fg_restore_scratch"

    def connect(database):
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST, port=settings.PGPORT, user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD, dbname=database,
        )
        conn.autocommit = True
        return conn

    admin = connect(settings.POSTGRES_DB)
    with admin.cursor() as cursor:
        cursor.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
        cursor.execute(f"CREATE DATABASE {name}")
    try:
        yield name, connect
    finally:
        with admin.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
        admin.close()


async def test_dump_restores_into_an_empty_database_under_a_strict_restore(
    db_adapter, backup_directory, scratch_database, monkeypatch,
):
    """Strict restores still work where objects are missing and the client is newer than the server."""
    name, connect = scratch_database
    backup = await create_backup_service(database_type="Postgres").create_backup()
    monkeypatch.setattr(settings, "POSTGRES_DB", name)

    await create_backup_service(database_type="Postgres").restore_backup(backup)

    restored = connect(name)
    try:
        with restored.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.memories') IS NOT NULL")
            assert cursor.fetchone()[0] is True
    finally:
        restored.close()


@posix_only
async def test_dump_and_new_backup_directory_are_owner_only(db_adapter, backup_directory):
    previous = os.umask(0o022)  # the common default, which used to yield a 0644 dump
    try:
        backup = await create_backup_service(database_type="Postgres").create_backup()
    finally:
        os.umask(previous)

    assert backup.parent == backup_directory
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600
    assert stat.S_IMODE(backup_directory.stat().st_mode) == 0o700
    assert "PostgreSQL database dump" in backup.read_text()
