"""Shared backup checks: real databases and CLI, with only the provider replaced."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

from app.bootstrap import create_backup_service
from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate


class BackupTestEmbeddings:
    """Use one known vector when seeding, and a different vector during migration."""

    def __init__(self, failure=None):
        self.failure = failure
        self.calls = 0

    async def generate_embedding(self, text):
        self.calls += 1
        # Three memories, batch size one: fail after a committed batch, or in validation.
        fail_at = {"provider_error": 2, "search_error": 4}.get(self.failure)
        if self.calls == fail_at:
            raise RuntimeError("Deliberate backup test provider failure")
        vector = [0.0] * settings.EMBEDDING_DIMENSIONS
        vector[1 if self.failure else 0] = 1.0
        return vector


async def seed_memories(repos):
    user = await repos["user"].create_user(UserCreate(
        external_id="backup-test-user", name="Backup Test", email="backup@example.test",
    ))
    repo = repos["memory"]
    memories = []
    for index in range(3):
        memories.append(await repo.create_memory(user.id, MemoryCreate(
            title=f"Original memory {index}", content=f"Original content {index}",
            context="Backup regression", keywords=["backup", str(index)],
            tags=["original"], importance=7,
        )))
    await repo.create_links_batch(user.id, memories[0].id, [memories[1].id])
    await repo.mark_obsolete(user.id, memories[2].id, "Replaced", memories[0].id)
    originals = [await repo.get_memory_by_id(user.id, item.id) for item in memories]
    return user.id, originals


async def assert_originals_restored(repo, user_id, originals):
    """Check content, metadata, links, lifecycle state, and vector search results."""
    assert await repo.count_all_memories() == 3
    for original in originals:
        assert await repo.get_memory_by_id(user_id, original.id) == original
    assert await repo.validate_embedding_count()
    assert await repo.validate_embedding_dimensions()
    found = await repo.search_scored(
        user_id=user_id, query="original vector", query_context="backup test", k=10,
        importance_threshold=None, project_ids=None, exclude_ids=None,
    )
    assert {item.id for item, _ in found} == {originals[0].id, originals[1].id}
    assert [score.similarity for _, score in found] == pytest.approx([1.0, 1.0])
    obsolete = await repo.find_obsolete_matches(
        user_id, originals[0].id, limit=3, min_similarity=0.89,
    )
    assert [item.id for item, _ in obsolete] == [originals[2].id]
    assert obsolete[0][1] == pytest.approx(1.0)


async def run_reembed_cli(failure):
    """Run the public CLI in its own process, including its real backup and restore."""
    env = os.environ.copy()
    # Pass the fixture's configuration, not the developer's default database location.
    for name in (
        "DATABASE", "SQLITE_PATH", "SQLITE_MEMORY", "POSTGRES_HOST", "PGPORT",
        "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "EMBEDDING_DIMENSIONS",
    ):
        env[name] = str(getattr(settings, name))
    env["RERANKING_ENABLED"] = "false"
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "tests.backup_restore_cases", failure,
        cwd=Path(__file__).resolve().parents[1], env=env,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
    return process.returncode, stdout.decode(), stderr.decode()


class BackupRestoreCases:
    async def test_backup_restores_memories_and_vectors(self, backup_database):
        # Arrange: real committed data, including links and an obsolete memory.
        adapter, repos = backup_database
        repo = repos["memory"]
        user_id, originals = await seed_memories(repos)
        if settings.DATABASE == "SQLite":
            # Keep SQLite open so the backup must include committed data still in its WAL.
            assert Path(f"{settings.SQLITE_PATH}-wal").stat().st_size > 0
        backup = create_backup_service()
        backup_path = await backup.create_backup()

        # Act: change data and reset vector storage, then restore the saved database.
        await repo.create_memory(user_id, MemoryCreate(
            title="Added after backup", content="Must disappear after restore",
            context="Backup regression", keywords=["added"], tags=["new"], importance=5,
        ))
        await repo.reset_embedding_storage()
        assert await repo.count_all_memories() == 4
        assert not await repo.validate_embedding_count()
        await adapter.dispose()
        await backup.restore_backup(backup_path)

        # Assert through fresh connections, as a restarted application would see it.
        await assert_originals_restored(repo, user_id, originals)

    @pytest.mark.parametrize("failure", ["provider_error", "search_error"])
    async def test_failed_cli_rebuild_restores_backup(self, backup_database, failure):
        # Arrange: the child process uses real repositories and backup tools.
        adapter, repos = backup_database
        user_id, originals = await seed_memories(repos)
        await adapter.dispose()

        # Act: save a changed batch, then fail in generation or final validation.
        returncode, stdout, stderr = await run_reembed_cli(failure)

        # Assert: failure is reported and automatic recovery restores the original data.
        assert returncode != 0, stdout + stderr
        assert "1/3 memories" in stdout, stdout + stderr
        assert "ERROR: Deliberate backup test provider failure" in stdout, stdout + stderr
        if failure == "search_error":
            assert "3/3 memories" in stdout, stdout + stderr
        assert "Database returned to pre-migration state." in stdout, stdout + stderr
        await assert_originals_restored(repos["memory"], user_id, originals)


if __name__ == "__main__":
    # Replace the external embedding provider only. CLI dispatch and recovery stay real.
    import app.bootstrap
    from main import cli

    provider = BackupTestEmbeddings(failure=sys.argv[1])
    app.bootstrap.get_embedding_adapter = lambda: provider
    sys.argv = ["forgetful", "re-embed", "--batch-size", "1"]
    sys.exit(cli())
