"""Bundle and memory-search migrations converge without losing upgrade paths."""
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from alembic import command


def test_skill_bundle_migration_roundtrip(tmp_path, monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    url = "sqlite:///" + str(tmp_path / "migration.db")
    config.set_main_option("sqlalchemy.url", url)
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "20261008_plan_external_ref")
            assert "skill_bundle_resources" not in inspect(connection).get_table_names()
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            inspector = inspect(connection)
            assert "skill_bundle_resources" in inspector.get_table_names()
            assert {r["name"] for r in inspector.get_unique_constraints("skill_bundle_resources")} == {"uq_skill_bundle_path"}
            assert {r["name"] for r in inspector.get_check_constraints("skill_bundle_resources")} == {"ck_skill_bundle_resource_kind"}
            assert len(inspector.get_foreign_keys("skill_bundle_resources")) == 4
    finally:
        engine.dispose()


def test_bundle_and_memory_search_share_one_head():
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    heads = scripts.get_heads()
    assert len(heads) == 1
    assert "20261111_skill_bundle_merge" in {
        revision.revision for revision in scripts.iterate_revisions(heads[0], "base")
    }
    assert set(scripts.get_revision("20261111_skill_bundle_merge").down_revision) == {
        "20261107_skill_bundle_resources", "20261103_memory_search_tsv",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("starting_revision", [
    None, "20261008_plan_external_ref", "20261103_memory_search_tsv",
    "20261107_skill_bundle_resources",
])
async def test_sqlite_startup_joins_both_migration_branches(
    tmp_path, monkeypatch, starting_revision,
):
    from sqlalchemy import text

    from app.config.settings import settings
    from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "upgrade.db"))
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    adapter = SqliteDatabaseAdapter()
    try:
        if starting_revision is not None:
            async with adapter._engine.begin() as connection:
                def prepare(sync_connection):
                    config.attributes["connection"] = sync_connection
                    command.upgrade(config, starting_revision)
                await connection.run_sync(prepare)
        await adapter.init_db()
        # A second startup must also work once both branches have converged.
        await adapter.init_db()
        async with adapter._engine.connect() as connection:
            versions = await connection.execute(text("SELECT version_num FROM alembic_version"))
            expected_heads = ScriptDirectory.from_config(config).get_heads()
            assert len(expected_heads) == 1
            assert versions.scalars().all() == expected_heads
            names = await connection.execute(text("SELECT name FROM sqlite_master"))
            assert {
                "skill_bundle_resources", "memories_fts", "memories_fts_src",
                "memories_fts_ai", "memories_fts_ad", "memories_fts_bu", "memories_fts_au",
            } <= set(names.scalars())
    finally:
        await adapter.dispose()
