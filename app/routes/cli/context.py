"""Context shim for in-process CLI tool execution.

Adapters receive the default-user identity plus the actual registry, instance
scope tokens and permitted-tool ceiling. Nested bundle resource checks use the
same scope resolver as MCP without inventing a FastMCP request or access token.

"""
from app.bootstrap import Runtime


class _CliRuntime:
    """Stands in for the FastMCP instance attributes that adapters read."""

    def __init__(self, runtime: Runtime):
        self.user_service = runtime.services.user
        self.auth = None
        self.registry = runtime.registry
        self._instance_permitted_tools = runtime.permitted_tools
        self._instance_scopes = runtime.instance_scopes


class CliContext:
    """Duck-typed FastMCP Context handed to tool adapters by LocalExecutor."""

    def __init__(self, runtime: Runtime):
        self.fastmcp = _CliRuntime(runtime)
