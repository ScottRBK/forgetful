"""The re-embed run on a real SQLite file: vector storage, skills, dry run and recovery.

Only the embedding provider is replaced. The service, repositories, backup tools and the
CLI entry point (in this process, or in a child process where a signal or a console
codec is involved) are the real ones.
"""

import argparse
import hashlib
import sqlite3

import pytest

import main
from app.bootstrap import create_repositories
from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.services.re_embedding_service import ReEmbeddingService

OLD_DIMS = 4
NEW_DIMS = 6


class FakeEmbedder:
    """Deterministic embedder whose output width follows the (changeable) configuration."""

    async def generate_embedding(self, text):
        digest = hashlib.sha256(text.encode()).digest()
        return [(digest[i] / 255.0) + 0.01 for i in range(settings.EMBEDDING_DIMENSIONS)]


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    """A file-backed SQLite configuration, first used with OLD_DIMS-wide vectors."""
    path = tmp_path / "data" / "forgetful.db"
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(path))
    monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", OLD_DIMS)
    return path


@pytest.fixture
def quiet_cli(monkeypatch):
    """Run main._run_reembed in this process without reconfiguring the test's logging."""
    import app.bootstrap
    import app.config.logging_config

    monkeypatch.setattr(app.config.logging_config, "configure_logging", lambda **_: None)
    monkeypatch.setattr(main.atexit, "register", lambda *_: None)
    monkeypatch.setattr(app.bootstrap, "get_embedding_adapter", FakeEmbedder)


async def open_stack():
    """Open the database the way a freshly started process would, then wire repositories."""
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    memories = SqliteMemoryRepository(
        db_adapter=adapter, embedding_adapter=FakeEmbedder(), rerank_adapter=None,
    )
    return adapter, memories


async def create_user(adapter):
    repos = create_repositories(adapter, FakeEmbedder(), None)
    user = await repos["user"].create_user(UserCreate(
        external_id="reembed-run-flow", name="Run Flow", email="run-flow@example.test",
    ))
    return user.id


def new_memory(title):
    return MemoryCreate(
        title=title, content=f"{title} content", context="run flow",
        keywords=["run"], tags=["flow"], importance=7,
    )


def vec_dimensions(path, table):
    """Width of a vec0 table, read from its definition without opening the application."""
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?", (table,),
        ).fetchone()
    finally:
        connection.close()
    return int(row[0].split("FLOAT[")[1].split("]")[0])


def use_new_dimensions(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", NEW_DIMS)


class TestEmptyDatabase:
    async def test_re_embed_all_resizes_vector_storage(self, db_file, monkeypatch):
        # Arrange: a database that never stored anything, then a wider embedding model.
        adapter, _ = await open_stack()
        await adapter.dispose()
        use_new_dimensions(monkeypatch)
        adapter, memories = await open_stack()
        try:
            assert vec_dimensions(db_file, "vec_memories") == OLD_DIMS  # init_db keeps it

            # Act
            result = await ReEmbeddingService(memories, FakeEmbedder()).re_embed_all()

            # Assert: storage matches the configuration, so the next insert succeeds.
            assert result.validation.all_passed
            assert vec_dimensions(db_file, "vec_memories") == NEW_DIMS
            user_id = await create_user(adapter)
            assert (await memories.create_memory(user_id, new_memory("after"))).id is not None
        finally:
            await adapter.dispose()

    async def test_cli_resizes_vector_storage_without_a_backup(
        self, db_file, monkeypatch, quiet_cli, capsys,
    ):
        adapter, _ = await open_stack()
        await adapter.dispose()
        use_new_dimensions(monkeypatch)

        await main._run_reembed(argparse.Namespace(batch_size=5, dry_run=False))

        assert "No memories to re-embed." in capsys.readouterr().out
        assert vec_dimensions(db_file, "vec_memories") == NEW_DIMS
        assert not list(db_file.parent.glob("*.bak-*"))  # nothing to protect
