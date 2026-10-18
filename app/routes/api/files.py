"""REST API endpoints for File operations.

Provides CRUD operations for binary files.
"""
import logging

from fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.exceptions import NotFoundError
from app.middleware.auth import get_user_from_request
from app.models.file_models import (
    FileCreate,
    FileUpdate,
)
from app.routes.api.validation import (
    parse_optional_int_query,
    validation_error_response,
)

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    """Register file REST routes with FastMCP"""

    @mcp.custom_route("/api/v1/files", methods=["GET"])
    async def list_files(request: Request) -> JSONResponse:
        """List files with optional filtering.

        Query params:
            project_id: Filter by project
            mime_type: Filter by MIME type
            tags: Comma-separated tags (OR logic)
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params
        mime_type = params.get("mime_type")
        tags_str = params.get("tags")

        try:
            project_id = parse_optional_int_query(params, "project_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        tags = [t.strip() for t in tags_str.split(",")] if tags_str else None

        files = await mcp.file_service.list_files(
            user_id=user.id,
            project_id=project_id,
            mime_type=mime_type,
            tags=tags,
        )

        return JSONResponse({
            "files": [f.model_dump(mode="json") for f in files],
            "total": len(files),
        })

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["GET"])
    async def get_file(request: Request) -> JSONResponse:
        """Get a single file by ID (includes base64 data)."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        file_id = int(request.path_params["file_id"])

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
            return validation_error_response(e)

        file = await mcp.file_service.create_file(
            user_id=user.id,
            file_data=file_data,
        )

        return JSONResponse(file.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["PUT"])
    async def update_file(request: Request) -> JSONResponse:
        """Update an existing file."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        file_id = int(request.path_params["file_id"])

        try:
            body = await request.json()
            update_data = FileUpdate(**body)
        except ValidationError as e:
            return validation_error_response(e)

        try:
            file = await mcp.file_service.update_file(
                user_id=user.id,
                file_id=file_id,
                file_data=update_data,
            )
        except NotFoundError:
            return JSONResponse({"error": "File not found"}, status_code=404)

        return JSONResponse(file.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/files/{file_id}", methods=["DELETE"])
    async def delete_file(request: Request) -> JSONResponse:
        """Delete a file."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        file_id = int(request.path_params["file_id"])

        try:
            success = await mcp.file_service.delete_file(
                user_id=user.id,
                file_id=file_id,
            )
        except NotFoundError:
            return JSONResponse({"error": "File not found"}, status_code=404)

        if not success:
            return JSONResponse({"error": "File not found"}, status_code=404)

        return JSONResponse({"success": True})
