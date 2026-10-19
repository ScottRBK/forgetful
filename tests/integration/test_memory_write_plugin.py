"""Write Plugin workflows through MemoryService with real isolated SQLite."""

import logging

import pytest

from app.config.settings import settings
from app.events import EventBus
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.protocols.write_plugin_protocol import MemoryPlugin
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.memory_service import MemoryService
from app.services.user_service import UserService


def checks(handler):
    return MemoryPlugin(before_save={"create": handler, "update": handler})


class RecordingEmbeddings:
    def __init__(self):
        self.requests = []

    async def generate_embedding(self, text):
        self.requests.append(text)
        return [1.0] + [0.0] * (settings.EMBEDDING_DIMENSIONS - 1)


def candidate(**changes):
    return MemoryCreate(
        **({"title": "A useful memory", "content": "A single useful fact",
            "context": "Testing writes", "keywords": [], "tags": []} | changes),
    )


@pytest.fixture
async def write_store(sqlite_runtime_settings, monkeypatch):
    monkeypatch.setattr(settings, "ACTIVITY_TRACK_READS", False)
    db = SqliteDatabaseAdapter()
    await db.init_db()
    embeddings = RecordingEmbeddings()
    repo = SqliteMemoryRepository(db, embeddings)
    user = await UserService(SqliteUserRepository(db)).get_or_create_user(
        UserCreate(external_id="plugin-test", name="Plugin test", email="test@example.com"),
    )
    bus = EventBus()
    try:
        yield repo, user.id, embeddings, bus
    finally:
        await bus.wait_for_pending()
        await db.dispose()


async def test_allowed_create_persists_and_blocked_tag_returns_plugin_message(write_store):
    from app.exceptions import WritePluginRejectedError
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, embeddings, bus = write_store

    async def check_write(request):
        if "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    service = MemoryService(repo, write_plugin=WritePluginService(checks(check_write)))
    await service.create_memory(user_id, candidate())
    with pytest.raises(WritePluginRejectedError, match=r"^Remove the blocked tag\.$"):
        await service.create_memory(user_id, candidate(tags=["blocked"]))
    memories, total = await service.list_memories(user_id)
    assert total == 1
    assert [memory.title for memory in memories] == ["A useful memory"]
    assert len(embeddings.requests) == 1


async def test_noop_preserves_timestamp_and_emits_no_update(write_store):
    from app.models.memory_models import MemoryUpdate

    repo, user_id, embeddings, bus = write_store
    events = []

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    service = MemoryService(repo, event_bus=bus)
    write_result = await service.create_memory(user_id, candidate())
    memory = write_result.memory
    before = await service.get_memory(user_id, memory.id)
    updated = await service.update_memory(user_id, memory.id, MemoryUpdate(title=memory.title))
    updated = updated.memory
    await bus.wait_for_pending()
    assert updated.updated_at == before.updated_at
    assert [event.action for event in events] == ["created"]
    assert len(embeddings.requests) == 1


async def test_memory_provenance_override_preserves_unset_fields(write_store, monkeypatch):
    from app.models.memory_models import MemoryUpdate

    monkeypatch.setattr(settings, "ENCODING_AGENT", "server-agent")
    monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", False)
    repo, user_id, _, _ = write_store
    service = MemoryService(repo)
    write_result = await service.create_memory(user_id, candidate(encoding_agent="original-agent"))
    memory = write_result.memory
    monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", True)
    updated = await service.update_memory(user_id, memory.id, MemoryUpdate(importance=9))
    updated = updated.memory
    assert updated.encoding_agent == "original-agent"
    updated = await service.update_memory(
        user_id, memory.id, MemoryUpdate(encoding_agent="submitted-agent"),
    )
    updated = updated.memory
    assert updated.encoding_agent == "server-agent"


@pytest.mark.parametrize("mode", ["warn", "enforce"])
async def test_warn_returns_explicit_result_without_persisting_warning(write_store, mode):
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, _, bus = write_store
    events = []

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)

    async def check_write(request):
        return WriteDecision(outcome="warn", message="Check the source.", code="source")

    service = MemoryService(repo, bus, WritePluginService(checks(check_write), mode=mode))
    result = await service.create_memory(user_id, candidate())
    assert result.plugin_warnings[0].message == "Check the source."
    memory = await service.get_memory(user_id, result.memory.id)
    assert "plugin_warnings" not in memory.model_dump()
    await bus.wait_for_pending()
    assert len(events) == 1
    assert "plugin_warnings" not in events[0].snapshot


