"""Code Artifact Plugin: registration, reject/warn, modes, no-op skip, cascade."""

import asyncio
import uuid

import pytest
from pydantic import ValidationError

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.code_artifact_models import (
    CodeArtifact,
    CodeArtifactCreate,
    CodeArtifactUpdate,
)
from app.models.write_plugin_models import (
    CodeArtifactDeletedRequest,
    CodeArtifactDeleteSubmission,
    CodeArtifactSavedRequest,
    CodeArtifactWriteRequest,
    PluginWarning,
    WriteDecision,
)
from app.protocols.write_plugin_protocol import CodeArtifactPlugin
from app.services.code_artifact_service import CodeArtifactService
from app.services.code_artifact_write_plugin_service import (
    CodeArtifactWritePluginService,
)

_USER = uuid.uuid4()


def candidate(**changes) -> CodeArtifactCreate:
    base = {
        "title": "Helper function",
        "description": "A small helper",
        "code": "def helper():\n    return 1\n",
        "language": "python",
        "tags": [],
    }
    base.update(changes)
    return CodeArtifactCreate(**base)


def _decider(decision):
    async def handler(request):
        return decision

    return handler


def _raiser():
    async def handler(request):
        raise RuntimeError("SECRET")

    return handler


def _service(handler, mode="enforce", timeout_seconds=5.0, phase="before_save"):
    return CodeArtifactWritePluginService(
        CodeArtifactPlugin(
            **{phase: {"create": handler, "update": handler, "delete": handler}},
        ),
        mode=mode, timeout_seconds=timeout_seconds,
    )


def _write_request(operation="create", tags=()):
    return CodeArtifactWriteRequest(
        operation=operation, user_id=_USER, submitted=candidate(),
        previous=None, proposed=candidate(tags=list(tags)),
    )


def _artifact(tags=()) -> CodeArtifact:
    return CodeArtifact(**candidate(tags=list(tags)).model_dump(), id=1)


def _saved_request(tags=()):
    return CodeArtifactSavedRequest(
        operation="create", user_id=_USER, saved=_artifact(tags), previous=None,
    )


def _deleted_request(tags=()):
    return CodeArtifactDeletedRequest(
        user_id=_USER, deleted_artifact_id=1, previous=_artifact(tags),
    )


# --- registration -----------------------------------------------------------


def test_registration_freezes_the_mapping_and_rejects_bad_operations():
    handlers = {"create": _decider(WriteDecision(outcome="allow"))}
    plugin = CodeArtifactPlugin(before_save=handlers)
    handlers["bogus"] = handlers["create"]
    assert "bogus" not in plugin.before_save
    with pytest.raises(ValueError, match="unsupported code artifact operation"):
        CodeArtifactPlugin(before_save={"bogus": handlers["create"]})


def test_registration_requires_async_handlers():
    def sync_handler(request):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="must be async"):
        CodeArtifactPlugin(before_save={"create": sync_handler})


def test_registration_rejects_wrong_arity():
    async def two_args(request, extra):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="one context argument"):
        CodeArtifactPlugin(before_save={"create": two_args})


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


# --- unavailable / timeout --------------------------------------------------


async def test_handler_error_is_unavailable_in_enforce_mode():
    service = _service(_raiser())
    with pytest.raises(
        WritePluginUnavailableError, match="Code Artifact Write Plugin unavailable",
    ):
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
    assert warnings[0].code == "CODE_ARTIFACT_PLUGIN_AFTER_SAVE_UNAVAILABLE"


async def test_after_save_delete_message_differs():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_deleted_request())
    assert "deleted" in warnings[0].message


# --- settings trio ----------------------------------------------------------


def test_settings_trio_defaults():
    from app.config.settings import Settings

    fresh = Settings()
    assert fresh.CODE_ARTIFACT_WRITE_PLUGIN == ""
    assert fresh.CODE_ARTIFACT_WRITE_PLUGIN_MODE == "enforce"
    assert fresh.CODE_ARTIFACT_WRITE_PLUGIN_TIMEOUT_SECONDS == 5.0


def test_settings_mode_is_constrained():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(CODE_ARTIFACT_WRITE_PLUGIN_MODE="ignore")


