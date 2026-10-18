"""E2E tests (in-memory SQLite) for memory model validation.

Drives the REST routes and MCP tools through the real stack to prove that
rejected input returns a client error, never reaches the database, and that
rows stored under looser limits or older rules stay readable.
"""

import json

from sqlalchemy import text

from app.config.settings import settings

JSON_HEADERS = {"content-type": "application/json"}


def _payload(**overrides) -> dict:
    data = {
        "title": "Python logging",
        "content": "Use QueueHandler for async logging.",
        "context": "Keeps the event loop free",
        "keywords": ["python", "logging"],
        "tags": ["pattern"],
        "importance": 7,
    }
    data.update(overrides)
    return data


async def _total(http_client) -> int:
    response = await http_client.get("/api/v1/memories")
    assert response.status_code == 200
    return response.json()["total"]


async def _create(http_client, **overrides) -> int:
    response = await http_client.post("/api/v1/memories", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _call(mcp_client, tool_name: str, arguments: dict):
    return await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


class TestStoredRowsStayReadable:
    """The Memory response model must not enforce write-time rules."""

    async def test_rows_stored_under_looser_rules_can_be_read_listed_and_searched(self, http_client, sqlite_app):
        memory_id = await _create(http_client)
        legacy_keywords = [f"keyword-{i}-" + "k" * 500 for i in range(15)]
        repo = sqlite_app.memory_service.memory_repo
        async with repo.db_adapter.system_session() as session:
            await session.execute(
                text(
                    "UPDATE memories SET title = :title, content = :content, keywords = :keywords "
                    "WHERE id = :id",
                ),
                {
                    "title": "   ",
                    "content": "c" * (settings.MEMORY_CONTENT_MAX_LENGTH + 500),
                    "keywords": json.dumps(legacy_keywords),
                    "id": memory_id,
                },
            )

        fetched = await http_client.get(f"/api/v1/memories/{memory_id}")
        assert fetched.status_code == 200
        assert len(fetched.json()["content"]) == settings.MEMORY_CONTENT_MAX_LENGTH + 500
        assert len(fetched.json()["keywords"]) == 15

        listed = await http_client.get("/api/v1/memories")
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        searched = await http_client.post(
            "/api/v1/memories/search",
            json={"query": "python logging", "query_context": "testing", "k": 5, "include_links": 0},
        )
        assert searched.status_code == 200
        assert [m["id"] for m in searched.json()["primary_memories"]] == [memory_id]
