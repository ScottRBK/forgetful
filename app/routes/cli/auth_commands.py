"""CLI auth commands: login (browser OAuth), status, logout.

login verifies connectivity/auth with a ping, then persists FORGETFUL_SERVER into
~/.config/forgetful/.env (the file settings.py already reads). logout only clears the
local token cache - the server-side session is untouched.
"""
import contextlib
import errno
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

from app.routes.cli.paths import token_cache_dir, user_env_file
from app.routes.cli.remote_executor import normalize_server_url


def _set_key_lines(lines: list[str], key: str, value: str) -> list[str]:
    """Return lines with every assignment of key set to value, or key=value appended.

    Lines keep their own trailing "\\r", so a CRLF file stays CRLF; an appended line
    follows the endings of the last line. Duplicates are all rewritten in place because
    dotenv lets the last one win. Nothing else is touched.
    """
    result = list(lines)
    found = False
    for index, line in enumerate(result):
        if line.strip().startswith(f"{key}="):
            result[index] = f"{key}={value}" + ("\r" if line.endswith("\r") else "")
            found = True
    if not found:
        result.append(f"{key}={value}" + ("\r" if result and result[-1].endswith("\r") else ""))
    return result


def _atomic_write(target: Path, data: bytes, mode: int | None) -> None:
    """Replace target with data via a synced temp file in the same directory.

    The original is untouched until os.replace succeeds, and the temp file is removed
    if anything fails. When mode is given it is applied to the new file; otherwise the
    file keeps mkstemp's owner-only 0o600.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f"{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(tmp_name, mode)
        os.replace(tmp_name, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def upsert_env_var(env_file: Path, key: str, value: str) -> None:
    """Set key=value in a dotenv file, preserving every other line.

    The file is read and written as UTF-8 (as settings.py parses it) and split on "\\n"
    only: str.splitlines() would also break lines inside values on U+2028, U+0085, form
    feed and the like. Every existing assignment of the key is updated, since dotenv
    lets the last duplicate win. The new content is written to a temp file and moved
    over the original, so a failed write can never leave the user's settings truncated.
    """
    # Follow a symlinked config file (dotfile managers) instead of replacing the link.
    target = Path(os.path.realpath(env_file))
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None

    text = ""
    if mode is not None:
        if not os.access(target, os.W_OK):
            # Replacing the file would sidestep a read-only config the user locked.
            raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(target))
        with target.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()

    data = ("\n".join(_set_key_lines(lines, key, value)) + "\n").encode("utf-8")
    _atomic_write(target, data, mode)


def _oauth_client_factory(url: str, token_dir: Path):
    """Build an OAuth fastmcp Client with a persistent on-disk token cache."""
    from fastmcp import Client
    from fastmcp.client.auth import OAuth

    from app.routes.cli.token_storage import oauth_token_file_tree_store

    token_dir.mkdir(parents=True, exist_ok=True)
    token_dir.chmod(0o700)
    oauth = OAuth(mcp_url=url, token_storage=oauth_token_file_tree_store(token_dir))
    return Client(url, auth=oauth)


def _plain_client_factory(url: str, _token: str | None = None):
    """A fastmcp Client with no auth, for verifying a connection without OAuth.

    Unlike the OAuth client it performs no dynamic client registration and writes
    nothing to the token cache, so a read-only status check can't resurrect the cache
    logout cleared (or pop a browser). Signature matches RemoteExecutor's factory seam.
    """
    from fastmcp import Client

    return Client(url)


async def _has_cached_credentials(url: str, token_dir: Path) -> bool:
    """True only when the OAuth cache holds tokens for exactly this server URL.

    fastmcp's FileTreeStore scopes token entries per server URL, so a bare "is the
    cache non-empty" test would treat server A's tokens as valid for server B and push
    status onto the OAuth path (dynamic client registration + browser) for a server we
    never logged into. Short-circuit an empty cache so a read-only status check writes
    nothing, then ask fastmcp's own token store whether it holds tokens for this URL.
    """
    if not (token_dir.exists() and any(token_dir.iterdir())):
        return False

    from fastmcp.client.auth import OAuth

    from app.routes.cli.token_storage import oauth_token_file_tree_store

    oauth = OAuth(mcp_url=url, token_storage=oauth_token_file_tree_store(token_dir))
    return await oauth.token_storage_adapter.get_tokens() is not None


async def login(
    server: str,
    *,
    env_file: Path | None = None,
    token_dir: Path | None = None,
    client_factory=None,
) -> int:
    """Run the browser OAuth flow against a server and save it as the default."""
    url = normalize_server_url(server)
    factory = client_factory or _oauth_client_factory
    client = factory(url, token_dir or token_cache_dir())

    try:
        async with client:
            await client.ping()
    except Exception as exc:
        print(f"Error: could not authenticate against {url}: {exc}", file=sys.stderr)
        return 1

    upsert_env_var(env_file or user_env_file(), "FORGETFUL_SERVER", url)
    print(f"Logged in to {url}")
    print(f"Saved FORGETFUL_SERVER to {env_file or user_env_file()}")
    return 0


async def status(*, server: str | None = None) -> int:
    """Report the active mode; in remote mode prove the credentials work.

    A status check must never mint credentials. We pick the client by what we already
    hold: a bearer token, or an existing OAuth cache to read; with neither we verify
    through a plain (no-OAuth) client so we never register a client or resurrect the
    cache logout cleared (nor pop a browser). A no-auth server still answers, so the
    User line is preserved; a secured server errors cleanly.
    """
    import os

    from app.config.settings import settings

    url = server or settings.FORGETFUL_SERVER
    if not url:
        print("Mode: local (no FORGETFUL_SERVER configured)")
        print(f"Database: {settings.DATABASE}")
        return 0

    from app.routes.cli.remote_executor import RemoteExecutor

    token = os.environ.get("FORGETFUL_TOKEN") or None
    cache = token_cache_dir()
    cached = await _has_cached_credentials(normalize_server_url(url), cache)

    if token:
        executor = RemoteExecutor(url, token=token)
    elif cached:
        executor = RemoteExecutor(url)
    else:
        executor = RemoteExecutor(url, client_factory=_plain_client_factory)

    try:
        user = await executor.execute("get_current_user", {})
    except Exception as exc:
        print(f"Server: {executor.server_url}", file=sys.stderr)
        print(f"Error: not authenticated: {exc}", file=sys.stderr)
        return 1
    finally:
        await executor.close()

    name = user.get("name") if isinstance(user, dict) else str(user)
    print(f"Server: {executor.server_url}")
    print(f"User: {name}")
    print(f"Cached credentials: {'yes' if cached else 'no'}")
    return 0


def logout(*, token_dir: Path | None = None) -> int:
    """Clear the local OAuth token cache."""
    target = token_dir or token_cache_dir()
    if target.exists():
        shutil.rmtree(target)
        print(f"Cleared token cache at {target}")
    else:
        print("No cached tokens to clear")
    return 0
