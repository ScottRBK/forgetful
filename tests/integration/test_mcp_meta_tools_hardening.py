"""Hardening of MCP tool error text and category discovery.

Covers, with stubbed services and no database:
- ``client_error_detail`` keeps authored messages and hides driver details.
- the per-category entity tools never put SQL, bound parameters or driver text in a ToolError.
- ``discover_forgetful_tools`` honours the advertised ``linking`` category.
- ``execute_forgetful_tool`` rejects argument names that cannot be keyword arguments.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest
import yaml
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.tool_registry_models import ToolCategory, ToolParameter
from app.routes.mcp import entity_tools
from app.routes.mcp.meta_tools import (
    build_discovery_payload,
    reject_invalid_argument_names,
)
from app.routes.mcp.tool_errors import (
    CONSTRAINT_FAILURE,
    GENERIC_FAILURE,
    INVALID_YAML_FAILURE,
    client_error_detail,
)
from app.routes.mcp.tool_registry import ToolRegistry

SECRET_USER_ID = "7f1c2b9e-0000-4000-8000-00000000abcd"
SQL_TEXT = "INSERT INTO entity_relationships (user_id, source_entity_id) VALUES (?, ?)"
LEAK_MARKERS = (
    "INSERT INTO",
    "[SQL:",
    "[parameters:",
    "sqlalche.me",
    "UNIQUE constraint failed",
    "sqlite3.",
    SECRET_USER_ID,
)


def _integrity_error() -> IntegrityError:
    return IntegrityError(
        SQL_TEXT,
        (SECRET_USER_ID, 1),
        Exception("UNIQUE constraint failed: entity_relationships.source_entity_id"),
    )


class TestClientErrorDetail:
    """Authored messages pass through; driver and unexpected errors are reduced."""

    @pytest.mark.parametrize(
        "error",
        [
            NotFoundError("Memory 7 not found"),
            ConflictError("A plan with this external_ref already exists."),
            InvalidStateTransitionError("todo -> done is not allowed"),
            DependencyNotMetError("task 3 is blocked"),
            CyclicDependencyError("cycle detected"),
            ValueError("project_id must be an integer"),
            TypeError("create_project() got an unexpected keyword argument 'name'"),
            ToolError("Entity 4 not found"),
        ],
    )
    def test_authored_messages_are_kept(self, error):
        assert client_error_detail(error) == str(error)

    def test_integrity_error_becomes_constraint_message(self):
        error = _integrity_error()

        detail = client_error_detail(error)

        assert detail == CONSTRAINT_FAILURE
        assert not [marker for marker in LEAK_MARKERS if marker in detail]
        assert "INSERT INTO" in str(error), "precondition: the raw text is what leaks"

    def test_yaml_error_becomes_short_message(self):
        with pytest.raises(yaml.YAMLError) as caught:
            yaml.safe_load("name: [unclosed")

        assert client_error_detail(caught.value) == INVALID_YAML_FAILURE

    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError(f"connection to {SECRET_USER_ID} dropped"),
            OverflowError("Python int too large to convert to SQLite INTEGER"),
            KeyError("password"),
        ],
    )
    def test_unexpected_errors_are_generic(self, error):
        assert client_error_detail(error) == GENERIC_FAILURE


class _StubUserService:
    async def get_or_create_user(self, user):
        return SimpleNamespace(id=uuid4())


class _FailingEntityService:
    """Every service method raises the configured error."""

    def __init__(self, error: Exception):
        self._error = error

    def __getattr__(self, name):
        async def _raise(**_kwargs):
            raise self._error

        return _raise


def _entity_tools_server(error: Exception) -> FastMCP:
    server = FastMCP("entity-tools-error-test")
    server.user_service = _StubUserService()
    server.entity_service = _FailingEntityService(error)
    entity_tools.register(server)
    return server


ENTITY_TOOL_CALLS = [
    ("create_entity", {"name": "Sarah", "entity_type": "Individual"}, "Failed to create entity"),
    ("get_entity", {"entity_id": 1}, "Failed to get entity"),
    ("list_entities", {}, "Failed to list entities"),
    ("search_entities", {"query": "sar"}, "Failed to search entities"),
    ("update_entity", {"entity_id": 1, "name": "S"}, "Failed to update entity"),
    ("delete_entity", {"entity_id": 1}, "Failed to delete entity"),
    (
        "link_entity_to_memory",
        {"entity_id": 1, "memory_id": 2},
        "Failed to link entity to memory",
    ),
    (
        "unlink_entity_from_memory",
        {"entity_id": 1, "memory_id": 2},
        "Failed to unlink entity from memory",
    ),
    (
        "link_entity_to_project",
        {"entity_id": 1, "project_id": 2},
        "Failed to link entity to project",
    ),
    (
        "unlink_entity_from_project",
        {"entity_id": 1, "project_id": 2},
        "Failed to unlink entity from project",
    ),
    (
        "create_entity_relationship",
        {"source_entity_id": 1, "target_entity_id": 2, "relationship_type": "works_with"},
        "Failed to create entity relationship",
    ),
    (
        "get_entity_relationships",
        {"entity_id": 1},
        "Failed to get entity relationships",
    ),
    (
        "update_entity_relationship",
        {"relationship_id": 1, "strength": 0.5},
        "Failed to update entity relationship",
    ),
    (
        "delete_entity_relationship",
        {"relationship_id": 1},
        "Failed to delete entity relationship",
    ),
    ("get_entity_memories", {"entity_id": 1}, "Failed to get entity memories"),
]


class TestEntityToolErrors:
    """Entity tools return a short message for database errors and keep authored ones."""

    @pytest.mark.parametrize(
        ("tool_name", "arguments", "prefix"),
        ENTITY_TOOL_CALLS,
        ids=[call[0] for call in ENTITY_TOOL_CALLS],
    )
    async def test_database_error_text_is_not_returned(self, tool_name, arguments, prefix):
        async with Client(_entity_tools_server(_integrity_error())) as client:
            with pytest.raises(ToolError) as caught:
                await client.call_tool(tool_name, arguments)

        message = str(caught.value)
        assert prefix in message
        assert CONSTRAINT_FAILURE in message
        assert not [marker for marker in LEAK_MARKERS if marker in message], message

    async def test_unexpected_error_text_is_not_returned(self):
        server = _entity_tools_server(RuntimeError(f"pool exhausted for {SECRET_USER_ID}"))

        async with Client(server) as client:
            with pytest.raises(ToolError) as caught:
                await client.call_tool("get_entity_memories", {"entity_id": 1})

        assert SECRET_USER_ID not in str(caught.value)
        assert GENERIC_FAILURE in str(caught.value)

    async def test_domain_message_is_kept(self):
        server = _entity_tools_server(NotFoundError("Entity 1 not found"))

        async with Client(server) as client:
            with pytest.raises(ToolError, match="Entity 1 not found"):
                await client.call_tool("get_entity", {"entity_id": 1})

    async def test_conflict_message_is_kept(self):
        server = _entity_tools_server(ConflictError("Relationship already exists"))

        async with Client(server) as client:
            with pytest.raises(ToolError, match="Relationship already exists"):
                await client.call_tool(
                    "create_entity_relationship",
                    {"source_entity_id": 1, "target_entity_id": 2, "relationship_type": "owns"},
                )


async def _noop(**_kwargs):
    return {}


def _registry_with_link_tools() -> ToolRegistry:
    registry = ToolRegistry()
    param = [ToolParameter(name="x", type="int", description="x", required=True)]
    for name, category, tags in [
        ("link_memories", ToolCategory.MEMORY, ["memory", "linking"]),
        ("link_entity_to_memory", ToolCategory.ENTITY, ["entity", "memory", "linking"]),
        ("link_skill_to_memory", ToolCategory.SKILL, ["skill", "memory", "linking"]),
        ("get_memory", ToolCategory.MEMORY, ["memory", "query"]),
        ("create_entity", ToolCategory.ENTITY, ["entity", "create"]),
    ]:
        registry.register(
            name=name,
            category=category,
            description=name,
            parameters=param,
            returns="dict",
            implementation=_noop,
            tags=tags,
        )
    return registry


class TestLinkingCategory:
    """The advertised ``linking`` category lists the tools tagged ``linking``."""

    def test_linking_category_returns_tagged_tools_across_categories(self):
        registry = _registry_with_link_tools()
        permitted = {meta.name for meta in registry.list_all_tools()}

        payload = build_discovery_payload(registry, permitted, "linking")

        names = {tool["name"] for tools in payload["tools_by_category"].values() for tool in tools}
        assert names == {"link_memories", "link_entity_to_memory", "link_skill_to_memory"}
        assert payload["total_count"] == 3
        assert payload["filtered_by"] == "linking"

    def test_linking_category_respects_permitted_tools(self):
        registry = _registry_with_link_tools()

        payload = build_discovery_payload(registry, {"link_memories", "get_memory"}, "linking")

        names = {tool["name"] for tools in payload["tools_by_category"].values() for tool in tools}
        assert names == {"link_memories"}

    def test_linking_is_case_insensitive_like_other_categories(self):
        registry = _registry_with_link_tools()
        permitted = {meta.name for meta in registry.list_all_tools()}

        payload = build_discovery_payload(registry, permitted, "LINKING")

        assert payload["total_count"] == 3

    def test_real_categories_are_unchanged(self):
        registry = _registry_with_link_tools()
        permitted = {meta.name for meta in registry.list_all_tools()}

        payload = build_discovery_payload(registry, permitted, "memory")

        names = {tool["name"] for tools in payload["tools_by_category"].values() for tool in tools}
        assert names == {"link_memories", "get_memory"}
        assert "linking" not in payload["categories_available"]


class TestRejectInvalidArgumentNames:
    """Argument names become keyword arguments; anything else is refused unseen."""

    @pytest.mark.parametrize(
        "arguments",
        [{}, {"query": 1}, {"memory_id": 1, "_private": 2, "ctx": 3}, {"naïve": 1}],
        ids=["empty", "plain", "underscore_and_ctx", "unicode_identifier"],
    )
    def test_valid_names_pass(self, arguments):
        reject_invalid_argument_names("get_memory", arguments)

    @pytest.mark.parametrize(
        "name",
        ["a\nb", "a\rb", "a\x1bb", "a b", "", "1a", "a-b", "a.b", 7, None],
        ids=["lf", "cr", "esc", "space", "empty", "digit_first", "dash", "dot", "int", "none"],
    )
    def test_invalid_names_are_refused_without_echo(self, name):
        arguments = {"ok": 1, name: 2}

        with pytest.raises(ToolError) as caught:
            reject_invalid_argument_names("get_memory", arguments)

        message = str(caught.value)
        assert "Invalid argument name" in message
        assert repr(name) not in message
        if isinstance(name, str) and name:
            assert name not in message
