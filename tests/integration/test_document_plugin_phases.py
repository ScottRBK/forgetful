"""Document Plugin phases through DocumentService and isolated SQLite."""

import asyncio
import logging

import pytest
from document_plugin_helpers import candidate

from app.exceptions import (
    NotFoundError,
    WritePluginRejectedError,
    WritePluginUnavailableError,
)
from app.models.document_models import DocumentUpdate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import DocumentPlugin
from app.services.document_service import DocumentService
from app.services.document_write_plugin_service import DocumentWritePluginService


async def test_no_plugin_returns_empty_warnings(document_store):
    repo, user_id, _ = document_store
    service = DocumentService(repo)
    result = await service.create_document(user_id, candidate())
    assert result.plugin_warnings == []
    assert result.document.title == "API Guide"


async def test_before_reject_blocks_create(document_store):
    repo, user_id, _ = document_store

    async def before(request):
        if "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(before_save={"create": before})),
    )
    await service.create_document(user_id, candidate())
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_document(user_id, candidate(tags=["blocked"]))


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "timeout", "reject", "mutated", "cancelled_child"])
async def test_after_failure_warns_without_failing_saved_create(document_store, mode, failure, caplog):
    repo, user_id, _ = document_store
    logging.getLogger("app.services.document_write_plugin_service").disabled = False

    async def after(request):
        if failure == "error":
            raise RuntimeError("SECRET document content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "reject":
            return {"outcome": "reject", "message": "SECRET document content"}
        if failure == "cancelled_child":
            child = asyncio.create_task(asyncio.sleep(10))
            child.cancel("SECRET document content")
            await child
        warning = PluginWarning(message="Valid originally")
        warning.message = " "
        return warning

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(after_save={"create": after}),
            mode=mode, timeout_seconds=0.01 if failure == "timeout" else 5,
        ),
    )
    result = await service.create_document(user_id, candidate())
    assert result.plugin_warnings == [PluginWarning(
        message="Document saved, but after-save plugin unavailable.",
        code="DOCUMENT_PLUGIN_AFTER_SAVE_UNAVAILABLE",
    )]
    assert (await service.get_document(user_id, result.document.id)).title == "API Guide"
    assert "after_save" in caplog.text
    if failure == "cancelled_child":
        assert "error_type=CancelledError" in caplog.text
    assert "SECRET" not in caplog.text


async def test_detached_snapshots_survive_handler_mutation(document_store):
    repo, user_id, _ = document_store
    seen = []

    async def before(request):
        seen.append(request.model_copy(deep=True))
        if request.proposed is not None:
            request.proposed.title = "mutated title"
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(before_save={"create": before})),
    )
    result = await service.create_document(user_id, candidate())
    assert seen[0].proposed.title == "API Guide"
    assert result.document.title == "API Guide"


async def test_noop_update_skips_plugin(document_store):
    repo, user_id, _ = document_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(before_save={"update": before})),
    )
    created = (await service.create_document(user_id, candidate(description="same"))).document
    await service.update_document(user_id, created.id, DocumentUpdate(notes="same"))
    await service.update_document(user_id, created.id, DocumentUpdate(notes="same"))
    assert calls == []


async def test_delete_missing_skips_plugin(document_store):
    repo, user_id, _ = document_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(before_save={"delete": before})),
    )
    result = await service.delete_document(user_id, 99999)
    assert result.deleted is False
    assert result.plugin_warnings == []
    assert calls == []


async def test_delete_after_receives_previous_not_saved_object(document_store):
    repo, user_id, _ = document_store
    seen = []

    async def after(request):
        seen.append(request)
        assert request.deleted_document_id == created_id
        assert request.previous.title == "API Guide"
        return None

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(after_save={"delete": after})),
    )
    created_id = (await service.create_document(user_id, candidate())).document.id
    result = await service.delete_document(user_id, created_id)
    assert result.deleted is True
    assert len(seen) == 1


async def test_update_not_found_raises(document_store):
    repo, user_id, _ = document_store
    service = DocumentService(repo)
    with pytest.raises(NotFoundError):
        await service.update_document(user_id, 99999, DocumentUpdate(notes="nope"))


