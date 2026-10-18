"""PostgreSQL E2E coverage for memory model validation.

The request rules are backend independent; these tests prove they also hold in front of
PostgreSQL (JSONB columns, pgvector search) and that the PostgreSQL repositories keep
stored rows readable and refuse to embed a blank query.
"""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings

pytestmark = pytest.mark.asyncio(loop_scope="session")

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


@pytest.mark.e2e
@pytest.mark.parametrize("overrides", [
    {"title": "   "},
    {"content": "\n\n"},
    {"keywords": ["k" * (settings.MEMORY_KEYWORD_MAX_LENGTH + 1)]},
    {"tags": ["t" * (settings.MEMORY_TAG_MAX_LENGTH + 1)]},
    {"source_files": ["f" * (settings.MEMORY_SOURCE_FILE_MAX_LENGTH + 1)]},
])
async def test_create_rejects_blank_text_and_oversized_items(http_client, overrides):
    response = await http_client.post("/api/v1/memories", json=_payload(**overrides))

    assert response.status_code == 400
    assert await _total(http_client) == 0


@pytest.mark.e2e
async def test_blank_update_and_lone_surrogate_are_rejected_without_changing_the_row(http_client):
    created = await http_client.post("/api/v1/memories", json=_payload())
    assert created.status_code == 201
    memory_id = created.json()["id"]

    blank = await http_client.put(f"/api/v1/memories/{memory_id}", json={"content": "   "})
    surrogate = await http_client.put(
        f"/api/v1/memories/{memory_id}",
        content=b'{"tags":["a\\ud83d"]}',
        headers=JSON_HEADERS,
    )

    assert blank.status_code == 400
    assert surrogate.status_code == 400
    stored = (await http_client.get(f"/api/v1/memories/{memory_id}")).json()
    assert stored["content"] == _payload()["content"]
    assert stored["tags"] == ["pattern"]


@pytest.mark.e2e
async def test_lone_surrogate_in_a_json_column_is_rejected_on_create(http_client):
    response = await http_client.post(
        "/api/v1/memories",
        content=b'{"title":"bad","content":"c","context":"x","keywords":["k"],"tags":["t"],'
                b'"source_files":["src/a\\ud83d.py"]}',
        headers=JSON_HEADERS,
    )

    assert response.status_code == 400
    assert await _total(http_client) == 0


@pytest.mark.e2e
async def test_blank_search_query_is_rejected(http_client):
    created = await http_client.post("/api/v1/memories", json=_payload())
    assert created.status_code == 201

    memories = await http_client.post(
        "/api/v1/memories/search",
        json={"query": "   ", "query_context": "looking for something", "k": 3},
    )
    skills = await http_client.get("/api/v1/skills/search", params={"query": "   "})

    assert memories.status_code == 400
    assert skills.status_code == 400


@pytest.mark.e2e
async def test_postgres_repositories_do_not_embed_a_blank_query(http_client, postgres_app):
    created = await http_client.post("/api/v1/memories", json=_payload())
    assert created.status_code == 201
    memory_repo = postgres_app.memory_service.memory_repo
    skill_repo = postgres_app.skill_service.skill_repo
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
        skills = await skill_repo.search_skills(user_id=uuid4(), query="\n\t ")
    finally:
        for repo, original in originals.items():
            repo.embedding_adapter.generate_embedding = original

    assert (scored, skills) == ([], [])
    assert seen == []


@pytest.mark.e2e
async def test_rows_stored_under_looser_rules_stay_readable(http_client, db_adapter):
    created = await http_client.post("/api/v1/memories", json=_payload())
    assert created.status_code == 201
    memory_id = created.json()["id"]
    legacy_keywords = [f"keyword-{i}-" + "k" * (settings.MEMORY_KEYWORD_MAX_LENGTH + 20) for i in range(15)]
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "UPDATE memories SET title = :title, content = :content, "
                "keywords = :keywords WHERE id = :id",
            ),
            {
                "title": "   ",
                "content": "c" * (settings.MEMORY_CONTENT_MAX_LENGTH + 500),
                "keywords": legacy_keywords,
                "id": memory_id,
            },
        )

    fetched = await http_client.get(f"/api/v1/memories/{memory_id}")
    listed = await http_client.get("/api/v1/memories")
    searched = await http_client.post(
        "/api/v1/memories/search",
        json={"query": "python logging", "query_context": "testing", "k": 5, "include_links": 0},
    )

    assert fetched.status_code == 200
    assert len(fetched.json()["keywords"]) == 15
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert searched.status_code == 200
    assert [m["id"] for m in searched.json()["primary_memories"]] == [memory_id]
