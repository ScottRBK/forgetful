"""Keep files that hold user data readable by their owner only.

Memories, documents and user records are stored in plain files (the SQLite database and
backups), so group and other access is removed where the operating system supports it.
Windows has no equivalent mode bits and is left alone.
"""

import contextlib
import os
import stat
import sys
from pathlib import Path

_OWNER_ONLY_FILE = 0o600
_OWNER_ONLY_DIR = 0o700


def make_private_dir(path: Path) -> None:
    """Create a directory (and missing parents) with the leaf readable by its owner only.

    A directory that already exists is never changed: the configured location may be a
    shared one such as a home directory, the working directory or /tmp.
    """
    path.mkdir(mode=_OWNER_ONLY_DIR, parents=True, exist_ok=True)


def restrict_to_owner(path: Path) -> None:
    """Remove group and other access from a file, keeping the owner's access as it is.

    Best effort: a missing file, or one owned by another account, is left unchanged.
    """
    if sys.platform == "win32":
        return
    with contextlib.suppress(OSError):
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            path.chmod(mode & 0o700)


def create_private_file(path: Path) -> None:
    """Create an empty file readable by its owner only, or restrict one that exists."""
    if path.exists():
        restrict_to_owner(path)
        return
    # O_EXCL makes a concurrent creator win cleanly: the file then exists and is restricted.
    try:
        os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _OWNER_ONLY_FILE))
    except FileExistsError:
        restrict_to_owner(path)