@pytest.mark.parametrize("mode", ["warn", "enforce"])
async def test_before_warn_returns_warning_and_persists(document_store, mode):
    repo, user_id, bus = document_store
    events = []

    async def collect(event):
        events.append(event)

    bus.subscribe("document.*", collect)

    async def before(request):
        return WriteDecision(outcome="warn", message="Check the source.", code="source")

    service = DocumentService(
        repo, bus, DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before}), mode=mode,
        ),
    )
    result = await service.create_document(user_id, candidate())
    assert result.plugin_warnings[0].message == "Check the source."
    saved = await service.get_document(user_id, result.document.id)
    assert "plugin_warnings" not in saved.model_dump()
    await bus.wait_for_pending()
    assert len(events) == 1
    assert "plugin_warnings" not in events[0].snapshot


async def test_warn_mode_downgrades_reject_and_persists(document_store):
    repo, user_id, _ = document_store

    async def before(request):
        return WriteDecision(outcome="reject", message="Check the source.", code="source")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before}), mode="warn",
        ),
    )
    result = await service.create_document(user_id, candidate())
    assert result.plugin_warnings[0].outcome == "warn"
    assert result.plugin_warnings[0].code == "source"
    listed = await service.list_documents(user_id)
    assert len(listed) == 1


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "bad_result", "blank", "mutated", "timeout"])
async def test_before_unavailable_is_generic_and_mode_controls_persistence(
    document_store, mode, failure, caplog,
):
    repo, user_id, _ = document_store
    logging.getLogger("app.services.document_write_plugin_service").disabled = False

    async def before(request):
        if failure == "error":
            raise RuntimeError("SECRET document content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "blank":
            return {"outcome": "reject", "message": "  "}
        if failure == "mutated":
            decision = WriteDecision(outcome="allow")
            decision.outcome = "invalid"
            return decision
        return {"outcome": "invalid", "message": "SECRET document content"}

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before}),
            mode=mode, timeout_seconds=0.01,
        ),
    )
    if mode == "enforce":
        with pytest.raises(
            WritePluginUnavailableError, match=r"^Document Write Plugin unavailable\.$",
        ):
            await service.create_document(user_id, candidate())
    else:
        result = await service.create_document(user_id, candidate())
        assert result.plugin_warnings[0].message == "Document Write Plugin unavailable."
        assert result.plugin_warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"
    listed = await service.list_documents(user_id)
    assert len(listed) == (1 if mode == "warn" else 0)
    assert "Document Write Plugin" in caplog.text
    assert "SECRET" not in caplog.text


async def test_unregistered_operation_runs_without_warnings(document_store):
    repo, user_id, _ = document_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before}),
        ),
    )
    created = (await service.create_document(user_id, candidate())).document
    updated = await service.update_document(user_id, created.id, DocumentUpdate(notes="changed"))
    assert updated.plugin_warnings == []
    assert calls == [calls[0]]
    assert calls[0].operation == "create"


async def test_update_rejection_leaves_document_unchanged(document_store):
    repo, user_id, _ = document_store

    async def check(request):
        if request.proposed and "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": check, "update": check}),
        ),
    )
    created = (await service.create_document(user_id, candidate())).document
    before = await service.get_document(user_id, created.id)
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.update_document(user_id, created.id, DocumentUpdate(tags=["blocked"]))
    assert (await service.get_document(user_id, created.id)).model_dump() == before.model_dump()


async def test_delete_rejection_leaves_document_unchanged(document_store):
    repo, user_id, _ = document_store

    async def check(request):
        if request.operation == "delete":
            return WriteDecision(outcome="reject", message="Keep this document.")
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": check, "delete": check}),
        ),
    )
    created = (await service.create_document(user_id, candidate())).document
    with pytest.raises(WritePluginRejectedError, match="Keep this document"):
        await service.delete_document(user_id, created.id)
    assert (await service.get_document(user_id, created.id)).id == created.id


