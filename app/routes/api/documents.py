"""REST API endpoints for Document operations.

Phase 3b of the Web UI foundation (Issue #3).
Provides CRUD operations for documents.
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
from app.models.document_models import (
    DocumentCreate,
    DocumentUpdate,
)
from app.routes.api.list_pagination import parse_list_pagination
from app.routes.api.params import parse_path_int
from app.routes.write_plugin_responses import (
    DocumentDeleteResponse,
    DocumentWriteResponse,
)

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    """Register document REST routes with FastMCP"""

    @mcp.custom_route("/api/v1/documents", methods=["GET"])
    async def list_documents(request: Request) -> JSONResponse:
        """List documents with optional filtering.

        Query params:
            limit: Results per page (1-100, default 20)
            offset: Results to skip (default 0)
            project_id: Filter by project
            document_type: Filter by document type
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
        document_type = params.get("document_type")
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

        documents, total = await mcp.document_service.list_documents_page(
            user_id=user.id,
            limit=limit,
            offset=offset,
            project_id=project_id,
            document_type=document_type,
            tags=tags,
        )

        return JSONResponse({
            "documents": [d.model_dump(mode="json") for d in documents],
            "total": total,
            "limit": limit,
            "offset": offset,
        })

    @mcp.custom_route("/api/v1/documents/{document_id}", methods=["GET"])
    async def get_document(request: Request) -> JSONResponse:
        """Get a single document by ID."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            document_id = parse_path_int(request, "document_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            document = await mcp.document_service.get_document(
                user_id=user.id,
                document_id=document_id,
            )
        except NotFoundError:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        return JSONResponse(document.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/documents", methods=["POST"])
    async def create_document(request: Request) -> JSONResponse:
        """Create a new document."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            body = await request.json()
            document_data = DocumentCreate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            write_result = await mcp.document_service.create_document(
                user_id=user.id,
                document_data=document_data,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)

        response = DocumentWriteResponse(
            **write_result.document.model_dump(), plugin_warnings=write_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/documents/{document_id}", methods=["PUT"])
    async def update_document(request: Request) -> JSONResponse:
        """Update an existing document."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            document_id = parse_path_int(request, "document_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            body = await request.json()
            update_data = DocumentUpdate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            write_result = await mcp.document_service.update_document(
                user_id=user.id,
                document_id=document_id,
                document_data=update_data,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        response = DocumentWriteResponse(
            **write_result.document.model_dump(), plugin_warnings=write_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/documents/{document_id}", methods=["DELETE"])
    async def delete_document(request: Request) -> JSONResponse:
        """Delete a document."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            document_id = parse_path_int(request, "document_id")
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        try:
            delete_result = await mcp.document_service.delete_document(
                user_id=user.id,
                document_id=document_id,
            )
        except WritePluginRejectedError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except WritePluginUnavailableError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except NotFoundError:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        if not delete_result.deleted:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        response = DocumentDeleteResponse(
            success=True, plugin_warnings=delete_result.plugin_warnings,
        )
        return JSONResponse(response.model_dump(mode="json"))
