"""Curated CLI verbs: friendly flags mapped onto registry tool arguments.

Every verb goes through the ToolExecutor seam, so it works identically against the
in-process runtime and a remote deployment by construction. Payloads are normalized
with to_jsonable first because local execution returns pydantic models while remote
execution returns plain dicts.
"""
from typing import Any

from app.routes.cli.render import (
    render_memory_detail,
    render_memory_lines,
    render_project_lines,
    to_jsonable,
)

DEFAULT_QUERY_CONTEXT = "cli search"
DEFAULT_SAVE_CONTEXT = "Saved from the Forgetful CLI"


class CliError(Exception):
    """User-facing verb failure; the command runner maps it onto exit code 1."""


async def resolve_project(executor, value: str) -> int:
    """Resolve a -p/--project value: numeric ids pass through, names via list_projects."""
    if value.isdigit():
        return int(value)

    listing = to_jsonable(await executor.execute("list_projects", {}))
    projects = listing.get("projects", [])
    for project in projects:
        if project["name"].lower() == value.lower():
            return project["id"]

    names = ", ".join(sorted(project["name"] for project in projects)) or "none"
    raise CliError(f"Unknown project '{value}'. Available projects: {names}")


async def run(executor, args) -> tuple[Any, str]:
    """Execute a curated verb; returns (json payload, human rendering)."""
    if args.command == "project":
        return await _project_list(executor)

    handler = {
        "search": _memory_search,
        "save": _memory_save,
        "get": _memory_get,
        "recent": _memory_recent,
    }[args.memory_command]
    return await handler(executor, args)


async def _memory_search(executor, args) -> tuple[Any, str]:
    arguments: dict[str, Any] = {
        "query": args.query,
        "query_context": args.context,
    }
    if args.limit is not None:
        arguments["k"] = args.limit
    if args.project:
        arguments["project_ids"] = [await resolve_project(executor, args.project)]

    payload = to_jsonable(await executor.execute("query_memory", arguments))
    return payload, render_memory_lines(payload.get("primary_memories", []))


async def _memory_save(executor, args) -> tuple[Any, str]:
    arguments: dict[str, Any] = {
        "title": args.title,
        "content": args.content,
        "context": DEFAULT_SAVE_CONTEXT,
        "keywords": [],
        "tags": [],
        "importance": args.importance,
    }
    if args.project:
        arguments["project_ids"] = [await resolve_project(executor, args.project)]

    payload = to_jsonable(await executor.execute("create_memory", arguments))
    return payload, f"Created memory {payload['id']}: {payload['title']}"


async def _memory_get(executor, args) -> tuple[Any, str]:
    payload = to_jsonable(await executor.execute("get_memory", {"memory_id": args.memory_id}))
    return payload, render_memory_detail(payload)


async def _memory_recent(executor, args) -> tuple[Any, str]:
    arguments: dict[str, Any] = {"limit": args.limit}
    if args.project:
        arguments["project_ids"] = [await resolve_project(executor, args.project)]

    payload = to_jsonable(await executor.execute("get_recent_memories", arguments))
    return payload, render_memory_lines(payload.get("memories", []))


async def _project_list(executor) -> tuple[Any, str]:
    payload = to_jsonable(await executor.execute("list_projects", {}))
    return payload, render_project_lines(payload.get("projects", []))