def test_settings_timeout_must_be_positive():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(CODE_ARTIFACT_WRITE_PLUGIN_TIMEOUT_SECONDS=0)


# --- service integration ----------------------------------------------------


async def test_create_rejects_through_service(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Remove the blocked tag.")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.create_code_artifact(user_id, candidate(tags=["blocked"]))
    assert await service.list_code_artifacts(user_id=user_id) == []


async def test_create_warns_through_service(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="warn", message="Check the source.", code="source")),
    ))
    result = await service.create_code_artifact(user_id, candidate())
    assert result.plugin_warnings[0].code == "source"
    assert result.artifact.id is not None


async def test_update_proposed_is_the_full_merged_record(code_artifact_store):
    """`proposed` is the whole artifact after the write, not just changed fields."""
    seen = {}

    async def capture(request):
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    repo, user_id, bus = code_artifact_store
    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(tags=["keep", "drop"]),
    )
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(capture))
    await service.update_code_artifact(
        user_id, created.artifact.id, CodeArtifactUpdate(description="New description"),
    )

    proposed = seen["proposed"]
    assert isinstance(proposed, CodeArtifactCreate)
    assert proposed.description == "New description"
    # Untouched fields are present in the snapshot.
    assert proposed.title == "Helper function"
    assert proposed.code == created.artifact.code
    assert proposed.language == "python"
    assert proposed.tags == ["keep", "drop"]


async def test_update_noop_skips_plugin(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(),
    )
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(counting))
    result = await service.update_code_artifact(
        user_id, created.artifact.id,
        CodeArtifactUpdate(description="A small helper"),
    )

    assert calls == []
    assert result.plugin_warnings == []


async def test_update_with_change_runs_plugin(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(),
    )
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(counting))
    await service.update_code_artifact(
        user_id, created.artifact.id, CodeArtifactUpdate(description="Changed"),
    )

    assert calls == ["update"]


async def test_delete_runs_before_and_after(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    calls = []

    async def before(request):
        calls.append(("before", request.operation))
        return WriteDecision(outcome="allow")

    async def after(request):
        calls.append(("after", request.operation))
        return None

    plugin = CodeArtifactPlugin(
        before_save={"delete": before}, after_save={"delete": after},
    )
    service = CodeArtifactService(
        repo, event_bus=bus, write_plugin=CodeArtifactWritePluginService(plugin),
    )
    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(),
    )
    result = await service.delete_code_artifact(user_id, created.artifact.id)

    assert result.deleted is True
    assert calls == [("before", "delete"), ("after", "delete")]


async def test_delete_rejected_leaves_artifact(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(),
    )
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Keep it")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.delete_code_artifact(user_id, created.artifact.id)
    still_there = await service.get_code_artifact(user_id, created.artifact.id)
    assert still_there.id == created.artifact.id


async def test_delete_missing_artifact_skips_the_plugin(code_artifact_store):
    """A delete of an artifact that does not exist never reaches a handler."""
    repo, user_id, bus = code_artifact_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(counting))
    result = await service.delete_code_artifact(user_id, 4242)

    assert result.deleted is False
    assert result.plugin_warnings == []
    assert calls == []


async def test_before_handler_mutation_does_not_reach_the_stored_artifact(
    code_artifact_store,
):
    async def tamper(request):
        request.proposed.tags.append("injected")
        return WriteDecision(outcome="allow")

    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(tamper))
    result = await service.create_code_artifact(user_id, candidate())
    assert result.artifact.tags == []


async def test_after_handler_mutation_does_not_reach_the_stored_artifact(
    code_artifact_store,
):
    async def tamper(request):
        request.saved.tags.append("injected")
        return None

    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(
        repo, event_bus=bus,
        write_plugin=CodeArtifactWritePluginService(
            CodeArtifactPlugin(after_save={"create": tamper}),
        ),
    )
    result = await service.create_code_artifact(user_id, candidate())
    assert result.artifact.tags == []
    stored = await service.get_code_artifact(user_id, result.artifact.id)
    assert stored.tags == []


