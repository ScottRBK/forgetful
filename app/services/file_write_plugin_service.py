"""Run selected File Plugin handlers with cooperative async deadlines."""

import asyncio
import logging
from typing import Literal

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.write_plugin_models import (
    FileDeletedRequest,
    FileOperation,
    FileSavedRequest,
    FileWriteRequest,
    PluginWarning,
    WriteDecision,
)
from app.protocols.write_plugin_protocol import FilePlugin

logger = logging.getLogger(__name__)
UNAVAILABLE_MESSAGE = "File Write Plugin unavailable."


class FileWritePluginService:
    def __init__(
        self, plugin: FilePlugin, mode: Literal["warn", "enforce"] = "enforce",
        timeout_seconds: float = 5.0,
    ):
        self._plugin = plugin
        self._mode = mode
        self._timeout_seconds = timeout_seconds

    def has_before(self, operation: FileOperation) -> bool:
        return operation in self._plugin.before_save

    def has_after(self, operation: FileOperation) -> bool:
        return operation in self._plugin.after_save

    async def before_save(self, request: FileWriteRequest) -> list[PluginWarning]:
        operation = request.operation
        handler = self._plugin.before_save.get(operation)
        if handler is None:
            return []
        try:
            async with asyncio.timeout(self._timeout_seconds):
                decision = WriteDecision.model_validate(await handler(request))
        except Exception as exc:
            # Exception text/tracebacks and validation inputs may contain file content or secrets.
            logger.warning(
                "File Write Plugin unavailable "
                "(phase=before_save, operation=%s, mode=%s, error_type=%s)",
                operation, self._mode, type(exc).__name__,
            )
            if self._mode == "enforce":
                raise WritePluginUnavailableError(UNAVAILABLE_MESSAGE) from None
            return [PluginWarning(
                message=UNAVAILABLE_MESSAGE, code="WRITE_PLUGIN_UNAVAILABLE",
            )]

        if decision.outcome == "reject":
            if self._mode == "enforce":
                raise WritePluginRejectedError(decision.message)
            decision = decision.model_copy(update={"outcome": "warn"})
        if decision.outcome == "warn":
            return [PluginWarning.model_validate(decision.model_dump())]
        return []

    async def after_save(
        self, request: FileSavedRequest | FileDeletedRequest,
    ) -> list[PluginWarning]:
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
            return [self.after_save_unavailable(request.operation, exc)]
        except Exception as exc:
            return [self.after_save_unavailable(request.operation, exc)]

    def after_save_unavailable(
        self, operation: FileOperation, exc: Exception | asyncio.CancelledError,
    ) -> PluginWarning:
        """Keep a persisted write successful when advisory work cannot complete."""
        logger.warning(
            "File Plugin unavailable (phase=after_save, operation=%s, error_type=%s)",
            operation, type(exc).__name__,
        )
        if operation == "delete":
            message = "File deleted, but after-save plugin unavailable."
        else:
            message = "File saved, but after-save plugin unavailable."
        return PluginWarning(
            message=message,
            code="FILE_PLUGIN_AFTER_SAVE_UNAVAILABLE",
        )
