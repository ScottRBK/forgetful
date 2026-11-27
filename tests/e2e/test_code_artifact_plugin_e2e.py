"""Code Artifact Plugin behaviour against the real PostgreSQL backend.

The SQLite integration tier proves the plugin contract. This tier proves the same
behaviour on the Postgres repository, where column types and array handling differ
from SQLite, so no-op detection and rejection round-trip through different code.

The e2e HTTP app builds services without write plugins, so these tests wire the
plugin onto the Postgres repository directly rather than assuming transport
coverage implies backend coverage.
"""

import uuid

import pytest

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.code_artifact_models import CodeArtifactCreate, CodeArtifactUpdate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import CodeArtifactPlugin
from app.repositories.postgres.code_artifact_repository import (
    PostgresCodeArtifactRepository,
)
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.services.code_artifact_service import CodeArtifactService
from app.services.code_artifact_write_plugin_service import (
    CodeArtifactWritePluginService,
)
from app.services.user_service import UserService

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}


def candidate(**changes) -> CodeArtifactCreate:
    base = {
        "title": "Postgres plugin artifact",
        "description": "Artifact under a plugin",
        "code": "def pg_helper():\n    return 1\n",
        "language": "python",
        "tags": [],
    }
    base.update(changes)
    return CodeArtifactCreate(**base)


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
        return PluginWarning(message="Indexer notified.", code="indexer") if (
            "after_warn" in getattr(request.saved, "tags", [])
        ) else None


async def _service(db_adapter, recorder: Recorder | None, mode: str = "enforce"):
    """Postgres CodeArtifactService with an optional plugin, plus its owning user."""
    user = await UserService(PostgresUserRepository(db_adapter)).get_or_create_user(
        UserCreate(
            external_id=f"artifact-plugin-{uuid.uuid4()}",
            name="Artifact plugin",
            email=f"ap-{uuid.uuid4()}@example.com",
        ),
    )
    plugin = None
    if recorder is not None:
        plugin = CodeArtifactWritePluginService(
            CodeArtifactPlugin(
                before_save={
                    "create": recorder.before, "update": recorder.before,
                    "delete": recorder.before,
                },
                after_save={"create": recorder.after, "update": recorder.after},
            ),
            mode=mode,
        )
    service = CodeArtifactService(
        PostgresCodeArtifactRepository(db_adapter), write_plugin=plugin,
    )
    return service, user.id


async def test_postgres_allow_creates_without_warnings(db_adapter, clean_database, app_settings):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)

    result = await service.create_code_artifact(user_id, candidate())

    assert result.plugin_warnings == []
    assert result.artifact.id is not None
    assert recorder.calls == ["create", "after:create"]


async def test_postgres_reject_blocks_the_write(db_adapter, clean_database, app_settings):
    recorder = Recorder(WriteDecision(outcome="reject", message="Remove the blocked tag."))
    service, user_id = await _service(db_adapter, recorder)

    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_code_artifact(user_id, candidate(tags=["blocked"]))

    assert await service.list_code_artifacts(user_id=user_id) == []


async def test_postgres_noop_update_skips_the_plugin(db_adapter, clean_database, app_settings):
    """Array tags round-trip on Postgres; resending them must read as unchanged."""
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)
    created = await service.create_code_artifact(user_id, candidate(tags=["keep"]))

    recorder.calls.clear()
    result = await service.update_code_artifact(
        user_id, created.artifact.id,
        CodeArtifactUpdate(description="Artifact under a plugin", tags=["keep"]),
    )

    assert recorder.calls == []
    assert result.plugin_warnings == []
    assert result.artifact.description == "Artifact under a plugin"


async def test_postgres_warn_mode_downgrades_rejection(db_adapter, clean_database, app_settings):
    recorder = Recorder(WriteDecision(outcome="reject", message="Blocked, but warned."))
    service, user_id = await _service(db_adapter, recorder, mode="warn")

    result = await service.create_code_artifact(user_id, candidate(tags=["blocked"]))

    assert result.plugin_warnings[0].outcome == "warn"
    assert result.artifact.id is not None


async def test_postgres_unavailable_before_save_blocks_in_enforce_mode(
    db_adapter, clean_database, app_settings,
):
    recorder = Recorder(raises=True)
    service, user_id = await _service(db_adapter, recorder)

    with pytest.raises(WritePluginUnavailableError):
        await service.create_code_artifact(user_id, candidate())

    assert await service.list_code_artifacts(user_id=user_id) == []


async def test_postgres_delete_reject_leaves_the_artifact(
    db_adapter, clean_database, app_settings,
):
    created_service, user_id = await _service(db_adapter, None)
    created = await created_service.create_code_artifact(user_id, candidate())

    recorder = Recorder(WriteDecision(outcome="reject", message="Keep it"))
    service, _ = await _service(db_adapter, recorder)
    with pytest.raises(WritePluginRejectedError):
        await service.delete_code_artifact(user_id, created.artifact.id)

    still_there = await created_service.get_code_artifact(user_id, created.artifact.id)
    assert still_there.id == created.artifact.id


async def test_postgres_after_save_warning_survives(db_adapter, clean_database, app_settings):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)

    result = await service.create_code_artifact(user_id, candidate(tags=["after_warn"]))

    assert result.plugin_warnings[0].code == "indexer"
    assert result.artifact.id is not None
