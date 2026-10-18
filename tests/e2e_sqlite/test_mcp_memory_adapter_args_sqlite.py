"""E2E tests (in-memory SQLite) for argument handling in the memory tool adapters.

`execute_forgetful_tool` passes free-form arguments straight to the adapters, so the
adapters themselves must validate or coerce them. These tests drive the real stack
(FastMCP client -> registry -> adapter -> service -> SQLite) and cover:

- id lists given as a bare string/int, and tag filters given as a bare string
- numeric string / float / null values for limit, offset, k and importance
- boolean strings for include_obsolete
- unknown (misspelled) parameters on adapters that accept **kwargs
- case-insensitive and validated sort_by / sort_order
"""
import json
from uuid import uuid4

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def disable_auto_linking():
    """Keep manual link/unlink assertions free of auto-linking side effects"""
    from app.config.settings import settings
    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _exec(client, tool_name, arguments):
    return await client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


def _payload(result):
    return json.loads(result.content[0].text)


async def _create_memory(client, title, **extra):
    arguments = {
        "title": title,
        "content": f"content for {title}",
        "context": "adapter argument handling",
        "keywords": ["adapter-args"],
        "tags": ["adapter-args"],
        "importance": 5,
    }
    arguments.update(extra)
    return _payload(await _exec(client, "create_memory", arguments))["id"]


async def _create_projects(client, count):
    ids = []
    for i in range(count):
        result = await _exec(client, "create_project", {
            "name": f"adapter-args-project-{i}",
            "description": f"project {i}",
            "project_type": "development",
        })
        ids.append(_payload(result)["id"])
    return ids


async def _recent_ids(client, **arguments):
    result = await _exec(client, "get_recent_memories", arguments)
    return [m["id"] for m in _payload(result)["memories"]]


# ---------------------------------------------------------------------------
# id lists / tag filters must never be iterated character by character
# ---------------------------------------------------------------------------

async def test_string_project_id_is_coerced_not_split_into_characters(mcp_client):
    project_ids = await _create_projects(mcp_client, 12)
    assert project_ids == list(range(1, 13))

    created = await _exec(mcp_client, "create_memory", {
        "title": "string project id",
        "content": "created with project_ids given as the string '12'",
        "context": "adapter argument handling",
        "keywords": ["adapter-args"],
        "tags": ["adapter-args"],
        "importance": 5,
        "project_ids": "12",
    })

    assert _payload(created)["project_ids"] == [12]


async def test_scalar_int_project_id_is_coerced(mcp_client):
    project_ids = await _create_projects(mcp_client, 3)

    created = await _exec(mcp_client, "create_memory", {
        "title": "scalar project id",
        "content": "created with project_ids given as a bare integer",
        "context": "adapter argument handling",
        "keywords": ["adapter-args"],
        "tags": ["adapter-args"],
        "importance": 5,
        "project_ids": project_ids[2],
    })

    assert _payload(created)["project_ids"] == [project_ids[2]]


async def test_non_numeric_project_ids_are_rejected(mcp_client):
    with pytest.raises(ToolError, match="project_ids"):
        await _exec(mcp_client, "create_memory", {
            "title": "bad project id",
            "content": "project_ids is not a number",
            "context": "adapter argument handling",
            "keywords": ["adapter-args"],
            "tags": ["adapter-args"],
            "importance": 5,
            "project_ids": "abc",
        })


async def test_get_recent_memories_string_project_id_filters_on_that_project(mcp_client):
    project_ids = await _create_projects(mcp_client, 12)
    in_project_12 = await _create_memory(mcp_client, "in 12", project_ids=[project_ids[11]])
    await _create_memory(mcp_client, "in 1", project_ids=[project_ids[0]])
    await _create_memory(mcp_client, "in 2", project_ids=[project_ids[1]])

    assert await _recent_ids(mcp_client, project_ids="12") == [in_project_12]


