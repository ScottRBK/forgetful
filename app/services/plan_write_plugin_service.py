"""Run selected Plan Plugin handlers with cooperative async deadlines."""

import asyncio
import logging
from typing import Literal

from app.exceptions import PlanPluginRejectedError, PlanPluginUnavailableError
from app.models.plan_plugin_models import (
    PlanDeleteRequest,
    PlanOperation,
    PlanSavedRequest,
    PlanWriteRequest,
)
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.plan_plugin_protocol import PlanPlugin

logger = logging.getLogger(__name__)
UNAVAILABLE_MESSAGE = "Plan Write Plugin unavailable."


class PlanWritePluginService:
    def __init__(
        self, plugin: PlanPlugin, mode: Literal["warn", "enforce"] = "enforce",
        timeout_seconds: float = 5.0,
    ):
        self._plugin = plugin
        self._mode = mode
        self._timeout_seconds = timeout_seconds

    def has_before(self, operation: PlanOperation) -> bool:
        return operation in self._plugin.before_save

    def has_after(self, operation: PlanOperation) -> bool:
        return operation in self._plugin.after_save

    async def before_save(
        self, request: PlanWriteRequest,
    ) -> list[PluginWarning]:
        operation = request.operation
        handler = self._plugin.before_save.get(operation)
        if handler is None:
            return []
        try:
            async with asyncio.timeout(self._timeout_seconds):
                decision = WriteDecision.model_validate(await handler(request.model_copy(deep=True)))
        except Exception as exc:
            # Exception text/tracebacks and validation inputs may contain plan content or secrets.
            logger.warning(
                "Plan Write Plugin unavailable "
                "(phase=before_save, operation=%s, mode=%s, error_type=%s)",
                operation, self._mode, type(exc).__name__,
            )
            if self._mode == "enforce":
                raise PlanPluginUnavailableError(UNAVAILABLE_MESSAGE) from None
            return [PluginWarning(
                message=UNAVAILABLE_MESSAGE, code="PLAN_PLUGIN_UNAVAILABLE",
            )]

        if decision.outcome == "reject":
            if self._mode == "enforce":
                raise PlanPluginRejectedError(decision.message)
            decision = decision.model_copy(update={"outcome": "warn"})
        if decision.outcome == "warn":
            return [PluginWarning.model_validate(decision.model_dump())]
        return []

    async def after_save(self, request: PlanSavedRequest | PlanDeleteRequest) -> list[PluginWarning]:
        handler = self._plugin.after_save.get(request.operation)
        if handler is None:
            return []
        try:
            async with asyncio.timeout(self._timeout_seconds):
                result = await handler(request.model_copy(deep=True))
                return [] if result is None else [PluginWarning.model_validate(result)]
        except asyncio.CancelledError as exc:
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                raise
            # A cancelled child awaited by the plugin must not fail an already persisted write.
            return [self.after_save_unavailable(request.operation, exc)]
        except Exception as exc:
            return [self.after_save_unavailable(request.operation, exc)]

    def after_save_unavailable(
        self, operation: PlanOperation, exc: Exception | asyncio.CancelledError,
    ) -> PluginWarning:
        """Keep a persisted write successful when advisory work cannot complete."""
        logger.warning(
            "Plan Plugin unavailable (phase=after_save, operation=%s, error_type=%s)",
            operation, type(exc).__name__,
        )
        return PluginWarning(
            message="Plan mutation succeeded, but after-save plugin unavailable.",
            code="PLAN_PLUGIN_AFTER_SAVE_UNAVAILABLE",
        )
