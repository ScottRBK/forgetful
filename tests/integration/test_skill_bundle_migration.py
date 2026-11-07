"""A fresh SQLite file can traverse the package migration in both directions."""
from pathlib import Path

from alembic.config import Config
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
            command.downgrade(config, "-1")
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
