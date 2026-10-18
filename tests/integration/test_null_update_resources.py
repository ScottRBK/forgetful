"""Integration tests: an update that changes nothing is a no-op.

The memory, project, plan and task services return the existing record when an
update carries no change. The document, code artifact, entity, file and skill
services used to call the repository anyway, which bumped ``updated_at`` (and
re-embedded a skill description) without emitting any activity event.

These tests run the services against the in-memory stub repositories.
"""
import asyncio
import base64
from dataclasses import dataclass
from typing import Any

import pytest

from app.models.activity_models import EntityType
from app.models.code_artifact_models import CodeArtifactCreate, CodeArtifactUpdate
from app.models.document_models import DocumentCreate, DocumentUpdate
from app.models.entity_models import (
    EntityCreate,
    EntityUpdate,
)
from app.models.entity_models import EntityType as EntityKind
from app.models.file_models import FileCreate, FileUpdate
from app.models.project_models import ProjectCreate, ProjectType, ProjectUpdate
from app.models.skill_models import SkillCreate, SkillUpdate
from app.models.user_models import User
from app.services.skill_service import SkillService
from tests.integration.conftest import CollectingEventBus

FILE_BYTES = base64.b64encode(b"Hello, World!").decode("utf-8")


@pytest.fixture
def test_user():
    return User(external_id="null-update", name="Null Update", email="null@example.com")


@dataclass
class Case:
    """One resource under test: how to create, read and update it."""

    name: str
    fixture: str
    model: type
    create: Any
    update: Any
    get: Any
    # Every field of the update model that must not accept a null.
    null_fields: dict[str, None]
    # A change that really modifies the stored record.
    change: dict[str, Any]
    # A payload that repeats what is already stored (a no-op).
    same: dict[str, Any]
    entity_type: EntityType

    def nulls_besides_change(self) -> dict[str, None]:
        """Null payload for every field the real change does not set."""
        return {field: None for field in self.null_fields if field not in self.change}


