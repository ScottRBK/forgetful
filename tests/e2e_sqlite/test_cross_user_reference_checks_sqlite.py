"""SQLite E2E tests: referenced projects and embeddings must belong to the caller.

Documents, code artifacts, files, plans and skills accepted any ``project_id``.
The foreign key only checks that the id exists, so a user could attach rows to
another user's project (and the project owner's later delete then rewrote or
cascade-deleted those rows), and an unused id surfaced as a raw
``FOREIGN KEY constraint failed`` 500. The SQLite memory repository also read
the source embedding for the similarity searches without checking that the
memory belongs to the caller.

Two layers are covered:
- the REST surface with two users (full stack), and
- the memory repository with an offline embedder, including the owner control.
"""
import base64
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.memory_models import MemoryCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

UNKNOWN_PROJECT_ID = 424_242
FILE_DATA = base64.b64encode(b"Hello, World!").decode("utf-8")

# kind -> (collection url, list key, payload builder taking project_id)
CREATE_CASES = {
    "documents": (
        "/api/v1/documents",
        "documents",
        lambda pid: {
            "title": "Linked document",
            "description": "Document with a project link",
            "content": "Document body with enough text to be valid.",
            "project_id": pid,
        },
    ),
    "code-artifacts": (
        "/api/v1/code-artifacts",
        "code_artifacts",
        lambda pid: {
            "title": "Linked artifact",
            "description": "Artifact with a project link",
            "code": "print('hello')",
            "language": "python",
            "project_id": pid,
        },
    ),
    "files": (
        "/api/v1/files",
        "files",
        lambda pid: {
            "filename": "linked.txt",
            "description": "File with a project link",
            "data": FILE_DATA,
            "mime_type": "text/plain",
            "project_id": pid,
        },
    ),
    "plans": (
        "/api/v1/plans",
        "plans",
        lambda pid: {"title": "Linked plan", "project_id": pid},
    ),
    "skills": (
        "/api/v1/skills",
        "skills",
        lambda pid: {
            "name": "linked-skill",
            "description": "Skill with a project link",
            "content": "# Linked skill\n\n1. Do the thing",
            "project_id": pid,
        },
    ),
}
UPDATE_KINDS = ["documents", "code-artifacts", "files", "skills"]


@contextmanager
def acting_as(monkeypatch, name: str):
    """Run REST calls as another user (the test app has no auth, so identity is a setting)."""
    with monkeypatch.context() as patch:
        patch.setattr(settings, "DEFAULT_USER_ID", f"ref-check-{name}")
        patch.setattr(settings, "DEFAULT_USER_EMAIL", f"ref-check-{name}@example.test")
        yield


async def _create_project(http_client, name: str) -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": name,
        "description": f"{name} description",
        "project_type": "development",
    })
    assert response.status_code == 201
    return response.json()["id"]


async def _create(http_client, kind: str, project_id: int | None):
    url, _, build = CREATE_CASES[kind]
    return await http_client.post(url, json=build(project_id))


async def _count(http_client, kind: str) -> int:
    url, key, _ = CREATE_CASES[kind]
    response = await http_client.get(url)
    assert response.status_code == 200
    return len(response.json()[key])


