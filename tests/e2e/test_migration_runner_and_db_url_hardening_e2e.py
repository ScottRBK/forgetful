"""PostgreSQL start-up: credentials with special characters and concurrent first starts.

Every test works in a throw-away database on the shared container, so it neither needs
nor disturbs the schema the other e2e tests use.
"""

import asyncio
import os
import subprocess
import sys
import textwrap
import time
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


async def stamped_revisions(admin_engine, database):
    engine = create_async_engine(
        build_postgres_url().set(
            username="forgetful", password="forgetful", database=database,
        ),
    )
    try:
        async with engine.connect() as connection:
            rows = await connection.execute(text("SELECT version_num FROM alembic_version"))
            return [row[0] for row in rows]
    finally:
        await engine.dispose()


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


async def test_init_db_waits_for_the_migration_lock(admin_engine, scratch_database):
    from app.repositories.postgres.postgres_adapter import MIGRATION_LOCK_KEY

    # Advisory locks are scoped to one database, so the holder has to be connected to the
    # same database the adapter is about to initialise.
    adapter = PostgresDatabaseAdapter()
    holder_engine = create_async_engine(build_postgres_url(), isolation_level="AUTOCOMMIT")
    holder = await holder_engine.connect()
    try:
        await holder.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK_KEY})
        starting = asyncio.create_task(adapter.init_db())

        done, _ = await asyncio.wait({starting}, timeout=2)
        assert not done, "init_db ran its migrations while another process held the lock"

        await holder.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK_KEY})
        await asyncio.wait_for(starting, timeout=120)
    finally:
        await holder.close()
        await holder_engine.dispose()
        await adapter.dispose()

    assert await stamped_revisions(admin_engine, scratch_database)


async def test_simultaneous_first_starts_all_succeed(admin_engine, scratch_database, tmp_path):
    """Alembic keeps process-global state, so the race has to be run across processes."""
    runner = tmp_path / "run_init_db.py"
    runner.write_text(textwrap.dedent(f"""
        import asyncio
        import sys
        import time

        sys.path.insert(0, {str(PROJECT_ROOT)!r})
        from app.repositories.postgres.postgres_adapter import PostgresDatabaseAdapter


        async def main():
            adapter = PostgresDatabaseAdapter()
            while time.time() < float(sys.argv[1]):  # release every process together
                await asyncio.sleep(0.0005)
            try:
                await adapter.init_db()
                print("OK")
            except Exception as error:
                print("FAIL", type(error).__name__, str(error)[:200])
                sys.exit(1)
            finally:
                await adapter.dispose()


        asyncio.run(main())
    """))
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update(
        DATABASE="Postgres",
        POSTGRES_HOST="127.0.0.1",
        PGPORT=str(settings.PGPORT),
        POSTGRES_USER="forgetful",
        POSTGRES_PASSWORD="forgetful",
        POSTGRES_DB=scratch_database,
        LOG_LEVEL="ERROR",
    )
    start = time.time() + 8  # imports take a few seconds; start only once all are ready
    processes = [
        subprocess.Popen(  # noqa: S603 - test-controlled arguments, no shell
            [sys.executable, str(runner), str(start)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        for _ in range(3)
    ]
    outputs = [process.communicate(timeout=180)[0] for process in processes]

    assert [process.returncode for process in processes] == [0, 0, 0], outputs
    assert len(await stamped_revisions(admin_engine, scratch_database)) == 1
