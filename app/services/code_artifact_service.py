"""Code Artifact Service - Business logic for code artifact operations

This service implements functionality for managing code artifacts:
    - CRUD operations (create, read, update, delete)
    - Filtering and search
    - Project association
    - Memory linking (via memory service)
"""
from typing import TYPE_CHECKING
from uuid import UUID

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.activity_models import (
    ActionType,
    ActivityEvent,
    ActorType,
    EntityType,
)
from app.models.code_artifact_models import (
    CodeArtifact,
    CodeArtifactCreate,
    CodeArtifactSummary,
    CodeArtifactUpdate,
)
from app.models.write_plugin_models import (
    CodeArtifactDeletedRequest,
    CodeArtifactDeleteResult,
    CodeArtifactDeleteSubmission,
    CodeArtifactSavedRequest,
    CodeArtifactWriteRequest,
    CodeArtifactWriteResult,
)
from app.protocols.code_artifact_protocol import CodeArtifactRepository
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)
from app.utils.pydantic_helper import get_changed_fields

if TYPE_CHECKING:
    from app.events import EventBus
    from app.services.code_artifact_write_plugin_service import (
        CodeArtifactWritePluginService,
    )

logger = logging.getLogger(__name__)


class CodeArtifactService:
    """Service layer for code artifact operations

    Handles business logic for creating, updating, querying, and deleting code artifacts.
    Uses repository protocol for data access.
    """

    def __init__(
        self,
        artifact_repo: CodeArtifactRepository,
        event_bus: "EventBus | None" = None,
        write_plugin: "CodeArtifactWritePluginService | None" = None,
    ):
        """Initialize with repository protocol (not concrete implementation)

        Args:
            artifact_repo: Code artifact repository implementing the protocol
            event_bus: Optional event bus for activity tracking
            write_plugin: Optional Code Artifact Plugin runner
        """
        self.artifact_repo = artifact_repo
        self._event_bus = event_bus
        self._write_plugin = write_plugin
        logger.info("Code artifact service initialized")

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

        Args:
            user_id: User ID for the event
            entity_type: Type of entity (code_artifact)
            entity_id: ID of the entity
            action: Action that occurred (created, updated, deleted, etc.)
            snapshot: Full entity state at event time
            changes: Field changes for updates
            metadata: Additional context
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

    async def create_code_artifact(
        self,
        user_id: UUID,
        artifact_data: CodeArtifactCreate,
    ) -> CodeArtifactWriteResult:
        """Create new code artifact

        Args:
            user_id: User ID for ownership
            artifact_data: CodeArtifactCreate with title, description, code, language, tags

        Returns:
            Created CodeArtifact with generated ID and timestamps, plus plugin warnings
        """
        logger.info(
            "creating code artifact",
            extra={
                "title": artifact_data.title[:50],
                "language": artifact_data.language,
                "user_id": str(user_id),
            },
        )

        submitted = artifact_data.model_copy(deep=True)
        artifact_data = apply_provenance_defaults(artifact_data)
        plugin_warnings = []
        if self._write_plugin and self._write_plugin.has_before("create"):
            plugin_warnings = await self._write_plugin.before_save(CodeArtifactWriteRequest(
                operation="create", user_id=user_id, submitted=submitted, previous=None,
                proposed=CodeArtifactCreate.model_validate(
                    artifact_data.model_dump(include=set(CodeArtifactCreate.model_fields)),
                ),
            ))
        artifact = await self.artifact_repo.create_code_artifact(
            user_id=user_id,
            artifact_data=artifact_data,
        )

        logger.info(
            "code artifact created",
            extra={
                "artifact_id": artifact.id,
                "user_id": str(user_id),
            },
        )

        # Emit created event
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.CODE_ARTIFACT,
            entity_id=artifact.id,
            action=ActionType.CREATED,
            snapshot=artifact.model_dump(mode="json"),
        )

        if self._write_plugin:
            plugin_warnings += await self._write_plugin.after_save(CodeArtifactSavedRequest(
                operation="create", user_id=user_id, previous=None, saved=artifact,
            ))

        return CodeArtifactWriteResult(artifact=artifact, plugin_warnings=plugin_warnings)

    async def get_code_artifact(
        self,
        user_id: UUID,
        artifact_id: int,
    ) -> CodeArtifact:
        """Get artifact by ID with ownership verification

        Args:
            user_id: User ID for ownership verification
            artifact_id: Artifact ID to retrieve

        Returns:
            CodeArtifact with full details

        Raises:
            NotFoundError: If artifact not found or not owned by user
        """
        logger.info(
            "getting code artifact",
            extra={
                "artifact_id": artifact_id,
                "user_id": str(user_id),
            },
        )

        artifact = await self.artifact_repo.get_code_artifact_by_id(
            user_id=user_id,
            artifact_id=artifact_id,
        )

        if not artifact:
            raise NotFoundError(f"Code artifact {artifact_id} not found")

        logger.info(
            "code artifact retrieved",
            extra={
                "artifact_id": artifact_id,
                "user_id": str(user_id),
            },
        )

        # Emit read event (opt-in via ACTIVITY_TRACK_READS)
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.CODE_ARTIFACT,
                entity_id=artifact_id,
                action=ActionType.READ,
                snapshot=artifact.model_dump(mode="json"),
            )

        return artifact

    async def list_code_artifacts(
        self,
        user_id: UUID,
        project_id: int | None = None,
        language: str | None = None,
        tags: list[str] | None = None,
    ) -> list[CodeArtifactSummary]:
        """List artifacts with optional filtering

        Args:
            user_id: User ID for ownership filtering
            project_id: Optional filter by project
            language: Optional filter by programming language
            tags: Optional filter by tags (returns artifacts with ANY of these tags)

        Returns:
            List of CodeArtifactSummary (lightweight, excludes full code)
        """
        logger.info(
            "listing code artifacts",
            extra={
                "user_id": str(user_id),
                "project_id": project_id,
                "language": language,
                "tags": tags,
            },
        )

        artifacts = await self.artifact_repo.list_code_artifacts(
            user_id=user_id,
            project_id=project_id,
            language=language,
            tags=tags,
        )

        logger.info(
            "code artifacts retrieved",
            extra={
                "count": len(artifacts),
                "user_id": str(user_id),
            },
        )

        # Emit queried event (opt-in via ACTIVITY_TRACK_READS)
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.CODE_ARTIFACT,
                entity_id=0,  # Query spans multiple artifacts
                action=ActionType.QUERIED,
                snapshot={
                    "result_ids": [a.id for a in artifacts],
                    "total_count": len(artifacts),
                },
                metadata={
                    "project_id": project_id,
                    "language": language,
                    "tags": tags,
                },
            )

        return artifacts

    async def list_code_artifacts_page(
        self,
        user_id: UUID,
        project_id: int | None = None,
        language: str | None = None,
        tags: list[str] | None = None,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[CodeArtifactSummary], int]:
        """Return one bounded page and its full filtered total for REST callers."""
        items, total = await self.artifact_repo.list_code_artifacts_page(
            user_id=user_id,
            project_id=project_id,
            language=language,
            tags=tags,
            limit=limit,
            offset=offset,
        )
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.CODE_ARTIFACT,
                entity_id=0,
                action=ActionType.QUERIED,
                snapshot={
                    "result_ids": [item.id for item in items],
                    "total_count": total,
                },
                metadata={
                    "project_id": project_id,
                    "language": language,
                    "tags": tags,
                    "limit": limit,
                    "offset": offset,
                },
            )
        return items, total

    async def update_code_artifact(
        self,
        user_id: UUID,
        artifact_id: int,
        artifact_data: CodeArtifactUpdate,
    ) -> CodeArtifactWriteResult:
        """Update existing artifact (PATCH semantics)

        Only provided fields are updated. None/omitted fields remain unchanged.

        Args:
            user_id: User ID for ownership verification
            artifact_id: Artifact ID to update
            artifact_data: CodeArtifactUpdate with fields to change

        Returns:
            Updated CodeArtifact plus plugin warnings

        Raises:
            NotFoundError: If artifact not found or not owned by user
        """
        logger.info(
            "updating code artifact",
            extra={
                "artifact_id": artifact_id,
                "user_id": str(user_id),
            },
        )

        submitted = artifact_data.model_copy(deep=True)
        # Null policy is unchanged by this feature. An explicit null is a submitted
        # value and reaches the repository as it does without a plugin, so a
        # nullable column is cleared by one and a required column still fails.
        artifact_data = apply_provenance_defaults_for_update(artifact_data)

        # Get existing artifact for change detection
        existing_artifact = await self.artifact_repo.get_code_artifact_by_id(
            user_id=user_id,
            artifact_id=artifact_id,
        )

        if not existing_artifact:
            raise NotFoundError(f"Code artifact {artifact_id} not found")

        # Detect changes
        changed_fields = get_changed_fields(
            input_model=artifact_data, existing_model=existing_artifact,
        )

        plugin_warnings = []
        if changed_fields and self._write_plugin and self._write_plugin.has_before("update"):
            # Merged view of the artifact as it will be after the write, matching the
            # snapshot rule set by the Memory Plugin contract (PR #164) and implemented
            # for entity writes in PR #184: the full record, not just changed fields.
            proposed_data = existing_artifact.model_dump(
                include=set(CodeArtifactCreate.model_fields),
            )
            proposed_data.update(artifact_data.model_dump(exclude_unset=True))
            # model_construct: a null on a required field must reach the repository and
            # fail there, as it does without a plugin, rather than fail while the
            # context is assembled. The caller already validated this payload.
            proposed = CodeArtifactCreate.model_construct(**proposed_data)
            plugin_warnings = await self._write_plugin.before_save(CodeArtifactWriteRequest(
                operation="update", user_id=user_id, submitted=submitted,
                previous=existing_artifact.model_copy(deep=True), proposed=proposed,
            ))
            existing_artifact = await self.artifact_repo.get_code_artifact_by_id(
                user_id=user_id,
                artifact_id=artifact_id,
            )
            if not existing_artifact:
                raise NotFoundError(f"Code artifact {artifact_id} not found")
            changed_fields = get_changed_fields(
                input_model=artifact_data, existing_model=existing_artifact,
            )
            if not changed_fields:
                return CodeArtifactWriteResult(
                    artifact=existing_artifact, plugin_warnings=plugin_warnings,
                )

        artifact = await self.artifact_repo.update_code_artifact(
            user_id=user_id,
            artifact_id=artifact_id,
            artifact_data=artifact_data,
        )

        logger.info(
            "code artifact updated",
            extra={
                "artifact_id": artifact_id,
                "user_id": str(user_id),
            },
        )

        # Emit updated event with changes
        if changed_fields:
            changes_dict = {
                field: {"old": old, "new": new}
                for field, (old, new) in changed_fields.items()
            }
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.CODE_ARTIFACT,
                entity_id=artifact_id,
                action=ActionType.UPDATED,
                snapshot=artifact.model_dump(mode="json"),
                changes=changes_dict,
            )
            if self._write_plugin:
                previous = existing_artifact.model_copy(deep=True)
                plugin_warnings += await self._write_plugin.after_save(
                    CodeArtifactSavedRequest(
                        operation="update", user_id=user_id, saved=artifact,
                        previous=previous,
                    ),
                )

        return CodeArtifactWriteResult(artifact=artifact, plugin_warnings=plugin_warnings)

    async def delete_code_artifact(
        self,
        user_id: UUID,
        artifact_id: int,
    ) -> CodeArtifactDeleteResult:
        """Delete artifact (cascade removes memory associations)

        Args:
            user_id: User ID for ownership verification
            artifact_id: Artifact ID to delete

        Returns:
            Whether it was deleted, plus any plugin warnings
        """
        logger.info(
            "deleting code artifact",
            extra={
                "artifact_id": artifact_id,
                "user_id": str(user_id),
            },
        )

        # Fetch artifact before deletion for snapshot
        existing_artifact = await self.artifact_repo.get_code_artifact_by_id(
            user_id=user_id,
            artifact_id=artifact_id,
        )

        plugin_warnings = []
        if existing_artifact and self._write_plugin and self._write_plugin.has_before("delete"):
            plugin_warnings = await self._write_plugin.before_save(CodeArtifactWriteRequest(
                operation="delete", user_id=user_id,
                submitted=CodeArtifactDeleteSubmission(artifact_id=artifact_id),
                previous=existing_artifact.model_copy(deep=True), proposed=None,
            ))
            existing_artifact = await self.artifact_repo.get_code_artifact_by_id(
                user_id=user_id,
                artifact_id=artifact_id,
            )
            if not existing_artifact:
                return CodeArtifactDeleteResult(
                    deleted=False, plugin_warnings=plugin_warnings,
                )

        success = await self.artifact_repo.delete_code_artifact(
            user_id=user_id,
            artifact_id=artifact_id,
        )

        if success:
            logger.info(
                "code artifact deleted",
                extra={
                    "artifact_id": artifact_id,
                    "user_id": str(user_id),
                },
            )

            # Emit deleted event with pre-deletion snapshot
            if existing_artifact:
                await self._emit_event(
                    user_id=user_id,
                    entity_type=EntityType.CODE_ARTIFACT,
                    entity_id=artifact_id,
                    action=ActionType.DELETED,
                    snapshot=existing_artifact.model_dump(mode="json"),
                )
        else:
            logger.warning(
                "code artifact not found for deletion",
                extra={
                    "artifact_id": artifact_id,
                    "user_id": str(user_id),
                },
            )

        if success and existing_artifact and self._write_plugin:
            plugin_warnings += await self._write_plugin.after_save(
                CodeArtifactDeletedRequest(
                    user_id=user_id, deleted_artifact_id=artifact_id,
                    previous=existing_artifact,
                ),
            )

        return CodeArtifactDeleteResult(deleted=success, plugin_warnings=plugin_warnings)
