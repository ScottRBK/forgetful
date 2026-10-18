"""SQLite storage permissions and consistent backups, against real files.

The database, its WAL and the backups hold every user's data, so they must be readable by
their owner only, and a backup must be one consistent snapshot even while another
connection commits.
"""

import os
import shutil
import sqlite3
import stat
import sys
import threading
from contextlib import closing
from pathlib import Path

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.repositories.backup_adapter import DatabaseBackupAdapter
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")


def mode(path: Path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


def sidecars(db_file: Path) -> list[Path]:
    return [Path(f"{db_file}{suffix}") for suffix in ("-wal", "-shm")]


@pytest.fixture
def umask022():
    """The common default umask, under which SQLite and mkdir create 0644 and 0755."""
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
async def database(tmp_path, monkeypatch, umask022):
    """A migrated file database holding one user, with every session closed."""
    data_dir = tmp_path / "forgetful_data" / "nested"
    db_path = data_dir / "forgetful.db"
    monkeypatch.setattr(settings, "DATABASE", "SQLite")  # a developer's configuration may differ
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(db_path))
    monkeypatch.setattr(settings, "BACKUP_DIR", "")
    adapter = SqliteDatabaseAdapter()
    try:
        await adapter.init_db()
        await add_user(adapter, "Secret Name")
        yield adapter, db_path
    finally:
        await adapter.dispose()


async def add_user(adapter, name):
    async with adapter.system_session() as session:
        await session.execute(
            text(
                "insert into users (id, external_id, name, email, created_at, updated_at) "
                "values (:name, :name, :name, :name, datetime('now'), datetime('now'))",
            ),
            {"name": name},
        )


@pytest.fixture
def committed_only_in_wal(database):
    """Another process still has the database open, so its last commit stays in the WAL."""
    _, db_path = database
    with closing(sqlite3.connect(db_path)) as other_process:
        other_process.execute("pragma wal_autocheckpoint=0")
        other_process.execute(
            "insert into users (id, external_id, name, email, created_at, updated_at) "
            "values ('w', 'ext-w', 'Only In Wal', 'w@example.com', datetime('now'), datetime('now'))",
        )
        other_process.commit()
        yield db_path


def read_names(db_file: Path) -> list[str]:
    with closing(sqlite3.connect(db_file)) as conn:
        return [row[0] for row in conn.execute("select name from users order by name")]


@posix_only
async def test_new_database_directory_and_files_are_owner_only(database, committed_only_in_wal):
    db_path = committed_only_in_wal

    assert mode(db_path.parent) == 0o700
    for path in (db_path, *sidecars(db_path)):
        assert path.exists(), path
        assert mode(path) == 0o600, path


@posix_only
async def test_existing_loose_database_is_tightened_without_touching_its_directory(
    tmp_path, monkeypatch, umask022,
):
    data_dir = tmp_path / "shared"
    data_dir.mkdir()
    data_dir.chmod(0o755)
    db_path = data_dir / "forgetful.db"
    for path in (db_path, *sidecars(db_path)):
        path.write_bytes(b"")
        path.chmod(0o644)
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(db_path))

    adapter = SqliteDatabaseAdapter()
    await adapter.dispose()

    # SQLITE_PATH may live in a shared directory (the working directory, /tmp), which is not ours.
    assert mode(data_dir) == 0o755
    for path in (db_path, *sidecars(db_path)):
        assert mode(path) == 0o600, path


@posix_only
async def test_read_only_database_stays_read_only_for_its_owner(tmp_path, monkeypatch):
    db_path = tmp_path / "forgetful.db"
    db_path.write_bytes(b"")
    db_path.chmod(0o444)
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(db_path))

    adapter = SqliteDatabaseAdapter()
    await adapter.dispose()

    assert mode(db_path) == 0o400


@posix_only
async def test_backup_is_one_owner_only_file(database, committed_only_in_wal):
    db_path = committed_only_in_wal

    backup = DatabaseBackupAdapter("SQLite").create_backup("20260101-000000")

    assert mode(backup) == 0o600
    assert sorted(p.name for p in db_path.parent.iterdir() if "bak" in p.name) == [backup.name]


