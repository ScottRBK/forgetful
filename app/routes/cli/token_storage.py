"""Persistent OAuth token cache for the CLI.

fastmcp stores tokens in a FileTreeStore keyed by server URL. The upstream store
defaults to a passthrough key sanitizer, which breaks on Windows because URL-shaped
keys join as nested paths with invalid ``:`` segments. We always wire the v1
sanitization strategies so keys land as flat, filesystem-safe files.
"""
from pathlib import Path

from key_value.aio.stores.filetree.store import (
    FileTreeStore,
    FileTreeV1CollectionSanitizationStrategy,
    FileTreeV1KeySanitizationStrategy,
)


def oauth_token_file_tree_store(token_dir: Path) -> FileTreeStore:
    """Build a FileTreeStore suitable for fastmcp OAuth token persistence."""
    resolved = token_dir.resolve()
    return FileTreeStore(
        data_directory=resolved,
        key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(directory=resolved),
        collection_sanitization_strategy=FileTreeV1CollectionSanitizationStrategy(
            directory=resolved,
        ),
    )
