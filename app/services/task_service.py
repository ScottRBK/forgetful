import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

from app.config.logging_config import logging
from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.activity_models import (
    ActionType,
    ActivityEvent,
    ActorType,
    EntityType,
)
from app.models.plan_models import (
    VALID_TASK_TRANSITIONS,
    Criterion,
    CriterionCreate,
    CriterionUpdate,
    PlanStatus,
    PlanUpdate,
    Task,
    TaskCreate,
    TaskPriority,
    TaskState,
    TaskSummary,
    TaskUpdate,
)
from app.protocols.task_protocol import TaskRepository
from app.services.plan_service import PlanService
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)
from app.utils.pydantic_helper import get_changed_fields

if TYPE_CHECKING:
    from app.events import EventBus

logger = logging.getLogger(__name__)


class TaskService:
    """Service layer for task operations with state machine enforcement."""

    def __init__(
        self,
        task_repo: TaskRepository,
        plan_service: PlanService,
        event_bus: "EventBus | None" = None,
    ):
        self.task_repo = task_repo
        self.plan_service = plan_service
        self._event_bus = event_bus
        # Orders dependency writers inside this process; the repository re-checks the
        # graph in the inserting transaction to cover other processes.
        self._dependency_lock = asyncio.Lock()
        logger.info("Task service initialised")

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

    async def _emit_task_changed(self, user_id: UUID, task_id: int, changes: dict) -> None:
        """Announce a criterion/dependency change as a TASK update with the refreshed snapshot.

        criteria_met, criteria_total and blocked all derive from these rows, so activity and
        SSE consumers need the new task state, not only the sibling row that changed.
        """
        if self._event_bus is None:
            return
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if task is None:
            return
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.TASK,
            entity_id=task_id,
            action=ActionType.UPDATED,
            snapshot=task.model_dump(mode="json"),
            changes=changes,
        )

    async def create_task(self, user_id: UUID, task_data: TaskCreate) -> Task:
        """Create task with optional inline criteria and dependencies."""
        logger.info("creating task", extra={"user_id": str(user_id), "plan_id": task_data.plan_id, "title": task_data.title})

        # Validate plan exists and is not COMPLETED/ARCHIVED
        plan = await self.plan_service.get_plan(user_id=user_id, plan_id=task_data.plan_id)

        plan_status = PlanStatus(plan.status)
        if plan_status in (PlanStatus.COMPLETED, PlanStatus.ARCHIVED):
            raise InvalidStateTransitionError(
                f"Cannot add tasks to plan in {plan_status.value} status",
            )

        # Validate every dependency before anything is persisted so a bad id cannot
        # leave a half-built task behind. A brand new task cannot be part of a cycle.
        dependency_ids = task_data.dependency_ids or []
        duplicates = sorted({dep_id for dep_id in dependency_ids if dependency_ids.count(dep_id) > 1})
        if duplicates:
            raise ValueError(f"dependency_ids lists the same task more than once: {duplicates}")
        for dep_id in dependency_ids:
            await self._validate_same_plan(user_id, dep_id, task_data.plan_id)

        # Create the task (without criteria/deps - repo handles basic creation)
        task_data = apply_provenance_defaults(task_data)
        task = await self.task_repo.create_task(user_id=user_id, task_data=task_data)

        try:
            # Create inline criteria
            for criterion_data in task_data.criteria or []:
                await self.task_repo.create_criterion(
                    user_id=user_id, task_id=task.id, criterion_data=criterion_data,
                )

            for dep_id in dependency_ids:
                await self.task_repo.add_dependency(
                    user_id=user_id, task_id=task.id, depends_on_task_id=dep_id,
                )
        except Exception:
            await self._discard_partial_task(user_id, task.id)
            raise

        # Re-fetch to get full task with criteria and deps
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task.id)

        logger.info("task created", extra={"task_id": task.id, "plan_id": task.plan_id})
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.TASK,
            entity_id=task.id,
            action=ActionType.CREATED,
            snapshot=task.model_dump(mode="json"),
        )
        return task

    async def get_task(self, user_id: UUID, task_id: int) -> Task:
        logger.info("getting task", extra={"user_id": str(user_id), "task_id": task_id})
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if task:
            logger.info("task retrieved", extra={"task_id": task_id})
            return task
        logger.info("task not found", extra={"task_id": task_id})
        raise NotFoundError(f"Task with id {task_id} not found")

    async def list_tasks(
        self,
        user_id: UUID,
        plan_id: int,
        state: TaskState | None = None,
        priority: TaskPriority | None = None,
        assigned_agent: str | None = None,
    ) -> list[TaskSummary]:
        logger.info("listing tasks", extra={"plan_id": plan_id})
        tasks = await self.task_repo.list_tasks(
            user_id=user_id, plan_id=plan_id,
            state=state, priority=priority, assigned_agent=assigned_agent,
        )
        logger.info("tasks retrieved", extra={"count": len(tasks)})
        return tasks

    async def list_tasks_for_user(
        self,
        user_id: UUID,
        plan_ids: list[int] | None = None,
    ) -> list[TaskSummary]:
        logger.info(
            "listing tasks for user",
            extra={"user_id": str(user_id), "plan_ids_count": len(plan_ids) if plan_ids is not None else None},
        )
        tasks = await self.task_repo.list_tasks_for_user(user_id=user_id, plan_ids=plan_ids)
        logger.info("tasks retrieved", extra={"count": len(tasks)})
        return tasks

    async def update_task(
        self, user_id: UUID, task_id: int, task_data: TaskUpdate,
    ) -> Task | None:
        """PATCH for metadata only (title, description, priority). NOT for state changes."""
        logger.info("updating task", extra={"user_id": str(user_id), "task_id": task_id})

        task_data = apply_provenance_defaults_for_update(task_data)

        existing = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not existing:
            return None

        changed_fields = get_changed_fields(input_model=task_data, existing_model=existing)
        if not changed_fields:
            return existing

        updated = await self.task_repo.update_task(user_id=user_id, task_id=task_id, task_data=task_data)
        logger.info("task updated", extra={"task_id": task_id})

        changes_dict = {
            field: {"old": old, "new": new}
            for field, (old, new) in changed_fields.items()
        }
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.TASK,
            entity_id=task_id,
            action=ActionType.UPDATED,
            snapshot=updated.model_dump(mode="json"),
            changes=changes_dict,
        )
        return updated

    async def delete_task(self, user_id: UUID, task_id: int) -> bool:
        logger.info("deleting task", extra={"user_id": str(user_id), "task_id": task_id})

        existing = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not existing:
            return False

        plan_id = existing.plan_id
        success = await self.task_repo.delete_task(user_id=user_id, task_id=task_id)
        if success:
            logger.info("task deleted", extra={"task_id": task_id})
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.TASK,
                entity_id=task_id,
                action=ActionType.DELETED,
                snapshot=existing.model_dump(mode="json"),
            )
            # Check plan auto-completion
            await self._check_plan_auto_completion(user_id, plan_id)
        return success

    async def transition_task(
        self,
        user_id: UUID,
        task_id: int,
        new_state: TaskState,
        expected_version: int,
    ) -> Task:
        """THE core method for state transitions with optimistic locking."""
        logger.info(
            "transitioning task",
            extra={"task_id": task_id, "new_state": new_state.value, "expected_version": expected_version},
        )

        # Fetch current task
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} not found")

        # Verify version (optimistic locking)
        if task.version != expected_version:
            raise ConflictError(
                f"Version mismatch: expected {expected_version}, got {task.version}. "
                f"Task was modified by another agent.",
            )

        # Validate state transition
        current_state = TaskState(task.state)
        valid_targets = VALID_TASK_TRANSITIONS.get(current_state, set())
        if new_state not in valid_targets:
            raise InvalidStateTransitionError(
                f"Cannot transition task from {current_state.value} to {new_state.value}. "
                f"Valid transitions: {[s.value for s in valid_targets]}",
            )

        # A finished plan only takes back work by reopening one of its finished tasks
        reopens_plan = await self._check_plan_accepts_task_change(user_id, task.plan_id, current_state)

        # If → doing or done: validate all dependencies are done. Re-checked on done because
        # an edge can be added, or a prerequisite reopened, while the task is in progress.
        if new_state in (TaskState.DOING, TaskState.DONE):
            await self._validate_dependencies_met(user_id, task)

        # If → done: validate all criteria are met (tasks with zero criteria CAN be marked done)
        if new_state == TaskState.DONE:
            await self._validate_all_criteria_met(user_id, task)

        # Atomic update
        updated = await self.task_repo.transition_task_state(
            user_id=user_id,
            task_id=task_id,
            new_state=new_state,
            expected_version=expected_version,
        )

        logger.info(
            "task transitioned",
            extra={"task_id": task_id, "old_state": current_state.value, "new_state": new_state.value},
        )

        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.TASK,
            entity_id=task_id,
            action=ActionType.UPDATED,
            snapshot=updated.model_dump(mode="json"),
            changes={"state": {"old": current_state.value, "new": new_state.value}},
        )

        # If task → done/cancelled: check plan auto-completion
        if new_state in (TaskState.DONE, TaskState.CANCELLED):
            await self._check_plan_auto_completion(user_id, task.plan_id)

        if reopens_plan:
            await self._reopen_plan(user_id, task.plan_id)

        return updated

    async def claim_task(
        self,
        user_id: UUID,
        task_id: int,
        agent_id: str,
        expected_version: int,
    ) -> Task:
        """Convenience wrapper: claim task by setting agent and transitioning to doing."""
        logger.info(
            "claiming task",
            extra={"task_id": task_id, "agent_id": agent_id, "expected_version": expected_version},
        )

        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} not found")

        if task.version != expected_version:
            raise ConflictError(
                f"Version mismatch: expected {expected_version}, got {task.version}. "
                f"Task was modified by another agent.",
            )

        current_state = TaskState(task.state)
        if current_state not in (TaskState.TODO, TaskState.WAITING):
            raise InvalidStateTransitionError(
                f"Cannot claim task in {current_state.value} state. Must be todo or waiting.",
            )

        await self._check_plan_accepts_task_change(user_id, task.plan_id, current_state)

        # Validate dependencies met
        await self._validate_dependencies_met(user_id, task)

        # Atomic: set assigned_agent + state=doing + version+=1
        updated = await self.task_repo.transition_task_state(
            user_id=user_id,
            task_id=task_id,
            new_state=TaskState.DOING,
            expected_version=expected_version,
            assigned_agent=agent_id,
        )

        logger.info("task claimed", extra={"task_id": task_id, "agent_id": agent_id})

        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.TASK,
            entity_id=task_id,
            action=ActionType.UPDATED,
            snapshot=updated.model_dump(mode="json"),
            changes={
                "state": {"old": current_state.value, "new": TaskState.DOING.value},
                "assigned_agent": {"old": task.assigned_agent, "new": agent_id},
            },
        )
        return updated

    # ---- Criteria ----

    async def add_criterion(
        self, user_id: UUID, task_id: int, criterion_data: CriterionCreate,
    ) -> Criterion:
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} not found")
        if TaskState(task.state) == TaskState.DONE:
            raise InvalidStateTransitionError("Cannot add criteria to a completed task")

        criterion = await self.task_repo.create_criterion(
            user_id=user_id, task_id=task_id, criterion_data=criterion_data,
        )
        logger.info("criterion added", extra={"criterion_id": criterion.id, "task_id": task_id})
        await self._emit_task_changed(
            user_id, task_id, {"criterion": {"old": None, "new": criterion.model_dump(mode="json")}},
        )
        return criterion

    async def update_criterion(
        self, user_id: UUID, criterion_id: int, criterion_data: CriterionUpdate,
    ) -> Criterion:
        existing = await self._get_editable_criterion(user_id, criterion_id)
        if existing is None:
            raise NotFoundError(f"Criterion with id {criterion_id} not found")

        criterion = await self.task_repo.update_criterion(
            user_id=user_id, criterion_id=criterion_id, criterion_data=criterion_data,
        )
        logger.info("criterion updated", extra={"criterion_id": criterion_id})
        if (criterion.description, criterion.met) != (existing.description, existing.met):
            await self._emit_task_changed(
                user_id,
                existing.task_id,
                {"criterion": {
                    "old": existing.model_dump(mode="json"),
                    "new": criterion.model_dump(mode="json"),
                }},
            )
        return criterion

    async def delete_criterion(self, user_id: UUID, criterion_id: int) -> bool:
        existing = await self._get_editable_criterion(user_id, criterion_id)
        if existing is None:
            return False

        success = await self.task_repo.delete_criterion(user_id=user_id, criterion_id=criterion_id)
        if success:
            logger.info("criterion deleted", extra={"criterion_id": criterion_id})
            await self._emit_task_changed(
                user_id,
                existing.task_id,
                {"criterion": {"old": existing.model_dump(mode="json"), "new": None}},
            )
        return success

    # ---- Dependencies ----

    async def add_dependency(
        self, user_id: UUID, task_id: int, depends_on_task_id: int,
    ):
        # Validate both tasks exist
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} not found")

        dep_task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=depends_on_task_id)
        if not dep_task:
            raise NotFoundError(f"Task with id {depends_on_task_id} not found")

        if TaskState(task.state) == TaskState.DONE:
            raise InvalidStateTransitionError("Cannot add dependencies to a completed task")

        # Validate same plan
        await self._validate_same_plan(user_id, depends_on_task_id, task.plan_id)

        if depends_on_task_id in task.dependency_ids:
            raise ConflictError(f"Task {task_id} already depends on task {depends_on_task_id}")

        # Cycle detection and insert must not interleave with another writer: two
        # opposite edges that each pass the check would otherwise both be stored.
        async with self._dependency_lock:
            await self._validate_no_cycle(user_id, task_id, depends_on_task_id)
            dep = await self.task_repo.add_dependency(
                user_id=user_id, task_id=task_id, depends_on_task_id=depends_on_task_id,
            )
        logger.info("dependency added", extra={"task_id": task_id, "depends_on": depends_on_task_id})
        await self._emit_task_changed(
            user_id, task_id, {"dependency": {"old": None, "new": depends_on_task_id}},
        )
        return dep

    async def remove_dependency(
        self, user_id: UUID, task_id: int, depends_on_task_id: int,
    ) -> bool:
        success = await self.task_repo.remove_dependency(
            user_id=user_id, task_id=task_id, depends_on_task_id=depends_on_task_id,
        )
        if success:
            logger.info("dependency removed", extra={"task_id": task_id, "depends_on": depends_on_task_id})
            await self._emit_task_changed(
                user_id, task_id, {"dependency": {"old": depends_on_task_id, "new": None}},
            )
        return success

    # ---- Private Helpers ----

    async def _get_editable_criterion(self, user_id: UUID, criterion_id: int) -> Criterion | None:
        """Return the criterion, or None if missing; refuse if its task is already DONE.

        Mirrors add_criterion: a completed task keeps the criteria it was completed with.
        """
        criterion = await self.task_repo.get_criterion_by_id(user_id=user_id, criterion_id=criterion_id)
        if criterion is None:
            return None
        task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=criterion.task_id)
        if task is not None and TaskState(task.state) == TaskState.DONE:
            raise InvalidStateTransitionError("Cannot modify criteria of a completed task")
        return criterion

    async def _validate_dependencies_met(self, user_id: UUID, task: Task) -> None:
        """Check all dependencies are in done state."""
        dep_ids = task.dependency_ids
        if not dep_ids:
            return

        for dep_id in dep_ids:
            dep_task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=dep_id)
            if not dep_task or TaskState(dep_task.state) != TaskState.DONE:
                raise DependencyNotMetError(
                    f"Dependency task {dep_id} is not done "
                    f"(state: {dep_task.state if dep_task else 'not found'})",
                )

    async def _validate_all_criteria_met(self, user_id: UUID, task: Task) -> None:
        """Check all criteria have met=True. Tasks with zero criteria CAN be marked done."""
        criteria = await self.task_repo.get_criteria_for_task(user_id=user_id, task_id=task.id)
        if not criteria:
            return  # Zero criteria = can be done

        unmet = [c for c in criteria if not c.met]
        if unmet:
            raise InvalidStateTransitionError(
                f"Cannot mark task as done: {len(unmet)} acceptance criteria not met. "
                f"Unmet: {[c.description[:50] for c in unmet]}",
            )

    async def _validate_no_cycle(self, user_id: UUID, task_id: int, new_dep_id: int) -> None:
        """BFS from new_dep_id following existing 'depends_on' edges.
        If we reach task_id, adding this edge would create a cycle.
        """
        if task_id == new_dep_id:
            raise CyclicDependencyError("A task cannot depend on itself")

        visited: set[int] = set()
        queue: list[int] = [new_dep_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            deps = await self.task_repo.get_dependencies(user_id, current)
            for dep_id in deps:
                if dep_id == task_id:
                    raise CyclicDependencyError(
                        f"Adding dependency {task_id} -> {new_dep_id} would create a cycle "
                        f"(path exists from {new_dep_id} back to {task_id})",
                    )
                queue.append(dep_id)

    async def _discard_partial_task(self, user_id: UUID, task_id: int) -> None:
        """Remove a task whose creation failed part-way (criteria and edges cascade)."""
        try:
            await self.task_repo.delete_task(user_id=user_id, task_id=task_id)
        except Exception:
            logger.exception("failed to roll back partially created task", extra={"task_id": task_id})

    async def _validate_same_plan(
        self, user_id: UUID, dep_task_id: int, expected_plan_id: int,
    ) -> None:
        """Validate that the dependency task belongs to the same plan."""
        dep_task = await self.task_repo.get_task_by_id(user_id=user_id, task_id=dep_task_id)
        if not dep_task:
            raise NotFoundError(f"Task with id {dep_task_id} not found")
        if dep_task.plan_id != expected_plan_id:
            raise ValueError(
                f"Task {dep_task_id} belongs to plan {dep_task.plan_id}, "
                f"not plan {expected_plan_id}. Dependencies must be within the same plan.",
            )

    async def _check_plan_accepts_task_change(
        self, user_id: UUID, plan_id: int, current_state: TaskState,
    ) -> bool:
        """Refuse task state changes in archived or completed plans, like create_task does.

        A completed plan still accepts the reopening of one of its finished (done or
        cancelled) tasks; the return value is True when that happens and the caller must
        move the plan back to active once the task change succeeded.
        """
        try:
            plan = await self.plan_service.get_plan(user_id=user_id, plan_id=plan_id)
        except NotFoundError:
            return False

        plan_status = PlanStatus(plan.status)
        if plan_status == PlanStatus.ARCHIVED:
            raise InvalidStateTransitionError(
                f"Cannot change task state in plan in {plan_status.value} status",
            )
        if plan_status == PlanStatus.COMPLETED:
            if current_state in (TaskState.DONE, TaskState.CANCELLED):
                return True
            raise InvalidStateTransitionError(
                f"Cannot change task state in plan in {plan_status.value} status. "
                f"Reopen a done or cancelled task first to resume work.",
            )
        return False

    async def _reopen_plan(self, user_id: UUID, plan_id: int) -> None:
        """Move a completed plan back to active after one of its tasks was reopened."""
        logger.info("reopening plan", extra={"plan_id": plan_id})
        await self.plan_service.update_plan(
            user_id=user_id,
            plan_id=plan_id,
            plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
        )

    async def _check_plan_auto_completion(self, user_id: UUID, plan_id: int) -> None:
        """If all tasks in the plan are done/cancelled (with at least one done),
        auto-transition plan to COMPLETED.
        """
        tasks = await self.task_repo.list_tasks(user_id=user_id, plan_id=plan_id)
        if not tasks:
            return

        all_terminal = all(
            TaskState(t.state) in (TaskState.DONE, TaskState.CANCELLED)
            for t in tasks
        )
        has_done = any(TaskState(t.state) == TaskState.DONE for t in tasks)

        if all_terminal and has_done:
            try:
                plan = await self.plan_service.get_plan(user_id=user_id, plan_id=plan_id)
            except NotFoundError:
                return
            if PlanStatus(plan.status) == PlanStatus.ACTIVE:
                logger.info("auto-completing plan", extra={"plan_id": plan_id})
                await self.plan_service.update_plan(
                    user_id=user_id,
                    plan_id=plan_id,
                    plan_data=PlanUpdate(status=PlanStatus.COMPLETED),
                )
