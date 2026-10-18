"""REST API endpoints for Activity operations.

Provides read access to the activity log for event-driven architecture (Issue #7).
Includes SSE streaming endpoint for real-time event updates.
"""

import json
import logging

from fastmcp import FastMCP
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.middleware.auth import get_user_from_request
from app.models.activity_models import ActionType, ActorType, EntityType
from app.routes.api.query_params import (
    INT32_MAX,
    INT32_MIN,
    parse_datetime_param,
    parse_int_param,
)

logger = logging.getLogger(__name__)


def parse_pagination(params) -> tuple[int, int]:
    """Parse and validate the limit/offset query parameters of the activity routes.

    Raises:
        ValueError: If either value is malformed or out of range
    """
    limit = parse_int_param(params, "limit", 50)
    offset = parse_int_param(params, "offset", 0)

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be >= 0")

    return limit, offset


def register(mcp: FastMCP):
    """Register activity REST routes with FastMCP."""

    @mcp.custom_route("/api/v1/activity", methods=["GET"])
    async def list_activity(request: Request) -> JSONResponse:
        """List activity events with filtering and pagination.

        Query params:
            entity_type: Filter by entity type (memory, project, document, etc.)
            action: Filter by action (created, updated, deleted, read, queried)
            entity_id: Filter by specific entity ID
            actor: Filter by actor (user, system, llm-maintenance)
            since: Only events after this timestamp (ISO 8601)
            until: Only events before this timestamp (ISO 8601)
            limit: Maximum results (1-100, default 50)
            offset: Skip N results for pagination (default 0)

        Returns:
            {
                "events": [...],
                "total": int,
                "limit": int,
                "offset": int
            }
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params

        # Parse query parameters; a malformed value is rejected, never ignored
        entity_type = params.get("entity_type")
        action = params.get("action")
        actor = params.get("actor")
        try:
            since = parse_datetime_param(params, "since")
            until = parse_datetime_param(params, "until")
            limit, offset = parse_pagination(params)
            # An empty entity_id means "no filter"; ids are 32-bit INTEGER columns on PostgreSQL
            entity_id = (
                parse_int_param(params, "entity_id", min_value=INT32_MIN, max_value=INT32_MAX)
                if params.get("entity_id")
                else None
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        # Convert and validate action if provided
        action_enum = None
        if action:
            try:
                action_enum = ActionType(action)
            except ValueError:
                valid = ", ".join(a.value for a in ActionType)
                return JSONResponse(
                    {"error": f"Invalid action: {action}. Valid values: {valid}"},
                    status_code=400,
                )

        # Convert and validate entity_type if provided
        entity_type_enum = None
        if entity_type:
            try:
                entity_type_enum = EntityType(entity_type)
            except ValueError:
                valid = ", ".join(e.value for e in EntityType)
                return JSONResponse(
                    {"error": f"Invalid entity_type: {entity_type}. Valid values: {valid}"},
                    status_code=400,
                )

        # Convert and validate actor if provided
        actor_enum = None
        if actor:
            try:
                actor_enum = ActorType(actor)
            except ValueError:
                valid = ", ".join(a.value for a in ActorType)
                return JSONResponse(
                    {"error": f"Invalid actor: {actor}. Valid values: {valid}"},
                    status_code=400,
                )

        response = await mcp.activity_service.get_activity(
            user_id=user.id,
            entity_type=entity_type_enum,
            action=action_enum,
            entity_id=entity_id,
            actor=actor_enum,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )

        return JSONResponse(response.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/activity/{entity_type}/{entity_id}", methods=["GET"])
    async def get_entity_history(request: Request) -> JSONResponse:
        """Get activity history for a specific entity.

        Path params:
            entity_type: Entity type (memory, project, document, code_artifact, entity)
            entity_id: Entity ID

        Query params:
            limit: Maximum results (1-100, default 50)
            offset: Skip N results for pagination (default 0)

        Returns:
            {
                "events": [...],
                "total": int,
                "limit": int,
                "offset": int
            }
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        entity_type_str = request.path_params["entity_type"]
        entity_id_str = request.path_params["entity_id"]

        # Convert and validate entity_type (excluding "link" for entity history)
        valid_for_history = {EntityType.MEMORY, EntityType.PROJECT, EntityType.DOCUMENT,
                            EntityType.CODE_ARTIFACT, EntityType.ENTITY}
        try:
            entity_type_enum = EntityType(entity_type_str)
            if entity_type_enum not in valid_for_history:
                raise ValueError("not valid for history")
        except ValueError:
            valid = ", ".join(e.value for e in valid_for_history)
            return JSONResponse(
                {"error": f"Invalid entity_type: {entity_type_str}. Valid values: {valid}"},
                status_code=400,
            )

        # Parse entity_id
        try:
            entity_id = int(entity_id_str)
        except ValueError:
            return JSONResponse(
                {"error": "entity_id must be an integer"},
                status_code=400,
            )

        try:
            limit, offset = parse_pagination(request.query_params)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        response = await mcp.activity_service.get_entity_history(
            user_id=user.id,
            entity_type=entity_type_enum,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

        return JSONResponse(response.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/activity/stream", methods=["GET"])
    async def stream_activity(request: Request) -> EventSourceResponse:
        """Stream activity events via Server-Sent Events (SSE).

        Events are filtered to only those belonging to the authenticated user.
        Each event includes a sequence number for gap detection; with
        entity_type/action filters it counts only the events matching them.
        Requires ACTIVITY_ENABLED=true.

        Query params:
            entity_type: Filter by entity type (optional)
            action: Filter by action (optional)

        Returns:
            SSE stream of activity events as JSON with sequence numbers.

        Event format:
            event: activity
            data: {"seq": 1, "entity_type": "memory", "action": "created", ...}

        Client recovery:
            Track 'seq' field to detect gaps. On gap detection,
            fetch missed events via GET /api/v1/activity endpoint.
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        event_bus = getattr(mcp, "event_bus", None)
        if event_bus is None:
            return JSONResponse(
                {"error": "Activity streaming not enabled (ACTIVITY_ENABLED=false)"},
                status_code=503,
            )

        # Optional query param filters
        params = request.query_params
        entity_type_filter = params.get("entity_type")
        action_filter = params.get("action")

        # Validate filters if provided
        if entity_type_filter:
            try:
                EntityType(entity_type_filter)
            except ValueError:
                valid = ", ".join(e.value for e in EntityType)
                return JSONResponse(
                    {"error": f"Invalid entity_type: {entity_type_filter}. Valid values: {valid}"},
                    status_code=400,
                )

        if action_filter:
            try:
                ActionType(action_filter)
            except ValueError:
                valid = ", ".join(a.value for a in ActionType)
                return JSONResponse(
                    {"error": f"Invalid action: {action_filter}. Valid values: {valid}"},
                    status_code=400,
                )

        logger.info(
            "SSE stream started",
            extra={
                "user_id": str(user.id),
                "entity_type_filter": entity_type_filter,
                "action_filter": action_filter,
            },
        )

        async def event_generator():
            try:
                # Filters are applied by the bus so that 'seq' only counts the
                # events this stream is entitled to receive (a gap means loss).
                async for event_dict in event_bus.subscribe_stream(
                    user.id,
                    entity_type=entity_type_filter or None,
                    action=action_filter or None,
                ):
                    yield {
                        "event": "activity",
                        "data": json.dumps(event_dict),
                    }
            except Exception:
                logger.exception("Error in SSE event generator")

        return EventSourceResponse(event_generator())
