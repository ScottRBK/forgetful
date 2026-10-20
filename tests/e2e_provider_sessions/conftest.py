"""Real file SQLite / opt-in isolated PostgreSQL, with only providers replaced.

PostgreSQL requires -m e2e and SESSION_TEST_POSTGRES_PORT for a disposable pgvector
server on 127.0.0.1. Credentials come from settings.POSTGRES_USER/POSTGRES_PASSWORD;
the role must be able to create databases and install pgvector. CI fails if opt-in is
missing. Each test creates/drops its own database, never the configured application DB.
"""
import asyncio
import os
from dataclasses import dataclass
from uuid import uuid4

import asyncpg
import pytest
from fastmcp import Client, FastMCP
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app import bootstrap
from app.config.settings import settings
from app.repositories.postgres import postgres_adapter
from app.repositories.sqlite import sqlite_adapter
from app.routes.api import memories, projects, skills
from app.routes.mcp import meta_tools


class Embeddings:
    """Deterministic, nonzero vectors; a gate controls external provider latency."""

    def __init__(self):
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.block = False
        self.fail = False
        self.block_text = None
        self.calls = []

    async def generate_embedding(self, text):
        self.calls.append(text)
        if self.block and (self.block_text is None or text == self.block_text):
            self.entered.set()
            await self.release.wait()
        if self.fail:
            raise RuntimeError("test embedding provider unavailable")
        if "new-topic" in text:
            vector = [0.0, 1.0]
        elif "candidate-" in text:
            number = int(text.split("candidate-")[1].split()[0])
            vector = [1.0, number / 10]
        else:
            vector = [1.0, 0.0]
        return vector + [0.0] * (settings.EMBEDDING_DIMENSIONS - 2)


class Reranker:
    def __init__(self):
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.block = False
        self.calls = []

    async def rerank(self, query, documents):
        self.calls.append((query, list(documents)))
        if self.block:
            self.entered.set()
            await self.release.wait()
        return [(i, 1.0) for i in reversed(range(len(documents)))]


@dataclass
class App:
    http: AsyncClient
    mcp: Client
    embedding: Embeddings
    reranker: Reranker
    runtime: bootstrap.Runtime
    backend: str


@pytest.fixture(params=["SQLite", pytest.param("Postgres", marks=pytest.mark.e2e)])
async def app(request, monkeypatch, tmp_path):
    backend = request.param
    admin = None
    database = None
    database_created = False
    runtime = None
    try:
        if backend == "Postgres":
            port = os.environ.get("SESSION_TEST_POSTGRES_PORT")
            if not port:
                message = "SESSION_TEST_POSTGRES_PORT not set (isolated pgvector required)"
                if os.environ.get("CI"):
                    pytest.fail(message)
                pytest.skip(message)
            admin = await asyncpg.connect(
                host="127.0.0.1", port=int(port), database="postgres",
                user=settings.POSTGRES_USER, password=settings.POSTGRES_PASSWORD,
            )
            database = f"provider_sessions_{uuid4().hex}"
            await admin.execute(f'CREATE DATABASE "{database}"')
            database_created = True
            monkeypatch.setattr(settings, "POSTGRES_HOST", "127.0.0.1")
            monkeypatch.setattr(settings, "PGPORT", int(port))
            monkeypatch.setattr(settings, "POSTGRES_DB", database)

        monkeypatch.setattr(settings, "DATABASE", backend)
        monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
        monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "sessions.db"))
        monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
        monkeypatch.setattr(settings, "FILES_ENABLED", False)
        monkeypatch.setattr(settings, "PLANNING_ENABLED", False)
        monkeypatch.setattr(settings, "ACTIVITY_ENABLED", False)
        monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", "")
        monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
        monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
        monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 4)
        monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", 384)
        monkeypatch.setattr(settings, "DEFAULT_USER_ID", "session-alice")
        monkeypatch.setattr(settings, "DEFAULT_USER_EMAIL", "alice@example.test")
        monkeypatch.setattr(settings, "FORGETFUL_SCOPES", "*")

        # Configure the real engine, retaining the adapter's extension/session wiring.
        # This is fixture setup, not a mocked database or a new production test seam.
        def one_slot_engine(*args, **kwargs):
            return create_async_engine(*args, **kwargs, pool_size=1, max_overflow=0, pool_timeout=2)

        module = sqlite_adapter if backend == "SQLite" else postgres_adapter
        monkeypatch.setattr(module, "create_async_engine", one_slot_engine)
        embedding, reranker = Embeddings(), Reranker()
        monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: embedding)
        monkeypatch.setattr(bootstrap, "get_reranker_adapter", lambda: reranker)
        runtime = await bootstrap.build_runtime()
        mcp = FastMCP("provider-session-tests")
        for name, service in vars(runtime.services).items():
            setattr(mcp, f"{name}_service", service)
        mcp.registry = runtime.registry
        mcp._instance_permitted_tools = runtime.permitted_tools
        mcp._instance_scopes = runtime.instance_scopes
        memories.register(mcp)
        projects.register(mcp)
        skills.register(mcp)
        meta_tools.register(mcp)
        async with Client(mcp) as client:
            transport = ASGITransport(app=mcp.http_app(), raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as http:
                yield App(http, client, embedding, reranker, runtime, backend)
    finally:
        try:
            if runtime is not None:
                await bootstrap.dispose_runtime(runtime)
        finally:
            if admin is not None:
                try:
                    if database_created:
                        await admin.execute(f'DROP DATABASE "{database}" WITH (FORCE)')
                finally:
                    await admin.close()
