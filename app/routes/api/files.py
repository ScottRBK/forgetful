"""REST API endpoints for File operations.

Provides CRUD operations for binary files.
"""
import logging

from fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.exceptions import (
    NotFoundError,
    WritePluginRejectedError,
    WritePluginUnavailableError,
)
from app.middleware.auth import get_user_from_request
from app.models.file_models import (
    FileCreate,
    FileUpdate,
)
from app.routes.api.list_pagination import parse_list_pagination
from app.routes.api.params import parse_path_int
from app.routes.write_plugin_responses import FileDeleteResponse, FileWriteResponse

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    """Register file REST routes with FastMCP"""

    @mcp.custom_route("/api/v1/files", methods=["GET"])
    async def list_files(request: Request) -> JSONResponse:
        """List files with optional filtering.

        Query params:
            limit: Results per page (1-100, default 20)
            offset: Results to skip (default 0)
            project_id: Filter by project
            mime_type: Filter by MIME type
            tags: Comma-separated tags (OR logic)
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params
        try:
            limit, offset = parse_list_pagination(params)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        project_id_str = params.get("project_id")
        mime_type = params.get("mime_type")
        tags_str = params.get("tags")

        project_id = None
        if project_id_str:
            try:
                project_id = int(project_id_str)
            except ValueError:
                return JSONResponse(
                    {"error": f"Invalid project_id: {project_id_str}. Must be an integer."},
                    status_code=400,
                )
        tags = [t.strip() for t in tags_str.split(",")] if tags_str else None

        files, total = await mcp.file_service.list_files_page(
            user_id=user.id,
            limit=limit,
            offset=offset,
            project_id=project_id,
            mime_type=mime_type,
            tags=tags,
        )

        return JSONResponse({
            "files": [f.model_dump(mode="json") for f in files],
            "total": total,
            "limit": limit,
            "offset": offset,
        })

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["GET"])
    async def get_file(request: Request) -> JSONResponse:
        """Get a single file by ID (includes base64 data)."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            file_id = parse_path_int(request, "file_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            file = await mcp.file_service.get_file(
                user_id=user.id,
                file_id=file_id,
            )
        except NotFoundError:
            return JSONResponse({"error": "File not found"}, status_code=404)

        return JSONResponse(file.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/files", methods=["POST"])
    async def create_file(request: Request) -> JSONResponse:
        """Create a new file."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            body = await request.json()
            file_data = FileCreate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            write_result = await mcp.file_service.create_file(
                user_id=user.id,
                file_data=file_data,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)

        response = FileWriteResponse(
            **write_result.file.model_dump(), plugin_warnings=write_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["PUT"])
    async def update_file(request: Request) -> JSONResponse:
        """Update an existing file."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            file_id = parse_path_int(request, "file_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            body = await request.json()
            update_data = FileUpdate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            write_result = await mcp.file_service.update_file(
                user_id=user.id,
                file_id=file_id,
                file_data=update_data,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError:
            return JSONResponse({"error": "File not found"}, status_code=404)

        response = FileWriteResponse(
            **write_result.file.model_dump(), plugin_warnings=write_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["DELETE"])
    async def delete_file(request: Request) -> JSONResponse:
        """Delete a file."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            file_id = parse_path_int(request, "file_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            delete_result = await mcp.file_service.delete_file(
                user_id=user.id,
                file_id=file_id,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError:
            return JSONResponse({"error": "File not found"}, status_code=404)

        if not delete_result.deleted:
            return JSONResponse({"error": "File not found"}, status_code=404)

        response = FileDeleteResponse(
            success=True, plugin_warnings=delete_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"))
