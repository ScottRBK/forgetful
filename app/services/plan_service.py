from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import TypeAdapter

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import (
    InvalidStateTransitionError,
    NotFoundError,
    PlanPluginStateChangedError,
)
from app.models.activity_models import (
    ActionType,
    ActivityEvent,
    ActorType,
    EntityType,
)
from app.models.plan_models import (
    VALID_PLAN_TRANSITIONS,
    ExternalRef,
    Plan,
    PlanCreate,
    PlanStatus,
    PlanSummary,
    PlanUpdate,
)
from app.models.plan_plugin_models import (
    PlanCreateResult,
    PlanDeleteRequest,
    PlanDeleteResult,
    PlanDeleteSubmission,
    PlanSavedRequest,
    PlanUpdateResult,
    PlanWriteRequest,
)
from app.models.write_plugin_models import PluginWarning
from app.protocols.plan_protocol import PlanRepository
from app.protocols.project_protocol import ProjectRepository
from app.services.plan_write_plugin_service import PlanWritePluginService
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)
from app.utils.pydantic_helper import get_changed_fields

if TYPE_CHECKING:
    from app.events import EventBus

logger = logging.getLogger(__name__)


class PlanService:
    """Service layer for plan operations."""

    def __init__(
        self,
        plan_repo: PlanRepository,
        event_bus: "EventBus | None" = None,
        plan_plugin: PlanWritePluginService | None = None,
        project_repo: ProjectRepository | None = None,
    ):
        self.plan_repo = plan_repo
        self._event_bus = event_bus
        self._plan_plugin = plan_plugin
        self._project_repo = project_repo
        logger.info("Plan service initialised")

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

    async def create_plan(self, user_id: UUID, plan_data: PlanCreate) -> PlanCreateResult:
        logger.info("creating plan", extra={"user_id": str(user_id), "title": plan_data.title})
        submitted = plan_data.model_copy(deep=True)
        plan_data = apply_provenance_defaults(plan_data)
        plugin = self._plan_plugin
        warnings: list[PluginWarning] = []
        if plugin is not None and (plugin.has_before("create") or plugin.has_after("create")):
            if self._project_repo is None:
                raise RuntimeError("Plan Plugin requires a project repository")
            project = await self._project_repo.get_project_by_id(
                user_id=user_id, project_id=plan_data.project_id,
            )
            if project is None:
                raise NotFoundError(f"Project {plan_data.project_id} not found")
            warnings = await plugin.before_save(PlanWriteRequest(
                operation="create", user_id=user_id, submitted=submitted,
                previous=None, proposed=plan_data.model_copy(deep=True),
            ))
        plan = await self.plan_repo.create_plan(user_id=user_id, plan_data=plan_data)
        logger.info("plan created", extra={"plan_id": plan.id, "user_id": str(user_id)})
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.PLAN,
            entity_id=plan.id,
            action=ActionType.CREATED,
            snapshot=plan.model_dump(mode="json"),
        )
        if plugin is not None:
            warnings.extend(await plugin.after_save(PlanSavedRequest(
                operation="create", user_id=user_id, saved=plan, previous=None,
            )))
        return PlanCreateResult(plan=plan, plugin_warnings=warnings)

    async def get_plan(self, user_id: UUID, plan_id: int) -> Plan:
        logger.info("getting plan", extra={"user_id": str(user_id), "plan_id": plan_id})
        plan = await self.plan_repo.get_plan_by_id(user_id=user_id, plan_id=plan_id)
        if plan:
            logger.info("plan retrieved", extra={"plan_id": plan_id})
            if settings.ACTIVITY_TRACK_READS and self._event_bus:
                await self._emit_event(
                    user_id=user_id,
                    entity_type=EntityType.PLAN,
                    entity_id=plan_id,
                    action=ActionType.READ,
                    snapshot=plan.model_dump(mode="json"),
                )
            return plan
        logger.info("plan not found", extra={"plan_id": plan_id})
        raise NotFoundError(f"Plan with id {plan_id} not found")

    async def list_plans(
        self,
        user_id: UUID,
        project_id: int | None = None,
        status: PlanStatus | None = None,
        external_ref: str | None = None,
    ) -> list[PlanSummary]:
        logger.info("listing plans", extra={"user_id": str(user_id), "project_id": project_id, "status": status.value if status else None})
        if external_ref is not None:
            external_ref = TypeAdapter(ExternalRef).validate_python(external_ref)
        plans = await self.plan_repo.list_plans(
            user_id=user_id, project_id=project_id, status=status, external_ref=external_ref,
        )
        logger.info("plans retrieved", extra={"count": len(plans)})
        return plans

    @staticmethod
    def _validate_transition(existing: Plan, plan_data: PlanUpdate) -> None:
        if plan_data.status is not None and plan_data.status != existing.status:
            current = PlanStatus(existing.status)
            target = plan_data.status
            if target not in VALID_PLAN_TRANSITIONS.get(current, set()):
                raise InvalidStateTransitionError(
                    f"Cannot transition plan from {current.value} to {target.value}. "
                    f"Valid transitions: {[s.value for s in VALID_PLAN_TRANSITIONS.get(current, set())]}",
                )

    async def update_plan(
        self, user_id: UUID, plan_id: int, plan_data: PlanUpdate,
        *, automatic: bool = False,
    ) -> PlanUpdateResult:
        logger.info("updating plan", extra={"user_id": str(user_id), "plan_id": plan_id})
        submitted = plan_data.model_copy(deep=True)
        plan_data = apply_provenance_defaults_for_update(plan_data)
        existing = await self.plan_repo.get_plan_by_id(user_id=user_id, plan_id=plan_id)
        if existing is None:
            logger.info("plan not found for update", extra={"plan_id": plan_id})
            return PlanUpdateResult(plan=None)
        self._validate_transition(existing, plan_data)
        changed_fields = get_changed_fields(input_model=plan_data, existing_model=existing)
        if not changed_fields:
            logger.info("no changes detected", extra={"plan_id": plan_id})
            return PlanUpdateResult(plan=existing)

        plugin = self._plan_plugin
        warnings: list[PluginWarning] = []
        if plugin is not None and plugin.has_before("update"):
            proposed = PlanCreate.model_validate({
                **existing.model_dump(), **plan_data.model_dump(exclude_unset=True),
            })
            warnings = await plugin.before_save(PlanWriteRequest(
                operation="update", user_id=user_id, submitted=submitted,
                previous=existing.model_copy(deep=True), proposed=proposed,
                automatic=automatic,
            ))
            current = await self.plan_repo.get_plan_by_id(user_id=user_id, plan_id=plan_id)
            if current is None:
                raise PlanPluginStateChangedError("Plan disappeared while plan policy was evaluated.")
            try:
                self._validate_transition(current, plan_data)
            except InvalidStateTransitionError:
                raise PlanPluginStateChangedError(
                    "Plan status changed while plan policy was evaluated.",
                ) from None
            existing = current
            changed_fields = get_changed_fields(input_model=plan_data, existing_model=existing)
            if not changed_fields:
                return PlanUpdateResult(plan=existing, plugin_warnings=warnings)

        previous = existing.model_copy(deep=True)
        updated = await self.plan_repo.update_plan(user_id=user_id, plan_id=plan_id, plan_data=plan_data)
        logger.info("plan updated", extra={"plan_id": plan_id})
        changes_dict = {
            field: {"old": old, "new": new}
            for field, (old, new) in changed_fields.items()
        }
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.PLAN,
            entity_id=plan_id,
            action=ActionType.UPDATED,
            snapshot=updated.model_dump(mode="json"),
            changes=changes_dict,
        )
        if plugin is not None:
            warnings.extend(await plugin.after_save(PlanSavedRequest(
                operation="update", user_id=user_id, saved=updated,
                previous=previous, automatic=automatic,
            )))
        return PlanUpdateResult(plan=updated, plugin_warnings=warnings)

    async def delete_plan(self, user_id: UUID, plan_id: int) -> PlanDeleteResult:
        logger.info("deleting plan", extra={"user_id": str(user_id), "plan_id": plan_id})
        existing = await self.plan_repo.get_plan_by_id(user_id=user_id, plan_id=plan_id)
        if existing is None:
            return PlanDeleteResult(success=False)
        previous = existing.model_copy(deep=True)
        plugin = self._plan_plugin
        warnings: list[PluginWarning] = []
        if plugin is not None and plugin.has_before("delete"):
            warnings = await plugin.before_save(PlanWriteRequest(
                operation="delete", user_id=user_id,
                submitted=PlanDeleteSubmission(plan_id=plan_id),
                previous=previous, proposed=None,
            ))
        success = await self.plan_repo.delete_plan(user_id=user_id, plan_id=plan_id)
        if success:
            logger.info("plan deleted", extra={"plan_id": plan_id})
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.PLAN,
                entity_id=plan_id,
                action=ActionType.DELETED,
                snapshot=previous.model_dump(mode="json"),
            )
            if plugin is not None:
                warnings.extend(await plugin.after_save(PlanDeleteRequest(
                    user_id=user_id, deleted_plan_id=plan_id, previous=previous,
                )))
        return PlanDeleteResult(success=success, plugin_warnings=warnings)

    async def check_plan_completion(self, user_id: UUID, plan_id: int) -> bool:
        """Check if all tasks in a plan are done/cancelled and auto-complete the plan.

        Called by TaskService after task transitions. If all tasks are done/cancelled
        (with at least one done), auto-transitions plan to COMPLETED.

        Returns True if plan was auto-completed.
        """
        plan = await self.plan_repo.get_plan_by_id(user_id=user_id, plan_id=plan_id)
        if not plan or PlanStatus(plan.status) != PlanStatus.ACTIVE:
            return False

        # We need to check tasks - this requires access to task_repo
        # but we don't have it. The TaskService will call us with task info.
        # This method is called from TaskService which passes task info.
        # For now, the TaskService handles the logic and calls update_plan.
        return False
