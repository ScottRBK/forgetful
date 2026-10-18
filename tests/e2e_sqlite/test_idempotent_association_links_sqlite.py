"""Association links on the real SQLite stack must be idempotent and report real creations.

Covers entity<->memory and entity<->project links. Concurrent identical link requests
(parallel tool calls, retries) must all succeed and leave exactly one association row,
and the activity log must only record a link as created once.

A file-backed database is used so that every concurrent call gets its own connection.
"""
import asyncio
from dataclasses import dataclass

import pytest

from app.config.settings import settings
from app.events import EventBus
from app.models.activity_models import ActionType
from app.models.activity_models import EntityType as ActivityEntityType
from app.models.entity_models import EntityCreate, EntityType
from app.models.memory_models import MemoryCreate
from app.models.project_models import ProjectCreate, ProjectType
from app.models.user_models import UserCreate
from app.repositories.sqlite.entity_repository import SqliteEntityRepository
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.project_repository import SqliteProjectRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.entity_service import EntityService

CONCURRENT_CALLS = 6


class CollectingEventBus(EventBus):
    """Real event bus that also records every emitted event."""

    def __init__(self):
        super().__init__()
        self.collected = []

    async def emit(self, event):
        self.collected.append(event)
        await super().emit(event)


class FakeEmbeddings:
    async def generate_embedding(self, text: str) -> list[float]:
        return [0.01] * settings.EMBEDDING_DIMENSIONS


@dataclass
class Stack:
    user_id: object
    entity_service: EntityService
    event_bus: CollectingEventBus
    projects: SqliteProjectRepository
    memories: SqliteMemoryRepository


@pytest.fixture
async def stack(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "links.db"))
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    try:
        user = await SqliteUserRepository(db_adapter=adapter).create_user(
            UserCreate(external_id="ext-links", name="u", email="u@example.com"),
        )
        event_bus = CollectingEventBus()
        embeddings = FakeEmbeddings()
        yield Stack(
            user_id=user.id,
            entity_service=EntityService(
                SqliteEntityRepository(db_adapter=adapter), event_bus=event_bus,
            ),
            event_bus=event_bus,
            projects=SqliteProjectRepository(db_adapter=adapter),
            memories=SqliteMemoryRepository(
                db_adapter=adapter, embedding_adapter=embeddings,
            ),
        )
    finally:
        await adapter.dispose()


async def _new_entity(stack: Stack, name: str):
    return await stack.entity_service.create_entity(
        stack.user_id, EntityCreate(name=name, entity_type=EntityType.ORGANIZATION),
    )


async def _new_target(stack: Stack, kind: str) -> int:
    """Create a project or memory that entities can be linked to."""
    if kind == "project":
        project = await stack.projects.create_project(
            stack.user_id,
            ProjectCreate(
                name="p", description="d", project_type=ProjectType.DEVELOPMENT,
            ),
        )
        return project.id
    memory = await stack.memories.create_memory(
        stack.user_id,
        MemoryCreate(
            title="m", content="c", context="x", keywords=["k"], tags=["t"], importance=7,
        ),
    )
    return memory.id


def _link(stack: Stack, kind: str):
    service = stack.entity_service
    return service.link_entity_to_project if kind == "project" else service.link_entity_to_memory


async def _linked_target_ids(stack: Stack, kind: str, entity_id: int) -> list[int]:
    if kind == "project":
        entity = await stack.entity_service.get_entity(stack.user_id, entity_id)
        return list(entity.project_ids or [])
    memory_ids, _, _ = await stack.entity_service.get_entity_memories(
        stack.user_id, entity_id,
    )
    return list(memory_ids)


def _created_events(stack: Stack, kind: str) -> list:
    link_type = (
        ActivityEntityType.ENTITY_PROJECT_LINK
        if kind == "project"
        else ActivityEntityType.ENTITY_MEMORY_LINK
    )
    return [
        e
        for e in stack.event_bus.collected
        if e.entity_type == link_type and e.action == ActionType.CREATED
    ]


@pytest.mark.parametrize("kind", ["project", "memory"])
async def test_relinking_entity_logs_created_event_once(stack, kind):
    entity = await _new_entity(stack, "Acme")
    target_id = await _new_target(stack, kind)
    link = _link(stack, kind)

    results = [await link(stack.user_id, entity.id, target_id) for _ in range(3)]

    assert results == [True, True, True]
    assert await _linked_target_ids(stack, kind, entity.id) == [target_id]
    assert len(_created_events(stack, kind)) == 1


@pytest.mark.parametrize("kind", ["project", "memory"])
async def test_concurrent_identical_entity_links_are_idempotent(stack, kind):
    target_id = await _new_target(stack, kind)
    entities = [await _new_entity(stack, f"e{i}") for i in range(CONCURRENT_CALLS)]
    link = _link(stack, kind)

    results = await asyncio.gather(
        *[
            link(stack.user_id, entity.id, target_id)
            for entity in entities
            for _ in range(3)
        ],
        return_exceptions=True,
    )

    failures = [r for r in results if r is not True]
    assert not failures, f"{len(failures)}/{len(results)} calls were not idempotent: {failures[:2]}"
    for entity in entities:
        assert await _linked_target_ids(stack, kind, entity.id) == [target_id]
    # One real link per entity -> one CREATED event per entity, however many calls raced
    assert len(_created_events(stack, kind)) == len(entities)
