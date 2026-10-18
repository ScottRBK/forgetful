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


async def _cached_access_token(url: str, token_dir: Path) -> str | None:
    """The access token the OAuth cache holds for exactly this server URL, or None.

    fastmcp's FileTreeStore scopes token entries per server URL, so a bare "is the
    cache non-empty" test would treat server A's tokens as valid for server B. Short-
    circuit an empty cache so a read-only status check writes nothing, then ask
    fastmcp's own token store for this URL's tokens.
    """
    if not (token_dir.exists() and any(token_dir.iterdir())):
        return None

    from fastmcp.client.auth import OAuth

    from app.routes.cli.token_storage import oauth_token_file_tree_store

    oauth = OAuth(mcp_url=url, token_storage=oauth_token_file_tree_store(token_dir))
    tokens = await oauth.token_storage_adapter.get_tokens()
    return tokens.access_token if tokens else None


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


# Server-side wording of the meta-tool scope denial (app/routes/mcp/meta_tools.py)
_SCOPE_DENIAL_MARKER = "is not permitted under current scopes"


async def _fetch_user_name(executor) -> str:
    """The authenticated user's name; raises when the server rejects the request.

    A scope denial is not an authentication failure: the server accepted the
    credentials and refused only the user lookup, which needs a scope (read:users)
    that a category-restricted deployment may not grant.
    """
    try:
        user = await executor.execute("get_current_user", {})
    except Exception as exc:
        if _SCOPE_DENIAL_MARKER in str(exc):
            return "(not shown: get_current_user is outside the granted scopes)"
        raise
    return user.get("name") if isinstance(user, dict) else str(user)


async def status(*, server: str | None = None) -> int:
    """Report the active mode; in remote mode prove the credentials work.

    A status check must never mint credentials or change state, so it never runs the
    interactive OAuth flow (no client registration, no browser, no callback wait, no
    cache clearing). It sends what we already hold as a plain bearer token - the
    FORGETFUL_TOKEN env var, else the access token cached by `auth login` - and with
    neither it verifies through a plain (no-auth) client. A rejected or expired token
    therefore fails fast as "not authenticated"; a no-auth server still answers, so
    the User line is preserved.
    """
    from app.config.settings import settings

    url = server or settings.FORGETFUL_SERVER
    if not url:
        print("Mode: local (no FORGETFUL_SERVER configured)")
        print(f"Database: {settings.DATABASE}")
        return 0

    from app.routes.cli.remote_executor import RemoteExecutor, bearer_token_from_env

    token = bearer_token_from_env()
    cache = token_cache_dir()
    normalized_url = normalize_server_url(url)
    cached_token = await _cached_access_token(normalized_url, cache)

    bearer = token or cached_token
    if bearer:
        executor = RemoteExecutor(url, token=bearer)
    else:
        executor = RemoteExecutor(url, client_factory=_plain_client_factory)

    try:
        name = await _fetch_user_name(executor)
    except Exception as exc:
        print(f"Server: {executor.server_url}", file=sys.stderr)
        print(f"Error: not authenticated: {exc}", file=sys.stderr)
        if cached_token and not token:
            print(
                f"If the cached login has expired, run `forgetful auth login "
                f"--server {executor.server_url}`.",
                file=sys.stderr,
            )
        return 1
    finally:
        await executor.close()

    print(f"Server: {executor.server_url}")
    print(f"User: {name}")
    print(f"Cached credentials: {'yes' if cached_token else 'no'}")
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
