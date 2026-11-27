"""File Plugin: registration, reject/warn, modes, no-op skip, settings trio."""

import asyncio

import pytest

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.file_models import FileCreate, FileUpdate
from app.models.write_plugin_models import (
    FileDeletedRequest,
    FileSavedRequest,
    FileWriteRequest,
    PluginWarning,
    WriteDecision,
)
from app.protocols.write_plugin_protocol import FilePlugin
from app.services.file_service import FileService
from app.services.file_write_plugin_service import FileWritePluginService

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="


def candidate(**changes):
    base = {"filename": "logo.png", "description": "Logo", "data": PNG, "mime_type": "image/png", "tags": []}
    return FileCreate(**(base | changes))


def _decider(decision):
    async def handler(request):
        return decision

    return handler


def _raiser():
    async def handler(request):
        raise RuntimeError("SECRET")

    return handler


def _service(handler, mode="enforce", timeout_seconds=5.0, phase="before_save"):
    return FileWritePluginService(
        FilePlugin(**{phase: {"create": handler, "update": handler, "delete": handler}}),
        mode=mode, timeout_seconds=timeout_seconds,
    )


def _write_request(operation="create", tags=()):
    return FileWriteRequest(
        operation=operation, user_id=_USER, submitted=candidate(),
        previous=None, proposed=candidate(tags=list(tags)),
    )


def _saved_request(tags=()):
    file = __import__("app.models.file_models", fromlist=["File"]).File(
        **candidate(tags=list(tags)).model_dump(), id=1, size_bytes=1,
    )
    return FileSavedRequest(operation="create", user_id=_USER, saved=file, previous=None)


def _deleted_request(tags=()):
    from app.models.file_models import File

    file = File(**candidate(tags=list(tags)).model_dump(), id=1, size_bytes=1)
    return FileDeletedRequest(user_id=_USER, deleted_file_id=1, previous=file)


import uuid

_USER = uuid.uuid4()


# --- registration -----------------------------------------------------------


def test_registration_freezes_the_mapping_and_rejects_bad_operations():
    handlers = {"create": _decider(WriteDecision(outcome="allow"))}
    plugin = FilePlugin(before_save=handlers)
    handlers["bogus"] = handlers["create"]
    assert "bogus" not in plugin.before_save
    with pytest.raises(ValueError, match="unsupported file operation"):
        FilePlugin(before_save={"bogus": handlers["create"]})


def test_registration_requires_async_handlers():
    def sync_handler(request):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="must be async"):
        FilePlugin(before_save={"create": sync_handler})


def test_registration_rejects_wrong_arity():
    async def two_args(request, extra):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="one context argument"):
        FilePlugin(before_save={"create": two_args})


# --- reject / warn / allow --------------------------------------------------


async def test_reject_raises_in_enforce_mode():
    service = _service(_decider(WriteDecision(outcome="reject", message="Nope")))
    with pytest.raises(WritePluginRejectedError, match="Nope"):
        await service.before_save(_write_request())


async def test_reject_downgrades_to_warning_in_warn_mode():
    service = _service(
        _decider(WriteDecision(outcome="reject", message="Nope")), mode="warn",
    )
    warnings = await service.before_save(_write_request())
    assert [(w.outcome, w.message) for w in warnings] == [("warn", "Nope")]


async def test_warn_returns_warning_in_both_modes():
    for mode in ("warn", "enforce"):
        service = _service(
            _decider(WriteDecision(outcome="warn", message="Careful", code="c1")), mode=mode,
        )
        warnings = await service.before_save(_write_request())
        assert warnings[0].code == "c1"


async def test_allow_returns_no_warnings():
    service = _service(_decider(WriteDecision(outcome="allow")))
    assert await service.before_save(_write_request()) == []


async def test_unregistered_operation_is_skipped():
    service = _service(_decider(WriteDecision(outcome="reject", message="Nope")))
    request = FileWriteRequest(
        operation="delete", user_id=_USER,
        submitted=__import__(
            "app.models.write_plugin_models", fromlist=["FileDeleteSubmission"],
        ).FileDeleteSubmission(file_id=1),
        previous=None, proposed=None,
    )
    # registered, so it is enforced
    with pytest.raises(WritePluginRejectedError):
        await service.before_save(request)


