"""E2E smoke test: CLI LocalExecutor against real PostgreSQL

docs/dev/cli_plan.md section 6: one passthrough create/query smoke test to prove the
CLI runtime is DB-agnostic. The CLI logic itself is covered exhaustively by the
integration and e2e_sqlite suites; no duplication here.
"""
import pytest

from app.bootstrap import build_runtime
from app.config.settings import settings
from app.routes.cli.local_executor import LocalExecutor

pytestmark = pytest.mark.asyncio(loop_scope="session")

_PATCHED_FIELDS = [
    "DATABASE",
    "POSTGRES_HOST",
    "EMBEDDING_PROVIDER",
    "RERANKING_ENABLED",
    "FORGETFUL_SCOPES",
    "SKILLS_ENABLED",
    "FILES_ENABLED",
    "PLANNING_ENABLED",
    "ACTIVITY_ENABLED",
]


@pytest.mark.e2e
async def test_cli_local_executor_create_and_query_against_postgres(postgres_container):
    original = {name: getattr(settings, name) for name in _PATCHED_FIELDS}
    settings.DATABASE = "Postgres"
    settings.POSTGRES_HOST = "127.0.0.1"
    settings.EMBEDDING_PROVIDER = "FastEmbed"
    settings.RERANKING_ENABLED = False
    settings.FORGETFUL_SCOPES = "*"
    settings.SKILLS_ENABLED = False
    settings.FILES_ENABLED = False
    settings.PLANNING_ENABLED = False
    settings.ACTIVITY_ENABLED = False

    try:
        executor = LocalExecutor(await build_runtime())
        try:
            created = await executor.execute(
                "create_memory",
                {
                    "title": "CLI Postgres smoke memory",
                    "content": "Created through LocalExecutor against real PostgreSQL",
                    "context": "Proving the CLI runtime is DB-agnostic",
                    "keywords": ["cli", "postgres"],
                    "tags": ["testing"],
                    "importance": 5,
                },
            )
            assert created.id is not None

            found = await executor.execute(
                "query_memory",
                {
                    "query": "CLI Postgres smoke",
                    "query_context": "cli postgres e2e smoke test",
                },
            )
            assert any(memory.id == created.id for memory in found.primary_memories)
        finally:
            await executor.close()
    finally:
        for name, value in original.items():
            setattr(settings, name, value)