async def test_update_missing_artifact_raises_not_found(code_artifact_store):
    from app.exceptions import NotFoundError

    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="allow")),
    ))
    with pytest.raises(NotFoundError):
        await service.update_code_artifact(
            user_id, 4242, CodeArtifactUpdate(description="x"),
        )


async def test_unavailable_before_save_persists_nothing_in_enforce_mode(code_artifact_store):
    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(_raiser()))
    with pytest.raises(WritePluginUnavailableError):
        await service.create_code_artifact(user_id, candidate())
    assert await service.list_code_artifacts(user_id=user_id) == []


async def test_after_save_warning_survives_create(code_artifact_store):
    repo, user_id, bus = code_artifact_store

    async def after(request):
        return PluginWarning(message="Indexer notified.", code="indexer")

    service = CodeArtifactService(
        repo, event_bus=bus,
        write_plugin=CodeArtifactWritePluginService(
            CodeArtifactPlugin(after_save={"create": after}),
        ),
    )
    result = await service.create_code_artifact(user_id, candidate())
    assert result.plugin_warnings[0].code == "indexer"


# --- cascade and indirect mutation -----------------------------------------


async def test_project_delete_nulls_project_id_without_running_the_plugin(
    code_artifact_store,
):
    """Deleting a project nulls code_artifacts.project_id; no phase runs for it."""
    from app.models.project_models import ProjectCreate
    from app.repositories.sqlite.project_repository import SqliteProjectRepository
    from app.services.project_service import ProjectService

    repo, user_id, bus = code_artifact_store
    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(record))
    project_service = ProjectService(SqliteProjectRepository(repo.db_adapter))
    project = await project_service.create_project(user_id, ProjectCreate(
        name="Artifact Cascade Project",
        description="Scoped to the cascade test",
        project_type="development",
    ))
    created = await service.create_code_artifact(
        user_id, candidate(project_id=project.id),
    )
    assert created.artifact.project_id == project.id
    calls.clear()

    await project_service.delete_project(user_id, project.id)

    refreshed = await service.get_code_artifact(user_id, created.artifact.id)
    assert refreshed.project_id is None
    assert calls == [], "an indirect mutation must not run the code artifact plugin"


async def test_delete_submission_carries_the_artifact_id(code_artifact_store):
    """The delete context names the artifact, so a rule does not have to infer it."""
    seen = {}

    async def capture(request):
        seen["submitted"] = request.submitted
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    repo, user_id, bus = code_artifact_store
    created = await CodeArtifactService(repo, event_bus=bus).create_code_artifact(
        user_id, candidate(),
    )
    service = CodeArtifactService(repo, event_bus=bus, write_plugin=_service(capture))
    await service.delete_code_artifact(user_id, created.artifact.id)

    assert isinstance(seen["submitted"], CodeArtifactDeleteSubmission)
    assert seen["submitted"].artifact_id == created.artifact.id
    assert seen["proposed"] is None


# --- null policy (must match the behaviour before this feature) -------------


async def test_explicit_null_still_clears_a_nullable_field(code_artifact_store):
    """source_repo is nullable: an explicit null clears it, as it did before.

    Dropping nulls before change detection would silently ignore this request.
    """
    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus)
    created = await service.create_code_artifact(
        user_id, candidate(source_repo="clear me"),
    )

    result = await service.update_code_artifact(
        user_id, created.artifact.id, CodeArtifactUpdate(source_repo=None),
    )

    assert result.artifact.source_repo is None
    refreshed = await service.get_code_artifact(user_id, created.artifact.id)
    assert refreshed.source_repo is None


async def test_explicit_null_on_a_required_field_still_fails(code_artifact_store):
    """language is NOT NULL: an explicit null must reach the repository and fail.

    Silently treating it as "unchanged" would accept a write the database rejects.
    """
    from sqlalchemy.exc import SQLAlchemyError

    repo, user_id, bus = code_artifact_store
    service = CodeArtifactService(repo, event_bus=bus)
    created = await service.create_code_artifact(user_id, candidate())

    with pytest.raises(SQLAlchemyError):
        await service.update_code_artifact(
            user_id, created.artifact.id, CodeArtifactUpdate(language=None),
        )

    refreshed = await service.get_code_artifact(user_id, created.artifact.id)
    assert refreshed.language == "python"
