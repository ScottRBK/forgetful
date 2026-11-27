"""Skill Plugin: registration, reject/warn, modes, no-op skip, bundle cascade."""

import asyncio
import uuid

import pytest
from pydantic import ValidationError

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.skill_models import Skill, SkillCreate, SkillUpdate
from app.models.write_plugin_models import (
    PluginWarning,
    SkillDeletedRequest,
    SkillDeleteSubmission,
    SkillSavedRequest,
    SkillWriteRequest,
    WriteDecision,
)
from app.protocols.write_plugin_protocol import SkillPlugin
from app.services.skill_service import SkillService
from app.services.skill_write_plugin_service import SkillWritePluginService

_USER = uuid.uuid4()


def candidate(**changes) -> SkillCreate:
    base = {
        "name": "code-review",
        "description": "Systematic code review process",
        "content": "# Code review\n\n1. Read the diff.\n",
        "tags": [],
        "importance": 7,
    }
    base.update(changes)
    return SkillCreate(**base)


def _decider(decision):
    async def handler(request):
        return decision

    return handler


def _raiser():
    async def handler(request):
        raise RuntimeError("SECRET")

    return handler


def _service(handler, mode="enforce", timeout_seconds=5.0, phase="before_save"):
    return SkillWritePluginService(
        SkillPlugin(**{phase: {"create": handler, "update": handler, "delete": handler}}),
        mode=mode, timeout_seconds=timeout_seconds,
    )


def _write_request(operation="create", tags=()):
    return SkillWriteRequest(
        operation=operation, user_id=_USER, submitted=candidate(),
        previous=None, proposed=candidate(tags=list(tags)),
    )


def _skill(tags=()) -> Skill:
    return Skill(**candidate(tags=list(tags)).model_dump(), id=1)


def _saved_request(tags=()):
    return SkillSavedRequest(
        operation="create", user_id=_USER, saved=_skill(tags), previous=None,
    )


def _deleted_request(tags=()):
    return SkillDeletedRequest(
        user_id=_USER, deleted_skill_id=1, previous=_skill(tags),
    )


# --- registration -----------------------------------------------------------


def test_registration_freezes_the_mapping_and_rejects_bad_operations():
    handlers = {"create": _decider(WriteDecision(outcome="allow"))}
    plugin = SkillPlugin(before_save=handlers)
    handlers["bogus"] = handlers["create"]
    assert "bogus" not in plugin.before_save
    with pytest.raises(ValueError, match="unsupported skill operation"):
        SkillPlugin(before_save={"bogus": handlers["create"]})


def test_registration_requires_async_handlers():
    def sync_handler(request):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="must be async"):
        SkillPlugin(before_save={"create": sync_handler})


def test_registration_rejects_wrong_arity():
    async def two_args(request, extra):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="one context argument"):
        SkillPlugin(before_save={"create": two_args})


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
    with pytest.raises(WritePluginUnavailableError, match="Skill Write Plugin unavailable"):
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
    assert warnings[0].code == "SKILL_PLUGIN_AFTER_SAVE_UNAVAILABLE"


async def test_after_save_delete_message_differs():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_deleted_request())
    assert "deleted" in warnings[0].message


# --- settings trio ----------------------------------------------------------


def test_settings_trio_defaults():
    from app.config.settings import Settings

    fresh = Settings()
    assert fresh.SKILL_WRITE_PLUGIN == ""
    assert fresh.SKILL_WRITE_PLUGIN_MODE == "enforce"
    assert fresh.SKILL_WRITE_PLUGIN_TIMEOUT_SECONDS == 5.0


def test_settings_mode_is_constrained():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(SKILL_WRITE_PLUGIN_MODE="ignore")


def test_settings_timeout_must_be_positive():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(SKILL_WRITE_PLUGIN_TIMEOUT_SECONDS=0)


# --- service integration ----------------------------------------------------


async def test_create_rejects_through_service(skill_store):
    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Remove the blocked tag.")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.create_skill(user_id, candidate(tags=["blocked"]))
    assert await service.list_skills(user_id=user_id) == []


async def test_create_warns_through_service(skill_store):
    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="warn", message="Check the source.", code="source")),
    ))
    result = await service.create_skill(user_id, candidate())
    assert result.plugin_warnings[0].code == "source"
    assert result.skill.id is not None


