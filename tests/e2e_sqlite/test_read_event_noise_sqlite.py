"""Full-stack (in-memory SQLite) tests: no READ noise from internal lookups.

Real repositories and services share one EventBus, the way bootstrap wires them, with
ACTIVITY_TRACK_READS on. Two paths used to log reads the user never made:

- rendering a graph hydrated every node through the public ``get_*`` methods, so one
  graph view wrote several ``read``/``queried`` events per node;
- ``unlink_memories`` checked the source memory through ``get_memory``, recording a
  ``memory.read`` event and bumping ``access_count``.
"""
import base64

import pytest

from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.activity_models import ActionType, EntityType
from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.file_models import FileCreate
from app.models.memory_models import MemoryCreate
from app.models.plan_models import PlanCreate, PlanStatus, PlanUpdate, TaskCreate
from app.models.project_models import ProjectCreate, ProjectType
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.activity_repository import SqliteActivityRepository
from app.repositories.sqlite.code_artifact_repository import (
    SqliteCodeArtifactRepository,
)
from app.repositories.sqlite.document_repository import SqliteDocumentRepository
from app.repositories.sqlite.entity_repository import SqliteEntityRepository
from app.repositories.sqlite.file_repository import SqliteFileRepository
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.plan_repository import SqlitePlanRepository
from app.repositories.sqlite.project_repository import SqliteProjectRepository
from app.repositories.sqlite.skill_repository import SqliteSkillRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.task_repository import SqliteTaskRepository
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.activity_service import ActivityService
from app.services.code_artifact_service import CodeArtifactService
from app.services.document_service import DocumentService
from app.services.file_service import FileService
from app.services.graph_service import GraphService
from app.services.memory_service import MemoryService
from app.services.plan_service import PlanService
from app.services.project_service import ProjectService
from app.services.skill_service import SkillService
from app.services.task_service import TaskService
from tests.integration.conftest import CollectingEventBus

NOISY_ACTIONS = (ActionType.READ, ActionType.QUERIED)


class _StaticEmbeddings:
    """Deterministic offline embeddings (no model download)."""

    async def generate_embedding(self, text: str) -> list[float]:
        seed = sum(ord(c) for c in text) or 1
        return [((seed * (i + 1)) % 97) / 97.0 + 0.01 for i in range(settings.EMBEDDING_DIMENSIONS)]


