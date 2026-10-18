"""The re-embed run on a real SQLite file: vector storage, skills, dry run and recovery.

Only the embedding provider is replaced. The service, repositories, backup tools and the
CLI entry point (in this process, or in a child process where a signal or a console
codec is involved) are the real ones.
"""

import argparse
import asyncio
import hashlib
import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config

import main
from alembic import command
from app.bootstrap import create_repositories
from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.skill_repository import SqliteSkillRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.services.re_embedding_service import ReEmbeddingService

ROOT = Path(__file__).resolve().parents[2]
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
    embedder = FakeEmbedder()
    memories = SqliteMemoryRepository(
        db_adapter=adapter, embedding_adapter=embedder, rerank_adapter=None,
    )
    skills = SqliteSkillRepository(
        db_adapter=adapter, embedding_adapter=embedder, rerank_adapter=None,
    )
    return adapter, memories, skills


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


def new_skill(name):
    return SkillCreate(
        name=name, description=f"Process pdf documents for {name}",
        content="# Steps\n1. open\n2. extract",
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
        adapter, _, _ = await open_stack()
        await adapter.dispose()
        use_new_dimensions(monkeypatch)
        adapter, memories, skills = await open_stack()
        try:
            assert vec_dimensions(db_file, "vec_memories") == OLD_DIMS  # init_db keeps it

            # Act
            result = await ReEmbeddingService(
                memories, FakeEmbedder(), skill_repository=skills,
            ).re_embed_all()

            # Assert: storage matches the configuration, so the next insert succeeds.
            assert result.validation.all_passed
            assert vec_dimensions(db_file, "vec_memories") == NEW_DIMS
            assert vec_dimensions(db_file, "vec_skills") == NEW_DIMS
            user_id = await create_user(adapter)
            assert (await memories.create_memory(user_id, new_memory("after"))).id is not None
            assert (await skills.create_skill(user_id, new_skill("after"))).id is not None
        finally:
            await adapter.dispose()

    async def test_cli_resizes_vector_storage_without_a_backup(
        self, db_file, monkeypatch, quiet_cli, capsys,
    ):
        adapter, _, _ = await open_stack()
        await adapter.dispose()
        use_new_dimensions(monkeypatch)

        await main._run_reembed(argparse.Namespace(batch_size=5, dry_run=False))

        assert "No memories to re-embed." in capsys.readouterr().out
        assert vec_dimensions(db_file, "vec_memories") == NEW_DIMS
        assert vec_dimensions(db_file, "vec_skills") == NEW_DIMS
        assert not list(db_file.parent.glob("*.bak-*"))  # nothing to protect


class TestSkills:
    async def test_skills_keep_working_after_a_dimension_change(self, db_file, monkeypatch):
        # Arrange: stored memories and skills, then a provider with wider vectors.
        adapter, memories, skills = await open_stack()
        user_id = await create_user(adapter)
        await memories.create_memory(user_id, new_memory("old memory"))
        await skills.create_skill(user_id, new_skill("pdf-processing"))
        await skills.create_skill(user_id, new_skill("docx-processing"))
        await adapter.dispose()
        use_new_dimensions(monkeypatch)
        adapter, memories, skills = await open_stack()
        try:
            # Act
            result = await ReEmbeddingService(
                memories, FakeEmbedder(), batch_size=1, skill_repository=skills,
            ).re_embed_all()

            # Assert: every skill has a fresh vector and creating or searching works.
            assert (result.total_skills, result.skills_processed) == (2, 2)
            assert result.validation.all_passed
            assert vec_dimensions(db_file, "vec_skills") == NEW_DIMS
            assert await skills.validate_embedding_count()
            await skills.create_skill(user_id, new_skill("xlsx-processing"))
            hits = await skills.search_skills(user_id=user_id, query="pdf", k=5)
            assert {hit.name for hit in hits} == {
                "pdf-processing", "docx-processing", "xlsx-processing",
            }
        finally:
            await adapter.dispose()

    async def test_cli_migrates_skills_even_when_the_skills_feature_is_off(
        self, db_file, monkeypatch, quiet_cli, capsys,
    ):
        # Arrange: skills stored while the feature was on; the re-embed runs with it off.
        adapter, _, skills = await open_stack()
        user_id = await create_user(adapter)
        await skills.create_skill(user_id, new_skill("pdf-processing"))
        await adapter.dispose()
        use_new_dimensions(monkeypatch)
        monkeypatch.setattr(settings, "SKILLS_ENABLED", False)

        # Act
        await main._run_reembed(argparse.Namespace(batch_size=5, dry_run=False))

        # Assert: skill vectors were rebuilt, a backup protected them, and they are searchable.
        out = capsys.readouterr().out
        assert "Skills to process: 1" in out
        assert list(db_file.parent.glob("*.bak-*"))
        assert vec_dimensions(db_file, "vec_skills") == NEW_DIMS
        adapter, _, skills = await open_stack()
        try:
            hits = await skills.search_skills(user_id=user_id, query="pdf", k=5)
            assert [hit.name for hit in hits] == ["pdf-processing"]
        finally:
            await adapter.dispose()


class TestDryRun:
    @pytest.fixture
    def older_schema(self, db_file):
        """A database one release behind, built the way that release's server built it."""
        async def build(revision):
            db_file.parent.mkdir(parents=True, exist_ok=True)
            config = Config(str(ROOT / "alembic.ini"))
            config.set_main_option("script_location", str(ROOT / "alembic"))
            # env.py reads settings.SQLITE_PATH and starts its own event loop.
            await asyncio.to_thread(command.upgrade, config, revision)
        return build

    @staticmethod
    def schema(path):
        connection = sqlite3.connect(path)
        try:
            version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'",
            )}
        finally:
            connection.close()
        return version, tables

    async def test_dry_run_does_not_migrate_the_schema(
        self, db_file, older_schema, quiet_cli, capsys,
    ):
        await older_schema("20260408_provenance_all")
        before = self.schema(db_file)

        await main._run_reembed(argparse.Namespace(batch_size=20, dry_run=True))

        out = capsys.readouterr().out
        assert "Memories to process: 0" in out
        assert "No changes were made." in out
        assert self.schema(db_file) == before
        assert "vec_memories" not in before[1]  # still no vector tables either

    async def test_dry_run_counts_a_database_that_predates_skills(
        self, db_file, older_schema, quiet_cli, capsys,
    ):
        await older_schema("20260315_files")  # before the skills table existed
        before = self.schema(db_file)

        await main._run_reembed(argparse.Namespace(batch_size=20, dry_run=True))

        assert "Would re-embed 0 memories" in capsys.readouterr().out
        assert self.schema(db_file) == before

    async def test_dry_run_does_not_create_a_missing_database(self, db_file, quiet_cli, capsys):
        await main._run_reembed(argparse.Namespace(batch_size=20, dry_run=True))

        assert "Memories to process: 0" in capsys.readouterr().out
        assert not db_file.exists()

    async def test_dry_run_reports_counts_and_leaves_vector_storage_alone(
        self, db_file, monkeypatch, quiet_cli, capsys,
    ):
        adapter, memories, skills = await open_stack()
        user_id = await create_user(adapter)
        await memories.create_memory(user_id, new_memory("one"))
        await memories.create_memory(user_id, new_memory("two"))
        await skills.create_skill(user_id, new_skill("pdf-processing"))
        await adapter.dispose()
        use_new_dimensions(monkeypatch)

        await main._run_reembed(argparse.Namespace(batch_size=20, dry_run=True))

        out = capsys.readouterr().out
        assert "Memories to process: 2" in out
        assert "Skills to process: 1" in out
        assert "Would re-embed 2 memories and 1 skills" in out
        assert vec_dimensions(db_file, "vec_memories") == OLD_DIMS
        assert vec_dimensions(db_file, "vec_skills") == OLD_DIMS
        assert not list(db_file.parent.glob("*.bak-*"))


def test_sqlite_skill_repository_is_available_without_the_feature_flag(monkeypatch):
    """Re-embedding must reach skill vectors even when SKILLS_ENABLED is off."""
    from app.bootstrap import create_db_adapter, create_skill_repository

    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SKILLS_ENABLED", False)
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)

    adapter = create_db_adapter()
    repository = create_skill_repository(adapter, FakeEmbedder())

    assert isinstance(repository, SqliteSkillRepository)
