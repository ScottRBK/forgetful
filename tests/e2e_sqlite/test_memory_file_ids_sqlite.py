"""E2E tests for file_ids on MCP create_memory / update_memory (issue #76)"""

import base64

import pytest

TINY_PNG_B64 = base64.b64encode(
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
).decode("utf-8")

MISSING_FILE_ID = 999999


async def _call(mcp_client, tool_name, arguments):
    return await mcp_client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


async def _create_file(mcp_client, filename):
    result = await _call(
        mcp_client,
        "create_file",
        {
            "filename": filename,
            "description": f"Attachment {filename}",
            "data": TINY_PNG_B64,
            "mime_type": "image/png",
        },
    )
    return result.data["id"]


async def _create_memory(mcp_client, title, file_ids=None):
    arguments = {
        "title": title,
        "content": f"Memory body for {title}",
        "context": "Testing MCP file_ids parity with REST",
        "keywords": ["file", "attachment"],
        "tags": ["test"],
        "importance": 6,
    }
    if file_ids is not None:
        arguments["file_ids"] = file_ids
    return await _call(mcp_client, "create_memory", arguments)


async def _get_file_ids(mcp_client, memory_id):
    result = await _call(mcp_client, "get_memory", {"memory_id": memory_id})
    return result.data["file_ids"]


def _param_names(result):
    return [param["name"] for param in result.data["parameters"]]


@pytest.mark.asyncio
async def test_create_memory_with_file_ids_e2e(mcp_client):
    file_id = await _create_file(mcp_client, "create-link.png")

    created = await _create_memory(mcp_client, "Create with file", [file_id])

    assert created.data["file_ids"] == [file_id]
    assert await _get_file_ids(mcp_client, created.data["id"]) == [file_id]


@pytest.mark.asyncio
async def test_update_memory_file_ids_replaces_e2e(mcp_client):
    first_id = await _create_file(mcp_client, "replace-first.png")
    second_id = await _create_file(mcp_client, "replace-second.png")
    created = await _create_memory(mcp_client, "Replace file link", [first_id])

    await _call(
        mcp_client,
        "update_memory",
        {"memory_id": created.data["id"], "file_ids": [second_id]},
    )

    assert await _get_file_ids(mcp_client, created.data["id"]) == [second_id]


@pytest.mark.asyncio
async def test_update_memory_empty_file_ids_clears_e2e(mcp_client):
    file_id = await _create_file(mcp_client, "clear-link.png")
    created = await _create_memory(mcp_client, "Clear file link", [file_id])

    updated = await _call(
        mcp_client, "update_memory", {"memory_id": created.data["id"], "file_ids": []},
    )

    assert updated.data["file_ids"] == []
    assert await _get_file_ids(mcp_client, created.data["id"]) == []


@pytest.mark.asyncio
async def test_update_memory_without_file_ids_preserves_links_e2e(mcp_client):
    file_id = await _create_file(mcp_client, "preserve-link.png")
    created = await _create_memory(mcp_client, "Preserve file link", [file_id])

    await _call(
        mcp_client,
        "update_memory",
        {"memory_id": created.data["id"], "title": "Preserve file link renamed"},
    )

    assert await _get_file_ids(mcp_client, created.data["id"]) == [file_id]


@pytest.mark.asyncio
async def test_create_memory_unknown_file_id_fails_e2e(mcp_client):
    with pytest.raises(Exception) as exc_info:
        await _create_memory(mcp_client, "Unknown file on create", [MISSING_FILE_ID])

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_memory_unknown_file_id_fails_and_keeps_links_e2e(mcp_client):
    file_id = await _create_file(mcp_client, "keep-on-error.png")
    created = await _create_memory(mcp_client, "Unknown file on update", [file_id])

    with pytest.raises(Exception) as exc_info:
        await _call(
            mcp_client,
            "update_memory",
            {"memory_id": created.data["id"], "file_ids": [MISSING_FILE_ID]},
        )

    assert "not found" in str(exc_info.value).lower()
    assert await _get_file_ids(mcp_client, created.data["id"]) == [file_id]


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", ["create_memory", "update_memory"])
async def test_memory_tools_advertise_file_ids_e2e(mcp_client, tool_name):
    result = await mcp_client.call_tool(
        "how_to_use_forgetful_tool", {"tool_name": tool_name},
    )

    assert "file_ids" in _param_names(result)
