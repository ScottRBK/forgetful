"""Explicit frozen Plan Plugin registrations for trusted administrator handlers."""

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, get_args

from app.models.plan_plugin_models import (
    PlanDeleteRequest,
    PlanOperation,
    PlanSavedRequest,
    PlanWriteRequest,
)
from app.models.write_plugin_models import PluginWarning, WriteDecision


class PlanBeforeSave(Protocol):
    async def __call__(self, request: PlanWriteRequest) -> WriteDecision:
        ...


class PlanAfterSave(Protocol):
    async def __call__(self, request: PlanSavedRequest | PlanDeleteRequest) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class PlanPlugin:
    before_save: Mapping[PlanOperation, PlanBeforeSave] = field(default_factory=dict)
    after_save: Mapping[PlanOperation, PlanAfterSave] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(PlanOperation):
                    raise ValueError(f"{phase} contains an unsupported plan operation")
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            object.__setattr__(self, phase, MappingProxyType(handlers))