# ============================================================================
# REST surface, two users
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_rejects_other_users_project(http_client, monkeypatch, kind):
    """A foreign project id is reported as not found and nothing is stored."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        response = await _create(http_client, kind, alice_project)

        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
        assert await _count(http_client, kind) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_unknown_project_is_not_found(http_client, kind):
    """An unused project id is a clean 404, not a raw foreign-key error."""
    response = await _create(http_client, kind, UNKNOWN_PROJECT_ID)

    assert response.status_code == 404
    assert "FOREIGN KEY" not in response.text
    assert await _count(http_client, kind) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_with_own_project_still_works(http_client, kind):
    """The owner can still attach rows to their own project."""
    project_id = await _create_project(http_client, "Alice own")

    response = await _create(http_client, kind, project_id)

    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_rejects_other_users_project(http_client, monkeypatch, kind):
    """Re-pointing an existing row at a foreign project is rejected and changes nothing."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        created = await _create(http_client, kind, None)
        assert created.status_code == 201
        item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

        response = await http_client.put(item_url, json={"project_id": alice_project})

        assert response.status_code == 404
        fetched = await http_client.get(item_url)
        assert fetched.json()["project_id"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_unknown_project_is_not_found(http_client, kind):
    """An unused project id on update is a clean 404, not a raw foreign-key error."""
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": UNKNOWN_PROJECT_ID})

    assert response.status_code == 404
    assert "FOREIGN KEY" not in response.text
    assert (await http_client.get(item_url)).json()["project_id"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_with_own_project_still_works(http_client, kind):
    """The owner can still move a row to their own project."""
    project_id = await _create_project(http_client, "Alice own")
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": project_id})

    assert response.status_code == 200
    assert response.json()["project_id"] == project_id


@pytest.mark.asyncio
async def test_import_skill_rejects_other_users_project(http_client, monkeypatch):
    """The import path goes through skill creation, so it is guarded as well."""
    alice_project = await _create_project(http_client, "Alice private")
    skill_md = "---\nname: imported-skill\ndescription: Imported skill\n---\n\n# Steps\n1. Do it\n"

    with acting_as(monkeypatch, "bob"):
        response = await http_client.post("/api/v1/skills/import", json={
            "skill_md": skill_md,
            "project_id": alice_project,
        })

        assert response.status_code == 404
        assert await _count(http_client, "skills") == 0


@pytest.mark.asyncio
async def test_owner_project_delete_leaves_other_users_rows_alone(http_client, monkeypatch):
    """Deleting a project must not delete or rewrite another user's plans and documents."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        bob_project = await _create_project(http_client, "Bob own")
        # Rejected attempts to hang Bob's rows on Alice's project
        assert (await _create(http_client, "plans", alice_project)).status_code == 404
        assert (await _create(http_client, "documents", alice_project)).status_code == 404
        # Bob's legitimate rows, linked to his own project
        plan = await _create(http_client, "plans", bob_project)
        document = await _create(http_client, "documents", bob_project)

    deleted = await http_client.delete(f"/api/v1/projects/{alice_project}")
    assert deleted.status_code == 200

    with acting_as(monkeypatch, "bob"):
        assert await _count(http_client, "plans") == 1
        fetched = await http_client.get(f"/api/v1/documents/{document.json()['id']}")
        assert fetched.json()["project_id"] == bob_project
        assert plan.json()["project_id"] == bob_project


# ============================================================================
# Memory repository: similarity searches must not use another user's embedding
# ============================================================================

DIMS = 384


class FakeEmbeddingAdapter:
    """Deterministic offline embedder: 'topic-alpha' texts share one direction."""

    async def generate_embedding(self, text: str) -> list[float]:
        vec = [0.0] * DIMS
        if "topic-alpha" in text:
            vec[0] = 1.0
            vec[1] = 0.01 * (len(text) % 7)
        else:
            vec[2] = 1.0
        return vec


@pytest.fixture
async def memory_repo_and_db():
    original = (settings.DATABASE, settings.SQLITE_MEMORY, settings.EMBEDDING_DIMENSIONS)
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_DIMENSIONS = DIMS
    db_adapter = SqliteDatabaseAdapter()
    await db_adapter.init_db()
    repo = SqliteMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=FakeEmbeddingAdapter(),
        rerank_adapter=None,
    )
    try:
        yield repo, db_adapter
    finally:
        await db_adapter.dispose()
        settings.DATABASE, settings.SQLITE_MEMORY, settings.EMBEDDING_DIMENSIONS = original


async def _create_user(db_adapter, user_id) -> None:
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, :name, :email, :created_at, :updated_at)",
            ),
            {
                "id": str(user_id),
                "external_id": f"ext-{user_id}",
                "name": "User",
                "email": f"{user_id}@example.test",
                "created_at": now,
                "updated_at": now,
            },
        )


def _memory(title: str) -> MemoryCreate:
    return MemoryCreate(
        title=title,
        content=f"{title} content about topic-alpha",
        context="isolation test",
        keywords=["topic-alpha"],
        tags=["t"],
        importance=7,
    )


@pytest.mark.asyncio
async def test_similar_memories_still_found_for_owner(memory_repo_and_db):
    """Control: the owner finds their own similar memory, so the setup is valid."""
    repo, db = memory_repo_and_db
    user = uuid4()
    await _create_user(db, user)
    first = await repo.create_memory(user, _memory("Alice one"))
    second = await repo.create_memory(user, _memory("Alice two"))

    scored = await repo.find_similar_memories_scored(user, first.id, max_links=5)

    assert [m.id for m, _ in scored] == [second.id]
    assert scored[0][1] >= settings.MEMORY_SIMILARITY_THRESHOLD


@pytest.mark.asyncio
async def test_find_similar_memories_scored_rejects_other_users_memory(memory_repo_and_db):
    """A foreign memory id raises NotFoundError instead of ranking against its embedding."""
    repo, db = memory_repo_and_db
    alice, bob = uuid4(), uuid4()
    await _create_user(db, alice)
    await _create_user(db, bob)
    alice_memory = await repo.create_memory(alice, _memory("Alice private secret"))
    await repo.create_memory(bob, _memory("Bob own note"))

    with pytest.raises(NotFoundError):
        await repo.find_similar_memories_scored(bob, alice_memory.id, max_links=5)


@pytest.mark.asyncio
async def test_find_similar_memories_rejects_other_users_memory(memory_repo_and_db):
    """Same through the unscored wrapper."""
    repo, db = memory_repo_and_db
    alice, bob = uuid4(), uuid4()
    await _create_user(db, alice)
    await _create_user(db, bob)
    alice_memory = await repo.create_memory(alice, _memory("Alice private secret"))
    await repo.create_memory(bob, _memory("Bob own note"))

    with pytest.raises(NotFoundError):
        await repo.find_similar_memories(bob, alice_memory.id, max_links=5)


@pytest.mark.asyncio
async def test_find_obsolete_matches_ignores_other_users_memory(memory_repo_and_db):
    """A foreign memory id yields no obsolete matches, as on PostgreSQL."""
    repo, db = memory_repo_and_db
    alice, bob = uuid4(), uuid4()
    await _create_user(db, alice)
    await _create_user(db, bob)
    alice_memory = await repo.create_memory(alice, _memory("Alice private secret"))
    bob_memory = await repo.create_memory(bob, _memory("Bob obsolete note"))
    assert await repo.mark_obsolete(
        user_id=bob, memory_id=bob_memory.id, reason="old", superseded_by=None,
    )

    matches = await repo.find_obsolete_matches(
        bob, alice_memory.id, limit=5, min_similarity=0.5,
    )

    assert matches == []


@pytest.mark.asyncio
async def test_find_obsolete_matches_still_found_for_owner(memory_repo_and_db):
    """Control: the owner still gets obsolete matches for their own memory."""
    repo, db = memory_repo_and_db
    user = uuid4()
    await _create_user(db, user)
    current = await repo.create_memory(user, _memory("Alice current"))
    old = await repo.create_memory(user, _memory("Alice old"))
    assert await repo.mark_obsolete(
        user_id=user, memory_id=old.id, reason="old", superseded_by=None,
    )

    matches = await repo.find_obsolete_matches(user, current.id, limit=5, min_similarity=0.5)

    assert [m.id for m, _ in matches] == [old.id]
