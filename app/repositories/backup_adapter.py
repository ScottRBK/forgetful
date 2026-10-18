"""Database adapter for file-copy and PostgreSQL backup operations.

Supports both SQLite (file copy) and PostgreSQL (pg_dump/psql) backup strategies.
"""
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _postgres_env() -> dict[str, str]:
    """Environment for pg_dump/psql: the caller's own, plus the password.

    Replacing it would hide the caller's PATH (so tools outside /bin:/usr/bin are not
    found) and HOME, PGSSLMODE, PGSERVICE and similar libpq settings.
    """
    return {**os.environ, "PGPASSWORD": settings.POSTGRES_PASSWORD}


# pg_dump 17 and later write `SET transaction_timeout = 0;` whatever server they dump, and
# servers before 17 reject it, so a strict psql restore would fail on its first statements.
_DUMP_HEADER_BYTES = 8192
_DUMPED_FROM = re.compile(rb"^-- Dumped from database version (\d+)", re.MULTILINE)
_TRANSACTION_TIMEOUT_SET = b"\nSET transaction_timeout = 0;"
_TRANSACTION_TIMEOUT_COMMENT = b"\n--  transaction_timeout = 0;"  # same length as the SET


def _comment_out_unsupported_settings(dump_path: Path) -> None:
    """Comment out `SET transaction_timeout` in a dump taken from a server older than 17.

    The statement only disables a timeout that such a server does not have. The
    replacement keeps the byte length, so the dump is patched in place.
    """
    with dump_path.open("r+b") as dump:
        header = dump.read(_DUMP_HEADER_BYTES)
        dumped_from = _DUMPED_FROM.search(header)
        if dumped_from is None or int(dumped_from.group(1)) >= 17:
            return
        patched = header.replace(_TRANSACTION_TIMEOUT_SET, _TRANSACTION_TIMEOUT_COMMENT)
        if patched != header:
            dump.seek(0)
            dump.write(patched)


class DatabaseBackupAdapter:
    """Handles database backup and restore for both SQLite and PostgreSQL"""

    def __init__(self, database_type: str | None = None):
        self.database_type = database_type or settings.DATABASE

    def create_backup(self, timestamp: str) -> Path:
        """Create a timestamped backup. Returns the backup path."""
        if self.database_type == "SQLite":
            return self._backup_sqlite(timestamp)
        if self.database_type == "Postgres":
            return self._backup_postgres(timestamp)
        raise ValueError(f"Unsupported database type: {self.database_type}")

    def restore_backup(self, backup_path: Path) -> None:
        """Restore database from backup."""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        if self.database_type == "SQLite":
            self._restore_sqlite(backup_path)
        elif self.database_type == "Postgres":
            self._restore_postgres(backup_path)
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    def _backup_sqlite(self, timestamp: str) -> Path:
        """Backup SQLite database by copying the .db file and WAL/SHM if present"""
        db_path = Path(settings.SQLITE_PATH)
        if not db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")

        backup_path = db_path.parent / f"{db_path.name}.bak-{timestamp}"
        shutil.copy2(str(db_path), str(backup_path))

        # Also copy WAL and SHM files if they exist
        for suffix in ["-wal", "-shm"]:
            wal_path = Path(str(db_path) + suffix)
            if wal_path.exists():
                shutil.copy2(str(wal_path), str(backup_path) + suffix)

        logger.info("SQLite backup created", extra={"backup_path": str(backup_path)})
        return backup_path

    def _restore_sqlite(self, backup_path: Path) -> None:
        """Restore SQLite database from backup file"""
        db_path = Path(settings.SQLITE_PATH)

        shutil.copy2(str(backup_path), str(db_path))

        # Restore WAL and SHM if they exist in backup, otherwise remove stale ones
        for suffix in ["-wal", "-shm"]:
            backup_extra = Path(str(backup_path) + suffix)
            db_extra = Path(str(db_path) + suffix)
            if backup_extra.exists():
                shutil.copy2(str(backup_extra), str(db_extra))
            elif db_extra.exists():
                db_extra.unlink()

        logger.info("SQLite database restored", extra={"backup_path": str(backup_path)})

    def _backup_postgres(self, timestamp: str) -> Path:
        """Backup PostgreSQL database using pg_dump"""
        backup_dir = Path(settings.SQLITE_PATH).parent  # reuse data dir
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"forgetful-pg-{timestamp}.sql"

        cmd = [
            "pg_dump",
            "--clean",
            "--if-exists",
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.PGPORT),
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
            "-f", str(backup_path),
        ]

        result = subprocess.run(cmd, env=_postgres_env(), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")

        _comment_out_unsupported_settings(backup_path)

        logger.info("PostgreSQL backup created", extra={"backup_path": str(backup_path)})
        return backup_path

    def _restore_postgres(self, backup_path: Path) -> None:
        """Restore PostgreSQL database from pg_dump file"""
        # psql exits 0 when statements inside a script fail unless ON_ERROR_STOP is set,
        # which would report a half-restored database as restored. The single transaction
        # makes a failed restore roll back and leave the database as it was.
        cmd = [
            "psql",
            "-X",
            "-v", "ON_ERROR_STOP=1",
            "--single-transaction",
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.PGPORT),
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
            "-f", str(backup_path),
        ]

        result = subprocess.run(cmd, env=_postgres_env(), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"psql restore failed: {result.stderr}")

        logger.info("PostgreSQL database restored", extra={"backup_path": str(backup_path)})
