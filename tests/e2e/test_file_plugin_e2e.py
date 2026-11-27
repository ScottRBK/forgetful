"""File Plugin behaviour against the real PostgreSQL backend.

The SQLite integration tier already proves the plugin contract. This tier proves
the same behaviour holds on the Postgres repository, where ``tags`` is an ARRAY
column rather than JSON, so no-op detection and rejection round-trip differently.

The e2e HTTP app builds FileService without a write plugin, so these tests wire
the plugin onto the Postgres repository directly instead of pretending the
transport tier covers it.
"""

import base64
import uuid

import pytest

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.file_models import FileCreate, FileUpdate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import FilePlugin
from app.repositories.postgres.file_repository import PostgresFileRepository
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.services.file_service import FileService
from app.services.file_write_plugin_service import FileWritePluginService
from app.services.user_service import UserService

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}

TINY_PNG_B64 = base64.b64encode(
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
).decode()


def candidate(**changes) -> FileCreate:
    base = {
        "filename": "pg-plugin.png",
        "description": "Postgres plugin file",
        "data": TINY_PNG_B64,
        "mime_type": "image/png",
        "tags": [],
    }
    base.update(changes)
    return FileCreate(**base)


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
        return PluginWarning(message="Post-save check.", code="post") if (
            "after_warn" in getattr(request.saved, "tags", [])
        ) else None


async def _service(db_adapter, recorder: Recorder | None, mode: str = "enforce"):
    """Postgres FileService with an optional plugin, plus its owning user."""
    user = await UserService(PostgresUserRepository(db_adapter)).get_or_create_user(
        UserCreate(
            external_id=f"file-plugin-{uuid.uuid4()}",
            name="File plugin",
            email=f"fp-{uuid.uuid4()}@example.com",
        ),
    )
    plugin = None
    if recorder is not None:
        plugin = FileWritePluginService(
            FilePlugin(
                before_save={"create": recorder.before, "update": recorder.before,
                             "delete": recorder.before},
                after_save={"create": recorder.after, "update": recorder.after},
            ),
            mode=mode,
        )
    service = FileService(PostgresFileRepository(db_adapter), write_plugin=plugin)
    return service, user.id


async def test_postgres_allow_creates_without_warnings(db_adapter, clean_database, app_settings):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)

    result = await service.create_file(user_id, candidate())

    assert result.plugin_warnings == []
    assert result.file.id is not None
    assert recorder.calls == ["create", "after:create"]


async def test_postgres_reject_blocks_the_write(db_adapter, clean_database, app_settings):
    recorder = Recorder(WriteDecision(outcome="reject", message="Remove the blocked tag."))
    service, user_id = await _service(db_adapter, recorder)

    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_file(user_id, candidate(tags=["blocked"]))

    assert await service.list_files(user_id=user_id) == []


async def test_postgres_noop_update_skips_the_plugin(db_adapter, clean_database, app_settings):
    """ARRAY tags round-trip on Postgres; resending them must read as unchanged."""
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)
    created = await service.create_file(user_id, candidate(tags=["keep"]))

    recorder.calls.clear()
    result = await service.update_file(
        user_id, created.file.id,
        FileUpdate(description="Postgres plugin file", tags=["keep"]),
    )

    assert recorder.calls == []
    assert result.plugin_warnings == []
    assert result.file.description == "Postgres plugin file"


async def test_postgres_warn_mode_downgrades_rejection(db_adapter, clean_database, app_settings):
    recorder = Recorder(WriteDecision(outcome="reject", message="Blocked, but warned."))
    service, user_id = await _service(db_adapter, recorder, mode="warn")

    result = await service.create_file(user_id, candidate(tags=["blocked"]))

    assert result.plugin_warnings[0].outcome == "warn"
    assert result.file.id is not None


async def test_postgres_unavailable_before_save_blocks_in_enforce_mode(db_adapter, clean_database, app_settings):
    recorder = Recorder(raises=True)
    service, user_id = await _service(db_adapter, recorder)

    with pytest.raises(WritePluginUnavailableError):
        await service.create_file(user_id, candidate())

    assert await service.list_files(user_id=user_id) == []


async def test_postgres_delete_reject_leaves_the_file(db_adapter, clean_database, app_settings):
    created_service, user_id = await _service(db_adapter, None)
    created = await created_service.create_file(user_id, candidate())

    recorder = Recorder(WriteDecision(outcome="reject", message="Keep it"))
    service, _ = await _service(db_adapter, recorder)
    with pytest.raises(WritePluginRejectedError):
        await service.delete_file(user_id, created.file.id)

    assert (await created_service.get_file(user_id, created.file.id)).id == created.file.id


async def test_postgres_after_save_warning_survives(db_adapter, clean_database, app_settings):
    recorder = Recorder()
    service, user_id = await _service(db_adapter, recorder)

    result = await service.create_file(user_id, candidate(tags=["after_warn"]))

    assert result.plugin_warnings[0].code == "post"
    assert result.file.id is not None
