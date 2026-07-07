"""Context shim for in-process CLI tool execution.

Tool adapters receive a FastMCP Context but read exactly two attributes from it:
ctx.fastmcp.user_service and ctx.fastmcp.auth (app/middleware/auth.py). auth=None
routes get_user_from_auth down its default-user branch - identical to today's
no-auth stdio server.
"""
from app.bootstrap import Runtime


class _CliRuntime:
    """Stands in for the FastMCP instance attributes that adapters read."""

    def __init__(self, runtime: Runtime):
        self.user_service = runtime.services.user
        self.auth = None


class CliContext:
    """Duck-typed FastMCP Context handed to tool adapters by LocalExecutor."""

    def __init__(self, runtime: Runtime):
        self.fastmcp = _CliRuntime(runtime)
