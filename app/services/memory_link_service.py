"""Domain link policy: preflight before writes; after handlers observe actual outcomes."""

import asyncio
import logging
from typing import Literal
from uuid import UUID

from app.exceptions import (
    NotFoundError,
    WritePluginRejectedError,
    WritePluginUnavailableError,
)
from app.models.write_plugin_models import (
    MemoryLinkOperation,
    MemoryLinkOutcome,
    MemoryLinkRequest,
    MemoryLinkResult,
    MemoryLinkSavedRequest,
    PluginWarning,
    WriteDecision,
)
from app.protocols.memory_protocol import MemoryRepository
from app.protocols.write_plugin_protocol import MemoryLinkPlugin

logger = logging.getLogger(__name__)
UNAVAILABLE = "Memory Link Plugin unavailable."


class MemoryLinkService:
    def __init__(
        self, repository: MemoryRepository, plugin: MemoryLinkPlugin,
        mode: Literal["warn", "enforce"] = "enforce", timeout_seconds: float = 5.0,
    ):
        self._repository = repository
        self._plugin = plugin
        self._mode = mode
        self._timeout_seconds = timeout_seconds

    def active(self, operation: MemoryLinkOperation) -> bool:
        return operation in self._plugin.before_save or operation in self._plugin.after_save

    async def _before(self, request: MemoryLinkRequest) -> list[PluginWarning]:
        handler = self._plugin.before_save.get(request.operation)
        if handler is None:
            return []
        try:
            async with asyncio.timeout(self._timeout_seconds):
                decision = WriteDecision.model_validate(await handler(request.model_copy(deep=True)))
        except asyncio.CancelledError as exc:
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                raise
            return self._before_unavailable(request, exc)
        except Exception as exc:
            return self._before_unavailable(request, exc)
        if decision.outcome == "reject":
            if self._mode == "enforce":
                # The ID was validated and read through the user's owned-memory repository.
                raise WritePluginRejectedError(
                    f"Memory link policy rejected target {request.target.id}: {decision.message}",
                )
            decision = decision.model_copy(update={"outcome": "warn"})
        if decision.outcome == "warn":
            return [PluginWarning.model_validate(decision.model_dump())]
        return []

    def _before_unavailable(self, request: MemoryLinkRequest, exc: BaseException) -> list[PluginWarning]:
        logger.warning(
            "Memory Link Plugin unavailable (phase=before_save, operation=%s, error_type=%s)",
            request.operation, type(exc).__name__,
        )
        if self._mode == "enforce":
            raise WritePluginUnavailableError(UNAVAILABLE) from None
        return [PluginWarning(message=UNAVAILABLE, code="WRITE_PLUGIN_UNAVAILABLE")]

    async def _after(
        self, operation: MemoryLinkOperation, user_id: UUID,
        origin: Literal["manual", "automatic"], pairs: list[MemoryLinkRequest],
        result: MemoryLinkResult,
    ) -> None:
        handler = self._plugin.after_save.get(operation)
        if handler is None or not pairs:
            return
        request = MemoryLinkSavedRequest(
            operation=operation, user_id=user_id, origin=origin,
            pairs=pairs, outcomes=result.outcomes,
        ).model_copy(deep=True)
        try:
            async with asyncio.timeout(self._timeout_seconds):
                warning = await handler(request)
                if warning is not None:
                    result.plugin_warnings.append(PluginWarning.model_validate(warning))
        except asyncio.CancelledError as exc:
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                raise
            self._after_unavailable(result, exc)
        except Exception as exc:
            self._after_unavailable(result, exc)

    def _after_unavailable(self, result: MemoryLinkResult, exc: BaseException) -> None:
        logger.warning(
            "Memory Link Plugin unavailable (phase=after_save, operation=%s, error_type=%s)",
            result.operation, type(exc).__name__,
        )
        result.plugin_warnings.append(PluginWarning(
            message="Memory links changed, but after-save plugin unavailable.",
            code="MEMORY_LINK_PLUGIN_AFTER_SAVE_UNAVAILABLE",
        ))

    async def link(
        self, user_id: UUID, source_id: int, target_ids: list[int],
        origin: Literal["manual", "automatic"] = "manual",
    ) -> MemoryLinkResult:
        return await self._mutate("link", user_id, source_id, target_ids, origin)

    async def unlink(
        self, user_id: UUID, source_id: int, target_ids: list[int],
    ) -> MemoryLinkResult:
        return await self._mutate("unlink", user_id, source_id, target_ids, "manual")

    async def _mutate(
        self, operation: MemoryLinkOperation, user_id: UUID, source_id: int,
        target_ids: list[int], origin: Literal["manual", "automatic"],
    ) -> MemoryLinkResult:
        repo = self._repository
        source = await repo.get_memory_by_id(user_id=user_id, memory_id=source_id)
        result = MemoryLinkResult(operation=operation)
        eligible: list[MemoryLinkRequest] = []
        pre_outcomes: dict[int, MemoryLinkOutcome] = {}
        # Sequential preflight deliberately costs at most N cooperative handler timeouts.
        # Every eligible manual before-handler finishes before the first mutation.
        for target_id in dict.fromkeys(target_ids):
            linked = target_id in source.linked_memory_ids
            skip = target_id == source_id or (operation == "link" and linked)
            if operation == "unlink" and not linked:
                skip = True
            if skip:
                pre_outcomes[target_id] = MemoryLinkOutcome(
                    target_id=target_id, status="skipped" if operation == "link" else "noop",
                )
                continue
            try:
                target = await repo.get_memory_by_id(user_id=user_id, memory_id=target_id)
            except NotFoundError:
                # Missing and another user's IDs are intentionally indistinguishable.
                pre_outcomes[target_id] = MemoryLinkOutcome(
                    target_id=target_id, status="skipped" if operation == "link" else "noop",
                )
                continue
            request = MemoryLinkRequest(
                operation=operation, user_id=user_id, origin=origin,
                source=source.model_copy(deep=True), target=target.model_copy(deep=True),
            )
            try:
                result.plugin_warnings.extend(await self._before(request))
            except (WritePluginRejectedError, WritePluginUnavailableError):
                if origin != "automatic":
                    raise
                result.plugin_warnings.append(PluginWarning(
                    message="Memory saved, but an automatic link was rejected or unavailable.",
                    code="MEMORY_LINK_PLUGIN_REJECTED",
                ))
                pre_outcomes[target_id] = MemoryLinkOutcome(target_id=target_id, status="rejected")
                continue
            eligible.append(request)

        # Recheck the source after policy awaits; never write back any detached snapshot.
        if eligible:
            await repo.get_memory_by_id(user_id=user_id, memory_id=source_id)
        written_pairs = []
        for request in eligible:
            target_id = request.target.id
            if operation == "link":
                created = await repo.create_links_batch(
                    user_id=user_id, source_id=source_id, target_ids=[target_id],
                )
                changed = target_id in created
                status = "created" if changed else "skipped"
            else:
                changed = await repo.unlink_memories(
                    user_id=user_id, source_id=source_id, target_id=target_id,
                )
                status = "removed" if changed else "noop"
            pre_outcomes[target_id] = MemoryLinkOutcome(target_id=target_id, status=status)
            if changed:
                written_pairs.append(request)
        result.outcomes = [pre_outcomes[target_id] for target_id in dict.fromkeys(target_ids)]
        await self._after(operation, user_id, origin, written_pairs, result)
        return result