async def test_before_handler_sees_caller_user_id_and_isolates_other_users(document_store):
    from app.models.user_models import UserCreate
    from app.repositories.sqlite.user_repository import SqliteUserRepository
    from app.services.user_service import UserService

    repo, user_id, _ = document_store
    other = await UserService(SqliteUserRepository(repo.db_adapter)).get_or_create_user(
        UserCreate(external_id="other-document", name="Other", email="other-document@example.com"),
    )
    observer = DocumentService(repo)
    foreign = (await observer.create_document(other.id, candidate())).document
    seen = []

    async def before(request):
        seen.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(DocumentPlugin(before_save={"create": before})),
    )
    await service.create_document(user_id, candidate())
    assert len(seen) == 1
    assert seen[0].user_id == user_id
    assert (await observer.get_document(other.id, foreign.id)).id == foreign.id


async def test_external_cancellation_after_save_propagates_but_write_remains(document_store):
    repo, user_id, _ = document_store
    entered = asyncio.Event()

    async def after(request):
        entered.set()
        await asyncio.Event().wait()

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(after_save={"create": after}),
        ),
    )
    task = asyncio.create_task(service.create_document(user_id, candidate()))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
    finally:
        task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    listed = await service.list_documents(user_id)
    assert len(listed) == 1


async def test_before_cancellation_propagates_in_warn_mode(document_store):
    repo, user_id, _ = document_store

    async def before(request):
        if request.proposed and "cancel" in request.proposed.tags:
            raise asyncio.CancelledError()
        return WriteDecision(outcome="reject", message="Check the source.", code="source")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before}), mode="warn",
        ),
    )
    await service.create_document(user_id, candidate())
    with pytest.raises(asyncio.CancelledError):
        await service.create_document(user_id, candidate(tags=["cancel"]))
    listed = await service.list_documents(user_id)
    assert len(listed) == 1


async def test_update_content_only_sets_proposed_size_bytes(document_store):
    repo, user_id, _ = document_store
    seen = []

    async def before(request):
        seen.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before, "update": before}),
        ),
    )
    content = "replacement body"
    created = (await service.create_document(user_id, candidate())).document
    result = await service.update_document(
        user_id, created.id, DocumentUpdate(content=content),
    )
    expected = len(content.encode("utf-8"))
    assert seen[-1].proposed.size_bytes == expected
    assert result.document.size_bytes == expected


async def test_update_without_content_keeps_proposed_size_bytes(document_store):
    repo, user_id, _ = document_store
    seen = []

    async def before(request):
        if request.operation == "update":
            seen.append(request)
        return WriteDecision(outcome="allow")

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before, "update": before}),
        ),
    )
    created = (await service.create_document(user_id, candidate())).document
    previous_size = created.size_bytes
    await service.update_document(user_id, created.id, DocumentUpdate(description="new summary"))
    assert seen[-1].proposed.size_bytes == previous_size


async def test_foreign_project_id_fails_after_allowing_before_save(document_store):
    from app.models.project_models import ProjectCreate
    from app.models.user_models import UserCreate
    from app.repositories.sqlite.project_repository import SqliteProjectRepository
    from app.repositories.sqlite.user_repository import SqliteUserRepository
    from app.services.project_service import ProjectService
    from app.services.user_service import UserService

    repo, user_id, _ = document_store
    other = await UserService(SqliteUserRepository(repo.db_adapter)).get_or_create_user(
        UserCreate(external_id="foreign-project-user", name="Other", email="foreign@example.com"),
    )
    foreign_project = await ProjectService(SqliteProjectRepository(repo.db_adapter)).create_project(
        other.id,
        ProjectCreate(name="Foreign", description="Not yours", project_type="personal"),
    )
    after_calls = []

    async def before(request):
        return WriteDecision(outcome="allow")

    async def after(request):
        after_calls.append(request)
        return None

    service = DocumentService(
        repo, write_plugin=DocumentWritePluginService(
            DocumentPlugin(before_save={"create": before, "update": before}, after_save={"update": after}),
        ),
    )
    created = (await service.create_document(user_id, candidate())).document
    with pytest.raises(NotFoundError):
        await service.update_document(
            user_id, created.id, DocumentUpdate(project_id=foreign_project.id),
        )
    assert after_calls == []

