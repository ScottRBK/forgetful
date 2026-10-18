"""Remote ToolExecutor: drives a deployed Forgetful server through fastmcp.Client.

execute()/list_tools()/tool_info() proxy the server's meta-tools, so identity and
scopes are enforced server-side from the token and help text always matches the
server's version (no doc skew).
"""
import contextlib
import json
import re
from typing import Any
from urllib.parse import urlparse, urlsplit, urlunsplit

# A real scheme is always followed by "://"; "localhost:8020" is NOT a scheme
# (urlparse misreads its scheme as "localhost"), so match on the "://" form.
_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*)://")
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def normalize_server_url(url: str) -> str:
    """Normalize a CLI server URL to a requestable http(s) URL with a mount path.

    Scheme-less input (bare ``host`` or ``host:port``) gets a default scheme:
    ``http://`` for loopback hosts (localhost / 127.0.0.1 / [::1]) and ``https://``
    for everything else (secure by default). The scheme is lower-cased, because
    fastmcp's transport inference is case-sensitive. The ``/mcp`` mount path is then
    set when the URL carries no explicit path; only the path component is edited, so
    a query string or fragment is preserved and normalizing twice changes nothing.
    Explicit ``http``/``https`` URLs keep their scheme; any other explicit scheme
    (e.g. ``ftp://``) is rejected.
    """
    match = _SCHEME_RE.match(url)
    if match:
        if match.group(1).lower() not in ("http", "https"):
            raise ValueError(f"Unsupported server URL scheme: {url!r}")
    else:
        # Prepend a throwaway scheme so urlparse can extract the real hostname
        # (it strips IPv6 brackets and lowercases), then pick the true default.
        host = urlparse(f"http://{url}").hostname or ""
        scheme = "http" if host in _LOOPBACK_HOSTS else "https"
        url = f"{scheme}://{url}"
    parts = urlsplit(url)  # also lower-cases the scheme
    return urlunsplit(parts._replace(path=parts.path.rstrip("/") or "/mcp"))


def _default_client_factory(url: str, token: str | None):
    """Build a fastmcp Client: bearer when a token is supplied, OAuth otherwise.

    OAuth must be given persistent token storage - fastmcp's default is in-memory,
    which would re-trigger the browser flow on every CLI invocation.
    """
    from fastmcp import Client

    if token:
        return Client(url, auth=token)

    from fastmcp.client.auth import OAuth

    from app.routes.cli.paths import token_cache_dir
    from app.routes.cli.token_storage import oauth_token_file_tree_store

    cache = token_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    cache.chmod(0o700)
    oauth = OAuth(mcp_url=url, token_storage=oauth_token_file_tree_store(cache))
    return Client(url, auth=oauth)


class RemoteExecutor:
    """ToolExecutor over a remote deployment via the server's meta-tools."""

    def __init__(self, server_url: str, *, token: str | None = None, client_factory=None):
        self.server_url = normalize_server_url(server_url)
        self._token = token
        factory = client_factory or _default_client_factory
        self._client = factory(self.server_url, token)

    async def _call(self, meta_tool: str, payload: dict[str, Any]) -> Any:
        async with self._client:
            result = await self._client.call_tool(meta_tool, payload)
        if result.data is not None:
            return result.data

        # Bare arrays/scalars produce no MCP structured content (object root required)
        # and execute_forgetful_tool declares no output schema, so .data is None; the
        # value survives only as JSON text in the single content block.
        for block in result.content or []:
            text = getattr(block, "text", None)
            if text is not None:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return None

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        return await self._call(
            "execute_forgetful_tool",
            {"tool_name": tool_name, "arguments": arguments},
        )

    async def list_tools(self, category: str | None = None) -> dict[str, Any]:
        payload = {"category": category} if category else {}
        return await self._call("discover_forgetful_tools", payload)

    async def tool_info(self, tool_name: str) -> dict[str, Any]:
        return await self._call("how_to_use_forgetful_tool", {"tool_name": tool_name})

    async def close(self) -> None:
        # Runs in the command runner's finally block: a connection that failed to
        # open re-raises its ConnectError here, which would bury the already-reported
        # error under a teardown traceback.
        with contextlib.suppress(Exception):
            await self._client.close()
