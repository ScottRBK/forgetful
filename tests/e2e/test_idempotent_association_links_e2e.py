"""PostgreSQL: association links must be idempotent under concurrency and report real creations.

Covers entity<->memory, entity<->project and skill<->{memory,file,code artifact,document}
links. Identical link requests racing each other (parallel tool calls, retries) must all
succeed and leave exactly one association row, and the activity log must only record a
link as created once.
"""
import asyncio
import base64
from dataclasses import dataclass

import pytest
import pytest_asyncio

from app.config.settings import settings
from app.events import EventBus
from app.models.activity_models import ActionType
from app.models.activity_models import EntityType as ActivityEntityType
from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.entity_models import EntityCreate, EntityType
from app.models.file_models import FileCreate
from app.models.memory_models import MemoryCreate
from app.models.project_models import ProjectCreate, ProjectType
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.postgres.code_artifact_repository import (
    PostgresCodeArtifactRepository,
)
from app.repositories.postgres.document_repository import PostgresDocumentRepository
from app.repositories.postgres.entity_repository import PostgresEntityRepository
from app.repositories.postgres.file_repository import PostgresFileRepository
from app.repositories.postgres.memory_repository import PostgresMemoryRepository
from app.repositories.postgres.project_repository import PostgresProjectRepository
from app.repositories.postgres.skill_repository import PostgresSkillRepository
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.services.entity_service import EntityService

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]

CONCURRENT_PAIRS = 8


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
    projects: PostgresProjectRepository
    memories: PostgresMemoryRepository
    files: PostgresFileRepository
    code_artifacts: PostgresCodeArtifactRepository
    documents: PostgresDocumentRepository
    skills: PostgresSkillRepository


@pytest_asyncio.fixture(loop_scope="session")
async def stack(db_adapter):
    user = await PostgresUserRepository(db_adapter).create_user(
        UserCreate(external_id="ext-links-e2e", name="u", email="u@example.com"),
    )
    event_bus = CollectingEventBus()
    embeddings = FakeEmbeddings()
    return Stack(
        user_id=user.id,
        entity_service=EntityService(
            PostgresEntityRepository(db_adapter), event_bus=event_bus,
        ),
        event_bus=event_bus,
        projects=PostgresProjectRepository(db_adapter),
        memories=PostgresMemoryRepository(db_adapter, embeddings),
        files=PostgresFileRepository(db_adapter),
        code_artifacts=PostgresCodeArtifactRepository(db_adapter),
        documents=PostgresDocumentRepository(db_adapter),
        skills=PostgresSkillRepository(db_adapter, embeddings),
    )


async def _new_entity(stack: Stack, name: str):
    return await stack.entity_service.create_entity(
        stack.user_id, EntityCreate(name=name, entity_type=EntityType.ORGANIZATION),
    )


async def _new_memory(stack: Stack) -> int:
    memory = await stack.memories.create_memory(
        stack.user_id,
        MemoryCreate(
            title="m", content="c", context="x", keywords=["k"], tags=["t"], importance=7,
        ),
    )
    return memory.id


async def _new_target(stack: Stack, kind: str) -> int:
    """Create a project or memory that entities can be linked to."""
    if kind == "memory":
        return await _new_memory(stack)
    project = await stack.projects.create_project(
        stack.user_id,
        ProjectCreate(name="p", description="d", project_type=ProjectType.DEVELOPMENT),
    )
    return project.id


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
    entities = [await _new_entity(stack, f"e{i}") for i in range(CONCURRENT_PAIRS)]
    link = _link(stack, kind)

    results = await asyncio.gather(
        *[
            link(stack.user_id, entity.id, target_id)
            for entity in entities
            for _ in range(2)
        ],
        return_exceptions=True,
    )

    failures = [r for r in results if r is not True]
    assert not failures, f"{len(failures)}/{len(results)} calls were not idempotent: {failures[:2]}"
    for entity in entities:
        assert await _linked_target_ids(stack, kind, entity.id) == [target_id]
    # One real link per entity -> one CREATED event per entity, however many calls raced
    assert len(_created_events(stack, kind)) == len(entities)


async def _create_skill_target(stack: Stack, kind: str) -> int:
    uid = stack.user_id
    if kind == "memory":
        return await _new_memory(stack)
    if kind == "file":
        created = await stack.files.create_file(
            uid,
            FileCreate(
                filename="a.txt",
                description="d",
                data=base64.b64encode(b"hello").decode(),
                mime_type="text/plain",
            ),
        )
    elif kind == "code_artifact":
        created = await stack.code_artifacts.create_code_artifact(
            uid,
            CodeArtifactCreate(
                title="t", description="d", code="print(1)", language="python",
            ),
        )
    else:
        created = await stack.documents.create_document(
            uid, DocumentCreate(title="t", description="d", content="body"),
        )
    return created.id


SKILL_LINK_KINDS = {
    "memory": ("link_skill_to_memory", "memory_id", "memory_ids"),
    "file": ("link_skill_to_file", "file_id", "file_ids"),
    "code_artifact": (
        "link_skill_to_code_artifact",
        "code_artifact_id",
        "code_artifact_ids",
    ),
    "document": ("link_skill_to_document", "document_id", "document_ids"),
}


@pytest.mark.parametrize("kind", list(SKILL_LINK_KINDS))
async def test_concurrent_identical_skill_links_are_idempotent(stack, kind):
    method_name, result_key, links_attr = SKILL_LINK_KINDS[kind]
    skill = await stack.skills.create_skill(
        stack.user_id, SkillCreate(name="my-skill", description="d", content="body"),
    )
    target_id = await _create_skill_target(stack, kind)
    link = getattr(stack.skills, method_name)

    results = await asyncio.gather(
        *[link(stack.user_id, skill.id, target_id) for _ in range(8)],
        return_exceptions=True,
    )

    errors = [r for r in results if isinstance(r, BaseException)]
    assert not errors, f"non-idempotent concurrent link: {[type(e).__name__ for e in errors]}"
    assert all(
        r == {"skill_id": skill.id, result_key: target_id, "linked": True}
        for r in results
    )
    links = await stack.skills.get_skill_links(stack.user_id, skill.id)
    assert getattr(links, links_attr) == [target_id]