CASES = [
    Case(
        name="document",
        fixture="test_document_service_with_event_bus",
        model=DocumentUpdate,
        create=lambda s, u: s.create_document(
            u,
            DocumentCreate(
                title="Doc",
                description="A document",
                content="Some document content.",
                tags=["keep"],
                source_url="https://example.test/x",
            ),
        ),
        update=lambda s, u, i, d: s.update_document(u, i, d),
        get=lambda s, u, i: s.get_document(u, i),
        null_fields={
            "title": None,
            "description": None,
            "content": None,
            "size_bytes": None,
            "tags": None,
            "source_url": None,
            "project_id": None,
        },
        change={"title": "Renamed"},
        same={"title": "Doc", "tags": ["keep"]},
        entity_type=EntityType.DOCUMENT,
    ),
    Case(
        name="code_artifact",
        fixture="test_code_artifact_service_with_event_bus",
        model=CodeArtifactUpdate,
        create=lambda s, u: s.create_code_artifact(
            u,
            CodeArtifactCreate(
                title="Snippet",
                description="A snippet",
                code="print(1)",
                language="python",
                tags=["keep"],
            ),
        ),
        update=lambda s, u, i, d: s.update_code_artifact(u, i, d),
        get=lambda s, u, i: s.get_code_artifact(u, i),
        null_fields={
            "title": None,
            "description": None,
            "code": None,
            "language": None,
            "tags": None,
            "project_id": None,
        },
        change={"title": "Renamed"},
        same={"title": "Snippet", "language": "python"},
        entity_type=EntityType.CODE_ARTIFACT,
    ),
    Case(
        name="entity",
        fixture="test_entity_service_with_event_bus",
        model=EntityUpdate,
        create=lambda s, u: s.create_entity(
            u,
            EntityCreate(
                name="Acme",
                entity_type=EntityKind.ORGANIZATION,
                notes="keep me",
                tags=["keep"],
                aka=["Acme Inc"],
            ),
        ),
        update=lambda s, u, i, d: s.update_entity(u, i, d),
        get=lambda s, u, i: s.get_entity(u, i),
        null_fields={
            "name": None,
            "entity_type": None,
            "notes": None,
            "tags": None,
            "aka": None,
            "project_ids": None,
        },
        change={"name": "Acme Corp"},
        same={"name": "Acme", "tags": ["keep"]},
        entity_type=EntityType.ENTITY,
    ),
    Case(
        name="file",
        fixture="test_file_service_with_event_bus",
        model=FileUpdate,
        create=lambda s, u: s.create_file(
            u,
            FileCreate(
                filename="hello.txt",
                description="A greeting",
                data=FILE_BYTES,
                mime_type="text/plain",
                tags=["keep"],
            ),
        ),
        update=lambda s, u, i, d: s.update_file(u, i, d),
        get=lambda s, u, i: s.get_file(u, i),
        null_fields={
            "filename": None,
            "description": None,
            "data": None,
            "mime_type": None,
            "tags": None,
            "project_id": None,
        },
        change={"filename": "renamed.txt"},
        same={"filename": "hello.txt", "tags": ["keep"]},
        entity_type=EntityType.FILE,
    ),
    Case(
        name="project",
        fixture="test_project_service_with_event_bus",
        model=ProjectUpdate,
        create=lambda s, u: s.create_project(
            u,
            ProjectCreate(
                name="Proj",
                description="A project",
                project_type=ProjectType.DEVELOPMENT,
                notes="keep me",
            ),
        ),
        update=lambda s, u, i, d: s.update_project(u, i, d),
        get=lambda s, u, i: s.get_project(u, i),
        null_fields={
            "name": None,
            "description": None,
            "project_type": None,
            "status": None,
            "notes": None,
            "repo_name": None,
        },
        change={"name": "Renamed"},
        same={"name": "Proj", "notes": "keep me"},
        entity_type=EntityType.PROJECT,
    ),
    Case(
        name="skill",
        fixture="skill_service_with_event_bus",
        model=SkillUpdate,
        create=lambda s, u: s.create_skill(
            u,
            SkillCreate(
                name="my-skill",
                description="Does a thing",
                content="# steps",
                license="MIT",
                tags=["keep"],
                importance=6,
            ),
        ),
        update=lambda s, u, i, d: s.update_skill(u, i, d),
        get=lambda s, u, i: s.get_skill(u, i),
        null_fields={
            "name": None,
            "description": None,
            "content": None,
            "license": None,
            "tags": None,
            "importance": None,
            "project_id": None,
        },
        change={"importance": 9},
        same={"importance": 6, "tags": ["keep"]},
        entity_type=EntityType.SKILL,
    ),
]


@pytest.fixture
def skill_service_with_event_bus(mock_skill_repository):
    bus = CollectingEventBus()
    return SkillService(mock_skill_repository, event_bus=bus), bus


def _ids(cases):
    return [case.name for case in cases]


# ---------------------------------------------------------------------------
# Services: an update that changes nothing is a no-op
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
async def test_service_noop_update_keeps_updated_at_and_emits_nothing(case, test_user, request):
    service, bus = request.getfixturevalue(case.fixture)
    created = await case.create(service, test_user.id)
    updated_at = created.updated_at
    bus.collected_events.clear()
    await asyncio.sleep(0.002)

    result = await case.update(service, test_user.id, created.id, case.model(**case.same))

    assert result.updated_at == updated_at
    assert (await case.get(service, test_user.id, created.id)).updated_at == updated_at
    assert bus.collected_events == []


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
async def test_service_empty_update_keeps_updated_at(case, test_user, request):
    service, _ = request.getfixturevalue(case.fixture)
    created = await case.create(service, test_user.id)
    updated_at = created.updated_at
    await asyncio.sleep(0.002)

    result = await case.update(service, test_user.id, created.id, case.model())

    assert result.updated_at == updated_at


async def test_skill_noop_update_does_not_touch_repository(mock_skill_repository, test_user):
    """The skill repository re-embeds the description on every call that sets it."""
    service = SkillService(mock_skill_repository, event_bus=None)
    skill = await service.create_skill(
        test_user.id,
        SkillCreate(name="my-skill", description="Does a thing", content="# steps"),
    )
    calls = []
    original = mock_skill_repository.update_skill

    async def spy(*args, **kwargs):
        calls.append(kwargs or args)
        return await original(*args, **kwargs)

    mock_skill_repository.update_skill = spy

    await service.update_skill(test_user.id, skill.id, SkillUpdate(description="Does a thing"))

    assert calls == []
