"""Detached Plan Plugin contexts and transient mutation results."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.plan_models import Plan, PlanCreate, PlanUpdate, Task
from app.models.write_plugin_models import PluginWarning

PlanOperation = Literal["create", "update", "delete"]


class PlanDeleteSubmission(BaseModel):
    plan_id: int


class PlanWriteRequest(BaseModel):
    operation: PlanOperation
    user_id: UUID
    submitted: PlanCreate | PlanUpdate | PlanDeleteSubmission
    previous: Plan | None
    proposed: PlanCreate | None
    automatic: bool = False


class PlanSavedRequest(BaseModel):
    operation: Literal["create", "update"]
    user_id: UUID
    saved: Plan
    previous: Plan | None
    automatic: bool = False


class PlanDeleteRequest(BaseModel):
    operation: Literal["delete"] = "delete"
    user_id: UUID
    deleted_plan_id: int
    previous: Plan
    automatic: bool = False


class PlanCreateResult(BaseModel):
    plan: Plan
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class PlanUpdateResult(BaseModel):
    plan: Plan | None
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class PlanDeleteResult(BaseModel):
    success: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class TaskTransitionResult(BaseModel):
    task: Task
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class TaskDeleteResult(BaseModel):
    success: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)
