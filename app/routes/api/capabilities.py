"""Public discovery of the instance's enabled optional features."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import settings


def register(mcp: FastMCP):
    """Register capability discovery independently of feature flags and authentication."""

    @mcp.custom_route("/.well-known", methods=["GET"])
    async def get_capabilities(request: Request) -> JSONResponse:
        """Report settings only; do not resolve a user or access domain services."""
        return JSONResponse({
            "schema_version": 1,
            "capabilities": {
                "planning": settings.PLANNING_ENABLED,
                "skills": settings.SKILLS_ENABLED,
                "files": settings.FILES_ENABLED,
                "activity_stream": settings.ACTIVITY_ENABLED,
            },
        })
