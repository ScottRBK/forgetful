"""Integration tests for BackupService.

Tests SQLite backup/restore with temporary files.
"""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from app.bootstrap import create_backup_service


def write_content(db_path, content):
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("create table if not exists notes (body text)")
        conn.execute("delete from notes")
        conn.execute("insert into notes values (?)", (content,))
        conn.commit()


def read_content(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute("select body from notes").fetchone()[0]


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database file for testing"""
    db_path = tmp_path / "forgetful.db"
    write_content(db_path, "original database content")
    return db_path


@pytest.mark.asyncio
async def test_sqlite_backup_creates_copy(temp_db):
    """Verify backup file is created at expected path"""
    with patch("app.repositories.backup_adapter.settings") as mock_settings:
        mock_settings.DATABASE = "SQLite"
        mock_settings.SQLITE_PATH = str(temp_db)
        mock_settings.SQLITE_MEMORY = False
        mock_settings.BACKUP_DIR = ""

        service = create_backup_service(database_type="SQLite")
        backup_path = await service.create_backup()

        assert backup_path.exists()
        assert read_content(backup_path) == "original database content"
        assert backup_path.parent == temp_db.parent


@pytest.mark.asyncio
async def test_sqlite_restore_overwrites_current(temp_db):
    """Verify restore replaces current DB"""
    with patch("app.repositories.backup_adapter.settings") as mock_settings:
        mock_settings.DATABASE = "SQLite"
        mock_settings.SQLITE_PATH = str(temp_db)
        mock_settings.SQLITE_MEMORY = False
        mock_settings.BACKUP_DIR = ""

        service = create_backup_service(database_type="SQLite")

        # Create backup
        backup_path = await service.create_backup()

        # Modify the original
        write_content(temp_db, "modified database content")
        assert read_content(temp_db) == "modified database content"

        # Restore
        await service.restore_backup(backup_path)

        # Should be back to original
        assert read_content(temp_db) == "original database content"


@pytest.mark.asyncio
async def test_backup_path_contains_timestamp(temp_db):
    """Naming convention check"""
    with patch("app.repositories.backup_adapter.settings") as mock_settings:
        mock_settings.DATABASE = "SQLite"
        mock_settings.SQLITE_PATH = str(temp_db)
        mock_settings.SQLITE_MEMORY = False
        mock_settings.BACKUP_DIR = ""

        service = create_backup_service(database_type="SQLite")
        backup_path = await service.create_backup()

        # Should contain .bak- and a timestamp-like pattern
        assert ".bak-" in backup_path.name
        # Name format: forgetful.db.bak-YYYYMMDD-HHMMSS
        parts = backup_path.name.split(".bak-")
        assert len(parts) == 2
        timestamp_part = parts[1]
        # Should be parseable as YYYYMMDD-HHMMSS
        datetime.strptime(timestamp_part, "%Y%m%d-%H%M%S")


@pytest.mark.asyncio
async def test_sqlite_backup_includes_wal_data_without_extra_files(temp_db):
    """A snapshot is one file that already holds what is still in the WAL"""
    with closing(sqlite3.connect(temp_db)) as other_connection:
        other_connection.execute("pragma journal_mode=wal")
        other_connection.execute("pragma wal_autocheckpoint=0")
        other_connection.execute("update notes set body = 'committed in the wal'")
        other_connection.commit()
        assert Path(str(temp_db) + "-wal").stat().st_size > 0

        with patch("app.repositories.backup_adapter.settings") as mock_settings:
            mock_settings.DATABASE = "SQLite"
            mock_settings.SQLITE_PATH = str(temp_db)
            mock_settings.SQLITE_MEMORY = False
            mock_settings.BACKUP_DIR = ""

            service = create_backup_service(database_type="SQLite")
            backup_path = await service.create_backup()

    assert read_content(backup_path) == "committed in the wal"
    assert not Path(str(backup_path) + "-wal").exists()
    assert not Path(str(backup_path) + "-shm").exists()


@pytest.mark.asyncio
async def test_restore_nonexistent_backup_raises():
    """Restoring a nonexistent backup should raise FileNotFoundError"""
    service = create_backup_service(database_type="SQLite")

    with pytest.raises(FileNotFoundError):
        await service.restore_backup(Path("/nonexistent/backup.db"))


@pytest.mark.asyncio
async def test_backup_missing_db_raises(tmp_path):
    """Backing up a nonexistent database should raise FileNotFoundError"""
    with patch("app.repositories.backup_adapter.settings") as mock_settings:
        mock_settings.DATABASE = "SQLite"
        mock_settings.SQLITE_PATH = str(tmp_path / "nonexistent.db")
        mock_settings.SQLITE_MEMORY = False
        mock_settings.BACKUP_DIR = ""

        service = create_backup_service(database_type="SQLite")

        with pytest.raises(FileNotFoundError):
            await service.create_backup()
