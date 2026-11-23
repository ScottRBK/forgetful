"""Exercise the actual in-memory page implementations and typed service seam."""
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.events import EventBus
from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.file_models import FileCreate
from app.models.plan_models import PlanCreate, TaskCreate, TaskDependency
from app.models.project_models import ProjectCreate
from app.models.skill_models import SkillCreate
from tests.list_pagination_cases import RESOURCES, payload

MODELS = {
    "projects": ("project", "project", ProjectCreate),
    "plans": ("plan", "plan", PlanCreate),
    "tasks": ("task", "task", TaskCreate),
    "documents": ("document", "document", DocumentCreate),
    "code_artifacts": ("code_artifact", "artifact", CodeArtifactCreate),
    "files": ("file", "file", FileCreate),
    "skills": ("skill", "skill", SkillCreate),
}


@pytest.mark.parametrize("resource", RESOURCES)
async def test_in_memory_page_and_service_keep_full_list_contract(request, resource, monkeypatch):
    singular, argument, model = MODELS[resource]
    repository = request.getfixturevalue("mock_" + singular + "_repository")
    service = request.getfixturevalue("test_" + singular + "_service")
    if resource == "tasks":
        service, _linked_plan_service = service  # fixture returns (TaskService, PlanService)
    user_id = uuid4()
    for index in range(3):
        await getattr(repository, "create_" + singular)(
            user_id=user_id,
            **{argument + "_data": model(**payload(resource, index, project_id=1, plan_id=1))},
        )
    filters = {"plan_id": 1} if resource == "tasks" else {}
    original = await getattr(repository, "list_" + resource)(user_id=user_id, **filters)
    items, total = await getattr(repository, "list_" + resource + "_page")(
        user_id=user_id, **filters, limit=1, offset=1,
    )
    assert total == len(original) == 3
    assert len(items) == 1
    expected = sorted(original, key=lambda row: (row.created_at, row.id), reverse=resource != "tasks")
    assert items[0].model_dump() == expected[1].model_dump()
    assert len(await getattr(repository, "list_" + resource)(user_id=user_id, **filters)) == 3
    events = []
    bus = EventBus()

    async def collect(event):
        events.append(event)

    bus.subscribe("*.*", collect)
    monkeypatch.setattr(service, "_event_bus", bus, raising=False)
    monkeypatch.setattr(settings, "ACTIVITY_TRACK_READS", True)
    result, count = await getattr(service, "list_" + resource + "_page")(
        user_id=user_id, **filters, limit=1, offset=1,
    )
    await bus.wait_for_pending(timeout=5)
    assert count == 3
    assert [item.model_dump() for item in result] == [item.model_dump() for item in items]
    queried = [event for event in events if event.action == "queried"]
    assert len(queried) == (0 if resource in ("plans", "tasks") else 1)
    if queried:
        assert queried[0].snapshot == {"result_ids": [items[0].id], "total_count": 3}
        assert queried[0].metadata["limit"] == queried[0].metadata["offset"] == 1
    empty, empty_count = await getattr(repository, "list_" + resource + "_page")(
        user_id=uuid4(), **filters, limit=1, offset=0,
    )
    assert empty == [] and empty_count == 0


async def test_missing_dependency_in_task_double_matches_legacy_full_list(mock_task_repository):
    """Characterize the legacy in-memory double for a missing target; not a real-database oracle."""
    user_id = uuid4()
    task = await mock_task_repository.create_task(
        user_id=user_id, task_data=TaskCreate(plan_id=1, title="Missing prerequisite"),
    )
    mock_task_repository._dependencies[user_id] = {
        1: TaskDependency(id=1, task_id=task.id, depends_on_task_id=999999, created_at=task.created_at),
    }
    original = await mock_task_repository.list_tasks(user_id=user_id, plan_id=1)
    page, total = await mock_task_repository.list_tasks_page(user_id=user_id, plan_id=1, limit=1, offset=0)
    assert original[0].blocked is False
    assert total == 1 and page[0].model_dump() == original[0].model_dump()