async def test_query_memory_string_project_id_filters_on_that_project(mcp_client):
    project_ids = await _create_projects(mcp_client, 12)
    in_project_12 = await _create_memory(mcp_client, "in 12", project_ids=[project_ids[11]])
    in_project_1 = await _create_memory(mcp_client, "in 1", project_ids=[project_ids[0]])

    result = await _exec(mcp_client, "query_memory", {
        "query": "content for in",
        "query_context": "adapter argument handling",
        "k": 10,
        "project_ids": "12",
        "strict_project_filter": True,
    })

    returned = {m["id"] for m in _payload(result)["primary_memories"]}
    assert in_project_12 in returned
    assert in_project_1 not in returned


async def test_get_recent_memories_tags_filter_matches_whole_tags(mcp_client):
    await _create_memory(mcp_client, "tag a", tags=["a"])
    tagged_ai = await _create_memory(mcp_client, "tag ai", tags=["ai"])

    assert await _recent_ids(mcp_client, tags=["ai"]) == [tagged_ai]


@pytest.mark.parametrize("bad_tags", ["ai", [1, 2], {"ai": 1}], ids=["str", "ints", "dict"])
async def test_get_recent_memories_rejects_tags_that_are_not_a_list_of_strings(mcp_client, bad_tags):
    await _create_memory(mcp_client, "tag a", tags=["a"])

    with pytest.raises(ToolError, match="tags must be a list of strings"):
        await _exec(mcp_client, "get_recent_memories", {"tags": bad_tags})


# ---------------------------------------------------------------------------
# numeric arguments: coerced like ids, clear errors otherwise (no raw TypeError)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("arguments", "expected_count"),
    [
        ({"limit": "2"}, 2),
        ({"limit": 2.0}, 2),
        ({"offset": "1"}, 2),
        ({"offset": 1.0}, 2),
        ({"limit": " 1 ", "offset": "1"}, 1),
    ],
    ids=["limit-str", "limit-float", "offset-str", "offset-float", "both-str"],
)
async def test_get_recent_memories_coerces_numeric_pagination(mcp_client, arguments, expected_count):
    for i in range(3):
        await _create_memory(mcp_client, f"pagination {i}")

    assert len(await _recent_ids(mcp_client, **arguments)) == expected_count


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"limit": None}, "limit cannot be None"),
        ({"limit": "abc"}, "limit must be a valid integer"),
        ({"limit": 2.5}, "limit must be an integer"),
        ({"limit": True}, "limit must be an integer"),
        ({"offset": "x"}, "offset must be a valid integer"),
    ],
    ids=["limit-null", "limit-text", "limit-fraction", "limit-bool", "offset-text"],
)
async def test_get_recent_memories_rejects_invalid_pagination_with_clear_error(mcp_client, arguments, message):
    with pytest.raises(ToolError, match=message) as excinfo:
        await _exec(mcp_client, "get_recent_memories", arguments)

    assert "not supported between" not in str(excinfo.value)


async def test_query_memory_accepts_numeric_strings_for_k_and_importance_threshold(mcp_client):
    memory_id = await _create_memory(mcp_client, "query numeric strings", importance=9)

    result = await _exec(mcp_client, "query_memory", {
        "query": "content for query numeric strings",
        "query_context": "adapter argument handling",
        "k": "5",
        "importance_threshold": "7",
    })

    assert memory_id in {m["id"] for m in _payload(result)["primary_memories"]}


async def test_query_memory_rejects_non_numeric_k(mcp_client):
    with pytest.raises(ToolError, match="k must be a valid integer"):
        await _exec(mcp_client, "query_memory", {
            "query": "anything",
            "query_context": "adapter argument handling",
            "k": "many",
        })


async def test_update_memory_accepts_numeric_string_importance(mcp_client):
    memory_id = await _create_memory(mcp_client, "update importance", importance=3)

    updated = await _exec(mcp_client, "update_memory", {"memory_id": memory_id, "importance": "8"})

    assert _payload(updated)["importance"] == 8


async def test_update_memory_rejects_non_numeric_importance_and_changes_nothing(mcp_client):
    memory_id = await _create_memory(mcp_client, "update bad importance", importance=3)

    with pytest.raises(ToolError, match="importance must be a valid integer"):
        await _exec(mcp_client, "update_memory", {
            "memory_id": memory_id,
            "title": "should not be applied",
            "importance": "high",
        })

    current = _payload(await _exec(mcp_client, "get_memory", {"memory_id": memory_id}))
    assert current["title"] == "update bad importance"
    assert current["importance"] == 3


