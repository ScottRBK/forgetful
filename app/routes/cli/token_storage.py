"""Persistent OAuth token cache for the CLI.

fastmcp stores tokens in a FileTreeStore keyed by server URL. The upstream store
defaults to a passthrough key sanitizer, which breaks on Windows because URL-shaped
keys join as nested paths with invalid ``:`` segments. We always wire the v1
sanitization strategies so keys land as flat, filesystem-safe files.
"""
import contextlib
import json
import os
import tempfile
from pathlib import Path

from key_value.aio.stores.filetree.store import (
    FileTreeStore,
    FileTreeV1CollectionSanitizationStrategy,
    FileTreeV1KeySanitizationStrategy,
)

_INFO_SUFFIX = "-info.json"


def _repair_relocated_collection_info(root: Path) -> None:
    """Point every collection's metadata at its directory under the current root.

    FileTreeStore records the absolute directory of each collection in
    ``<collection>-info.json`` and refuses any path that resolves outside the root it
    was given, so a cache that was moved (renamed home, container bind mount, restored
    backup, different XDG_CONFIG_HOME) failed with PathSecurityError on every access -
    including login, which is how the user would normally recover. The metadata only
    ever describes ``<root>/<collection>``, so rewrite a stale pointer in place; the
    cached token files stay where they are. Unreadable metadata is left alone for the
    store to report.
    """
    if not root.is_dir():
        return
    for info_file in root.glob(f"*{_INFO_SUFFIX}"):
        collection_dir = root / info_file.name.removesuffix(_INFO_SUFFIX)
        with contextlib.suppress(OSError, ValueError):
            info = json.loads(info_file.read_text(encoding="utf-8"))
            if not isinstance(info, dict) or Path(str(info.get("directory"))) == collection_dir:
                continue
            info["directory"] = str(collection_dir)
            _write_atomic(info_file, json.dumps(info))


def _write_atomic(target: Path, text: str) -> None:
    """Write-then-rename so a crash never leaves half a metadata file behind."""
    fd, temp_name = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_name, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)
        raise


def oauth_token_file_tree_store(token_dir: Path) -> FileTreeStore:
    """Build a FileTreeStore suitable for fastmcp OAuth token persistence."""
    resolved = token_dir.resolve()
    _repair_relocated_collection_info(resolved)
    return FileTreeStore(
        data_directory=resolved,
        key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(directory=resolved),
        collection_sanitization_strategy=FileTreeV1CollectionSanitizationStrategy(
            directory=resolved,
        ),
    )