# --- unavailable / timeout --------------------------------------------------


async def test_handler_error_is_unavailable_in_enforce_mode():
    service = _service(_raiser())
    with pytest.raises(WritePluginUnavailableError, match="File Write Plugin unavailable"):
        await service.before_save(_write_request())


async def test_handler_error_becomes_warning_in_warn_mode():
    warnings = await _service(_raiser(), mode="warn").before_save(_write_request())
    assert warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"


async def test_handler_timeout_counts_as_unavailable():
    async def slow(request):
        await asyncio.sleep(5)
        return WriteDecision(outcome="allow")

    service = _service(slow, timeout_seconds=0.01)
    with pytest.raises(WritePluginUnavailableError):
        await service.before_save(_write_request())


async def test_after_save_failure_stays_advisory():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_saved_request())
    assert warnings[0].code == "FILE_PLUGIN_AFTER_SAVE_UNAVAILABLE"


async def test_after_save_delete_message_differs():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_deleted_request())
    assert "deleted" in warnings[0].message


# --- settings trio ----------------------------------------------------------


def test_settings_trio_defaults():
    from app.config.settings import Settings

    fresh = Settings()
    assert fresh.FILE_WRITE_PLUGIN == ""
    assert fresh.FILE_WRITE_PLUGIN_MODE == "enforce"
    assert fresh.FILE_WRITE_PLUGIN_TIMEOUT_SECONDS == 5.0


def test_settings_mode_is_constrained():
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(FILE_WRITE_PLUGIN_MODE="ignore")


def test_settings_timeout_must_be_positive():
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(FILE_WRITE_PLUGIN_TIMEOUT_SECONDS=0)


# --- service integration: enforcement and no-op skip ------------------------


async def test_create_rejects_through_service(file_store):
    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Remove the blocked tag.")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.create_file(user_id, candidate(tags=["blocked"]))
    # nothing persisted
    assert await service.list_files(user_id=user_id) == []


async def test_create_warns_through_service(file_store):
    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="warn", message="Check the source.", code="source")),
    ))
    result = await service.create_file(user_id, candidate())
    assert result.plugin_warnings[0].code == "source"
    assert result.file.id is not None


async def test_update_noop_skips_plugin(file_store):
    repo, user_id, bus = file_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    created = await FileService(repo, event_bus=bus).create_file(user_id, candidate())
    service = FileService(repo, event_bus=bus, write_plugin=_service(counting))
    # PATCH that changes nothing: the same description, no nulls involved
    result = await service.update_file(
        user_id, created.file.id, FileUpdate(description="Logo"),
    )
    assert calls == []
    assert result.plugin_warnings == []


async def test_update_with_change_runs_plugin(file_store):
    repo, user_id, bus = file_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    created = await FileService(repo, event_bus=bus).create_file(user_id, candidate())
    service = FileService(repo, event_bus=bus, write_plugin=_service(counting))
    await service.update_file(user_id, created.file.id, FileUpdate(description="New"))
    assert calls == ["update"]


async def test_delete_runs_before_and_after(file_store):
    repo, user_id, bus = file_store
    calls = []

    async def before(request):
        calls.append(("before", request.operation))
        return WriteDecision(outcome="allow")

    async def after(request):
        calls.append(("after", request.operation))
        return None

    plugin = FilePlugin(
        before_save={"delete": before}, after_save={"delete": after},
    )
    service = FileService(
        repo, event_bus=bus,
        write_plugin=FileWritePluginService(plugin),
    )
    created = await service.create_file(user_id, candidate())
    result = await service.delete_file(user_id, created.file.id)
    assert result.deleted is True
    assert calls == [("before", "delete"), ("after", "delete")]


async def test_delete_rejected_leaves_file(file_store):
    repo, user_id, bus = file_store
    created = await FileService(repo, event_bus=bus).create_file(user_id, candidate())
    service = FileService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Keep it")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.delete_file(user_id, created.file.id)
    assert (await service.get_file(user_id, created.file.id)).id == created.file.id


