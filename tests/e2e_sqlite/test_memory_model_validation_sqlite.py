"""E2E tests (in-memory SQLite) for memory model validation.

Drives the REST routes and MCP tools through the real stack to prove that
rejected input returns a client error, never reaches the database, and that
rows stored under looser limits or older rules stay readable.
"""

import json

import pytest
from fastmcp.exceptions import ToolError
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


class TestBlankMemoryText:
    """Whitespace-only title, content and context are rejected."""

    @pytest.mark.parametrize("overrides", [
        {"title": "   "},
        {"content": "\n\n"},
        {"title": "   ", "content": "\n\n", "context": ""},
    ])
    async def test_create_rejects_blank_text(self, http_client, overrides):
        response = await http_client.post("/api/v1/memories", json=_payload(**overrides))

        assert response.status_code == 400
        assert "cannot be empty or whitespace only" in response.json()["error"][0]["msg"]
        assert await _total(http_client) == 0

    @pytest.mark.parametrize("field", ["title", "content", "context"])
    async def test_update_rejects_blank_text_and_keeps_stored_value(self, http_client, field):
        memory_id = await _create(http_client)

        response = await http_client.put(f"/api/v1/memories/{memory_id}", json={field: "   "})

        assert response.status_code == 400
        stored = (await http_client.get(f"/api/v1/memories/{memory_id}")).json()
        assert stored[field] == _payload()[field]

    async def test_create_with_empty_context_still_works(self, http_client):
        memory_id = await _create(http_client, context="")

        stored = (await http_client.get(f"/api/v1/memories/{memory_id}")).json()
        assert stored["context"] == ""

    async def test_mcp_create_and_update_reject_blank_text(self, mcp_client):
        with pytest.raises(ToolError, match="whitespace only"):
            await _call(mcp_client, "create_memory", _payload(title="   "))

        created = await _call(mcp_client, "create_memory", _payload())
        memory_id = created.data["id"]
        with pytest.raises(ToolError, match="whitespace only"):
            await _call(mcp_client, "update_memory", {"memory_id": memory_id, "content": "   "})


class TestOversizedListItems:
    """Per-item length bounds keep one memory from dominating query_memory."""

    @pytest.mark.parametrize(("field", "limit"), [
        ("keywords", settings.MEMORY_KEYWORD_MAX_LENGTH),
        ("tags", settings.MEMORY_TAG_MAX_LENGTH),
        ("source_files", settings.MEMORY_SOURCE_FILE_MAX_LENGTH),
    ])
    async def test_create_and_update_reject_oversized_item(self, http_client, field, limit):
        oversized = "a" * (limit + 1)

        created = await http_client.post("/api/v1/memories", json=_payload(**{field: [oversized]}))
        assert created.status_code == 400
        assert created.json()["error"][0]["loc"][0] == field
        assert await _total(http_client) == 0

        memory_id = await _create(http_client)
        updated = await http_client.put(f"/api/v1/memories/{memory_id}", json={field: [oversized]})
        assert updated.status_code == 400

    async def test_item_at_the_limit_is_stored(self, http_client):
        keyword = "k" * settings.MEMORY_KEYWORD_MAX_LENGTH

        memory_id = await _create(http_client, keywords=[keyword])

        stored = (await http_client.get(f"/api/v1/memories/{memory_id}")).json()
        assert stored["keywords"] == [keyword]

    async def test_oversized_memory_can_no_longer_blank_search_results(self, http_client):
        """An importance-10 memory with a huge keyword used to empty the whole result."""
        for index in range(3):
            await _create(http_client, title=f"python logging tip {index}", importance=5)
        huge = await http_client.post(
            "/api/v1/memories",
            json=_payload(title="python logging huge", keywords=["a" * 70_000], importance=10),
        )
        assert huge.status_code == 400

        response = await http_client.post(
            "/api/v1/memories/search",
            json={"query": "python logging", "query_context": "testing", "k": 5},
        )

        assert response.status_code == 200
        assert len(response.json()["primary_memories"]) == 3


