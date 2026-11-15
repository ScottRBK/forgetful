"""Operation-wide rebuild outcomes across real SQLite persistence batches."""

import importlib

from memory_link_plugin_helpers import link_runtime as link_runtime
from memory_link_plugin_helpers import memory_arguments

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate


async def test_targeted_rebuild_preserves_link_outcomes_across_batches(link_runtime, monkeypatch):
    runtime = await build_runtime()
    try:
        user = await runtime.services.user.get_or_create_user(UserCreate(
            external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ))
        memories = []
        for title, tags in (("source A", []), ("source B", []), ("rejected target", ["reject"])):
            saved = await runtime.services.memory.create_memory(
                user.id, MemoryCreate(**memory_arguments(title, tags)),
            )
            memories.append(saved.memory)
        first, second, rejected = memories
        module = importlib.import_module(link_runtime)
        module.before_calls.clear()
        module.after_calls.clear()
        monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
        rebuild = runtime.services.re_embedding
        rebuild.batch_size = 1

        result = await rebuild.rebuild_targeted(user.id, memory_ids=[first.id, second.id])

        expected = {
            (first.id, second.id, "created"),
            (first.id, rejected.id, "rejected"),
            (second.id, first.id, "skipped"),
            (second.id, rejected.id, "rejected"),
        }
        assert result.rebuilt_ids == [first.id, second.id]
        assert result.skipped_ids == [] and result.failed == []
        assert result.link_outcomes is not None and len(result.link_outcomes) == 4
        assert {(item["source_id"], item["target_id"], item["status"]) for item in result.link_outcomes} == expected
        assert [warning["code"] for warning in result.plugin_warnings] == ["MEMORY_LINK_PLUGIN_REJECTED"] * 2
        assert len(module.before_calls) == 3
        assert len(module.after_calls) == 1
        assert module.after_calls[0].pairs[0].source.id == first.id
        assert (await runtime.services.memory.get_memory(user.id, first.id)).linked_memory_ids == [second.id]
        assert (await runtime.services.memory.get_memory(user.id, second.id)).linked_memory_ids == [first.id]
        assert (await runtime.services.memory.get_memory(user.id, rejected.id)).linked_memory_ids == []

        module.before_calls.clear()
        module.after_calls.clear()
        repeated = await rebuild.rebuild_targeted(user.id, memory_ids=[first.id, second.id])

        assert repeated is not result
        assert repeated.rebuilt_ids == [first.id, second.id]
        assert repeated.skipped_ids == [] and repeated.failed == []
        assert repeated.link_outcomes is not None and len(repeated.link_outcomes) == 4
        assert {(item["source_id"], item["target_id"], item["status"]) for item in repeated.link_outcomes} == {
            (source, target, "skipped" if status == "created" else status)
            for source, target, status in expected
        }
        assert [warning["code"] for warning in repeated.plugin_warnings] == ["MEMORY_LINK_PLUGIN_REJECTED"] * 2
        assert len(module.before_calls) == 2
        assert module.after_calls == []
        assert {(item["source_id"], item["target_id"], item["status"]) for item in result.link_outcomes} == expected
    finally:
        await dispose_runtime(runtime)