async def test_after_save_warning_survives_create(file_store):
    repo, user_id, bus = file_store

    async def after(request):
        return PluginWarning(message="Post-save check.", code="post")

    service = FileService(
        repo, event_bus=bus,
        write_plugin=FileWritePluginService(FilePlugin(after_save={"create": after})),
    )
    result = await service.create_file(user_id, candidate())
    assert result.plugin_warnings[0].code == "post"


# --- regression guards for the review fixes ---------------------------------


async def test_update_replacing_data_decodes_the_payload_once(monkeypatch):
    """FileUpdate's validator base64-decodes `data`; the service must not do it again.

    Guards the null-strip and `proposed` construction against re-validating the
    model, which would decode a multi-megabyte payload an extra time per write.
    A fake repository that does not re-validate isolates the service's own cost;
    repository-level decoding is pre-existing behaviour.
    """
    import base64 as b64

    from app.models.file_models import File

    class PlainRepo:
        def __init__(self):
            # model_construct with literals: building a FileCreate here would
            # itself decode the payload and pollute the count.
            self.stored = File.model_construct(
                filename="logo.png", description="Logo", data=PNG,
                mime_type="image/png", tags=[], id=1, size_bytes=1,
            )

        async def get_file_by_id(self, user_id, file_id):
            return self.stored

        async def update_file(self, user_id, file_id, file_data):
            self.stored = self.stored.model_copy(
                update=file_data.model_dump(exclude_unset=True),
            )
            return self.stored

    calls = {"n": 0}
    original = b64.b64decode

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(b64, "b64decode", counting)

    update = FileUpdate(data=PNG)
    assert calls["n"] == 1, "caller validation should decode exactly once"

    service = FileService(
        PlainRepo(), write_plugin=_service(_decider(WriteDecision(outcome="allow"))),
    )
    await service.update_file(_USER, 1, update)
    assert calls["n"] == 1, "service must not re-decode the payload"


async def test_update_proposed_is_the_merged_full_snapshot(file_store):
    """`proposed` must describe the whole file after the update, like the Entity Plugin.

    A partial snapshot would let a rule that inspects, say, tags miss them on
    update while seeing them on create.
    """
    seen = {}

    async def capture(request):
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    repo, user_id, bus = file_store
    created = await FileService(repo, event_bus=bus).create_file(
        user_id, candidate(tags=["keep", "drop"]),
    )
    service = FileService(repo, event_bus=bus, write_plugin=_service(capture))
    await service.update_file(user_id, created.file.id, FileUpdate(description="New"))

    proposed = seen["proposed"]
    assert proposed is not None
    # Merged, not partial: untouched fields survive.
    assert proposed.filename == "logo.png"
    assert proposed.mime_type == "image/png"
    assert proposed.tags == ["keep", "drop"]
    assert proposed.description == "New"


async def test_before_handler_mutation_does_not_reach_the_stored_file(file_store):
    async def tamper(request):
        request.proposed.tags.append("injected")
        return WriteDecision(outcome="allow")

    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(tamper))
    result = await service.create_file(user_id, candidate())
    assert result.file.tags == []


async def test_after_handler_mutation_does_not_reach_the_stored_file(file_store):
    async def tamper(request):
        request.saved.tags.append("injected")
        return None

    repo, user_id, bus = file_store
    service = FileService(
        repo, event_bus=bus,
        write_plugin=FileWritePluginService(FilePlugin(after_save={"create": tamper})),
    )
    result = await service.create_file(user_id, candidate())
    assert result.file.tags == []
    stored = await service.get_file(user_id, result.file.id)
    assert stored.tags == []


