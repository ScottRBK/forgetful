"""Database URL handling and alembic.ini safety, without a running database.

- credentials with URL-special characters survive the round trip into SQLAlchemy
- a `%` in the URL no longer breaks Alembic's ConfigParser-backed options
- alembic/env.py builds the same escaped URL for its own (command line) engine
- alembic.ini never puts the working directory on sys.path
"""

import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from alembic import command
from app.config.settings import settings
from app.repositories.postgres.postgres_adapter import PostgresDatabaseAdapter
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

CREDENTIALS = [
    pytest.param("forgetful", "forgetful", id="plain"),
    pytest.param("forgetful", "p@ss", id="at-sign"),
    pytest.param("forgetful", "p%ss", id="percent"),
    pytest.param("forgetful", "p%40ss", id="pre-encoded"),
    pytest.param("forgetful", "100%", id="trailing-percent"),
    pytest.param("forgetful", "a:b/c?d#e", id="reserved-characters"),
    pytest.param("us@er:name", "pä ss+word", id="special-user-and-unicode"),
]


@pytest.fixture
def postgres_settings(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "Postgres")
    monkeypatch.setattr(settings, "POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setattr(settings, "PGPORT", 5099)
    monkeypatch.setattr(settings, "POSTGRES_DB", "forgetful")


def use_credentials(monkeypatch, user, password):
    monkeypatch.setattr(settings, "POSTGRES_USER", user)
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", password)


def assert_url_matches_settings(url):
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+asyncpg"
    assert (parsed.username, parsed.password) == (
        settings.POSTGRES_USER, settings.POSTGRES_PASSWORD,
    )
    assert (parsed.host, parsed.port, parsed.database) == ("127.0.0.1", 5099, "forgetful")


class TestPostgresConnectionString:
    @pytest.mark.parametrize(("user", "password"), CREDENTIALS)
    def test_credentials_round_trip(self, postgres_settings, monkeypatch, user, password):
        use_credentials(monkeypatch, user, password)
        adapter = PostgresDatabaseAdapter()

        assert_url_matches_settings(adapter.construct_postgres_connection_string())
        # The engine itself must be built from the same, correctly parsed credentials.
        assert (adapter._engine.url.username, adapter._engine.url.password) == (user, password)
        assert adapter._engine.url.host == "127.0.0.1"


class TestAlembicUrlOption:
    """`Config.set_main_option` interpolates `%`, so a raw URL with one raises ValueError."""

    @pytest.fixture
    def captured_config(self, monkeypatch):
        captured = []
        monkeypatch.setattr(command, "upgrade", lambda config, revision: captured.append(config))
        return captured

    @pytest.mark.parametrize(("user", "password"), CREDENTIALS)
    def test_postgres_migrations_accept_special_credentials(
        self, postgres_settings, monkeypatch, captured_config, user, password,
    ):
        use_credentials(monkeypatch, user, password)
        adapter = PostgresDatabaseAdapter()

        adapter._run_migrations(connection=object())

        (config,) = captured_config
        assert config.get_main_option("sqlalchemy.url") == adapter.construct_postgres_connection_string()
        assert_url_matches_settings(config.get_main_option("sqlalchemy.url"))

    def test_sqlite_migrations_accept_percent_in_path(self, tmp_path, monkeypatch, captured_config):
        monkeypatch.setattr(settings, "DATABASE", "SQLite")
        monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
        monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "50%" / "100%25" / "forgetful.db"))
        adapter = SqliteDatabaseAdapter()

        adapter._run_migrations(connection=object())

        (config,) = captured_config
        assert config.get_main_option("sqlalchemy.url") == adapter._construct_connection_string()
        assert "50%/100%25" in config.get_main_option("sqlalchemy.url")


class TestEnvPyDatabaseUrl:
    """The command line path (`alembic upgrade head`) builds its own engine from settings."""

    class Stop(Exception):
        """Raised by the stand-ins to end the run once the URL has been captured."""

    @pytest.mark.parametrize(("user", "password"), CREDENTIALS)
    def test_online_engine_url_escapes_credentials(
        self, postgres_settings, monkeypatch, user, password,
    ):
        use_credentials(monkeypatch, user, password)
        captured = {}

        def fake_engine(configuration, **kwargs):
            captured.update(configuration)
            raise self.Stop

        monkeypatch.setattr("sqlalchemy.ext.asyncio.async_engine_from_config", fake_engine)

        with pytest.raises(self.Stop):
            command.upgrade(Config(str(ALEMBIC_INI)), "head")

        assert_url_matches_settings(captured["sqlalchemy.url"])

    @pytest.mark.parametrize(("user", "password"), CREDENTIALS)
    def test_offline_url_escapes_credentials(
        self, postgres_settings, monkeypatch, user, password,
    ):
        use_credentials(monkeypatch, user, password)
        captured = {}

        def fake_configure(environment, *args, **kwargs):
            captured.update(kwargs)
            raise self.Stop

        monkeypatch.setattr(
            "alembic.runtime.environment.EnvironmentContext.configure", fake_configure,
        )

        with pytest.raises(self.Stop):
            command.upgrade(Config(str(ALEMBIC_INI)), "head", sql=True)

        assert_url_matches_settings(captured["url"])


class TestAlembicDoesNotTrustWorkingDirectory:
    def test_configured_sys_path_entries_are_absolute_and_inside_the_project(self):
        entries = Config(str(ALEMBIC_INI)).get_prepend_sys_paths_list() or []

        for entry in entries:
            assert Path(entry).is_absolute(), f"cwd-relative sys.path entry: {entry!r}"
            assert Path(entry).resolve() == ALEMBIC_INI.parent, entry

    def test_script_directory_does_not_prepend_the_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Drop any "" or "." left behind by earlier tests so only new entries are inspected.
        monkeypatch.setattr(sys, "path", [p for p in sys.path if p not in ("", ".")])
        before = list(sys.path)

        ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))

        added = [entry for entry in sys.path if entry not in before]
        assert [entry for entry in added if Path(entry).resolve() == tmp_path.resolve()] == []
        assert "." not in sys.path