async def test_import_skill_markdown_runs_the_plugin(skill_store):
    """import_skill delegates to create_skill, so it is covered by the same hooks."""
    repo, user_id, bus = skill_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    service = SkillService(repo, event_bus=bus, write_plugin=_service(counting))
    markdown = "---\nname: imported-skill\ndescription: Imported from markdown\n---\n\nBody\n"
    result = await service.import_skill(user_id, markdown)

    assert calls == ["create"]
    assert result.skill.name == "imported-skill"


async def test_update_proposed_is_the_full_merged_record(skill_store):
    """`proposed` is the whole skill after the write, not just changed fields."""
    seen = {}

    async def capture(request):
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    repo, user_id, bus = skill_store
    created = await SkillService(repo, event_bus=bus).create_skill(
        user_id, candidate(tags=["keep", "drop"]),
    )
    service = SkillService(repo, event_bus=bus, write_plugin=_service(capture))
    await service.update_skill(
        user_id, created.skill.id, SkillUpdate(description="New description"),
    )

    proposed = seen["proposed"]
    assert isinstance(proposed, SkillCreate)
    assert proposed.description == "New description"
    assert proposed.name == "code-review"
    assert proposed.content == created.skill.content
    assert proposed.tags == ["keep", "drop"]
    assert proposed.importance == 7


async def test_update_noop_skips_plugin(skill_store):
    repo, user_id, bus = skill_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    service = SkillService(repo, event_bus=bus, write_plugin=_service(counting))
    result = await service.update_skill(
        user_id, created.skill.id,
        SkillUpdate(description="Systematic code review process"),
    )

    assert calls == []
    assert result.plugin_warnings == []


async def test_update_with_change_runs_plugin(skill_store):
    repo, user_id, bus = skill_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    service = SkillService(repo, event_bus=bus, write_plugin=_service(counting))
    await service.update_skill(
        user_id, created.skill.id, SkillUpdate(description="Changed"),
    )

    assert calls == ["update"]


async def test_delete_runs_before_and_after(skill_store):
    repo, user_id, bus = skill_store
    calls = []

    async def before(request):
        calls.append(("before", request.operation))
        return WriteDecision(outcome="allow")

    async def after(request):
        calls.append(("after", request.operation))
        return None

    plugin = SkillPlugin(before_save={"delete": before}, after_save={"delete": after})
    service = SkillService(
        repo, event_bus=bus, write_plugin=SkillWritePluginService(plugin),
    )
    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    result = await service.delete_skill(user_id, created.skill.id)

    assert result.deleted is True
    assert calls == [("before", "delete"), ("after", "delete")]


async def test_delete_rejected_leaves_skill(skill_store):
    repo, user_id, bus = skill_store
    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    service = SkillService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="reject", message="Keep it")),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.delete_skill(user_id, created.skill.id)
    still_there = await service.get_skill(user_id, created.skill.id)
    assert still_there.id == created.skill.id


async def test_delete_missing_skill_skips_the_plugin(skill_store):
    """A delete of a skill that does not exist never reaches a handler."""
    repo, user_id, bus = skill_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    service = SkillService(repo, event_bus=bus, write_plugin=_service(counting))
    result = await service.delete_skill(user_id, 4242)

    assert result.deleted is False
    assert result.plugin_warnings == []
    assert calls == []


async def test_before_handler_mutation_does_not_reach_the_stored_skill(skill_store):
    async def tamper(request):
        request.proposed.tags.append("injected")
        return WriteDecision(outcome="allow")

    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus, write_plugin=_service(tamper))
    result = await service.create_skill(user_id, candidate())
    assert result.skill.tags == []


async def test_update_missing_skill_raises_not_found(skill_store):
    from app.exceptions import NotFoundError

    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus, write_plugin=_service(
        _decider(WriteDecision(outcome="allow")),
    ))
    with pytest.raises(NotFoundError):
        await service.update_skill(user_id, 4242, SkillUpdate(description="x"))


async def test_unavailable_before_save_persists_nothing_in_enforce_mode(skill_store):
    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus, write_plugin=_service(_raiser()))
    with pytest.raises(WritePluginUnavailableError):
        await service.create_skill(user_id, candidate())
    assert await service.list_skills(user_id=user_id) == []