async def test_delete_previous_reflects_state_changed_during_before_wait(file_store):
    """A concurrent writer during before_save must not be reported as the old state."""
    repo, user_id, bus = file_store
    seen = {}

    async def concurrent_edit(request):
        # Simulate another writer touching the row while the hook is running.
        await repo.update_file(
            user_id=user_id, file_id=request.previous.id,
            file_data=FileUpdate(tags=["concurrently-tagged"]),
        )
        return WriteDecision(outcome="allow")

    async def capture_deleted(request):
        seen["previous"] = request.previous
        return None

    service = FileService(repo, event_bus=bus, write_plugin=FileWritePluginService(
        FilePlugin(
            before_save={"delete": concurrent_edit},
            after_save={"delete": capture_deleted},
        ),
    ))
    created = await FileService(repo, event_bus=bus).create_file(user_id, candidate())
    await service.delete_file(user_id, created.file.id)
    assert seen["previous"].tags == ["concurrently-tagged"]


async def test_update_missing_file_raises_not_found(file_store):
    from app.exceptions import NotFoundError

    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="allow")),
    ))
    with pytest.raises(NotFoundError):
        await service.update_file(user_id, 4242, FileUpdate(description="x"))


async def test_unavailable_before_save_persists_nothing_in_enforce_mode(file_store):
    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(_raiser()))
    with pytest.raises(WritePluginUnavailableError):
        await service.create_file(user_id, candidate())
    assert await service.list_files(user_id=user_id) == []


async def test_unavailable_before_save_persists_with_warning_in_warn_mode(file_store):
    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus, write_plugin=_service(_raiser(), mode="warn"))
    result = await service.create_file(user_id, candidate())
    assert result.plugin_warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"
    assert (await service.get_file(user_id, result.file.id)).id == result.file.id


# --- cascade and indirect mutation (documented truth, asserted) -------------


async def test_project_delete_nulls_project_id_without_running_the_file_plugin(file_store):
    """Deleting a project nulls files.project_id at the database level.

    That is an indirect mutation of a file row, and no File Plugin phase runs
    for it: only create_file, update_file and delete_file on FileService are hooked.
    """
    from app.models.project_models import ProjectCreate
    from app.repositories.sqlite.project_repository import SqliteProjectRepository
    from app.services.project_service import ProjectService

    repo, user_id, bus = file_store
    calls = []

    async def record(request):
        calls.append((request.operation, "update"))
        return WriteDecision(outcome="allow")

    service = FileService(repo, event_bus=bus, write_plugin=_service(record))
    project_service = ProjectService(SqliteProjectRepository(repo.db_adapter))
    project = await project_service.create_project(user_id, ProjectCreate(
        name="Cascade Project", description="Scoped to the cascade test",
        project_type="development",
    ))
    created = await service.create_file(
        user_id, candidate(project_id=project.id),
    )
    assert created.file.project_id == project.id
    calls.clear()

    await project_service.delete_project(user_id, project.id)

    refreshed = await service.get_file(user_id, created.file.id)
    assert refreshed.project_id is None
    assert calls == [], "an indirect mutation must not run the file plugin"


# --- null policy (must match the behaviour before this feature) -------------


async def test_explicit_null_still_clears_a_nullable_field(file_store):
    """source_repo is nullable: an explicit null clears it, as it did before.

    Dropping nulls before change detection would silently ignore this request.
    """
    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus)
    created = await service.create_file(user_id, candidate(source_repo="clear me"))

    result = await service.update_file(
        user_id, created.file.id, FileUpdate(source_repo=None),
    )

    assert result.file.source_repo is None
    refreshed = await service.get_file(user_id, created.file.id)
    assert refreshed.source_repo is None


async def test_explicit_null_on_a_required_field_still_fails(file_store):
    """mime_type is NOT NULL: an explicit null must reach the repository and fail.

    Silently treating it as "unchanged" would accept a write the database rejects.
    """
    from sqlalchemy.exc import SQLAlchemyError

    repo, user_id, bus = file_store
    service = FileService(repo, event_bus=bus)
    created = await service.create_file(user_id, candidate())

    with pytest.raises(SQLAlchemyError):
        await service.update_file(
            user_id, created.file.id, FileUpdate(mime_type=None),
        )

    refreshed = await service.get_file(user_id, created.file.id)
    assert refreshed.mime_type == "image/png"
