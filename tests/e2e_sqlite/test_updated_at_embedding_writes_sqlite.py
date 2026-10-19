"""Real-SQL regression tests (in-memory SQLite) for read telemetry and embedding writes.

Covers:
- `record_memory_access` must not advance `updated_at` (column `onupdate` used to fire).
- A targeted rebuild must not overwrite a vector regenerated for newer content.
- `rebuild_embeddings` failures return stable reason codes and blame only the failing memory.
- `rebuild_embeddings(project_id=...)` rejects unknown or foreign projects.

Uses a deterministic offline embedding adapter, so no model download is needed.
"""
import asyncio
import hashlib
import random
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
import sqlite_vec
from fastmcp.exceptions import ToolError
from sqlalchemy import event, text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate, MemoryUpdate
from app.models.user_models import User, UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.routes.mcp.tool_adapters import MemoryToolAdapters
from app.services.memory_service import MemoryService
from app.services.re_embedding_service import ReEmbeddingService

DIMS = 384
LEAK_MARKERS = ("[SQL:", "INSERT INTO", "[parameters:", "vec_memories", "\\x00", "b'", "Dimension mismatch")


class GatedEmbeddingAdapter:
    """Deterministic adapter; can hold calls whose text contains `gate_marker`.

    `wrong_dimension_marker` makes texts containing it return a vector of the wrong length,
    which the vec0 table rejects at write time (like a misconfigured provider would).
    """

    def __init__(self) -> None:
        self.gate_marker: str | None = None
        self.wrong_dimension_marker: str | None = None
        self.reached = asyncio.Event()
        self.release = asyncio.Event()

    @staticmethod
    def vector(text_: str, dims: int = DIMS) -> list[float]:
        rng = random.Random(int(hashlib.md5(text_.encode()).hexdigest()[:8], 16))
        vec = [rng.random() for _ in range(dims)]
        magnitude = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / magnitude for x in vec]

    async def generate_embedding(self, text: str) -> list[float]:
        if self.gate_marker and self.gate_marker in text:
            self.reached.set()
            await self.release.wait()
        if self.wrong_dimension_marker and self.wrong_dimension_marker in text:
            return self.vector(text, DIMS + 1)
        return self.vector(text)


@asynccontextmanager
async def _open_stack(sqlite_path: str | None = None):
    """Yield (repo, db_adapter, embedder, user_id) on in-memory SQLite or a database file."""
    saved = (
        settings.DATABASE,
        settings.SQLITE_MEMORY,
        settings.SQLITE_PATH,
        settings.EMBEDDING_DIMENSIONS,
        settings.MEMORY_NUM_AUTO_LINK,
    )
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = sqlite_path is None
    if sqlite_path is not None:
        settings.SQLITE_PATH = sqlite_path
    settings.EMBEDDING_DIMENSIONS = DIMS
    settings.MEMORY_NUM_AUTO_LINK = 0

    db_adapter = SqliteDatabaseAdapter()
    await db_adapter.init_db()
    embedder = GatedEmbeddingAdapter()
    repo = SqliteMemoryRepository(db_adapter=db_adapter, embedding_adapter=embedder, rerank_adapter=None)
    users = SqliteUserRepository(db_adapter=db_adapter)
    user = await users.create_user(UserCreate(external_id=f"ext-{uuid4()}", name="u", email="u@example.com"))
    try:
        yield repo, db_adapter, embedder, user.id
    finally:
        try:
            await db_adapter.dispose()
        except Exception:  # noqa: BLE001
            pass
        (
            settings.DATABASE,
            settings.SQLITE_MEMORY,
            settings.SQLITE_PATH,
            settings.EMBEDDING_DIMENSIONS,
            settings.MEMORY_NUM_AUTO_LINK,
        ) = saved


@pytest.fixture
async def stack():
    async with _open_stack() as opened:
        yield opened


@pytest.fixture
async def file_stack(tmp_path):
    """File-backed database: separate connections really are separate, as in production."""
    db_file = tmp_path / "forgetful.db"
    async with _open_stack(str(db_file)) as opened:
        yield (*opened, str(db_file))


def _memory(content: str, project_id: int | None = None) -> MemoryCreate:
    return MemoryCreate(
        title="T",
        content=content,
        context="c",
        keywords=["k"],
        tags=["t"],
        importance=5,
        project_ids=[project_id] if project_id else [],
    )