async def test_after_save_warning_survives_create(skill_store):
    repo, user_id, bus = skill_store

    async def after(request):
        return PluginWarning(message="Catalogue notified.", code="catalogue")

    service = SkillService(
        repo, event_bus=bus,
        write_plugin=SkillWritePluginService(SkillPlugin(after_save={"create": after})),
    )
    result = await service.create_skill(user_id, candidate())
    assert result.plugin_warnings[0].code == "catalogue"


async def test_delete_submission_carries_the_skill_id(skill_store):
    """The delete context names the skill, so a rule does not have to infer it."""
    seen = {}

    async def capture(request):
        seen["submitted"] = request.submitted
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    repo, user_id, bus = skill_store
    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    service = SkillService(repo, event_bus=bus, write_plugin=_service(capture))
    await service.delete_skill(user_id, created.skill.id)

    assert isinstance(seen["submitted"], SkillDeleteSubmission)
    assert seen["submitted"].skill_id == created.skill.id
    assert seen["proposed"] is None


# --- cascade and indirect mutation -----------------------------------------


async def test_project_delete_nulls_project_id_without_running_the_plugin(skill_store):
    """Deleting a project nulls skills.project_id; no phase runs for it."""
    from app.models.project_models import ProjectCreate
    from app.repositories.sqlite.project_repository import SqliteProjectRepository
    from app.services.project_service import ProjectService

    repo, user_id, bus = skill_store
    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    service = SkillService(repo, event_bus=bus, write_plugin=_service(record))
    project_service = ProjectService(SqliteProjectRepository(repo.db_adapter))
    project = await project_service.create_project(user_id, ProjectCreate(
        name="Skill Cascade Project",
        description="Scoped to the cascade test",
        project_type="development",
    ))
    created = await service.create_skill(
        user_id, candidate(project_id=project.id),
    )
    assert created.skill.project_id == project.id
    calls.clear()

    await project_service.delete_project(user_id, project.id)

    refreshed = await service.get_skill(user_id, created.skill.id)
    assert refreshed.project_id is None
    assert calls == [], "an indirect mutation must not run the skill plugin"


async def test_deleting_a_skill_removes_its_links(skill_store):
    """Association rows cascade; the plugin still sees only the delete phases."""
    from app.models.memory_models import MemoryCreate
    from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
    from app.services.memory_service import MemoryService

    repo, user_id, bus = skill_store
    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    memory_service = MemoryService(
        SqliteMemoryRepository(repo.db_adapter, embedding_adapter=repo.embedding_adapter),
    )
    created = await SkillService(repo, event_bus=bus).create_skill(user_id, candidate())
    await memory_service.create_memory(user_id, MemoryCreate(
        title="Memory linked to a skill", content="Content",
        context="skill cascade test", keywords=["cascade"], tags=[], importance=5,
        skill_ids=[created.skill.id],
    ))
    before = (await memory_service.list_memories(user_id=user_id))[0][0]
    assert created.skill.id in before.skill_ids

    service = SkillService(repo, event_bus=bus, write_plugin=_service(record))
    calls.clear()
    result = await service.delete_skill(user_id, created.skill.id)

    assert result.deleted is True
    assert calls == ["delete"]
    after = (await memory_service.list_memories(user_id=user_id))[0][0]
    assert after.skill_ids == []


# --- null policy (must match the behaviour before this feature) -------------


async def test_explicit_null_still_clears_a_nullable_field(skill_store):
    """license is nullable: an explicit null clears it, as it did before.

    Dropping nulls before change detection would silently ignore this request.
    """
    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus)
    created = await service.create_skill(user_id, candidate(license="clear me"))

    result = await service.update_skill(
        user_id, created.skill.id, SkillUpdate(license=None),
    )

    assert result.skill.license is None
    refreshed = await service.get_skill(user_id, created.skill.id)
    assert refreshed.license is None


async def test_explicit_null_on_a_required_field_still_fails(skill_store):
    """content is NOT NULL: an explicit null must reach the repository and fail.

    Silently treating it as "unchanged" would accept a write the database rejects.
    """
    from sqlalchemy.exc import SQLAlchemyError

    repo, user_id, bus = skill_store
    service = SkillService(repo, event_bus=bus)
    created = await service.create_skill(user_id, candidate())

    with pytest.raises(SQLAlchemyError):
        await service.update_skill(
            user_id, created.skill.id, SkillUpdate(content=None),
        )

    refreshed = await service.get_skill(user_id, created.skill.id)
    assert refreshed.content
