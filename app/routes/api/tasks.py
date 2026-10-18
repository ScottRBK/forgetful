"""REST API endpoints for Task, Criterion, and Dependency operations.
"""
import logging

from fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.middleware.auth import get_user_from_request
from app.models.plan_models import (
    CriterionCreate,
    CriterionUpdate,
    TaskCreate,
    TaskPriority,
    TaskState,
    TaskUpdate,
)
from app.routes.api.request_utils import (
    body_int,
    handle_request_errors,
    path_id,
    query_enum,
    query_int,
    read_json_object,
)

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    """Register task REST routes with FastMCP"""
    # ---- Task endpoints ----

    @mcp.custom_route("/api/v1/tasks", methods=["GET"])
    @handle_request_errors
    async def list_tasks(request: Request) -> JSONResponse:
        """Query tasks. plan_id is required."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params
        plan_id_str = params.get("plan_id")
        if not plan_id_str:
            return JSONResponse({"error": "plan_id query param is required"}, status_code=400)

        plan_id = query_int(params, "plan_id")
        assigned_agent = params.get("assigned_agent")

        state = query_enum(params, "state", TaskState)
        priority = query_enum(params, "priority", TaskPriority)

        tasks = await mcp.task_service.list_tasks(
            user_id=user.id, plan_id=plan_id,
            state=state, priority=priority, assigned_agent=assigned_agent,
        )
        return JSONResponse({
            "tasks": [t.model_dump(mode="json") for t in tasks],
            "total": len(tasks),
        })

    @mcp.custom_route("/api/v1/tasks/{task_id}", methods=["GET"])
    @handle_request_errors
    async def get_task(request: Request) -> JSONResponse:
        """Get task with criteria and dependency_ids."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")
        try:
            task = await mcp.task_service.get_task(user_id=user.id, task_id=task_id)
        except NotFoundError:
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse(task.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/tasks", methods=["POST"])
    @handle_request_errors
    async def create_task(request: Request) -> JSONResponse:
        """Create task with inline criteria + dependency_ids."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        try:
            body = await read_json_object(request)
            task_data = TaskCreate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            task = await mcp.task_service.create_task(user_id=user.id, task_data=task_data)
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except InvalidStateTransitionError as e:
            return JSONResponse({"error": str(e)}, status_code=422)
        except CyclicDependencyError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        return JSONResponse(task.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/tasks/{task_id}", methods=["PUT"])
    @handle_request_errors
    async def update_task(request: Request) -> JSONResponse:
        """Update task metadata (not state)."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")

        try:
            body = await read_json_object(request)
            update_data = TaskUpdate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        task = await mcp.task_service.update_task(
            user_id=user.id, task_id=task_id, task_data=update_data,
        )
        if not task:
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse(task.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/tasks/{task_id}", methods=["DELETE"])
    @handle_request_errors
    async def delete_task(request: Request) -> JSONResponse:
        """Delete task."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")
        success = await mcp.task_service.delete_task(user_id=user.id, task_id=task_id)
        if not success:
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse({"success": True})

    @mcp.custom_route("/api/v1/tasks/{task_id}/transition", methods=["POST"])
    @handle_request_errors
    async def transition_task(request: Request) -> JSONResponse:
        """Transition task state. Body: {state, version}."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")

        try:
            body = await read_json_object(request)
            new_state = TaskState(body["state"])
            version = body_int(body["version"], "version")
        except (KeyError, ValueError) as e:
            return JSONResponse({"error": f"Invalid body: {e}"}, status_code=400)

        try:
            task = await mcp.task_service.transition_task(
                user_id=user.id, task_id=task_id,
                new_state=new_state, expected_version=version,
            )
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except ConflictError as e:
            return JSONResponse({"error": str(e)}, status_code=409)
        except InvalidStateTransitionError as e:
            return JSONResponse({"error": str(e)}, status_code=422)
        except DependencyNotMetError as e:
            return JSONResponse({"error": str(e)}, status_code=422)

        return JSONResponse(task.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/tasks/{task_id}/claim", methods=["POST"])
    @handle_request_errors
    async def claim_task(request: Request) -> JSONResponse:
        """Claim task. Body: {agent_id, version}."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")

        try:
            body = await read_json_object(request)
            agent_id = body["agent_id"]
            version = body_int(body["version"], "version")
        except (KeyError, ValueError) as e:
            return JSONResponse({"error": f"Invalid body: {e}"}, status_code=400)

        try:
            task = await mcp.task_service.claim_task(
                user_id=user.id, task_id=task_id,
                agent_id=agent_id, expected_version=version,
            )
        except ValidationError as e:
            # Without the rejected value: it can be huge or not representable as JSON.
            return JSONResponse({"error": e.errors(include_input=False)}, status_code=400)
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except ConflictError as e:
            return JSONResponse({"error": str(e)}, status_code=409)
        except InvalidStateTransitionError as e:
            return JSONResponse({"error": str(e)}, status_code=422)
        except DependencyNotMetError as e:
            return JSONResponse({"error": str(e)}, status_code=422)

        return JSONResponse(task.model_dump(mode="json"))

    # ---- Criteria endpoints ----

    @mcp.custom_route("/api/v1/tasks/{task_id}/criteria", methods=["POST"])
    @handle_request_errors
    async def add_criterion(request: Request) -> JSONResponse:
        """Add criterion to task."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")

        try:
            body = await read_json_object(request)
            criterion_data = CriterionCreate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            criterion = await mcp.task_service.add_criterion(
                user_id=user.id, task_id=task_id, criterion_data=criterion_data,
            )
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except InvalidStateTransitionError as e:
            return JSONResponse({"error": str(e)}, status_code=422)

        return JSONResponse(criterion.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/criteria/{criterion_id}", methods=["PUT"])
    @handle_request_errors
    async def update_criterion(request: Request) -> JSONResponse:
        """Update criterion (set met)."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        criterion_id = path_id(request, "criterion_id")

        try:
            body = await read_json_object(request)
            criterion_data = CriterionUpdate(**body)
        except ValidationError as e:
            return JSONResponse({"error": e.errors()}, status_code=400)

        try:
            criterion = await mcp.task_service.update_criterion(
                user_id=user.id, criterion_id=criterion_id, criterion_data=criterion_data,
            )
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)

        return JSONResponse(criterion.model_dump(mode="json"))

    @mcp.custom_route("/api/v1/criteria/{criterion_id}", methods=["DELETE"])
    @handle_request_errors
    async def delete_criterion(request: Request) -> JSONResponse:
        """Delete criterion."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        criterion_id = path_id(request, "criterion_id")
        success = await mcp.task_service.delete_criterion(
            user_id=user.id, criterion_id=criterion_id,
        )
        if not success:
            return JSONResponse({"error": "Criterion not found"}, status_code=404)
        return JSONResponse({"success": True})

    # ---- Dependency endpoints ----

    @mcp.custom_route("/api/v1/tasks/{task_id}/dependencies", methods=["POST"])
    @handle_request_errors
    async def add_dependency(request: Request) -> JSONResponse:
        """Add dependency. Body: {depends_on_task_id}."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")

        try:
            body = await read_json_object(request)
            depends_on_task_id = body_int(body["depends_on_task_id"], "depends_on_task_id")
        except (KeyError, ValueError) as e:
            return JSONResponse({"error": f"Invalid body: {e}"}, status_code=400)

        try:
            dep = await mcp.task_service.add_dependency(
                user_id=user.id, task_id=task_id, depends_on_task_id=depends_on_task_id,
            )
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except CyclicDependencyError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        return JSONResponse(dep.model_dump(mode="json"), status_code=201)

    @mcp.custom_route("/api/v1/tasks/{task_id}/dependencies/{depends_on_task_id}", methods=["DELETE"])
    @handle_request_errors
    async def remove_dependency(request: Request) -> JSONResponse:
        """Remove dependency."""
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        task_id = path_id(request, "task_id")
        depends_on_task_id = path_id(request, "depends_on_task_id")

        success = await mcp.task_service.remove_dependency(
            user_id=user.id, task_id=task_id, depends_on_task_id=depends_on_task_id,
        )
        if not success:
            return JSONResponse({"error": "Dependency not found"}, status_code=404)
        return JSONResponse({"success": True})
