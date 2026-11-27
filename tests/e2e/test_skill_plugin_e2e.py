"""Skill Plugin behaviour against the real PostgreSQL backend.

The SQLite integration tier proves the plugin contract. This tier proves the same
behaviour on the Postgres repository, where skills carry an embedding and stored
columns differ, so change detection and rejection round-trip through different
code.

The e2e HTTP app builds services without write plugins, so these tests wire the
plugin onto the Postgres repository directly rather than assuming transport
coverage implies backend coverage.
"""

import uuid

import pytest

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.skill_models import SkillCreate, SkillUpdate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import SkillPlugin
from app.repositories.postgres.skill_repository import PostgresSkillRepository
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.services.skill_service import SkillService
from app.services.skill_write_plugin_service import SkillWritePluginService
from app.services.user_service import UserService

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}


def candidate(**changes) -> SkillCreate:
    base = {
        "name": "postgres-plugin-skill",
        "description": "Skill under a plugin",
        "content": "# Skill\n\n1. Do the thing.\n",
        "tags": [],
        "importance": 7,
    }
    base.update(changes)
    return SkillCreate(**base)


class Recorder:
    """Records operations and returns a scripted decision."""

    def __init__(self, decision: WriteDecision | None = None, *, raises: bool = False):
        self.decision = decision or WriteDecision(outcome="allow")
        self.raises = raises
        self.calls: list[str] = []

    async def before(self, request):
        self.calls.append(request.operation)
        if self.raises:
            raise RuntimeError("SECRET")
        return self.decision

    async def after(self, request):
        self.calls.append(f"after:{request.operation}")
        return PluginWarning(message="Catalogue notified.", code="catalogue") if (
            "after_warn" in getattr(request.saved, "tags", [])
        ) else None


async def _service(db_adapter, embedding_adapter, recorder: Recorder | None, mode="enforce"):
    """Postgres SkillService with an optional plugin, plus its owning user."""
    user = await UserService(PostgresUserRepository(db_adapter)).get_or_create_user(
        UserCreate(
            external_id=f"skill-plugin-{uuid.uuid4()}",
            name="Skill plugin",
            email=f"sp-{uuid.uuid4()}@example.com",
        ),
    )
    plugin = None
    if recorder is not None:
        plugin = SkillWritePluginService(
            SkillPlugin(
                before_save={
                    "create": recorder.before, "update": recorder.before,
                    "delete": recorder.before,
                },
                after_save={"create": recorder.after, "update": recorder.after},
            ),
            mode=mode,
        )
    service = SkillService(
        PostgresSkillRepository(db_adapter, embedding_adapter=embedding_adapter),
        write_plugin=plugin,
    )
    return service, user.id


async def test_postgres_allow_creates_without_warnings(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, embedding_adapter, recorder)

    result = await service.create_skill(user_id, candidate())

    assert result.plugin_warnings == []
    assert result.skill.id is not None
    assert recorder.calls == ["create", "after:create"]


async def test_postgres_reject_blocks_the_write(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    recorder = Recorder(WriteDecision(outcome="reject", message="Remove the blocked tag."))
    service, user_id = await _service(db_adapter, embedding_adapter, recorder)

    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_skill(user_id, candidate(tags=["blocked"]))

    assert await service.list_skills(user_id=user_id) == []


async def test_postgres_noop_update_skips_the_plugin(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    """Resending the stored values must read as unchanged on Postgres too."""
    recorder = Recorder()
    service, user_id = await _service(db_adapter, embedding_adapter, recorder)
    created = await service.create_skill(user_id, candidate(tags=["keep"]))

    recorder.calls.clear()
    result = await service.update_skill(
        user_id, created.skill.id,
        SkillUpdate(description="Skill under a plugin", tags=["keep"]),
    )

    assert recorder.calls == []
    assert result.plugin_warnings == []
    assert result.skill.description == "Skill under a plugin"


async def test_postgres_warn_mode_downgrades_rejection(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    recorder = Recorder(WriteDecision(outcome="reject", message="Blocked, but warned."))
    service, user_id = await _service(db_adapter, embedding_adapter, recorder, mode="warn")

    result = await service.create_skill(user_id, candidate(tags=["blocked"]))

    assert result.plugin_warnings[0].outcome == "warn"
    assert result.skill.id is not None


async def test_postgres_unavailable_before_save_blocks_in_enforce_mode(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    recorder = Recorder(raises=True)
    service, user_id = await _service(db_adapter, embedding_adapter, recorder)

    with pytest.raises(WritePluginUnavailableError):
        await service.create_skill(user_id, candidate())

    assert await service.list_skills(user_id=user_id) == []


async def test_postgres_delete_reject_leaves_the_skill(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    created_service, user_id = await _service(db_adapter, embedding_adapter, None)
    created = await created_service.create_skill(user_id, candidate())

    recorder = Recorder(WriteDecision(outcome="reject", message="Keep it"))
    service, _ = await _service(db_adapter, embedding_adapter, recorder)
    with pytest.raises(WritePluginRejectedError):
        await service.delete_skill(user_id, created.skill.id)

    still_there = await created_service.get_skill(user_id, created.skill.id)
    assert still_there.id == created.skill.id


async def test_postgres_after_save_warning_survives(
    db_adapter, embedding_adapter, clean_database, app_settings,
):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, embedding_adapter, recorder)

    result = await service.create_skill(user_id, candidate(tags=["after_warn"]))

    assert result.plugin_warnings[0].code == "catalogue"
    assert result.skill.id is not None
