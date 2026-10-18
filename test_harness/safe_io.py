"""Symlink-safe host-side file I/O for the agent-writable run tree.

`<run_dir>/skills` is bind-mounted read-write into the sandbox container, so the agent
can create, replace and delete anything below it - symlinks included, and including the
directories of skills that have not run yet. Host code that touches that tree with plain
pathlib/shutil calls follows those links: a planted `workspace/SKILL.md -> ~/.bashrc` is
overwritten by the next copy, a planted `workspace/report.json -> <host file>` is parsed
and its content echoed into meta.json.

Every helper takes the trusted root (the mount directory, which the agent cannot replace)
and treats everything below it as hostile:

- reads refuse a symlink anywhere between the root and the file, and never open anything
  but a regular file (a planted FIFO would otherwise block the harness forever)
- writes replace a planted symlink with a regular file - unlinking removes the link, never
  its target - and open the final component with O_NOFOLLOW

Parent directories are checked with lstat just before use, so a background process of the
agent that is still running could in theory swap one in that window. Closing it fully needs
directory-fd traversal, which is POSIX-only; the final path component is race-free.
"""
import errno
import os
import shutil
import stat
from pathlib import Path

_O_BINARY = getattr(os, "O_BINARY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
# What open(O_NOFOLLOW) reports when the final component is a symlink
_SYMLINK_ERRNOS = {errno.ELOOP, errno.EMLINK}


class UnsafePathError(OSError):
    """A path in the agent-writable tree is, or sits below, a symlink, or is not a
    regular file. Refused rather than followed."""


def _first_link(path: Path, root: Path) -> Path | None:
    """The outermost symlink among the components of `path` below `root`, if any."""
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise UnsafePathError(f"{path} is not inside {root}") from exc
    current = root
    for part in parts:
        current = current / part
        try:
            if stat.S_ISLNK(os.lstat(current).st_mode):
                return current
        except (FileNotFoundError, NotADirectoryError):
            return None  # nothing exists from here down, so nothing can be a link
    return None


def read_bytes(path: Path, root: Path | None = None) -> bytes:
    """Read a regular file, refusing symlinks below `root` (default: the file itself)."""
    link = _first_link(path, path.parent if root is None else root)
    if link is not None:
        raise UnsafePathError(f"{link} is a symlink")
    try:
        fd = os.open(path, os.O_RDONLY | _O_BINARY | _O_NOFOLLOW | _O_NONBLOCK)
    except OSError as exc:
        if exc.errno in _SYMLINK_ERRNOS:
            raise UnsafePathError(f"{path} is a symlink") from exc
        raise
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise UnsafePathError(f"{path} is not a regular file")
    except BaseException:
        os.close(fd)
        raise
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def make_dirs(path: Path, root: Path) -> None:
    """`mkdir -p` that replaces a symlink planted below `root` with a real directory."""
    link = _first_link(path, root)
    if link is not None:
        link.unlink()
    path.mkdir(parents=True, exist_ok=True)


def write_bytes(path: Path, data: bytes, root: Path) -> None:
    """Write a regular file below `root`, never through a symlink."""
    make_dirs(path.parent, root)
    link = _first_link(path, root)
    if link is not None:
        link.unlink()
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _O_BINARY | _O_NOFOLLOW | _O_NONBLOCK
    try:
        fd = os.open(path, flags, 0o666)
    except OSError as exc:
        if exc.errno in _SYMLINK_ERRNOS:
            raise UnsafePathError(f"{path} became a symlink while writing") from exc
        raise
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)


def write_text(path: Path, text: str, root: Path) -> None:
    write_bytes(path, text.encode("utf-8"), root)


def replace_tree(src: Path, dst: Path, root: Path) -> None:
    """Install the trusted directory `src` at `dst` below `root`, replacing whatever the
    agent left there (a symlink is unlinked, a directory removed, never followed)."""
    make_dirs(dst.parent, root)
    if dst.is_dir() and not dst.is_symlink():
        shutil.rmtree(dst)
    elif os.path.lexists(dst):
        dst.unlink()
    shutil.copytree(src, dst, symlinks=True)
