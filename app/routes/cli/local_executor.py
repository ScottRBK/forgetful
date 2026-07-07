"""Local ToolExecutor: executes the in-process ToolRegistry.

Same execution path as meta_tools.execute_forgetful_tool - identical existence and
FORGETFUL_SCOPES checks, identical ctx injection - but against a runtime built by
app.bootstrap instead of a live FastMCP server.
"""
from typing import Any

from app.bootstrap import Runtime, build_runtime, dispose_runtime
from app.routes.cli.context import CliContext
from app.routes.mcp.meta_tools import (
    build_discovery_payload,
    build_tool_documentation,
    ensure_tool_executable,
)


class LocalExecutor:
    """ToolExecutor over an in-process runtime (default user, instance scope ceiling)."""

    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self._ctx = CliContext(runtime)

    @classmethod
    async def create(cls) -> "LocalExecutor":
        return cls(await build_runtime())

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        registry = self._runtime.registry
        ensure_tool_executable(registry, self._runtime.permitted_tools, tool_name)

        # Copy before injecting ctx so the caller's dict is left untouched
        arguments = dict(arguments)
        arguments["ctx"] = self._ctx
        return await registry.execute(name=tool_name, arguments=arguments)

    async def list_tools(self, category: str | None = None) -> dict[str, Any]:
        return build_discovery_payload(
            self._runtime.registry, self._runtime.permitted_tools, category,
        )

    async def tool_info(self, tool_name: str) -> dict[str, Any]:
        return build_tool_documentation(
            self._runtime.registry, self._runtime.permitted_tools, tool_name,
        )

    async def close(self) -> None:
        await dispose_runtime(self._runtime)
