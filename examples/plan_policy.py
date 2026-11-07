"""Copy into an administrator-owned installed package; not loaded by default."""

from app.models.plan_models import PlanStatus
from app.models.plan_plugin_models import (
    PlanDeleteRequest,
    PlanSavedRequest,
    PlanWriteRequest,
)
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.plan_plugin_protocol import PlanPlugin


async def require_completion_goal(request: PlanWriteRequest) -> WriteDecision:
    if (request.proposed is not None
            and request.proposed.status == PlanStatus.COMPLETED
            and not request.proposed.goal):
        return WriteDecision(
            outcome="reject", message="Add a plan goal before completion.", code="PLAN_GOAL_REQUIRED",
        )
    return WriteDecision(outcome="allow")


async def review_completion(request: PlanSavedRequest | PlanDeleteRequest) -> PluginWarning | None:
    if isinstance(request, PlanSavedRequest) and request.saved.status == PlanStatus.COMPLETED:
        return PluginWarning(
            message="Review the completed plan's outcome.", code="PLAN_COMPLETION_REVIEW",
        )
    return None


plugin = PlanPlugin(
    before_save={"create": require_completion_goal, "update": require_completion_goal},
    after_save={"update": review_completion},
)
