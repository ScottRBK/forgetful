"""Storage operations required by the backup workflow."""

from pathlib import Path
from typing import Protocol


class BackupAdapter(Protocol):
    def create_backup(self, timestamp: str) -> Path: ...
    def restore_backup(self, backup_path: Path) -> None: ...
