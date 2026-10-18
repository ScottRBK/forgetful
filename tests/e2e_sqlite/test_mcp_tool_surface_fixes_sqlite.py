"""E2E tests for MCP tool-surface argument validation with in-memory SQLite

Covers the document, code artifact, entity, file and project tools reached through
``execute_forgetful_tool``, plus the unmounted legacy skill link/unlink tools.
"""
import base64

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from app.routes.mcp import skill_tools

FILE_DATA = base64.b64encode(b"hello").decode("utf-8")


async def call(client, tool_name, **arguments):
    return await client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


async def make_document(client, tags=None, **extra):
    result = await call(
        client, "create_document", title="doc", description="d", content="c",
        document_type="text", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_code_artifact(client, tags=None, **extra):
    result = await call(
        client, "create_code_artifact", title="art", description="d", code="print(1)",
        language="python", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_entity(client, name="ent", tags=None, **extra):
    result = await call(
        client, "create_entity", name=name, entity_type="Organization", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_file(client, tags=None, **extra):
    result = await call(
        client, "create_file", filename="f.txt", description="d", data=FILE_DATA,
        mime_type="text/plain", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_project(client, name="proj"):
    result = await call(
        client, "create_project", name=name, description="d", project_type="development",
    )
    return result.data["id"]


async def make_memory(client):
    result = await call(
        client, "create_memory", title="m", content="c", context="ctx",
        keywords=["k"], tags=["t"], importance=7,
    )
    return result.data["id"]


# (create helper, get tool, id parameter, [(tool, extra arguments)])
ID_TOOL_CASES = [
    pytest.param(
        make_document, "get_document", "document_id",
        [("get_document", {}), ("update_document", {"title": "changed"}),
         ("delete_document", {})],
        id="document",
    ),
    pytest.param(
        make_code_artifact, "get_code_artifact", "artifact_id",
        [("get_code_artifact", {}), ("update_code_artifact", {"title": "changed"}),
         ("delete_code_artifact", {})],
        id="code_artifact",
    ),
    pytest.param(
        make_entity, "get_entity", "entity_id",
        [("get_entity", {}), ("update_entity", {"name": "changed"}),
         ("delete_entity", {}), ("get_entity_relationships", {}),
         ("get_entity_memories", {})],
        id="entity",
    ),
    pytest.param(
        make_file, "get_file", "file_id",
        [("get_file", {}), ("update_file", {"filename": "changed.txt"}),
         ("delete_file", {})],
        id="file",
    ),
]

INVALID_IDS = [True, 1.9, "not-an-id", [1], {"id": 1}, None]


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_id", INVALID_IDS, ids=repr)
@pytest.mark.parametrize(("create", "get_tool", "id_arg", "tools"), ID_TOOL_CASES)
async def test_tools_reject_invalid_ids_and_leave_object_intact(
    mcp_client, create, get_tool, id_arg, tools, invalid_id,
):
    """Invalid ids give a parameter error (like the project tools) and delete nothing."""
    object_id = await create(mcp_client)
    assert object_id == 1

    for tool_name, extra in tools:
        with pytest.raises(ToolError, match=f"{id_arg} (must|cannot)") as excinfo:
            await call(mcp_client, tool_name, **{id_arg: invalid_id}, **extra)
        message = str(excinfo.value)
        assert "[SQL:" not in message
        assert "[parameters:" not in message

    survivor = await call(mcp_client, get_tool, **{id_arg: object_id})
    assert survivor.data["id"] == object_id


@pytest.mark.asyncio
async def test_numeric_string_and_integral_float_ids_are_accepted(mcp_client):
    """'1' and 1.0 identify object 1, just as they do for the project tools."""
    document_id = await make_document(mcp_client)
    entity_id = await make_entity(mcp_client)

    assert (await call(mcp_client, "get_document", document_id=str(document_id))).data["id"] == 1
    assert (await call(mcp_client, "get_entity", entity_id=float(entity_id))).data["id"] == 1

    deleted = await call(mcp_client, "delete_document", document_id=f" {document_id} ")
    assert deleted.data["success"] is True
    assert deleted.data["deleted_id"] == document_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "arguments", "param"),
    [
        ("link_entity_to_memory", {"entity_id": 1, "memory_id": True}, "memory_id"),
        ("unlink_entity_from_memory", {"entity_id": True, "memory_id": 1}, "entity_id"),
        ("link_entity_to_project", {"entity_id": 1, "project_id": True}, "project_id"),
        ("unlink_entity_from_project", {"entity_id": 1, "project_id": 1.5}, "project_id"),
        (
            "create_entity_relationship",
            {"source_entity_id": True, "target_entity_id": 2, "relationship_type": "knows"},
            "source_entity_id",
        ),
        (
            "create_entity_relationship",
            {"source_entity_id": 1, "target_entity_id": "x", "relationship_type": "knows"},
            "target_entity_id",
        ),
        ("update_entity_relationship", {"relationship_id": True, "strength": 0.5},
         "relationship_id"),
        ("delete_entity_relationship", {"relationship_id": True}, "relationship_id"),
        ("get_memory_entities", {"memory_id": True}, "memory_id"),
    ],
)
async def test_entity_link_and_relationship_tools_reject_invalid_ids(
    mcp_client, tool_name, arguments, param,
):
    await make_entity(mcp_client, name="one")
    await make_entity(mcp_client, name="two")
    await make_project(mcp_client)
    await make_memory(mcp_client)

    with pytest.raises(ToolError, match=f"{param} (must|cannot)"):
        await call(mcp_client, tool_name, **arguments)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "extra"),
    [
        ("create_document", {"title": "t", "description": "d", "content": "c"}),
        ("create_code_artifact",
         {"title": "t", "description": "d", "code": "x", "language": "python"}),
        ("create_file",
         {"filename": "f.txt", "description": "d", "data": FILE_DATA,
          "mime_type": "text/plain"}),
        ("create_entity", {"name": "n", "entity_type": "Organization"}),
    ],
)
async def test_create_tools_reject_boolean_project_reference(mcp_client, tool_name, extra):
    """project_id=True must not silently link the new object to project 1."""
    await make_project(mcp_client)
    argument = "project_ids" if tool_name == "create_entity" else "project_id"
    value = [True] if tool_name == "create_entity" else True

    with pytest.raises(ToolError, match=f"{argument} (must|cannot)"):
        await call(mcp_client, tool_name, **extra, **{argument: value})


