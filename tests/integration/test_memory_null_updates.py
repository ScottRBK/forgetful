"""Memory null updates through the service and real isolated SQLite storage."""

import pytest
from test_memory_write_plugin import candidate
from test_memory_write_plugin import write_store as write_store

from app.config.settings import settings
from app.models.memory_models import MemoryUpdate
from app.models.write_plugin_models import WriteDecision
from app.services.memory_service import MemoryService
from app.services.write_plugin_service import WritePluginService


@pytest.mark.parametrize("field", ["title", "content", "context", "tags", "confidence"])
async def test_null_only_preserves_memory_timestamp_and_side_effects(write_store, field):
    repo, user_id, embeddings, bus = write_store
    events = []

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    service = MemoryService(repo, event_bus=bus)
    created = (await service.create_memory(user_id, candidate(tags=["saved"], confidence=0.8))).memory
    before = await service.get_memory(user_id, created.id)
    updated = (await service.update_memory(user_id, before.id, MemoryUpdate(**{field: None}))).memory
    await bus.wait_for_pending()
    assert updated.model_dump() == before.model_dump()
    assert [event.action for event in events] == ["created"]
    assert len(embeddings.requests) == 1
    assert (await service.get_memory(user_id, before.id)).updated_at == before.updated_at


async def test_mixed_null_update_changes_only_non_null_fields(write_store):
    repo, user_id, embeddings, _ = write_store
    service = MemoryService(repo)
    before = (await service.create_memory(user_id, candidate())).memory
    update = MemoryUpdate(title=None, importance=9)
    updated = (await service.update_memory(user_id, before.id, update)).memory
    saved = await service.get_memory(user_id, before.id)
    assert saved.title == before.title == updated.title
    assert saved.importance == updated.importance == 9
    assert update.title is None and update.model_fields_set == {"title", "importance"}
    assert len(embeddings.requests) == 1


async def test_empty_tags_and_zero_confidence_are_meaningful_updates(write_store):
    repo, user_id, _, _ = write_store
    service = MemoryService(repo)
    created = (await service.create_memory(user_id, candidate(tags=["saved"], confidence=0.8))).memory
    before = await service.get_memory(user_id, created.id)
    await service.update_memory(user_id, before.id, MemoryUpdate(tags=[], confidence=0))
    saved = await service.get_memory(user_id, before.id)
    assert saved.tags == []
    assert saved.confidence == 0


@pytest.mark.parametrize("enforce", [False, True])
async def test_provenance_null_is_not_supplied_but_non_null_is(write_store, monkeypatch, enforce):
    repo, user_id, _, _ = write_store
    monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", False)
    monkeypatch.setattr(settings, "AGENT_ID", "server-agent")
    service = MemoryService(repo)
    created = (await service.create_memory(user_id, candidate(agent_id="original-agent"))).memory
    before = await service.get_memory(user_id, created.id)
    monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", enforce)
    update = MemoryUpdate(agent_id=None)
    unchanged = (await service.update_memory(user_id, before.id, update)).memory
    assert unchanged.agent_id == "original-agent"
    assert unchanged.updated_at == before.updated_at
    assert update.agent_id is None and update.model_fields_set == {"agent_id"}
    changed = (await service.update_memory(user_id, before.id, MemoryUpdate(agent_id="client-agent"))).memory
    assert changed.agent_id == ("server-agent" if enforce else "client-agent")


async def test_plugin_keeps_raw_nulls_but_proposes_unchanged_values(write_store):
    repo, user_id, embeddings, _ = write_store
    calls = []

    async def check(request):
        calls.append(request.model_copy(deep=True))
        return WriteDecision(outcome="allow")

    service = MemoryService(repo, write_plugin=WritePluginService(check))
    created = (await service.create_memory(user_id, candidate(source_url="old"))).memory
    before = await service.get_memory(user_id, created.id)
    noop = (await service.update_memory(user_id, before.id, MemoryUpdate(title=None))).memory
    assert noop.updated_at == before.updated_at and len(calls) == 1
    mixed = MemoryUpdate(title=None, source_url=None, importance=9)
    result = (await service.update_memory(user_id, before.id, mixed)).memory
    assert result.title == before.title and result.source_url == "old" and result.importance == 9
    assert calls[-1].submitted.model_fields_set == {"title", "source_url", "importance"}
    assert calls[-1].submitted.title is None and calls[-1].submitted.source_url is None
    assert calls[-1].proposed.title == before.title and calls[-1].proposed.source_url == "old"
    assert len(embeddings.requests) == 1
