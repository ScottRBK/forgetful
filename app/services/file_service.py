"""File Service - Business logic for file operations

This service implements functionality for managing binary files:
    - CRUD operations (create, read, update, delete)
    - Filtering and search
    - Project association
    - Memory/entity linking (via association tables)
"""
from typing import TYPE_CHECKING
from uuid import UUID

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.activity_models import ActionType, ActivityEvent, ActorType, EntityType
from app.models.file_models import File, FileCreate, FileSummary, FileUpdate
from app.models.write_plugin_models import (
    FileDeletedRequest,
    FileDeleteResult,
    FileDeleteSubmission,
    FileSavedRequest,
    FileWriteRequest,
    FileWriteResult,
)
from app.protocols.file_protocol import FileRepository
from app.utils.file_snapshot import file_snapshot
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)
from app.utils.pydantic_helper import get_changed_fields

if TYPE_CHECKING:
    from app.events import EventBus
    from app.services.file_write_plugin_service import FileWritePluginService

logger = logging.getLogger(__name__)


class FileService:
    """Service layer for file operations

    Handles business logic for creating, updating, querying, and deleting files.
    Uses repository protocol for data access.
    """

    def __init__(
        self,
        file_repo: FileRepository,
        event_bus: "EventBus | None" = None,
        write_plugin: "FileWritePluginService | None" = None,
    ):
        """Initialize with repository protocol (not concrete implementation)

        Args:
            file_repo: File repository implementing the protocol
            event_bus: Optional event bus for activity tracking
            write_plugin: Optional File Plugin runner
        """
        self.file_repo = file_repo
        self._event_bus = event_bus
        self._write_plugin = write_plugin
        logger.info("File service initialized")

    async def _emit_event(
        self,
        user_id: UUID,
        entity_type: EntityType,
        entity_id: int,
        action: ActionType,
        snapshot: dict,
        changes: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Emit an activity event to the event bus.

        This is a no-op if no event bus is configured.
        """
        if self._event_bus is None:
            return

        event = ActivityEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            snapshot=snapshot,
            actor=ActorType.USER,
            metadata=metadata,
            user_id=str(user_id),
        )

        await self._event_bus.emit(event)

    def _snapshot_without_data(self, file: File) -> dict:
        """Create a snapshot dict excluding the base64 data field to avoid bloating events."""
        return file_snapshot(file)

    async def create_file(
        self,
        user_id: UUID,
        file_data: FileCreate,
    ) -> FileWriteResult:
        """Create new file

        Args:
            user_id: User ID for ownership
            file_data: FileCreate with filename, description, data (base64), mime_type, tags

        Returns:
            Created File with generated ID, size_bytes, and timestamps, plus plugin warnings
        """
        logger.info(
            "creating file",
            extra={
                "filename": file_data.filename[:50],
                "mime_type": file_data.mime_type,
                "user_id": str(user_id),
            },
        )

        submitted = file_data.model_copy(deep=True)
        file_data = apply_provenance_defaults(file_data)
        plugin_warnings = []
        if self._write_plugin and self._write_plugin.has_before("create"):
            plugin_warnings = await self._write_plugin.before_save(FileWriteRequest(
                operation="create", user_id=user_id, submitted=submitted, previous=None,
                # model_construct: the caller already validated, and re-validating
                # would decode the whole base64 payload a second time.
                proposed=FileCreate.model_construct(
                    **file_data.model_dump(include=set(FileCreate.model_fields)),
                ),
            ))
        file = await self.file_repo.create_file(
            user_id=user_id,
            file_data=file_data,
        )

        logger.info(
            "file created",
            extra={
                "file_id": file.id,
                "user_id": str(user_id),
            },
        )

        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.FILE,
            entity_id=file.id,
            action=ActionType.CREATED,
            snapshot=self._snapshot_without_data(file),
        )

        if self._write_plugin:
            plugin_warnings += await self._write_plugin.after_save(FileSavedRequest(
                operation="create", user_id=user_id, previous=None, saved=file,
            ))

        return FileWriteResult(file=file, plugin_warnings=plugin_warnings)

    async def get_file(
        self,
        user_id: UUID,
        file_id: int,
    ) -> File:
        """Get file by ID with ownership verification

        Args:
            user_id: User ID for ownership verification
            file_id: File ID to retrieve

        Returns:
            File with full details including base64 data

        Raises:
            NotFoundError: If file not found or not owned by user
        """
        logger.info(
            "getting file",
            extra={
                "file_id": file_id,
                "user_id": str(user_id),
            },
        )

        file = await self.file_repo.get_file_by_id(
            user_id=user_id,
            file_id=file_id,
        )

        if not file:
            raise NotFoundError(f"File {file_id} not found")

        logger.info(
            "file retrieved",
            extra={
                "file_id": file_id,
                "user_id": str(user_id),
            },
        )

        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.FILE,
                entity_id=file_id,
                action=ActionType.READ,
                snapshot=self._snapshot_without_data(file),
            )

        return file

    async def list_files(
        self,
        user_id: UUID,
        project_id: int | None = None,
        mime_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[FileSummary]:
        """List files with optional filtering

        Args:
            user_id: User ID for ownership filtering
            project_id: Optional filter by project
            mime_type: Optional filter by MIME type
            tags: Optional filter by tags (returns files with ANY of these tags)

        Returns:
            List of FileSummary (lightweight, excludes base64 data)
        """
        logger.info(
            "listing files",
            extra={
                "user_id": str(user_id),
                "project_id": project_id,
                "mime_type": mime_type,
                "tags": tags,
            },
        )

        files = await self.file_repo.list_files(
            user_id=user_id,
            project_id=project_id,
            mime_type=mime_type,
            tags=tags,
        )

        logger.info(
            "files retrieved",
            extra={
                "count": len(files),
                "user_id": str(user_id),
            },
        )

        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.FILE,
                entity_id=0,
                action=ActionType.QUERIED,
                snapshot={
                    "result_ids": [f.id for f in files],
                    "total_count": len(files),
                },
                metadata={
                    "project_id": project_id,
                    "mime_type": mime_type,
                    "tags": tags,
                },
            )

        return files

    async def list_files_page(
        self,
        user_id: UUID,
        project_id: int | None = None,
        mime_type: str | None = None,
        tags: list[str] | None = None,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[FileSummary], int]:
        """Return one bounded page and its full filtered total for REST callers."""
        items, total = await self.file_repo.list_files_page(
            user_id=user_id,
            project_id=project_id,
            mime_type=mime_type,
            tags=tags,
            limit=limit,
            offset=offset,
        )
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.FILE,
                entity_id=0,
                action=ActionType.QUERIED,
                snapshot={
                    "result_ids": [item.id for item in items],
                    "total_count": total,
                },
                metadata={
                    "project_id": project_id,
                    "mime_type": mime_type,
                    "tags": tags,
                    "limit": limit,
                    "offset": offset,
                },
            )
        return items, total

    async def update_file(
        self,
        user_id: UUID,
        file_id: int,
        file_data: FileUpdate,
    ) -> FileWriteResult:
        """Update existing file (PATCH semantics)

        Only provided fields are updated. None/omitted fields remain unchanged.

        Args:
            user_id: User ID for ownership verification
            file_id: File ID to update
            file_data: FileUpdate with fields to change

        Returns:
            Updated File plus plugin warnings

        Raises:
            NotFoundError: If file not found or not owned by user
        """
        logger.info(
            "updating file",
            extra={
                "file_id": file_id,
                "user_id": str(user_id),
            },
        )

        submitted = file_data.model_copy(deep=True)
        # Null policy is unchanged by this feature. An explicit null is a submitted
        # value and reaches the repository as it does without a plugin, so a
        # nullable column is cleared by one and a required column still fails.
        file_data = apply_provenance_defaults_for_update(file_data)

        existing_file = await self.file_repo.get_file_by_id(
            user_id=user_id,
            file_id=file_id,
        )

        if not existing_file:
            raise NotFoundError(f"File {file_id} not found")

        changed_fields = get_changed_fields(
            input_model=file_data, existing_model=existing_file,
        )

        plugin_warnings = []
        if changed_fields and self._write_plugin and self._write_plugin.has_before("update"):
            # Merged view of the file as it will be after the update, matching the
            # snapshot rule set by the Memory Plugin contract (PR #164) and implemented
            # for entity writes in PR #184: a full snapshot, not just changed fields.
            # model_construct avoids re-decoding ``data``; both inputs are validated.
            proposed_data = existing_file.model_dump(include=set(FileCreate.model_fields))
            proposed_data.update(file_data.model_dump(exclude_unset=True))
            proposed = FileCreate.model_construct(**proposed_data)
            plugin_warnings = await self._write_plugin.before_save(FileWriteRequest(
                operation="update", user_id=user_id, submitted=submitted,
                previous=existing_file.model_copy(deep=True), proposed=proposed,
            ))
            existing_file = await self.file_repo.get_file_by_id(
                user_id=user_id,
                file_id=file_id,
            )
            if not existing_file:
                raise NotFoundError(f"File {file_id} not found")
            changed_fields = get_changed_fields(
                input_model=file_data, existing_model=existing_file,
            )
            if not changed_fields:
                return FileWriteResult(
                    file=existing_file, plugin_warnings=plugin_warnings,
                )

        file = await self.file_repo.update_file(
            user_id=user_id,
            file_id=file_id,
            file_data=file_data,
        )

        logger.info(
            "file updated",
            extra={
                "file_id": file_id,
                "user_id": str(user_id),
            },
        )

        if changed_fields:
            # Exclude 'data' from changes to avoid bloating events
            changes_dict = {
                field: {"old": old, "new": new}
                for field, (old, new) in changed_fields.items()
                if field != "data"
            }
            if changes_dict:
                await self._emit_event(
                    user_id=user_id,
                    entity_type=EntityType.FILE,
                    entity_id=file_id,
                    action=ActionType.UPDATED,
                    snapshot=self._snapshot_without_data(file),
                    changes=changes_dict,
                )
            if self._write_plugin:
                previous = existing_file.model_copy(deep=True)
                plugin_warnings += await self._write_plugin.after_save(FileSavedRequest(
                    operation="update", user_id=user_id, saved=file, previous=previous,
                ))

        return FileWriteResult(file=file, plugin_warnings=plugin_warnings)

    async def delete_file(
        self,
        user_id: UUID,
        file_id: int,
    ) -> FileDeleteResult:
        """Delete file (cascade removes memory/entity associations)

        Args:
            user_id: User ID for ownership verification
            file_id: File ID to delete

        Returns:
            Whether the file was deleted, plus any plugin warnings
        """
        logger.info(
            "deleting file",
            extra={
                "file_id": file_id,
                "user_id": str(user_id),
            },
        )

        existing_file = await self.file_repo.get_file_by_id(
            user_id=user_id,
            file_id=file_id,
        )

        plugin_warnings = []
        if existing_file and self._write_plugin and self._write_plugin.has_before("delete"):
            plugin_warnings = await self._write_plugin.before_save(FileWriteRequest(
                operation="delete", user_id=user_id,
                submitted=FileDeleteSubmission(file_id=file_id),
                previous=existing_file.model_copy(deep=True), proposed=None,
            ))
            existing_file = await self.file_repo.get_file_by_id(
                user_id=user_id,
                file_id=file_id,
            )
            if not existing_file:
                return FileDeleteResult(deleted=False, plugin_warnings=plugin_warnings)

        success = await self.file_repo.delete_file(
            user_id=user_id,
            file_id=file_id,
        )

        if success:
            logger.info(
                "file deleted",
                extra={
                    "file_id": file_id,
                    "user_id": str(user_id),
                },
            )

            if existing_file:
                await self._emit_event(
                    user_id=user_id,
                    entity_type=EntityType.FILE,
                    entity_id=file_id,
                    action=ActionType.DELETED,
                    snapshot=self._snapshot_without_data(existing_file),
                )
        else:
            logger.warning(
                "file not found for deletion",
                extra={
                    "file_id": file_id,
                    "user_id": str(user_id),
                },
            )

        if success and existing_file and self._write_plugin:
            plugin_warnings += await self._write_plugin.after_save(FileDeletedRequest(
                operation="delete", user_id=user_id,
                deleted_file_id=file_id, previous=existing_file,
            ))

        return FileDeleteResult(deleted=success, plugin_warnings=plugin_warnings)