async def test_backup_holds_committed_wal_data_without_any_sidecar(
    database, committed_only_in_wal, tmp_path,
):
    # One row is committed but still lives in the WAL: the main file does not have it yet.
    assert Path(f"{committed_only_in_wal}-wal").stat().st_size > 0

    backup = DatabaseBackupAdapter("SQLite").create_backup("20260101-000000")

    # Move only the backup file elsewhere, as someone keeping or shipping it would.
    alone = tmp_path / "alone"
    alone.mkdir()
    shutil.copy2(backup, alone / "restored.db")
    with closing(sqlite3.connect(alone / "restored.db")) as conn:
        assert conn.execute("pragma integrity_check").fetchall() == [("ok",)]
    assert read_names(alone / "restored.db") == ["Only In Wal", "Secret Name"]


def test_backup_stays_consistent_while_another_connection_commits(tmp_path, monkeypatch):
    """Copying the .db and then the -wal can pair files from different moments."""
    db_path = tmp_path / "forgetful.db"
    monkeypatch.setattr(settings, "SQLITE_PATH", str(db_path))
    monkeypatch.setattr(settings, "BACKUP_DIR", "")
    rows, payload = 2000, b"x" * 3000

    def insert_pair(conn):
        conn.execute("insert into a(v) values (?)", (payload,))
        conn.execute("insert into b(v) values (?)", (payload,))

    with closing(sqlite3.connect(db_path, isolation_level=None)) as setup:
        setup.execute("pragma journal_mode=wal")
        setup.execute("create table a(id integer primary key, v blob)")
        setup.execute("create table b(id integer primary key, v blob)")
        setup.execute("begin")
        for _ in range(rows):
            insert_pair(setup)
        setup.execute("commit")

    stop = threading.Event()

    def commit_pairs_until_stopped():
        with closing(sqlite3.connect(db_path, isolation_level=None, timeout=30)) as conn:
            conn.execute("pragma journal_mode=wal")
            conn.execute("pragma wal_autocheckpoint=20")  # checkpoint often, as busy writers do
            while not stop.is_set():
                conn.execute("begin immediate")
                insert_pair(conn)
                conn.execute("delete from a where id <= (select max(id) from a) - ?", (rows,))
                conn.execute("delete from b where id <= (select max(id) from b) - ?", (rows,))
                conn.execute("commit")

    writer = threading.Thread(target=commit_pairs_until_stopped)
    writer.start()
    problems = []
    try:
        adapter = DatabaseBackupAdapter("SQLite")
        for attempt in range(30):
            backup = adapter.create_backup(f"20260101-{attempt:06d}")
            # Check the backup together with whatever sidecars came with it, in isolation.
            checked = tmp_path / f"checked-{attempt}"
            checked.mkdir()
            for source in (backup, *sidecars(backup)):
                if source.exists():
                    shutil.copy2(source, checked / source.name.replace(backup.name, "copy.db"))
            try:
                with closing(sqlite3.connect(checked / "copy.db")) as conn:
                    verdict = conn.execute("pragma integrity_check").fetchall()
                    counts = (
                        conn.execute("select count(*) from a").fetchone()[0],
                        conn.execute("select count(*) from b").fetchone()[0],
                    )
                if verdict != [("ok",)] or counts[0] != counts[1]:
                    problems.append((attempt, verdict[0][0], counts))
            except sqlite3.DatabaseError as error:
                problems.append((attempt, str(error)))
            if problems:
                break
    finally:
        stop.set()
        writer.join()

    assert not problems, f"inconsistent backup: {problems}"


async def test_backup_dir_setting_moves_sqlite_backups_and_restore_reads_them(
    database, tmp_path, monkeypatch,
):
    adapter, db_path = database
    target = tmp_path / "persistent" / "backups"
    monkeypatch.setattr(settings, "BACKUP_DIR", str(target))
    backups = DatabaseBackupAdapter("SQLite")

    backup = backups.create_backup("20260101-000000")

    assert backup.parent == target
    await add_user(adapter, "Added Later")
    await adapter.dispose()
    backups.restore_backup(backup)
    assert read_names(db_path) == ["Secret Name"]


@posix_only
async def test_restore_removes_a_stale_wal_and_leaves_owner_only_files(database):
    adapter, db_path = database
    backups = DatabaseBackupAdapter("SQLite")
    backup = backups.create_backup("20260101-000000")
    backup.chmod(0o644)  # a backup written by a release that did not restrict it
    await add_user(adapter, "Added Later")
    await adapter.dispose()
    # What a crashed process leaves behind: replayed onto the restored file it would corrupt it.
    for stale in sidecars(db_path):
        stale.write_bytes(b"stale")

    backups.restore_backup(backup)

    assert read_names(db_path) == ["Secret Name"]
    assert mode(db_path) == 0o600
    assert not [path for path in sidecars(db_path) if path.exists()]
