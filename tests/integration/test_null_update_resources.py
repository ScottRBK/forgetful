"""Integration tests: an explicit null in an update means "unchanged".

Every ``*Update`` model documents "None/omitted fields remain unchanged".
The MCP adapters strip ``None`` before building the model, but REST clients
(``PUT {"tags": null}``) and direct callers can hand a literal null to the
model, where it used to count as an explicitly set field. It was then written
to the row (NOT NULL violations, or JSON null in list columns that made the
record unreadable and undeletable) and ignored by the no-op detection.

These tests run the services against the in-memory stub repositories, which
apply updates the same way as the real ones (``model_dump(exclude_unset=True)``).
"""
import asyncio
import base64
from dataclasses import dataclass
from typing import Any

import pytest

from app.models.activity_models import ActionType, EntityType
from app.models.code_artifact_models import CodeArtifactCreate, CodeArtifactUpdate
from app.models.document_models import DocumentCreate, DocumentUpdate
from app.models.entity_models import (
    EntityCreate,
    EntityRelationshipUpdate,
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
# Update models: a literal null is not a change request
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_update_model_ignores_explicit_null(case):
    update = case.model(**case.null_fields)

    assert update.model_fields_set == set()
    assert update.model_dump(exclude_unset=True) == {}


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_update_model_keeps_real_values_next_to_nulls(case):
    update = case.model(**case.nulls_besides_change(), **case.change)

    assert update.model_fields_set == set(case.change)
    assert update.model_dump(exclude_unset=True) == case.change


def test_relationship_update_ignores_explicit_null():
    update = EntityRelationshipUpdate(relationship_type=None, strength=None, confidence=None)

    assert update.model_fields_set == set()


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (ProjectUpdate, "notes"),
        (ProjectUpdate, "repo_name"),
        (ProjectUpdate, "last_encoding_point"),
        (EntityUpdate, "notes"),
        (DocumentUpdate, "filename"),
    ],
)
def test_empty_string_still_clears_optional_fields(model, field):
    """The documented way to clear an optional field is the empty string."""
    update = model(**{field: ""})

    assert field in update.model_fields_set
    assert update.model_dump(exclude_unset=True) == {field: None}


# ---------------------------------------------------------------------------
# Services: nothing is written, nothing is emitted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
async def test_service_update_with_only_nulls_leaves_record_untouched(case, test_user, request):
    service, bus = request.getfixturevalue(case.fixture)
    created = await case.create(service, test_user.id)
    before = (await case.get(service, test_user.id, created.id)).model_dump(mode="json")
    bus.collected_events.clear()
    await asyncio.sleep(0.002)

    result = await case.update(service, test_user.id, created.id, case.model(**case.null_fields))

    after = (await case.get(service, test_user.id, created.id)).model_dump(mode="json")
    assert after == before
    assert result.model_dump(mode="json") == before
    assert bus.collected_events == []


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
async def test_service_update_applies_value_and_ignores_null_sibling(case, test_user, request):
    service, bus = request.getfixturevalue(case.fixture)
    created = await case.create(service, test_user.id)
    before = (await case.get(service, test_user.id, created.id)).model_dump(mode="json")
    bus.collected_events.clear()

    await case.update(service, test_user.id, created.id, case.model(**case.nulls_besides_change(), **case.change))

    after = (await case.get(service, test_user.id, created.id)).model_dump(mode="json")
    for field, value in after.items():
        if field in case.change:
            assert value == case.change[field]
        elif field != "updated_at":
            assert value == before[field], f"{field} changed"
    assert len(bus.collected_events) == 1
    event = bus.collected_events[0]
    assert event.entity_type == case.entity_type
    assert event.action == ActionType.UPDATED
    assert set(event.changes) == set(case.change)


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
    await service.update_skill(test_user.id, skill.id, SkillUpdate(description=None))

    assert calls == []


# ---------------------------------------------------------------------------
# Files: replacing only the content is a change
# ---------------------------------------------------------------------------


async def test_file_content_only_update_emits_updated_event(test_file_service_with_event_bus, test_user):
    service, bus = test_file_service_with_event_bus
    created = await service.create_file(
        test_user.id,
        FileCreate(
            filename="data.bin",
            description="Binary data",
            data=FILE_BYTES,
            mime_type="application/octet-stream",
        ),
    )
    original_size = created.size_bytes
    bus.collected_events.clear()
    new_content = b"This is much longer content than Hello, World!"
    new_data = base64.b64encode(new_content).decode("utf-8")

    updated = await service.update_file(test_user.id, created.id, FileUpdate(data=new_data))

    assert updated.data == new_data
    assert len(bus.collected_events) == 1
    event = bus.collected_events[0]
    assert event.entity_type == EntityType.FILE
    assert event.entity_id == created.id
    assert event.action == ActionType.UPDATED
    assert "data" not in event.changes
    assert event.changes["size_bytes"] == {"old": original_size, "new": len(new_content)}
    assert "data" not in event.snapshot


async def test_file_content_and_metadata_update_reports_size_and_metadata(
    test_file_service_with_event_bus, test_user,
):
    service, bus = test_file_service_with_event_bus
    created = await service.create_file(
        test_user.id,
        FileCreate(
            filename="data.bin",
            description="Binary data",
            data=FILE_BYTES,
            mime_type="application/octet-stream",
        ),
    )
    bus.collected_events.clear()
    new_data = base64.b64encode(b"x").decode("utf-8")

    await service.update_file(
        test_user.id, created.id, FileUpdate(data=new_data, filename="renamed.bin"),
    )

    assert len(bus.collected_events) == 1
    changes = bus.collected_events[0].changes
    assert set(changes) == {"filename", "size_bytes"}
    assert changes["filename"] == {"old": "data.bin", "new": "renamed.bin"}