async def _vec_blob(db_adapter, memory_id: int):
    async with db_adapter.system_session() as session:
        return (
            await session.execute(
                text("SELECT embedding FROM vec_memories WHERE memory_id = :memory_id"),
                {"memory_id": str(memory_id)},
            )
        ).scalar_one_or_none()


async def _create_project(db_adapter, user_id, name="P"):
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        result = await session.execute(
            text(
                "INSERT INTO projects (user_id, name, description, project_type, status, created_at, updated_at) "
                "VALUES (:user_id, :name, 'd', 'development', 'active', :now, :now) RETURNING id",
            ),
            {"user_id": str(user_id), "name": name, "now": now},
        )
        return result.scalar_one()


async def _create_other_user(db_adapter):
    users = SqliteUserRepository(db_adapter=db_adapter)
    user = await users.create_user(UserCreate(external_id=f"ext-{uuid4()}", name="o", email="o@example.com"))
    return user.id


def _tool_adapters(repo, embedder, user_id):
    class FakeUserService:
        async def get_or_create_user(self, user):
            return User(id=user_id, external_id=user.external_id, name=user.name, email=user.email)

    user_service = FakeUserService()
    ctx = SimpleNamespace(fastmcp=SimpleNamespace(auth=None, user_service=user_service))
    adapters = MemoryToolAdapters(
        memory_service=SimpleNamespace(),
        user_service=user_service,
        re_embedding_service=ReEmbeddingService(repo, embedder),
    )
    return ctx, adapters


# ---------------------------------------------------------------------------
# updated_at must not move on telemetry or derived-data writes
# ---------------------------------------------------------------------------


async def test_record_memory_access_does_not_change_updated_at(stack):
    repo, _db, _embedder, user_id = stack
    memory = await repo.create_memory(user_id, _memory("content"))
    before = await repo.get_memory_by_id(user_id, memory.id)
    assert before.access_count == 0

    await asyncio.sleep(0.05)
    assert await repo.record_memory_access(user_id, [memory.id]) == 1

    after = await repo.get_memory_by_id(user_id, memory.id)
    assert after.access_count == 1
    assert after.last_accessed_at is not None
    assert after.updated_at == before.updated_at


async def test_targeted_rebuild_does_not_change_updated_at(stack):
    repo, _db, embedder, user_id = stack
    memory = await repo.create_memory(user_id, _memory("content"))
    before = await repo.get_memory_by_id(user_id, memory.id)

    await asyncio.sleep(0.05)
    result = await ReEmbeddingService(repo, embedder).rebuild_targeted(user_id=user_id)

    assert result.rebuilt_ids == [memory.id]
    assert (await repo.get_memory_by_id(user_id, memory.id)).updated_at == before.updated_at


# ---------------------------------------------------------------------------
# rebuild must not overwrite a vector computed for newer content
# ---------------------------------------------------------------------------


async def test_rebuild_does_not_clobber_embedding_of_concurrent_update(stack):
    repo, db_adapter, embedder, user_id = stack
    memory_service = MemoryService(memory_repo=repo)
    re_service = ReEmbeddingService(repo, embedder, batch_size=20)
    write_result = await memory_service.create_memory(user_id=user_id, memory_data=_memory("OLD-CONTENT"))
    memory = write_result.memory

    # Hold the rebuild inside generate_embedding(OLD text) ...
    embedder.gate_marker = "OLD-CONTENT"
    rebuild = asyncio.create_task(re_service.rebuild_targeted(user_id=user_id, memory_ids=[memory.id]))
    await asyncio.wait_for(embedder.reached.wait(), timeout=10)

    # ... while update_memory commits NEW content together with its fresh vector.
    embedder.gate_marker = None
    update_result = await memory_service.update_memory(
        user_id=user_id, memory_id=memory.id, updated_memory=MemoryUpdate(content="NEW-CONTENT"),
    )
    assert update_result.memory is not None
    assert update_result.memory.content == "NEW-CONTENT"
    new_vector = sqlite_vec.serialize_float32(embedder.vector("T NEW-CONTENT c k t"))
    assert await _vec_blob(db_adapter, memory.id) == new_vector

    embedder.release.set()
    result = await asyncio.wait_for(rebuild, timeout=10)

    assert await _vec_blob(db_adapter, memory.id) == new_vector
    assert result.rebuilt_ids == []
    assert result.skipped_ids == [memory.id]
    assert result.failed == []


