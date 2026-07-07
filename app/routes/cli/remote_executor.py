"""Remote ToolExecutor: drives a deployed Forgetful server through fastmcp.Client.

execute()/list_tools()/tool_info() proxy the server's meta-tools, so identity and
scopes are enforced server-side from the token and help text always matches the
server's version (no doc skew).
"""
import json
from typing import Any
from urllib.parse import urlparse


def normalize_server_url(url: str) -> str:
    """Append the default /mcp mount path when the URL has no explicit path."""
    url = url.rstrip("/")
    if urlparse(url).path in ("", "/"):
        return f"{url}/mcp"
    return url


def _default_client_factory(url: str, token: str | None):
    """Build a fastmcp Client: bearer when a token is supplied, OAuth otherwise.

    OAuth must be given persistent token storage - fastmcp's default is in-memory,
    which would re-trigger the browser flow on every CLI invocation.
    """
    from fastmcp import Client

    if token:
        return Client(url, auth=token)

    from fastmcp.client.auth import OAuth
    from key_value.aio.stores.filetree.store import FileTreeStore

    from app.routes.cli.paths import token_cache_dir

    cache = token_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    cache.chmod(0o700)
    oauth = OAuth(mcp_url=url, token_storage=FileTreeStore(data_directory=cache))
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
        await self._client.close()
