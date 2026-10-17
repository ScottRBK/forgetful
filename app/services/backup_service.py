"""Coordinate timestamped backups through the configured database adapter."""

from datetime import datetime
from pathlib import Path

from app.protocols.backup_protocol import BackupAdapter


class BackupService:
    """Create and restore database backups without knowing the storage implementation."""

    def __init__(self, adapter: BackupAdapter):
        self.adapter = adapter

    async def create_backup(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.adapter.create_backup(timestamp)

    async def restore_backup(self, backup_path: Path) -> None:
        self.adapter.restore_backup(backup_path)
