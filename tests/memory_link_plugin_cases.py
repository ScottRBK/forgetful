"""The same policy invariants against the real SQLite and PostgreSQL repositories."""
import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.exceptions import WritePluginRejectedError
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import WriteDecision
from app.protocols.write_plugin_protocol import MemoryLinkPlugin
from app.services.memory_link_service import MemoryLinkService


async def native_policy_case(app, monkeypatch, mode, operation="link", cancel=False):
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    service = app.memory_service
    previous = service._link_plugin
    user = await app.user_service.get_or_create_user(UserCreate(
        external_id=f"link-policy-{uuid4().hex}", name="Synthetic", email=f"{uuid4().hex}@example.test",
    ))
    other = await app.user_service.get_or_create_user(UserCreate(
        external_id=f"link-policy-{uuid4().hex}", name="Other", email=f"{uuid4().hex}@example.test",
    ))

    async def create(owner, title):
        return (await service.create_memory(owner.id, MemoryCreate(
            title=title, content="Policy backend case", context="Synthetic", keywords=[], tags=[], importance=6,
        ))).memory

    source, duplicate, allowed, rejected = [await create(user, title) for title in (
        "source", "already linked", "allowed", "rejected",
    )]
    foreign = await create(other, "foreign")
    await service.memory_repo.create_links_batch(user.id, source.id, [duplicate.id])
    if operation == "unlink":
        await service.memory_repo.create_links_batch(user.id, source.id, [allowed.id, rejected.id])
    initial = {duplicate.id, allowed.id, rejected.id} if operation == "unlink" else {duplicate.id}
    calls, after = [], []
    active_sessions = 0
    original_session = service.memory_repo.db_adapter.session

    @asynccontextmanager
    async def tracked_session(*args, **kwargs):
        nonlocal active_sessions
        async with original_session(*args, **kwargs) as session:
            active_sessions += 1
            try:
                yield session
            finally:
                active_sessions -= 1

    monkeypatch.setattr(service.memory_repo.db_adapter, "session", tracked_session)

    async def before(request):
        assert active_sessions == 0
        calls.append(request.target.id)
        current = await service.get_memory(user.id, source.id)
        assert set(current.linked_memory_ids) == initial
        if request.target.id == rejected.id:
            if cancel:
                asyncio.current_task().cancel()
                await asyncio.sleep(0)
            return WriteDecision(outcome="reject", message="Synthetic policy")
        return WriteDecision(outcome="allow")

    async def saved(request):
        assert active_sessions == 0
        after.append(request)

    service._link_plugin = MemoryLinkService(
        service.memory_repo, MemoryLinkPlugin(before_save={operation: before}, after_save={operation: saved}),
        mode=mode,
    )
    targets = [source.id, foreign.id, 2_000_000_000, allowed.id, rejected.id, allowed.id]
    if operation == "link":
        targets.insert(1, duplicate.id)
    mutate = service.link_memories if operation == "link" else service.unlink_memories_batch
    try:
        if mode == "enforce" or cancel:
            expected = asyncio.CancelledError if cancel else WritePluginRejectedError
            with pytest.raises(expected):
                await asyncio.create_task(mutate(user.id, source.id, targets))
            assert set((await service.get_memory(user.id, source.id)).linked_memory_ids) == initial
            assert after == []
        else:
            result = await mutate(user.id, source.id, targets)
            skipped = "skipped" if operation == "link" else "noop"
            changed = "created" if operation == "link" else "removed"
            assert [item.status for item in result.outcomes] == (
                [skipped] * (4 if operation == "link" else 3) + [changed, changed]
            )
            if operation == "link":
                assert result.created_ids == [allowed.id, rejected.id]
            else:
                assert set((await service.get_memory(user.id, source.id)).linked_memory_ids) == {duplicate.id}
            assert len(result.plugin_warnings) == 1
            assert len(after) == 1 and len(after[0].pairs) == 2
            # Neither foreign nor missing IDs can provide a detached content snapshot.
            assert {pair.target.id for pair in after[0].pairs} == {allowed.id, rejected.id}
        assert calls == [allowed.id, rejected.id]
        if operation == "unlink" and mode == "warn" and not cancel:
            no_op = await service.unlink_memories_batch(user.id, source.id, [allowed.id, rejected.id])
            assert [item.status for item in no_op.outcomes] == ["noop", "noop"]
            assert calls == [allowed.id, rejected.id] and len(after) == 1
    finally:
        service._link_plugin = previous