@pytest.mark.asyncio
async def test_update_tools_reject_boolean_project_reference(mcp_client):
    await make_project(mcp_client)
    document_id = await make_document(mcp_client)
    entity_id = await make_entity(mcp_client)

    with pytest.raises(ToolError, match="project_id (must|cannot)"):
        await call(mcp_client, "update_document", document_id=document_id, project_id=True)
    with pytest.raises(ToolError, match="project_ids (must|cannot)"):
        await call(mcp_client, "update_entity", entity_id=entity_id, project_ids=[True])

    document = await call(mcp_client, "get_document", document_id=document_id)
    assert document.data["project_id"] is None


@pytest.mark.asyncio
async def test_list_id_does_not_leak_sql_or_user_id(mcp_client):
    """A list id is a parameter error, not a driver error echoing statement and user id."""
    await make_entity(mcp_client)

    with pytest.raises(ToolError) as excinfo:
        await call(mcp_client, "get_entity", entity_id=[1])

    message = str(excinfo.value)
    assert "entity_id" in message
    assert "SELECT" not in message
    assert "[parameters:" not in message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("make", "list_tool", "key"),
    [
        (make_document, "list_documents", "documents"),
        (make_code_artifact, "list_code_artifacts", "code_artifacts"),
        (make_entity, "list_entities", "entities"),
        (make_file, "list_files", "files"),
    ],
)
async def test_list_tools_treat_scalar_tags_string_as_one_tag(mcp_client, make, list_tool, key):
    """tags='adr' filters on the tag 'adr' instead of the letters 'a', 'd', 'r'."""
    await make(mcp_client, tags=["adr"])
    await make(mcp_client, tags=["other"])

    as_list = await call(mcp_client, list_tool, tags=["adr"])
    as_string = await call(mcp_client, list_tool, tags="adr")

    assert as_list.data["total_count"] == 1
    assert as_string.data["total_count"] == 1
    assert as_string.data[key][0]["tags"] == ["adr"]

    with pytest.raises(ToolError, match="tags must be a list of strings"):
        await call(mcp_client, list_tool, tags=5)


@pytest.mark.asyncio
async def test_search_entities_treats_scalar_tags_string_as_one_tag(mcp_client):
    await make_entity(mcp_client, name="Acme Tagged", tags=["adr"])
    await make_entity(mcp_client, name="Acme Plain", tags=["other"])

    result = await call(mcp_client, "search_entities", query="Acme", tags="adr")

    assert [entity["name"] for entity in result.data["entities"]] == ["Acme Tagged"]
    assert result.data["filters"]["tags"] == ["adr"]