class TestUnencodableText:
    """Lone surrogates from JSON escapes never reach the database."""

    @pytest.mark.parametrize("body", [
        b'{"title":"bad","content":"c","context":"x","keywords":["k"],"tags":["t"],"source_files":["src/a\\ud83d.py"]}',
        b'{"title":"bad","content":"c","context":"x","keywords":["k\\ud800"],"tags":["t"]}',
        b'{"title":"bad","content":"c","context":"x","keywords":["k"],"tags":["\\udfff"]}',
        b'{"title":"b\\ud83dad","content":"c","context":"x","keywords":["k"],"tags":["t"]}',
    ])
    async def test_create_rejects_lone_surrogate_and_store_stays_readable(self, http_client, body):
        response = await http_client.post("/api/v1/memories", content=body, headers=JSON_HEADERS)

        assert response.status_code == 400
        listing = await http_client.get("/api/v1/memories")
        assert listing.status_code == 200
        assert listing.json()["total"] == 0

    async def test_update_rejects_lone_surrogate(self, http_client):
        memory_id = await _create(http_client)

        response = await http_client.put(
            f"/api/v1/memories/{memory_id}",
            content=b'{"source_files":["a\\ud83d"]}',
            headers=JSON_HEADERS,
        )

        assert response.status_code == 400
        assert "cannot be encoded as UTF-8" in response.json()["error"][0]["msg"]
        stored = await http_client.get(f"/api/v1/memories/{memory_id}")
        assert stored.status_code == 200
        assert stored.json()["source_files"] is None

    async def test_search_rejects_lone_surrogate_query(self, http_client):
        response = await http_client.post(
            "/api/v1/memories/search",
            content=b'{"query":"find \\ud83d","query_context":"ctx"}',
            headers=JSON_HEADERS,
        )

        assert response.status_code == 400

    async def test_paired_surrogate_escape_is_stored_as_the_real_character(self, http_client):
        response = await http_client.post(
            "/api/v1/memories",
            content=json.dumps(_payload(), ensure_ascii=True).replace("Python", "Python \\ud83d\\ude00").encode(),
            headers=JSON_HEADERS,
        )

        assert response.status_code == 201
        stored = (await http_client.get(f"/api/v1/memories/{response.json()['id']}")).json()
        assert stored["title"] == "Python \U0001f600 logging"


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

    async def test_legacy_blank_memory_can_be_replaced_with_valid_text(self, http_client, sqlite_app):
        memory_id = await _create(http_client)
        repo = sqlite_app.memory_service.memory_repo
        async with repo.db_adapter.system_session() as session:
            await session.execute(text("UPDATE memories SET content = '   ' WHERE id = :id"), {"id": memory_id})

        updated = await http_client.put(f"/api/v1/memories/{memory_id}", json={"content": "Fixed content"})

        assert updated.status_code == 200
        assert updated.json()["content"] == "Fixed content"


class TestBlankSearchQuery:
    """A blank query is rejected instead of returning arbitrary neighbours."""

    @pytest.mark.parametrize("blank", ["   ", "\n\t "])
    async def test_rest_search_rejects_blank_query(self, http_client, blank):
        await _create(http_client)

        response = await http_client.post(
            "/api/v1/memories/search",
            json={"query": blank, "query_context": "looking for something", "k": 3},
        )

        assert response.status_code == 400
        assert response.json()["error"][0]["loc"] == ["query"]

    async def test_mcp_query_memory_rejects_blank_query(self, mcp_client):
        await _call(mcp_client, "create_memory", _payload())

        with pytest.raises(ToolError, match="whitespace only"):
            await _call(
                mcp_client,
                "query_memory",
                {"query": "   ", "query_context": "looking for something", "include_links": False},
            )

    async def test_blank_query_never_reaches_the_embedding_adapter(self, http_client, sqlite_app):
        await _create(http_client)
        adapter = sqlite_app.memory_service.memory_repo.embedding_adapter
        original = adapter.generate_embedding
        seen: list[str] = []

        async def spy(*args, **kwargs):
            seen.extend(str(value) for value in (*args, *kwargs.values()))
            return await original(*args, **kwargs)

        adapter.generate_embedding = spy
        try:
            response = await http_client.post(
                "/api/v1/memories/search",
                json={"query": "   ", "query_context": "ctx", "k": 3},
            )
        finally:
            adapter.generate_embedding = original

        assert response.status_code == 400
        assert [t for t in seen if not t.strip()] == []

    async def test_repositories_return_nothing_for_blank_query_without_embedding(self, http_client, sqlite_app):
        """Direct repository callers get no hits instead of neighbours of the empty vector."""
        from uuid import uuid4

        await _create(http_client)
        memory_repo = sqlite_app.memory_service.memory_repo
        skill_repo = sqlite_app.skill_service.skill_repo
        seen: list[str] = []
        originals = {}
        for repo in (memory_repo, skill_repo):
            adapter = repo.embedding_adapter
            originals[repo] = adapter.generate_embedding

            async def spy(*args, _original=adapter.generate_embedding, **kwargs):
                seen.extend(list(args) + list(kwargs.values()))
                return await _original(*args, **kwargs)

            adapter.generate_embedding = spy

        try:
            scored = await memory_repo.search_scored(
                user_id=uuid4(), query="   ", query_context="ctx", k=3,
                importance_threshold=None, project_ids=None, exclude_ids=None,
            )
            semantic = await memory_repo.semantic_search_scored(
                user_id=uuid4(), query="\n\t ", k=3,
                importance_threshold=None, project_ids=None, exclude_ids=None,
            )
            skills = await skill_repo.search_skills(user_id=uuid4(), query="   ")
        finally:
            for repo, original in originals.items():
                repo.embedding_adapter.generate_embedding = original

        assert (scored, semantic, skills) == ([], [], [])
        assert seen == []

    async def test_rest_skill_search_rejects_blank_query(self, http_client):
        response = await http_client.get("/api/v1/skills/search", params={"query": "   "})

        assert response.status_code == 400

    async def test_mcp_search_skills_rejects_blank_query(self, mcp_client):
        with pytest.raises(ToolError, match="whitespace only"):
            await _call(mcp_client, "search_skills", {"query": "   "})

    async def test_normal_queries_still_return_hits(self, http_client):
        memory_id = await _create(http_client)

        response = await http_client.post(
            "/api/v1/memories/search",
            json={"query": "python logging", "query_context": "testing", "k": 3},
        )

        assert response.status_code == 200
        assert [m["id"] for m in response.json()["primary_memories"]] == [memory_id]