@pytest.fixture
async def stack(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    monkeypatch.setattr(settings, "ACTIVITY_ENABLED", True)
    monkeypatch.setattr(settings, "ACTIVITY_TRACK_READS", True)

    db = SqliteDatabaseAdapter()
    await db.init_db()
    try:
        user = await SqliteUserRepository(db_adapter=db).create_user(
            UserCreate(external_id="read-noise", name="U", email="u@example.com"),
        )
        bus = CollectingEventBus()
        activity_service = ActivityService(SqliteActivityRepository(db_adapter=db))
        bus.subscribe("*.*", activity_service.handle_event)

        embeddings = _StaticEmbeddings()
        memory_repo = SqliteMemoryRepository(
            db_adapter=db, embedding_adapter=embeddings, rerank_adapter=None,
        )
        memory_service = MemoryService(memory_repo, event_bus=bus)
        memory_service.register_access_tracking_handlers(bus)
        project_service = ProjectService(SqliteProjectRepository(db_adapter=db), event_bus=bus)
        document_service = DocumentService(SqliteDocumentRepository(db_adapter=db), event_bus=bus)
        artifact_service = CodeArtifactService(
            SqliteCodeArtifactRepository(db_adapter=db), event_bus=bus,
        )
        file_service = FileService(SqliteFileRepository(db_adapter=db), event_bus=bus)
        skill_service = SkillService(
            SqliteSkillRepository(db_adapter=db, embedding_adapter=embeddings, rerank_adapter=None),
            event_bus=bus,
        )
        plan_service = PlanService(SqlitePlanRepository(db_adapter=db), event_bus=bus)
        task_service = TaskService(
            SqliteTaskRepository(db_adapter=db), plan_service=plan_service, event_bus=bus,
        )
        graph = GraphService(
            memory_repo,
            SqliteEntityRepository(db_adapter=db),
            project_service=project_service,
            document_service=document_service,
            code_artifact_service=artifact_service,
            file_service=file_service,
            skill_service=skill_service,
            plan_service=plan_service,
            task_service=task_service,
        )
        yield {
            "user_id": user.id,
            "bus": bus,
            "activity_repo": activity_service.activity_repo,
            "memory_repo": memory_repo,
            "memory": memory_service,
            "project": project_service,
            "document": document_service,
            "artifact": artifact_service,
            "file": file_service,
            "skill": skill_service,
            "plan": plan_service,
            "task": task_service,
            "graph": graph,
        }
    finally:
        await db.dispose()


async def _seed_project_content(s):
    """A project holding one document, artifact, file, skill, plan and task."""
    uid = s["user_id"]
    project = await s["project"].create_project(
        uid, ProjectCreate(name="P", description="proj", project_type=ProjectType.DEVELOPMENT),
    )
    pid = project.id
    ids = {"project": pid}
    ids["document"] = (await s["document"].create_document(
        uid, DocumentCreate(title="D", description="doc", content="body", project_id=pid),
    )).id
    ids["code_artifact"] = (await s["artifact"].create_code_artifact(
        uid,
        CodeArtifactCreate(
            title="A", description="art", code="print(1)", language="python", project_id=pid,
        ),
    )).id
    ids["file"] = (await s["file"].create_file(
        uid,
        FileCreate(
            filename="a.txt",
            description="file",
            data=base64.b64encode(b"hello").decode(),
            mime_type="text/plain",
            project_id=pid,
        ),
    )).id
    ids["skill"] = (await s["skill"].create_skill(
        uid, SkillCreate(name="noise-skill", description="d", content="# body", project_id=pid),
    )).id
    plan = await s["plan"].create_plan(uid, PlanCreate(title="plan", project_id=pid, goal="g"))
    await s["plan"].update_plan(uid, plan.id, PlanUpdate(status=PlanStatus.ACTIVE))
    ids["plan"] = plan.id
    ids["task"] = (await s["task"].create_task(uid, TaskCreate(title="t", plan_id=plan.id))).id
    await s["bus"].wait_for_pending()
    s["bus"].collected_events.clear()
    return ids


def _noisy_events(s):
    return [
        (str(e.entity_type), e.entity_id, str(e.action))
        for e in s["bus"].collected_events
        if e.action in NOISY_ACTIONS
    ]


@pytest.mark.asyncio
async def test_project_graph_renders_without_read_or_query_events(stack):
    s = stack
    ids = await _seed_project_content(s)

    sub = await s["graph"].get_subgraph(s["user_id"], f"project_{ids['project']}", depth=2)

    # Sanity: every service-backed node type and its project edge really rendered
    node_ids = {n.id for n in sub.nodes}
    for kind, entity_id in ids.items():
        assert f"{kind}_{entity_id}" in node_ids, f"{kind} node missing from graph"
    edge_types = {e.type for e in sub.edges}
    assert {
        "document_project", "code_artifact_project", "file_project", "skill_project", "plan_project",
    } <= edge_types

    await s["bus"].wait_for_pending()
    assert _noisy_events(s) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("center", ["document", "code_artifact", "file", "skill", "plan", "project"])
async def test_graph_center_validation_emits_no_read_event(stack, center):
    s = stack
    ids = await _seed_project_content(s)

    sub = await s["graph"].get_subgraph(s["user_id"], f"{center}_{ids[center]}", depth=1)

    assert f"{center}_{ids[center]}" in {n.id for n in sub.nodes}
    await s["bus"].wait_for_pending()
    assert _noisy_events(s) == []


@pytest.mark.asyncio
async def test_explicit_gets_still_emit_read_events(stack):
    """Only the internal lookups are silenced: an explicit get_* still logs its read."""
    s = stack
    uid = s["user_id"]
    ids = await _seed_project_content(s)

    await s["project"].get_project(uid, ids["project"])
    await s["document"].get_document(uid, ids["document"])
    await s["artifact"].get_code_artifact(uid, ids["code_artifact"])
    await s["file"].get_file(uid, ids["file"])
    await s["skill"].get_skill(uid, ids["skill"])
    await s["plan"].get_plan(uid, ids["plan"])
    await s["file"].list_files(uid)

    assert {(kind, action) for kind, _id, action in _noisy_events(s)} == {
        ("project", "read"),
        ("document", "read"),
        ("code_artifact", "read"),
        ("file", "read"),
        ("skill", "read"),
        ("plan", "read"),
        ("file", "queried"),
    }


@pytest.mark.asyncio
async def test_unlink_memories_does_not_count_as_a_read(stack):
    s = stack
    uid = s["user_id"]

    async def make(title):
        mem, _ = await s["memory"].create_memory(
            user_id=uid,
            memory_data=MemoryCreate(
                title=title,
                content=f"content of {title}",
                context="ctx",
                keywords=["k"],
                tags=["t"],
                importance=5,
            ),
        )
        return mem

    m1 = await make("alpha")
    m2 = await make("beta")
    await s["memory"].link_memories(user_id=uid, memory_id=m1.id, related_ids=[m2.id])
    await s["bus"].wait_for_pending()
    before = await s["memory_repo"].get_memory_by_id(user_id=uid, memory_id=m1.id)
    assert before.access_count == 0

    removed = await s["memory"].unlink_memories(user_id=uid, memory_id=m1.id, target_id=m2.id)
    await s["bus"].wait_for_pending()

    assert removed is True
    after = await s["memory_repo"].get_memory_by_id(user_id=uid, memory_id=m1.id)
    assert after.access_count == 0
    assert after.last_accessed_at is None
    entries, total = await s["activity_repo"].query_events(
        user_id=uid, entity_type=EntityType.MEMORY, action=ActionType.READ,
    )
    assert total == 0
    assert entries == []


@pytest.mark.asyncio
async def test_unlink_memories_still_rejects_a_missing_source(stack):
    s = stack

    with pytest.raises(NotFoundError):
        await s["memory"].unlink_memories(user_id=s["user_id"], memory_id=999, target_id=1)

    await s["bus"].wait_for_pending()
    assert _noisy_events(s) == []