async def test_upsert_targeted_embeddings_only_writes_rows_unchanged_since_read(stack):
    repo, db_adapter, embedder, user_id = stack
    first = await repo.create_memory(user_id, _memory("first"))
    second = await repo.create_memory(user_id, _memory("second"))
    first_read = await repo.get_memory_by_id(user_id, first.id)
    second_read = await repo.get_memory_by_id(user_id, second.id)
    original = {
        first.id: await _vec_blob(db_adapter, first.id),
        second.id: await _vec_blob(db_adapter, second.id),
    }
    new_vector = embedder.vector("refreshed")

    await asyncio.sleep(0.05)
    await repo.update_memory(
        user_id=user_id,
        memory_id=first.id,
        updated_memory=MemoryUpdate(content="edited after the read"),
        existing_memory=first_read,
        search_fields_changed=False,
    )

    written = await repo.upsert_targeted_embeddings(
        user_id=user_id,
        updates=[(first.id, new_vector), (second.id, new_vector)],
        expected_updated_at={first.id: first_read.updated_at, second.id: second_read.updated_at},
    )

    assert written == [second.id]
    assert await _vec_blob(db_adapter, first.id) == original[first.id]
    assert await _vec_blob(db_adapter, second.id) == sqlite_vec.serialize_float32(new_vector)


async def test_upsert_targeted_embeddings_without_expectation_still_writes(stack):
    repo, db_adapter, embedder, user_id = stack
    memory = await repo.create_memory(user_id, _memory("content"))
    new_vector = embedder.vector("refreshed")

    written = await repo.upsert_targeted_embeddings(user_id=user_id, updates=[(memory.id, new_vector)])

    assert written == [memory.id]
    assert await _vec_blob(db_adapter, memory.id) == sqlite_vec.serialize_float32(new_vector)


def _commit_edit_on_second_connection(db_file: str, memory_id: int, vector: bytes) -> str | None:
    """Do what a concurrent update_memory does, on its own connection: bump `updated_at` and swap the vector.

    Returns None when the edit committed, or the SQLite error text when it could not (no waiting).
    """
    conn = sqlite3.connect(db_file)
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.execute("PRAGMA busy_timeout=0")
        conn.execute("UPDATE memories SET updated_at = '2099-01-01 00:00:00.000000' WHERE id = ?", (memory_id,))
        conn.execute("DELETE FROM vec_memories WHERE memory_id = ?", (str(memory_id),))
        conn.execute("INSERT INTO vec_memories (memory_id, embedding) VALUES (?, ?)", (str(memory_id), vector))
        conn.commit()
        return None
    except sqlite3.OperationalError as exc:
        conn.rollback()
        return str(exc)
    finally:
        conn.close()