# ---------------------------------------------------------------------------
# include_obsolete: textual booleans must be parsed, not treated as truthy
# ---------------------------------------------------------------------------

@pytest.fixture
async def obsolete_memory_id(mcp_client):
    memory_id = await _create_memory(mcp_client, "obsolete memory")
    await _exec(mcp_client, "mark_memory_obsolete", {"memory_id": memory_id, "reason": "test"})
    return memory_id


@pytest.mark.parametrize(
    "value",
    [False, 0, "false", "False", "FALSE", " false ", "0", "no", "off", None],
)
async def test_include_obsolete_false_values_hide_obsolete_memories(mcp_client, obsolete_memory_id, value):
    assert await _recent_ids(mcp_client, include_obsolete=value) == []


@pytest.mark.parametrize("value", [True, 1, "true", "True", "TRUE", "1", "yes", "on"])
async def test_include_obsolete_true_values_show_obsolete_memories(mcp_client, obsolete_memory_id, value):
    assert await _recent_ids(mcp_client, include_obsolete=value) == [obsolete_memory_id]


@pytest.mark.parametrize("value", ["maybe", "", 2, [], {}])
async def test_include_obsolete_rejects_values_that_are_not_boolean(mcp_client, obsolete_memory_id, value):
    with pytest.raises(ToolError, match="include_obsolete must be a boolean"):
        await _exec(mcp_client, "get_recent_memories", {"include_obsolete": value})


# ---------------------------------------------------------------------------
# unknown parameters are rejected instead of being silently dropped
# ---------------------------------------------------------------------------

async def test_mark_memory_obsolete_rejects_misspelled_superseded_by_and_changes_nothing(mcp_client):
    old_id = await _create_memory(mcp_client, "old")
    new_id = await _create_memory(mcp_client, "new")

    with pytest.raises(ToolError, match="superseded_by_id"):
        await _exec(mcp_client, "mark_memory_obsolete", {
            "memory_id": old_id,
            "reason": "replaced",
            "superseded_by_id": new_id,
        })

    assert _payload(await _exec(mcp_client, "get_memory", {"memory_id": old_id}))["is_obsolete"] is False


async def test_mark_memory_obsolete_still_records_documented_superseded_by(mcp_client):
    old_id = await _create_memory(mcp_client, "old documented")
    new_id = await _create_memory(mcp_client, "new documented")

    await _exec(mcp_client, "mark_memory_obsolete", {
        "memory_id": old_id,
        "reason": "replaced",
        "superseded_by": new_id,
    })

    old = _payload(await _exec(mcp_client, "get_memory", {"memory_id": old_id}))
    assert old["is_obsolete"] is True
    assert old["superseded_by"] == new_id


async def test_update_memory_rejects_unknown_parameters_naming_all_of_them(mcp_client):
    memory_id = await _create_memory(mcp_client, "update unknown", tags=["keep"], importance=5)

    with pytest.raises(ToolError, match="importance_level, tag"):
        await _exec(mcp_client, "update_memory", {
            "memory_id": memory_id,
            "tag": ["zzz"],
            "importance_level": 9,
        })

    current = _payload(await _exec(mcp_client, "get_memory", {"memory_id": memory_id}))
    assert current["tags"] == ["keep"]
    assert current["importance"] == 5


async def test_update_memory_does_not_pretend_to_support_skill_ids(mcp_client):
    memory_id = await _create_memory(mcp_client, "update skill ids")

    with pytest.raises(ToolError, match="skill_ids"):
        await _exec(mcp_client, "update_memory", {"memory_id": memory_id, "skill_ids": [1]})