@pytest.mark.asyncio
async def test_list_filters_validate_project_ids_and_project_id(mcp_client):
    """Scalar project ids work as one-item lists and bad ids are parameter errors."""
    project_id = await make_project(mcp_client)
    await make_entity(mcp_client, name="in project", project_ids=[project_id])
    await make_entity(mcp_client, name="no project")
    await make_document(mcp_client, project_id=project_id)
    await make_document(mcp_client)

    scalar = await call(mcp_client, "list_entities", project_ids=str(project_id))
    listed = await call(mcp_client, "list_entities", project_ids=[project_id])
    assert scalar.data["total_count"] == 1
    assert listed.data["total_count"] == 1

    with pytest.raises(ToolError, match="project_ids (must|cannot)"):
        await call(mcp_client, "list_entities", project_ids=[True])
    with pytest.raises(ToolError, match="project_id (must|cannot)"):
        await call(mcp_client, "list_documents", project_id=True)
    with pytest.raises(ToolError, match="project_id (must|cannot)"):
        await call(mcp_client, "list_code_artifacts", project_id=1.5)
    with pytest.raises(ToolError, match="project_id (must|cannot)"):
        await call(mcp_client, "list_files", project_id="x")

    by_project = await call(mcp_client, "list_documents", project_id=str(project_id))
    assert by_project.data["total_count"] == 1


@pytest.mark.asyncio
async def test_search_entities_limit_is_clamped_to_documented_range(mcp_client):
    """limit is 1-100: negative and zero give one result, large values stop at 100."""
    for number in range(105):
        await make_entity(mcp_client, name=f"Acme Widget {number:03d}")

    async def search(**arguments):
        result = await call(mcp_client, "search_entities", query="Acme", **arguments)
        return len(result.data["entities"]), result.data["filters"]["limit"]

    assert await search(limit=-1) == (1, 1)
    assert await search(limit=0) == (1, 1)
    assert await search(limit=5) == (5, 5)
    assert await search(limit=100) == (100, 100)
    assert await search(limit=150) == (100, 100)
    assert await search(limit=100000) == (100, 100)
    assert await search(limit="7") == (7, 7)
    assert await search() == (20, 20)

    with pytest.raises(ToolError, match="limit (must|cannot)"):
        await call(mcp_client, "search_entities", query="Acme", limit=True)


@pytest.mark.asyncio
async def test_update_project_missing_project_is_not_found_error(mcp_client):
    """Updating a project that does not exist is an error, not a successful null result."""
    with pytest.raises(ToolError, match="Project with id 99999 not found"):
        await call(mcp_client, "update_project", project_id=99999, name="x")


@pytest.mark.asyncio
async def test_update_project_existing_project_still_updates(mcp_client):
    project_id = await make_project(mcp_client)

    updated = await call(mcp_client, "update_project", project_id=project_id, name="renamed")

    assert updated.data["id"] == project_id
    assert updated.data["name"] == "renamed"


@pytest.mark.asyncio
async def test_get_entity_relationships_direction_is_normalised_or_rejected(mcp_client):
    """Entity 2 has one incoming and one outgoing edge; direction narrows or errors."""
    first = await make_entity(mcp_client, name="first")
    middle = await make_entity(mcp_client, name="middle")
    last = await make_entity(mcp_client, name="last")
    for source, target in ((first, middle), (middle, last)):
        await call(
            mcp_client, "create_entity_relationship", source_entity_id=source,
            target_entity_id=target, relationship_type="manages",
        )

    async def count(direction):
        result = await call(
            mcp_client, "get_entity_relationships", entity_id=middle, direction=direction,
        )
        return len(result.data["relationships"])

    assert await count("incoming") == 1
    assert await count("outgoing") == 1
    assert await count("Incoming") == 1
    assert await count("OUTGOING") == 1
    assert await count("both") == 2
    assert await count(None) == 2

    for unknown in ("sideways", "in"):
        with pytest.raises(ToolError, match="direction"):
            await count(unknown)


@pytest.fixture
async def legacy_skill_client(sqlite_app, mcp_client):
    """The unmounted legacy skill tool module wired to the real services."""
    legacy = FastMCP("legacy-skill-tools")
    legacy.user_service = sqlite_app.user_service
    legacy.skill_service = sqlite_app.skill_service
    skill_tools.register(legacy)
    async with Client(legacy) as client:
        yield client


@pytest.mark.asyncio
async def test_legacy_skill_unlink_reports_whether_a_link_was_removed(
    legacy_skill_client, mcp_client,
):
    """The legacy tools return the service confirmation, not an always-truthy wrapper."""
    skill = await call(
        mcp_client, "create_skill", name="legacy-skill", description="d", content="# body",
    )
    skill_id = skill.data["id"]
    memory_id = await make_memory(mcp_client)

    linked = await legacy_skill_client.call_tool(
        "link_skill_to_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    assert linked.data["skill_id"] == skill_id
    assert linked.data["memory_id"] == memory_id
    assert "success" not in linked.data

    first = await legacy_skill_client.call_tool(
        "unlink_skill_from_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    second = await legacy_skill_client.call_tool(
        "unlink_skill_from_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    assert first.data["unlinked"] is True
    assert second.data["unlinked"] is False

    never_linked = await legacy_skill_client.call_tool(
        "unlink_skill_from_file", {"skill_id": skill_id, "file_id": 999},
    )
    assert never_linked.data["unlinked"] is False
    assert never_linked.data["file_id"] == 999
