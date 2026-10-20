"""Provider waits must not prevent unrelated public requests from using the DB."""
import asyncio
from contextlib import asynccontextmanager, contextmanager

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings


@contextmanager
def acting_as_bob(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(settings, "DEFAULT_USER_ID", "session-bob")
        patch.setattr(settings, "DEFAULT_USER_EMAIL", "bob@example.test")
        yield


@asynccontextmanager
async def blocked(provider, operation):
    provider.block = True
    provider.entered.clear()
    provider.release.clear()
    task = asyncio.create_task(operation)
    try:
        await asyncio.wait_for(provider.entered.wait(), timeout=3)
        yield task
    finally:
        provider.block = False
        provider.release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def create_skill(app, name="sample-skill", description="old-topic", **extra):
    response = await app.http.post("/api/v1/skills", json={
        "name": name, "description": description, "content": "Original skill instructions",
        **extra,
    })
    assert response.status_code == 201, response.text
    return response.json()


async def test_skill_embedding_wait_allows_another_users_read(app, monkeypatch):
    # Arrange: both users have a real persisted skill and share a one-slot pool.
    skill = await create_skill(app)
    with acting_as_bob(monkeypatch):
        bob = await create_skill(app, name="bobs-skill")
    url = f"/api/v1/skills/{skill['id']}"

    # Act: pause Alice at the external provider, then issue Bob's ordinary GET.
    async with blocked(app.embedding, app.http.put(url, json={"description": "new-topic"})) as task:
        with acting_as_bob(monkeypatch):
            response = await asyncio.wait_for(
                app.http.get(f"/api/v1/skills/{bob['id']}"), timeout=1,
            )
        # Assert: the read finishes before the provider is released.
        assert response.status_code == 200
        assert response.json()["id"] == bob["id"]
        assert not task.done()
        app.embedding.release.set()
        updated = await asyncio.wait_for(task, timeout=3)
        assert updated.status_code == 200
    assert (await app.http.get(url)).json()["description"] == "new-topic"


async def search_skills(app, query="old-topic", k=10, **params):
    response = await app.http.get(
        "/api/v1/skills/search", params={"query": query, "k": k, **params},
    )
    assert response.status_code == 200, response.text
    return response.json()["skills"]


async def create_project(app, name="Sample project"):
    response = await app.http.post("/api/v1/projects", json={
        "name": name, "description": "Project for session tests", "project_type": "development",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_invalid_skill_references_reject_before_failing_provider(app, monkeypatch):
    # Arrange: a valid owned skill, a foreign skill/project, and unused IDs.
    skill = await create_skill(app)
    with acting_as_bob(monkeypatch):
        foreign_skill = await create_skill(app, name="bobs-skill")
        foreign_project = await create_project(app)
    app.embedding.calls.clear()
    app.embedding.fail = True

    # Act/Assert: REST and MCP keep NotFound precedence without contacting the provider.
    cases = [
        (skill["id"], foreign_project), (skill["id"], 424242),
        (foreign_skill["id"], None), (424242, None),
    ]
    for skill_id, project_id in cases:
        patch = {"description": "new-topic"}
        if project_id is not None:
            patch["project_id"] = project_id
        response = await app.http.put(f"/api/v1/skills/{skill_id}", json=patch)
        assert response.status_code == 404, response.text
        with pytest.raises(ToolError, match="not found"):
            await app.mcp.call_tool("execute_forgetful_tool", {
                "tool_name": "update_skill", "arguments": {"skill_id": skill_id, **patch},
            })
    assert app.embedding.calls == []
    assert (await app.http.get(f"/api/v1/skills/{skill['id']}")).json() == skill


async def test_failed_and_cancelled_skill_embedding_preserves_text_and_search(app):
    # Arrange: distinct vectors make stale or partially saved vectors visible through search.
    skill = await create_skill(app)
    competitor = await create_skill(app, name="competitor", description="candidate-5")
    url = f"/api/v1/skills/{skill['id']}"
    app.embedding.fail = True

    # Act: fail, then cancel a later description update before the provider finishes.
    response = await app.http.put(url, json={
        "description": "new-topic", "tags": ["must-not-save"],
    })
    assert response.status_code == 500
    app.embedding.fail = False
    async with blocked(app.embedding, app.http.put(url, json={"description": "new-topic"})) as task:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    # Assert: read-back and vector ranking both retain the original state.
    assert (await app.http.get(url)).json() == skill
    assert (await search_skills(app))[0]["id"] == skill["id"]
    assert (await search_skills(app, "new-topic"))[0]["id"] == competitor["id"]

    # Successful MCP update changes text/vector together and preserves other fields.
    project_id = await create_project(app)
    result = await app.mcp.call_tool("execute_forgetful_tool", {
        "tool_name": "update_skill",
        "arguments": {
            "skill_id": skill["id"], "description": "new-topic", "project_id": project_id,
        },
    })
    assert result.data["description"] == "new-topic"
    saved = (await app.http.get(url)).json()
    assert saved["content"] == skill["content"]
    assert saved["project_id"] == project_id
    assert saved["created_at"] == skill["created_at"]
    assert saved["updated_at"] != skill["updated_at"]
    assert (await search_skills(app, "new-topic"))[0]["id"] == skill["id"]
    assert (await search_skills(app))[0]["id"] == competitor["id"]


async def test_skill_update_preserves_unsubmitted_concurrent_patch(app):
    # Arrange / Act: an independent non-embedding patch lands during the provider wait.
    skill = await create_skill(app)
    url = f"/api/v1/skills/{skill['id']}"
    async with blocked(app.embedding, app.http.put(url, json={"description": "new-topic"})) as task:
        response = await asyncio.wait_for(app.http.put(url, json={
            "content": "New independent instructions", "metadata": {"edited": "while waiting"},
        }), timeout=1)
        assert response.status_code == 200
        app.embedding.release.set()
        assert (await asyncio.wait_for(task, timeout=3)).status_code == 200

    # Assert: only the submitted description was applied to a fresh row.
    saved = (await app.http.get(url)).json()
    assert saved["description"] == "new-topic"
    assert saved["content"] == "New independent instructions"
    assert saved["metadata"] == {"edited": "while waiting"}


async def test_skill_update_rechecks_deleted_skill_and_project(app):
    # Arrange: the submitted project isn't the skill's current project.
    skill = await create_skill(app)
    project_id = await create_project(app)
    url = f"/api/v1/skills/{skill['id']}"
    patch = {"description": "new-topic", "project_id": project_id}

    # Act / Assert: deleting that project during embedding must reject the entire patch.
    async with blocked(app.embedding, app.http.put(url, json=patch)) as task:
        deleted = await asyncio.wait_for(
            app.http.delete(f"/api/v1/projects/{project_id}"), timeout=1,
        )
        assert deleted.status_code == 200
        app.embedding.release.set()
        assert (await asyncio.wait_for(task, timeout=3)).status_code == 404
    assert (await app.http.get(url)).json() == skill

    # A deleted owned skill likewise returns NotFound, not an ORM stale-row error.
    async with blocked(app.embedding, app.http.put(url, json={"description": "new-topic"})) as task:
        assert (await asyncio.wait_for(app.http.delete(url), timeout=1)).status_code == 200
        app.embedding.release.set()
        assert (await asyncio.wait_for(task, timeout=3)).status_code == 404
    assert (await app.http.get(url)).status_code == 404
    assert await search_skills(app) == []


async def test_skill_rerank_wait_releases_pool_and_keeps_candidate_snapshot(app, monkeypatch):
    # Arrange: more matches than either backend's existing candidate limit.
    project_id = await create_project(app)
    candidates = [
        await create_skill(app, name=f"skill-{i}", description=f"candidate-{i}",
                           project_id=project_id)
        for i in range(8)
    ]
    await create_skill(app, name="other-project", description="old-topic")
    with acting_as_bob(monkeypatch):
        bob = await create_skill(app, name="bobs-skill")
    expected_index = 3 if app.backend == "SQLite" else 2
    selected = candidates[expected_index]

    # Act: hold reranking while another user reads and the selected skill is renamed.
    async with blocked(app.reranker, search_skills(
        app, " old-topic ", k=1, project_id=project_id,
    )) as task:
        with acting_as_bob(monkeypatch):
            response = await asyncio.wait_for(
                app.http.get(f"/api/v1/skills/{bob['id']}"), timeout=1,
            )
        assert response.status_code == 200
        renamed = await asyncio.wait_for(app.http.put(
            f"/api/v1/skills/{selected['id']}", json={"name": "renamed-during-rerank"},
        ), timeout=1)
        assert renamed.status_code == 200
        assert not task.done()
        app.reranker.release.set()
        result = await asyncio.wait_for(task, timeout=3)

    # Assert: same candidates, text and ordering; never refetch after scoring.
    assert [s["id"] for s in result] == [selected["id"]]
    assert result[0]["name"] == selected["name"]
    if app.backend == "SQLite":
        assert app.reranker.calls == [("old-topic", [
            f"Name: skill-{i}\nDescription: candidate-{i}" for i in range(4)
        ])]
    else:
        assert app.reranker.calls == [(" old-topic ", [
            "candidate-0", "candidate-1", "candidate-2",
        ])]

    # A caller asking for more must not raise SQLite's configured dense budget.
    # PostgreSQL retains its distinct, existing k*3 rule (not PR152's policy).
    app.reranker.calls.clear()
    result = await search_skills(app, k=5, project_id=project_id)
    if app.backend == "SQLite":
        assert [s["id"] for s in result] == [s["id"] for s in candidates[:4]]
        assert app.reranker.calls == []
    else:
        assert [s["id"] for s in result] == [s["id"] for s in candidates[:2:-1]]
        assert len(app.reranker.calls[0][1]) == 8


async def create_memory(app, content="old-topic", **extra):
    response = await app.http.post("/api/v1/memories", json={
        "title": "Memory for provider session tests", "content": content,
        "context": "Local lifecycle regression", "keywords": ["session"], "tags": ["test"],
        "importance": 7, **extra,
    })
    assert response.status_code == 201, response.text
    memory_id = response.json()["id"]
    return (await app.http.get(f"/api/v1/memories/{memory_id}")).json()


async def search_memories(app, query="old-topic", k=10):
    response = await app.http.post("/api/v1/memories/search", json={
        "query": query, "query_context": "Checking stored vectors", "k": k, "include_links": 0,
    })
    assert response.status_code == 200, response.text
    return response.json()


async def test_memory_embedding_wait_allows_another_users_read(app, monkeypatch):
    # SQLite is the unchanged control: its update session acquires lazily after embedding.
    memory = await create_memory(app)
    project_id = await create_project(app)
    with acting_as_bob(monkeypatch):
        bob = await create_skill(app, name="bobs-skill")
    url = f"/api/v1/memories/{memory['id']}"
    patch = {"content": "new-topic", "project_ids": [project_id]}

    async with blocked(app.embedding, app.http.put(url, json=patch)) as task:
        with acting_as_bob(monkeypatch):
            response = await asyncio.wait_for(
                app.http.get(f"/api/v1/skills/{bob['id']}"), timeout=1,
            )
        assert response.status_code == 200
        assert not task.done()
        app.embedding.release.set()
        assert (await asyncio.wait_for(task, timeout=3)).status_code == 200

    saved = (await app.http.get(url)).json()
    assert saved["content"] == "new-topic"
    assert saved["project_ids"] == [project_id]
    assert saved["context"] == memory["context"]
    assert saved["created_at"] == memory["created_at"]
    assert saved["updated_at"] != memory["updated_at"]
    result = await search_memories(app, "new-topic")
    assert result["primary_memories"][0]["id"] == memory["id"]
    assert result["scores"][0]["similarity"] == 1.0


@pytest.mark.parametrize("obsolete", [False, True], ids=["active", "obsolete-only"])
async def test_reembedding_validation_wait_allows_another_users_read(app, monkeypatch, obsolete):
    # Arrange: the empty workflow succeeds without an embedding call.
    service = app.runtime.services.re_embedding
    assert (await service.validate()).all_passed
    empty = await service.re_embed_all()
    assert empty.total_processed == 0
    assert empty.validation.all_passed
    assert app.embedding.calls == []
    memory = await create_memory(app)
    url = f"/api/v1/memories/{memory['id']}"
    if obsolete:
        assert (await app.http.delete(url)).status_code == 200
    before = (await app.http.get(url)).json()
    with acting_as_bob(monkeypatch):
        bob = await create_skill(app, name="bobs-skill")
    # Batch embedding uses the whole memory. Gate only the title-only validation call.
    app.embedding.block_text = memory["title"]

    # Act: the full rebuild reaches search validation, then another user reads.
    async with blocked(app.embedding, service.re_embed_all()) as task:
        with acting_as_bob(monkeypatch):
            response = await asyncio.wait_for(
                app.http.get(f"/api/v1/skills/{bob['id']}"), timeout=1,
            )
        assert response.status_code == 200
        assert not task.done()
        app.embedding.release.set()
        result = await asyncio.wait_for(task, timeout=3)

    # Assert: normal and obsolete-only storage still validate; content is untouched.
    assert result.total_processed == result.total_memories == 1
    assert result.validation.all_passed
    after = (await app.http.get(url)).json()
    # PostgreSQL's existing bulk rebuild updates updated_at; SQLite does not.
    if app.backend == "Postgres":
        assert after.pop("updated_at") != before.pop("updated_at")
    assert after == before


async def test_failed_and_cancelled_memory_embedding_preserves_text_and_search(app):
    # Arrange: an association patch must not be saved if embedding fails either.
    memory = await create_memory(app)
    project_id = await create_project(app)
    url = f"/api/v1/memories/{memory['id']}"
    patch = {"content": "new-topic", "project_ids": [project_id]}
    app.embedding.fail = True

    # Act: failure and cancellation both occur before the write transaction.
    assert (await app.http.put(url, json=patch)).status_code == 500
    app.embedding.fail = False
    async with blocked(app.embedding, app.http.put(url, json=patch)) as task:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    # Assert: original content, associations, timestamp and vector remain consistent.
    assert (await app.http.get(url)).json() == memory
    result = await search_memories(app)
    assert result["primary_memories"][0]["id"] == memory["id"]
    assert result["scores"][0]["similarity"] == 1.0
    result = await search_memories(app, "new-topic")
    assert result["scores"][0]["similarity"] == 0.0


async def test_memory_search_retains_configured_dense_budget(app):
    # Arrange: callers can request more than the configured four dense candidates.
    memories = [await create_memory(app, content=f"candidate-{i}") for i in range(8)]
    app.reranker.calls.clear()

    # Act / Assert: k never expands that budget; existing dense ordering is retained.
    result = await search_memories(app, k=5)
    assert [m["id"] for m in result["primary_memories"]] == [m["id"] for m in memories[:4]]
    assert app.reranker.calls == []
    result = await search_memories(app, k=1)
    assert [m["id"] for m in result["primary_memories"]] == [memories[3]["id"]]
    assert len(app.reranker.calls) == 1
    assert len(app.reranker.calls[0][1]) == 4


async def test_skill_row_rejection_rolls_back_matching_vector(app):
    # Arrange: use the existing REST null inconsistency to cause a real DB row rejection.
    # This does not change null policy. It verifies SQLite's separate vec_skills write
    # rolls back with the row, without mocking a session or querying internal tables.
    skill = await create_skill(app)
    competitor = await create_skill(app, name="competitor", description="candidate-5")
    url = f"/api/v1/skills/{skill['id']}"

    # Act: embedding succeeds, but the row's NOT NULL constraint rejects content.
    response = await app.http.put(url, json={"description": "new-topic", "content": None})
    assert response.status_code == 500

    # Assert: both text and vector were rolled back, not just the ordinary row.
    assert (await app.http.get(url)).json() == skill
    assert (await search_skills(app))[0]["id"] == skill["id"]
    assert (await search_skills(app, "new-topic"))[0]["id"] == competitor["id"]