async def test_update_rejection_precedes_embeddings_links_and_events(write_store):
    from app.exceptions import WritePluginRejectedError
    from app.models.memory_models import MemoryUpdate
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, embeddings, bus = write_store
    seen, events = [], []

    async def collect(event):
        events.append(event)

    async def check_write(request):
        seen.append(request)
        if "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    bus.subscribe("*.*", collect)
    service = MemoryService(repo, bus, WritePluginService(checks(check_write)))
    first = await service.create_memory(user_id, candidate())
    await bus.wait_for_pending()
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.update_memory(user_id, first.memory.id, MemoryUpdate(tags=["blocked"]))
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_memory(user_id, candidate(tags=["blocked"]))
    noop = await service.update_memory(user_id, first.memory.id, MemoryUpdate())
    await bus.wait_for_pending()
    saved = await service.get_memory(user_id, first.memory.id)
    assert saved.tags == []
    assert saved.linked_memory_ids == []
    assert noop.plugin_warnings == []
    assert len(seen) == 3  # No-op skips plugin.
    assert len(embeddings.requests) == 1
    assert [event.action for event in events] == ["created"]


async def test_snapshots_detached_and_candidate_matches_update_semantics(write_store, monkeypatch):
    from app.models.memory_models import Memory, MemoryUpdate
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    monkeypatch.setattr(settings, "ENCODING_AGENT", "server-agent")
    monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", True)
    repo, user_id, _, _ = write_store
    seen = []

    async def check_write(request):
        seen.append(request.model_copy(deep=True))
        assert type(request.proposed) is MemoryCreate
        assert not hasattr(request.proposed, "id")
        request.proposed.tags.append("plugin-mutation")
        assert "plugin-mutation" not in request.submitted.tags
        request.submitted.tags.append("submitted-mutation")
        if request.previous:
            assert type(request.previous) is Memory
            assert request.previous.tags == ["original"]
            request.previous.tags.append("previous-mutation")
        return WriteDecision(outcome="allow")

    service = MemoryService(repo, write_plugin=WritePluginService(checks(check_write)))
    submitted = candidate(tags=["original"], encoding_agent="client-agent", source_url="old")
    created = await service.create_memory(user_id, submitted)
    update = MemoryUpdate(tags=["revised"], source_url=None, project_ids=None)
    result = await service.update_memory(user_id, created.memory.id, update)
    assert submitted.tags == ["original"]
    assert update.tags == ["revised"]
    assert result.memory.tags == ["revised"]
    assert result.memory.source_url == "old"
    assert seen[0].submitted.encoding_agent == "client-agent"
    assert seen[0].proposed.encoding_agent == "server-agent"
    assert seen[1].operation == "update"
    assert seen[1].user_id == user_id
    assert seen[1].previous.id == created.memory.id
    assert seen[1].submitted.model_fields_set == {"tags", "source_url", "project_ids"}
    assert seen[1].proposed.project_ids == []  # Relationship null means unchanged.
    assert seen[1].proposed.source_url == "old"  # Explicit null leaves it unchanged.
    assert seen[1].proposed.encoding_agent == "server-agent"
    saved = await service.get_memory(user_id, created.memory.id)
    assert saved.tags == ["revised"]


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "bad_result", "blank", "mutated", "timeout"])
async def test_unavailable_is_generic_and_mode_controls_persistence(
    write_store, mode, failure, caplog,
):
    import asyncio

    from app.exceptions import WritePluginUnavailableError
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, embeddings, _ = write_store
    logging.getLogger("app.services.write_plugin_service").disabled = False

    async def check_write(request):
        if failure == "error":
            raise RuntimeError("SECRET full memory content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "blank":
            return {"outcome": "reject", "message": "  "}
        if failure == "mutated":
            decision = WriteDecision(outcome="allow")
            decision.outcome = "invalid"
            return decision
        return {"outcome": "invalid", "message": "SECRET full memory content"}

    service = MemoryService(
        repo, write_plugin=WritePluginService(checks(check_write), mode=mode, timeout_seconds=0.01),
    )
    if mode == "enforce":
        with pytest.raises(
            WritePluginUnavailableError, match=r"^Memory Write Plugin unavailable\.$",
        ):
            await service.create_memory(user_id, candidate())
    else:
        result = await service.create_memory(user_id, candidate())
        assert result.plugin_warnings[0].message == "Memory Write Plugin unavailable."
        assert result.plugin_warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"
    _, total = await service.list_memories(user_id)
    assert total == (1 if mode == "warn" else 0)
    assert len(embeddings.requests) == total
    assert "Write Plugin" in caplog.text
    assert "SECRET" not in caplog.text


async def test_warn_mode_downgrades_reject_and_cancellation_propagates(write_store):
    import asyncio

    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, _, _ = write_store

    async def check_write(request):
        if "cancel" in request.proposed.tags:
            raise asyncio.CancelledError()
        return WriteDecision(outcome="reject", message="Check the source.", code="source")

    service = MemoryService(repo, write_plugin=WritePluginService(checks(check_write), mode="warn"))
    result = await service.create_memory(user_id, candidate())
    assert result.plugin_warnings[0].outcome == "warn"
    assert result.plugin_warnings[0].code == "source"
    with pytest.raises(asyncio.CancelledError):
        await service.create_memory(user_id, candidate(tags=["cancel"]))
    _, total = await service.list_memories(user_id)
    assert total == 1


async def test_null_update_and_missing_memory_do_not_reach_plugin(write_store):
    from app.exceptions import NotFoundError
    from app.models.memory_models import MemoryUpdate
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, embeddings, _ = write_store
    calls = []

    async def check_write(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = MemoryService(repo, write_plugin=WritePluginService(checks(check_write)))
    created = await service.create_memory(user_id, candidate())
    before = await service.get_memory(user_id, created.memory.id)
    unchanged = await service.update_memory(user_id, created.memory.id, MemoryUpdate(title=None))
    assert unchanged.memory.title == created.memory.title
    assert unchanged.memory.updated_at == before.updated_at
    assert len(calls) == 1
    assert len(embeddings.requests) == 1
    with pytest.raises(NotFoundError):
        await service.update_memory(user_id, created.memory.id + 100, MemoryUpdate(title="New"))
    saved = await service.get_memory(user_id, created.memory.id)
    assert saved.title == "A useful memory"
    assert len(calls) == 1
    assert len(embeddings.requests) == 1


async def test_update_candidate_preserves_null_relationship_and_clears_empty_list(write_store):
    from app.models.memory_models import MemoryUpdate
    from app.models.project_models import ProjectCreate
    from app.models.write_plugin_models import WriteDecision
    from app.repositories.sqlite.project_repository import SqliteProjectRepository
    from app.services.project_service import ProjectService
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, _, _ = write_store
    project = await ProjectService(SqliteProjectRepository(repo.db_adapter)).create_project(
        user_id, ProjectCreate(name="Plugin project", description="Relationship test",
                               project_type="development"),
    )
    candidates = []

    async def check_write(request):
        candidates.append(request.proposed)
        return WriteDecision(outcome="allow")

    service = MemoryService(repo, write_plugin=WritePluginService(checks(check_write)))
    created = await service.create_memory(user_id, candidate(project_ids=[project.id]))
    preserved = await service.update_memory(
        user_id, created.memory.id, MemoryUpdate(project_ids=None, importance=9),
    )
    cleared = await service.update_memory(
        user_id, created.memory.id, MemoryUpdate(project_ids=[]),
    )
    assert candidates[1].project_ids == [project.id]
    assert preserved.memory.project_ids == [project.id]
    assert candidates[2].project_ids == []
    assert cleared.memory.project_ids == []


@pytest.mark.parametrize("concurrent_tags,concurrent_importance,expected_embeddings", [
    (["concurrent"], 8, 3),
    (["pending"], 9, 2),
    (["pending"], 8, 2),
])
async def test_update_refreshes_state_after_plugin_wait(
    write_store, concurrent_tags, concurrent_importance, expected_embeddings,
):
    import asyncio

    from app.models.memory_models import MemoryUpdate
    from app.models.write_plugin_models import WriteDecision
    from app.services.write_plugin_service import WritePluginService

    repo, user_id, embeddings, bus = write_store
    paused, release = asyncio.Event(), asyncio.Event()
    evaluated, events = [], []

    async def collect(event):
        events.append(event)

    async def check_write(request):
        if request.operation == "update" and request.submitted.content is None:
            evaluated.append(request)
            paused.set()
            await release.wait()
            return WriteDecision(outcome="warn", message="Check concurrent edits.")
        return WriteDecision(outcome="allow")

    bus.subscribe("memory.*", collect)
    service = MemoryService(repo, bus, WritePluginService(checks(check_write)))
    created = await service.create_memory(user_id, candidate(content="ORIGINAL content"))
    async with asyncio.timeout(5), asyncio.TaskGroup() as tasks:
        pending = tasks.create_task(service.update_memory(
            user_id, created.memory.id, MemoryUpdate(tags=["pending"], importance=9),
        ))
        await paused.wait()
        try:
            await service.update_memory(user_id, created.memory.id, MemoryUpdate(
                content="NEW content", tags=concurrent_tags, importance=concurrent_importance,
            ))
            before_resume = await service.get_memory(user_id, created.memory.id)
        finally:
            release.set()
    await bus.wait_for_pending()

    saved = await service.get_memory(user_id, created.memory.id)
    assert saved.content == "NEW content"
    assert saved.tags == ["pending"]
    assert saved.importance == 9
    assert "NEW content" in embeddings.requests[-1]
    assert "ORIGINAL content" not in embeddings.requests[-1]
    assert len(embeddings.requests) == expected_embeddings
    assert pending.result().plugin_warnings[0].message == "Check concurrent edits."
    assert len(evaluated) == 1
    assert evaluated[0].previous.content == "ORIGINAL content"
    assert evaluated[0].proposed.content == "ORIGINAL content"
    if concurrent_importance == 9:
        assert len(events) == 2  # Creation and B; A is now a no-op.
        assert saved.updated_at == before_resume.updated_at
        assert pending.result().memory.updated_at == before_resume.updated_at
    elif concurrent_tags == ["pending"]:
        assert events[-1].changes == {"importance": {"old": 8, "new": 9}}
    else:
        assert events[-1].changes == {
            "tags": {"old": ["concurrent"], "new": ["pending"]},
            "importance": {"old": 8, "new": 9},
        }