async def test_upsert_targeted_embeddings_version_check_is_atomic_with_the_write(file_stack):
    """An edit committed after the version check but before the vector write must not be overwritten.

    The edit is injected from a second connection right before the first `DELETE FROM vec_memories`,
    that is between the version check and the vector write. pysqlite starts a transaction only at the
    first DML statement, so a check done with a plain SELECT leaves exactly this gap open (the stale
    vector replaced the new one, silently). With the check done as the first write of the transaction
    the write lock is already held at that point, so the competing edit has to wait.
    """
    repo, db_adapter, embedder, user_id, db_file = file_stack
    memory = await repo.create_memory(user_id, _memory("OLD-CONTENT"))
    read = await repo.get_memory_by_id(user_id, memory.id)
    stale_vector = embedder.vector("computed from OLD-CONTENT")
    fresh_blob = sqlite_vec.serialize_float32(embedder.vector("computed from NEW-CONTENT"))

    competing_edits: list[str | None] = []

    def edit_between_check_and_write(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        if "DELETE FROM vec_memories" in statement and not competing_edits:
            competing_edits.append(_commit_edit_on_second_connection(db_file, memory.id, fresh_blob))

    sync_engine = db_adapter._engine.sync_engine
    event.listen(sync_engine, "before_cursor_execute", edit_between_check_and_write)
    try:
        written = await repo.upsert_targeted_embeddings(
            user_id=user_id,
            updates=[(memory.id, stale_vector)],
            expected_updated_at={memory.id: read.updated_at},
        )
    finally:
        event.remove(sync_engine, "before_cursor_execute", edit_between_check_and_write)

    assert len(competing_edits) == 1
    assert competing_edits[0] is not None, "the edit committed inside the check-to-write window"
    assert "locked" in competing_edits[0]
    assert written == [memory.id]

    # The edit has to wait for the batch, then lands on top of it (as update_memory would).
    assert _commit_edit_on_second_connection(db_file, memory.id, fresh_blob) is None
    assert await _vec_blob(db_adapter, memory.id) == fresh_blob


async def test_upsert_targeted_embeddings_skips_row_edited_on_another_connection(file_stack):
    repo, db_adapter, embedder, user_id, db_file = file_stack
    memory = await repo.create_memory(user_id, _memory("OLD-CONTENT"))
    read = await repo.get_memory_by_id(user_id, memory.id)
    fresh_blob = sqlite_vec.serialize_float32(embedder.vector("computed from NEW-CONTENT"))
    assert _commit_edit_on_second_connection(db_file, memory.id, fresh_blob) is None

    written = await repo.upsert_targeted_embeddings(
        user_id=user_id,
        updates=[(memory.id, embedder.vector("computed from OLD-CONTENT"))],
        expected_updated_at={memory.id: read.updated_at},
    )

    assert written == []
    assert await _vec_blob(db_adapter, memory.id) == fresh_blob


# ---------------------------------------------------------------------------
# failure reporting
# ---------------------------------------------------------------------------


async def test_failed_reasons_are_stable_codes_without_sql_or_vector_bytes(stack):
    repo, _db, embedder, user_id = stack
    for index in range(3):
        await repo.create_memory(user_id, _memory(f"content {index}"))
    embedder.wrong_dimension_marker = "content"

    ctx, adapters = _tool_adapters(repo, embedder, user_id)
    out = await adapters.rebuild_embeddings(ctx)

    assert out["rebuilt_ids"] == []
    assert len(out["failed"]) == 3
    for failure in out["failed"]:
        assert failure["reason"] == "persistence_failed"
        for marker in LEAK_MARKERS:
            assert marker not in failure["reason"]


async def test_batch_write_failure_blames_only_the_failing_memory(stack):
    repo, db_adapter, embedder, user_id = stack
    memories = [await repo.create_memory(user_id, _memory(f"content {index}")) for index in range(3)]
    embedder.wrong_dimension_marker = "content 1"
    original = {memory.id: await _vec_blob(db_adapter, memory.id) for memory in memories}

    result = await ReEmbeddingService(repo, embedder, batch_size=10).rebuild_targeted(user_id=user_id)

    assert result.failed == [{"memory_id": memories[1].id, "reason": "persistence_failed"}]
    assert sorted(result.rebuilt_ids) == [memories[0].id, memories[2].id]
    assert result.skipped_ids == []
    assert await _vec_blob(db_adapter, memories[1].id) == original[memories[1].id]
    for memory in (memories[0], memories[2]):
        expected = embedder.vector(f"T content {memory.id - memories[0].id} c k t")
        assert await _vec_blob(db_adapter, memory.id) == sqlite_vec.serialize_float32(expected)


# ---------------------------------------------------------------------------
# project scope validation
# ---------------------------------------------------------------------------


async def test_rebuild_embeddings_rejects_nonexistent_project(stack):
    repo, db_adapter, embedder, user_id = stack
    project_id = await _create_project(db_adapter, user_id)
    await repo.create_memory(user_id, _memory("content", project_id))
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    with pytest.raises(ToolError, match=r"VALIDATION_ERROR: project_id=999 not found or not owned"):
        await adapters.rebuild_embeddings(ctx, project_id=999)


async def test_rebuild_embeddings_rejects_foreign_project_without_rebuilding(stack):
    repo, db_adapter, embedder, user_id = stack
    owner_id = await _create_other_user(db_adapter)
    project_id = await _create_project(db_adapter, owner_id, name="owner project")
    owner_memory = await repo.create_memory(owner_id, _memory("owner content", project_id))
    before = await _vec_blob(db_adapter, owner_memory.id)
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    with pytest.raises(ToolError, match=rf"project_id={project_id} not found or not owned"):
        await adapters.rebuild_embeddings(ctx, project_id=project_id)

    assert await _vec_blob(db_adapter, owner_memory.id) == before


async def test_rebuild_embeddings_accepts_owned_project_with_and_without_memories(stack):
    repo, db_adapter, embedder, user_id = stack
    empty_project = await _create_project(db_adapter, user_id, name="empty")
    used_project = await _create_project(db_adapter, user_id, name="used")
    memory = await repo.create_memory(user_id, _memory("content", used_project))
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    empty = await adapters.rebuild_embeddings(ctx, project_id=empty_project)
    used = await adapters.rebuild_embeddings(ctx, project_id=used_project)

    assert empty == {"rebuilt_ids": [], "skipped_ids": [], "failed": []}
    assert used == {"rebuilt_ids": [memory.id], "skipped_ids": [], "failed": []}
