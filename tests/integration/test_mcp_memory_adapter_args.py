"""Integration tests for argument handling in the memory tool adapters.

Covers the coercion helpers, the sort option validation in MemoryService.list_memories
(shared by the MCP adapter, the REST routes and the CLI), and a guard that rejecting
unknown parameters never rejects a parameter documented in the tool metadata.
"""
import inspect
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.memory_models import (
    VALID_SORT_BY,
    VALID_SORT_ORDER,
    MemoryCreate,
)
from app.routes.api import memories as memories_routes
from app.routes.mcp.tool_adapters import (
    _coerce_bool,
    _coerce_int,
    _coerce_str_list,
    _reject_unknown_args,
    create_memory_adapters,
)
from app.routes.mcp.tool_metadata_registry import register_memory_tools_metadata
from app.routes.mcp.tool_registry import ToolRegistry

# ---------------------------------------------------------------------------
# coercion helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [(5, 5), ("5", 5), (" 5 ", 5), (5.0, 5), (-3, -3), ("-3", -3)],
)
def test_coerce_int_accepts_integral_values(value, expected):
    assert _coerce_int(value, "limit") == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "limit cannot be None"),
        (True, "limit must be an integer"),
        (2.5, "limit must be an integer"),
        (float("nan"), "limit must be an integer"),
        ("", "limit cannot be empty string"),
        ("abc", "limit must be a valid integer"),
        ("1.5", "limit must be a valid integer"),
        ([1], "limit must be an integer"),
    ],
)
def test_coerce_int_rejects_everything_else_naming_the_parameter(value, message):
    with pytest.raises(ValueError, match=message):
        _coerce_int(value, "limit")


@pytest.mark.parametrize(
    "value",
    [False, 0, "false", "False", "FALSE", " false ", "0", "no", "off", "f", "n"],
)
def test_coerce_bool_false_spellings(value):
    assert _coerce_bool(value, "include_obsolete") is False


@pytest.mark.parametrize(
    "value",
    [True, 1, "true", "True", "TRUE", " true ", "1", "yes", "on", "t", "y"],
)
def test_coerce_bool_true_spellings(value):
    assert _coerce_bool(value, "include_obsolete") is True


@pytest.mark.parametrize("value", [None, "", "maybe", 2, -1, 1.0, [], {}])
def test_coerce_bool_rejects_non_boolean_values(value):
    with pytest.raises(ValueError, match="include_obsolete must be a boolean"):
        _coerce_bool(value, "include_obsolete")


def test_coerce_str_list_accepts_collections_of_strings():
    assert _coerce_str_list(["a", "ai"], "tags") == ["a", "ai"]
    assert _coerce_str_list(("a",), "tags") == ["a"]
    assert _coerce_str_list([], "tags") == []


@pytest.mark.parametrize("value", ["ai", b"ai", [1, 2], ["a", 1], {"a": 1}, 5])
def test_coerce_str_list_rejects_a_bare_string_and_non_string_items(value):
    with pytest.raises(ValueError, match="tags must be a list of strings"):
        _coerce_str_list(value, "tags")


def test_reject_unknown_args_is_silent_without_extras():
    _reject_unknown_args("get_memory", {})


def test_reject_unknown_args_names_every_unexpected_parameter_sorted():
    with pytest.raises(ValueError, match=r"update_memory got unexpected parameter\(s\): bar, foo"):
        _reject_unknown_args("update_memory", {"foo": 1, "bar": 2})


# ---------------------------------------------------------------------------
# sort option validation in MemoryService.list_memories
# ---------------------------------------------------------------------------


async def _seed(service, user_id, importances=(3, 9, 6)):
    """Create memories oldest to newest; the stub repository stamps increasing created_at values"""
    ids = []
    for i, importance in enumerate(importances):
        memory, _ = await service.create_memory(
            user_id=user_id,
            memory_data=MemoryCreate(
                title=f"sort probe {i}",
                content=f"content {i}",
                context="sort validation",
                keywords=["sort"],
                tags=["sort"],
                importance=importance,
            ),
        )
        ids.append(memory.id)
    return ids


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["desc", "DESC", "Desc", " desc ", "\tdesc\n"])
async def test_list_memories_normalises_descending_sort_order(test_memory_service, sort_order):
    user_id = uuid4()
    ids = await _seed(test_memory_service, user_id)

    memories, total = await test_memory_service.list_memories(user_id=user_id, sort_order=sort_order)

    assert [m.id for m in memories] == ids[::-1]
    assert total == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["asc", "ASC", " Asc "])
async def test_list_memories_normalises_ascending_sort_order(test_memory_service, sort_order):
    user_id = uuid4()
    ids = await _seed(test_memory_service, user_id)

    memories, _ = await test_memory_service.list_memories(user_id=user_id, sort_order=sort_order)

    assert [m.id for m in memories] == ids


@pytest.mark.asyncio
async def test_list_memories_normalises_sort_by(test_memory_service):
    user_id = uuid4()
    first, second, third = await _seed(test_memory_service, user_id)

    memories, _ = await test_memory_service.list_memories(
        user_id=user_id, sort_by="Importance", sort_order="DESC",
    )

    assert [m.id for m in memories] == [second, third, first]


@pytest.mark.asyncio
async def test_list_memories_passes_only_normalised_sort_options_to_the_repository(test_memory_service):
    seen = {}

    async def fake_list_memories(**kwargs):
        seen.update(kwargs)
        return [], 0

    test_memory_service.memory_repo.list_memories = fake_list_memories

    await test_memory_service.list_memories(
        user_id=uuid4(), sort_by=" Updated_At ", sort_order=" ASC ",
    )

    assert seen["sort_by"] == "updated_at"
    assert seen["sort_order"] == "asc"


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["descending", "newest", "", None, 5])
async def test_list_memories_rejects_invalid_sort_order(test_memory_service, sort_order):
    with pytest.raises(ValueError, match="sort_order must be one of: asc, desc"):
        await test_memory_service.list_memories(user_id=uuid4(), sort_order=sort_order)


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_by", ["bogus", "createdat", "", None, 5])
async def test_list_memories_rejects_invalid_sort_by(test_memory_service, sort_by):
    with pytest.raises(ValueError, match="sort_by must be one of: created_at, updated_at, importance"):
        await test_memory_service.list_memories(user_id=uuid4(), sort_by=sort_by)


def test_shared_sort_constants_match_the_rest_route():
    assert set(VALID_SORT_BY) == memories_routes.VALID_SORT_BY
    assert set(VALID_SORT_ORDER) == memories_routes.VALID_SORT_ORDER


# ---------------------------------------------------------------------------
# rejecting unknown parameters must never reject a documented parameter
# ---------------------------------------------------------------------------


def test_every_documented_memory_tool_parameter_is_accepted_by_its_adapter():
    adapters = create_memory_adapters(MagicMock(), MagicMock(), MagicMock())
    registry = ToolRegistry()
    register_memory_tools_metadata(registry, adapters)

    rejected = {}
    for name in adapters:
        tool = registry.get_tool(name)
        accepted = inspect.signature(tool.implementation).parameters
        missing = [p.name for p in tool.metadata.parameters if p.name not in accepted]
        if missing:
            rejected[name] = missing

    assert rejected == {}
