"""PostgreSQL start-up with special characters in the password.

Every test works in a throw-away database on the shared container, so it neither needs
nor disturbs the schema the other e2e tests use.
"""

import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import settings
from app.repositories.postgres.postgres_adapter import (
    PostgresDatabaseAdapter,
    build_postgres_url,
)

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECIAL_PASSWORD = "p@ss%w:rd/?#40"


@pytest_asyncio.fixture(loop_scope="session")
async def admin_engine(postgres_container):
    engine = create_async_engine(
        build_postgres_url().set(
            username="forgetful", password="forgetful", host="127.0.0.1", database="postgres",
        ),
        isolation_level="AUTOCOMMIT",
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def scratch_database(admin_engine, monkeypatch):
    """An empty database that the adapter under test will be pointed at."""
    name = f"migration_hardening_{uuid.uuid4().hex[:12]}"
    async with admin_engine.connect() as connection:
        await connection.execute(text(f'CREATE DATABASE "{name}"'))
    monkeypatch.setattr(settings, "DATABASE", "Postgres")
    monkeypatch.setattr(settings, "POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setattr(settings, "POSTGRES_USER", "forgetful")
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", "forgetful")
    monkeypatch.setattr(settings, "POSTGRES_DB", name)
    yield name
    async with admin_engine.connect() as connection:
        await connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


async def test_init_db_with_special_characters_in_the_password(
    admin_engine, scratch_database, monkeypatch,
):
    role = f"special_{uuid.uuid4().hex[:10]}"
    async with admin_engine.connect() as connection:
        await connection.execute(
            text(f"CREATE ROLE \"{role}\" LOGIN SUPERUSER PASSWORD '{SPECIAL_PASSWORD}'"),
        )
    monkeypatch.setattr(settings, "POSTGRES_USER", role)
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", SPECIAL_PASSWORD)
    adapter = PostgresDatabaseAdapter()
    try:
        await adapter.init_db()
        async with adapter.system_session() as session:
            current_user = (await session.execute(text("SELECT current_user"))).scalar_one()
    finally:
        await adapter.dispose()
        async with admin_engine.connect() as connection:
            await connection.execute(text(f'DROP DATABASE IF EXISTS "{scratch_database}" WITH (FORCE)'))
            await connection.execute(text(f'DROP ROLE IF EXISTS "{role}"'))

    assert current_user == role
