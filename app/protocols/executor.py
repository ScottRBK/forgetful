"""Protocol for CLI tool execution.

Every CLI tool command is written once against this seam; whether it runs against the
in-process registry (LocalExecutor) or a remote deployment via the fastmcp client
(RemoteExecutor) is a construction-time choice.
"""
from typing import Any, Protocol


class ToolExecutor(Protocol):
    """Executes Forgetful registry tools and exposes their discovery metadata."""

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        ...

    async def list_tools(self, category: str | None = None) -> dict[str, Any]:
        ...

    async def tool_info(self, tool_name: str) -> dict[str, Any]:
        ...

    async def close(self) -> None:
        ...