@pytest.mark.parametrize(
    "tool_name",
    ["get_memory", "unobsolete_memory", "link_memories", "unlink_memories"],
)
async def test_other_kwargs_adapters_reject_unknown_parameters(mcp_client, tool_name):
    first = await _create_memory(mcp_client, "first")
    second = await _create_memory(mcp_client, "second")
    arguments = {"memory_id": first, "bogus_param": 1}
    if tool_name == "link_memories":
        arguments["related_ids"] = [second]
    if tool_name == "unlink_memories":
        arguments["target_id"] = second

    with pytest.raises(ToolError, match="bogus_param"):
        await _exec(mcp_client, tool_name, arguments)


async def test_documented_aliases_are_still_accepted(mcp_client):
    first = await _create_memory(mcp_client, "alias first")
    second = await _create_memory(mcp_client, "alias second")

    fetched = await _exec(mcp_client, "get_memory", {"id": first})
    assert _payload(fetched)["id"] == first

    updated = await _exec(mcp_client, "update_memory", {"id": first, "title": "alias renamed"})
    assert _payload(updated)["title"] == "alias renamed"

    linked = await _exec(mcp_client, "link_memories", {"source_id": first, "target_id": second})
    assert second in _payload(linked)["linked_memory_ids"]

    unlinked = await _exec(mcp_client, "unlink_memories", {"source_id": first, "target_id": second})
    assert _payload(unlinked)["success"] is True

    assert _payload(await _exec(mcp_client, "mark_memory_obsolete", {"id": first, "reason": "alias"}))["success"]
    assert _payload(await _exec(mcp_client, "unobsolete_memory", {"id": first}))["success"]


# ---------------------------------------------------------------------------
# sort_by / sort_order: case-insensitive, validated, never silently reversed
# ---------------------------------------------------------------------------

@pytest.fixture
async def three_memories(mcp_client):
    """Memories created oldest to newest with importance 3, 9 and 6."""
    return [
        await _create_memory(mcp_client, f"sort {i}", importance=importance)
        for i, importance in enumerate((3, 9, 6))
    ]


@pytest.mark.parametrize("sort_order", ["desc", "DESC", "Desc", " desc ", "desc\n"])
async def test_sort_order_desc_is_case_insensitive_and_returns_newest_first(mcp_client, three_memories, sort_order):
    assert await _recent_ids(mcp_client, sort_order=sort_order) == three_memories[::-1]


@pytest.mark.parametrize("sort_order", ["asc", "ASC", " Asc "])
async def test_sort_order_asc_is_case_insensitive_and_returns_oldest_first(mcp_client, three_memories, sort_order):
    assert await _recent_ids(mcp_client, sort_order=sort_order) == three_memories


async def test_sort_by_is_case_insensitive(mcp_client, three_memories):
    first, second, third = three_memories

    ids = await _recent_ids(mcp_client, sort_by="Importance", sort_order="DESC")

    assert ids == [second, third, first]


@pytest.mark.parametrize("sort_order", ["descending", "newest", "", None, 5])
async def test_invalid_sort_order_is_rejected(mcp_client, three_memories, sort_order):
    with pytest.raises(ToolError, match="sort_order must be one of: asc, desc"):
        await _exec(mcp_client, "get_recent_memories", {"sort_order": sort_order})


@pytest.mark.parametrize("sort_by", ["bogus", "createdat", "", None, 5])
async def test_invalid_sort_by_is_rejected(mcp_client, three_memories, sort_by):
    with pytest.raises(ToolError, match="sort_by must be one of: created_at, updated_at, importance"):
        await _exec(mcp_client, "get_recent_memories", {"sort_by": sort_by})


@pytest.mark.parametrize(
    ("sort_by", "sort_order", "message"),
    [
        ("bogus", "desc", "sort_by must be one of"),
        ("created_at", "DESC", "sort_order must be one of"),
        ("created_at", "newest", "sort_order must be one of"),
    ],
)
async def test_repository_refuses_unknown_sort_options_instead_of_falling_back(
    mcp_client, sqlite_app, sort_by, sort_order, message,
):
    # mcp_client starts the app lifespan, which attaches the services
    repo = sqlite_app.memory_service.memory_repo

    with pytest.raises(ValueError, match=message):
        await repo.list_memories(user_id=uuid4(), limit=10, sort_by=sort_by, sort_order=sort_order)
