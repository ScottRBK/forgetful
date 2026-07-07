"""CLI auth commands: login (browser OAuth), status, logout.

login verifies connectivity/auth with a ping, then persists FORGETFUL_SERVER into
~/.config/forgetful/.env (the file settings.py already reads). logout only clears the
local token cache - the server-side session is untouched.
"""
import shutil
import sys
from pathlib import Path

from app.routes.cli.paths import token_cache_dir, user_env_file
from app.routes.cli.remote_executor import normalize_server_url


def upsert_env_var(env_file: Path, key: str, value: str) -> None:
    """Set key=value in a dotenv file, preserving every other line."""
    lines = env_file.read_text().splitlines() if env_file.exists() else []

    for index, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[index] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")

    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(lines) + "\n")


def _oauth_client_factory(url: str, token_dir: Path):
    """Build an OAuth fastmcp Client with a persistent on-disk token cache."""
    from fastmcp import Client
    from fastmcp.client.auth import OAuth
    from key_value.aio.stores.filetree.store import FileTreeStore

    token_dir.mkdir(parents=True, exist_ok=True)
    token_dir.chmod(0o700)
    oauth = OAuth(mcp_url=url, token_storage=FileTreeStore(data_directory=token_dir))
    return Client(url, auth=oauth)


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
    """Report the active mode; in remote mode prove the credentials work."""
    import os

    from app.config.settings import settings

    url = server or settings.FORGETFUL_SERVER
    if not url:
        print("Mode: local (no FORGETFUL_SERVER configured)")
        print(f"Database: {settings.DATABASE}")
        return 0

    from app.routes.cli.remote_executor import RemoteExecutor

    executor = RemoteExecutor(url, token=os.environ.get("FORGETFUL_TOKEN") or None)
    try:
        user = await executor.execute("get_current_user", {})
    except Exception as exc:
        print(f"Server: {executor.server_url}", file=sys.stderr)
        print(f"Error: not authenticated: {exc}", file=sys.stderr)
        return 1
    finally:
        await executor.close()

    name = user.get("name") if isinstance(user, dict) else str(user)
    cache = token_cache_dir()
    cached = cache.exists() and any(cache.iterdir())
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
