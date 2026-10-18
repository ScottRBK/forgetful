"""Evaluate a memory write before persistence, with a cooperative async deadline."""

import asyncio
import logging
from typing import Literal

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.write_plugin_models import MemoryWriteRequest, WriteDecision
from app.protocols.write_plugin_protocol import WritePlugin

logger = logging.getLogger(__name__)
UNAVAILABLE_MESSAGE = "Memory Write Plugin unavailable."


class WritePluginService:
    def __init__(
        self, handler: WritePlugin, mode: Literal["warn", "enforce"] = "enforce",
        timeout_seconds: float = 5.0,
    ):
        self._handler = handler
        self._mode = mode
        self._timeout_seconds = timeout_seconds

    async def evaluate(self, request: MemoryWriteRequest) -> list[WriteDecision]:
        operation = request.operation
        try:
            async with asyncio.timeout(self._timeout_seconds):
                decision = WriteDecision.model_validate(await self._handler(request))
        except Exception as exc:
            # Exception text/tracebacks and validation inputs may contain memory content or secrets.
            logger.warning(
                "Memory Write Plugin unavailable (operation=%s, mode=%s, error_type=%s)",
                operation, self._mode, type(exc).__name__,
            )
            if self._mode == "enforce":
                raise WritePluginUnavailableError(UNAVAILABLE_MESSAGE) from None
            return [WriteDecision(
                outcome="warn", message=UNAVAILABLE_MESSAGE, code="WRITE_PLUGIN_UNAVAILABLE",
            )]

        if decision.outcome == "reject":
            if self._mode == "enforce":
                raise WritePluginRejectedError(decision.message)
            decision = decision.model_copy(update={"outcome": "warn"})
        return [decision] if decision.outcome == "warn" else []
