"""Models for Plans, Tasks, Acceptance Criteria, and Task Dependencies.

These are tightly coupled aggregates forming the hierarchy:
    Project ← Plan ← Task ← Criterion
    Task ← TaskDependency → Task
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.config.settings import settings

# ============================================================================
# Enums
# ============================================================================


class PlanStatus(StrEnum):
    """Plan lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskState(StrEnum):
    """Task state machine states."""
    TODO = "todo"
    DOING = "doing"
    WAITING = "waiting"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    """Task priority levels."""
    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low


# ============================================================================
# State Machine Transitions
# ============================================================================


VALID_TASK_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.TODO:      {TaskState.DOING, TaskState.WAITING, TaskState.CANCELLED},
    TaskState.DOING:     {TaskState.DONE, TaskState.WAITING, TaskState.TODO, TaskState.CANCELLED},
    TaskState.WAITING:   {TaskState.TODO, TaskState.DOING, TaskState.CANCELLED},
    TaskState.DONE:      {TaskState.TODO},       # Reopen only
    TaskState.CANCELLED: {TaskState.TODO},        # Reinstate only
}

VALID_PLAN_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.DRAFT:     {PlanStatus.ACTIVE, PlanStatus.ARCHIVED},
    PlanStatus.ACTIVE:    {PlanStatus.COMPLETED, PlanStatus.ARCHIVED},
    PlanStatus.COMPLETED: {PlanStatus.ACTIVE},    # Reopen
    PlanStatus.ARCHIVED:  {PlanStatus.ACTIVE},    # Unarchive
}


# ============================================================================
# Criterion Models
# ============================================================================


class CriterionCreate(BaseModel):
    """Input model for creating an acceptance criterion."""
    description: str = Field(..., max_length=settings.CRITERION_DESCRIPTION_MAX_LENGTH)

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()


class CriterionUpdate(BaseModel):
    """PATCH model for updating a criterion."""
    description: str | None = Field(None, max_length=settings.CRITERION_DESCRIPTION_MAX_LENGTH)
    met: bool | None = None

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class Criterion(BaseModel):
    """Full criterion model returned from repository."""
    id: int
    task_id: int
    description: str
    met: bool = False
    met_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Task Dependency Models
# ============================================================================


class TaskDependencyCreate(BaseModel):
    """Input model for adding a dependency."""
    task_id: int
    depends_on_task_id: int

    @field_validator("depends_on_task_id")
    @classmethod
    def cannot_depend_on_self(cls, v: int, info) -> int:
        if info.data.get("task_id") == v:
            raise ValueError("A task cannot depend on itself")
        return v


class TaskDependency(BaseModel):
    """Full dependency model returned from repository."""
    id: int
    task_id: int
    depends_on_task_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Plan Models
# ============================================================================


ExternalRef = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class PlanCreate(BaseModel):
    """Input model for creating a plan."""
    title: str = Field(..., max_length=settings.PLAN_TITLE_MAX_LENGTH)
    project_id: int
    goal: str | None = Field(None, max_length=settings.PLAN_GOAL_MAX_LENGTH)
    context: str | None = Field(None, max_length=settings.PLAN_CONTEXT_MAX_LENGTH)
    status: PlanStatus = PlanStatus.DRAFT
    external_ref: ExternalRef | None = Field(
        default=None,
        description="Opaque, case-sensitive reference unique per user; whitespace trimmed.",
    )

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="Repository/project source (e.g., 'owner/repo')")
    source_files: list[str] | None = Field(default=None, description="Files that informed this (JSON list of paths)")
    source_url: str | None = Field(default=None, max_length=2048, description="URL to original source material")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Encoding confidence score (0.0-1.0)")
    encoding_agent: str | None = Field(default=None, max_length=100, description="Software running the agent")
    encoding_version: str | None = Field(default=None, max_length=50, description="Version of encoding software")
    agent_id: str | None = Field(default=None, max_length=100, description="Agent identity")
    agent_version: str | None = Field(default=None, max_length=50, description="Agent version")
    agent_model: str | None = Field(default=None, max_length=100, description="LLM model used")

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()

    @field_validator("goal", "context")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class PlanUpdate(BaseModel):
    """PATCH model for updating a plan."""
    title: str | None = Field(None, max_length=settings.PLAN_TITLE_MAX_LENGTH)
    goal: str | None = Field(None, max_length=settings.PLAN_GOAL_MAX_LENGTH)
    context: str | None = Field(None, max_length=settings.PLAN_CONTEXT_MAX_LENGTH)
    status: PlanStatus | None = None
    external_ref: ExternalRef | None = Field(
        default=None,
        description="New external reference. Omitted or null leaves the reference unchanged.",
    )

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="New repository source. Unchanged if null.")
    source_files: list[str] | None = Field(default=None, description="New source files. Unchanged if null.")
    source_url: str | None = Field(default=None, max_length=2048, description="New source URL. Unchanged if null.")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="New confidence score. Unchanged if null.")
    encoding_agent: str | None = Field(default=None, max_length=100, description="New encoding agent. Unchanged if null.")
    encoding_version: str | None = Field(default=None, max_length=50, description="New encoding version. Unchanged if null.")
    agent_id: str | None = Field(default=None, max_length=100, description="New agent identity. Unchanged if null.")
    agent_version: str | None = Field(default=None, max_length=50, description="New agent version. Unchanged if null.")
    agent_model: str | None = Field(default=None, max_length=100, description="New LLM model. Unchanged if null.")

    @model_validator(mode="before")
    @classmethod
    def ignore_null_external_ref(cls, data: Any) -> Any:
        """Treat null as omitted for every caller, including REST and direct service calls."""
        if isinstance(data, dict) and data.get("external_ref") is None:
            return {key: value for key, value in data.items() if key != "external_ref"}
        return data

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("goal", "context")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class Plan(PlanCreate):
    """Full plan model returned from repository."""
    id: int
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanSummary(BaseModel):
    """Lightweight plan model for list operations."""
    id: int
    title: str
    project_id: int
    status: PlanStatus
    external_ref: str | None = None
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Task Models
# ============================================================================


class TaskCreate(BaseModel):
    """Input model for creating a task."""
    title: str = Field(..., max_length=settings.TASK_TITLE_MAX_LENGTH)
    plan_id: int
    description: str | None = Field(None, max_length=settings.TASK_DESCRIPTION_MAX_LENGTH)
    priority: TaskPriority = TaskPriority.P2
    assigned_agent: str | None = Field(None, max_length=settings.TASK_AGENT_MAX_LENGTH)
    criteria: list[CriterionCreate] | None = None
    dependency_ids: list[int] | None = None

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="Repository/project source (e.g., 'owner/repo')")
    source_files: list[str] | None = Field(default=None, description="Files that informed this (JSON list of paths)")
    source_url: str | None = Field(default=None, max_length=2048, description="URL to original source material")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Encoding confidence score (0.0-1.0)")
    encoding_agent: str | None = Field(default=None, max_length=100, description="Software running the agent")
    encoding_version: str | None = Field(default=None, max_length=50, description="Version of encoding software")
    agent_id: str | None = Field(default=None, max_length=100, description="Agent identity")
    agent_version: str | None = Field(default=None, max_length=50, description="Agent version")
    agent_model: str | None = Field(default=None, max_length=100, description="LLM model used")

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class TaskUpdate(BaseModel):
    """PATCH model for updating task metadata. State changes go through transition_task."""
    title: str | None = Field(None, max_length=settings.TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(None, max_length=settings.TASK_DESCRIPTION_MAX_LENGTH)
    priority: TaskPriority | None = None

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="New repository source. Unchanged if null.")
    source_files: list[str] | None = Field(default=None, description="New source files. Unchanged if null.")
    source_url: str | None = Field(default=None, max_length=2048, description="New source URL. Unchanged if null.")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="New confidence score. Unchanged if null.")
    encoding_agent: str | None = Field(default=None, max_length=100, description="New encoding agent. Unchanged if null.")
    encoding_version: str | None = Field(default=None, max_length=50, description="New encoding version. Unchanged if null.")
    agent_id: str | None = Field(default=None, max_length=100, description="New agent identity. Unchanged if null.")
    agent_version: str | None = Field(default=None, max_length=50, description="New agent version. Unchanged if null.")
    agent_model: str | None = Field(default=None, max_length=100, description="New LLM model. Unchanged if null.")

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class Task(BaseModel):
    """Full task model returned from repository."""
    id: int
    plan_id: int
    title: str
    description: str | None = None
    state: TaskState = TaskState.TODO
    priority: TaskPriority = TaskPriority.P2
    assigned_agent: str | None = None
    version: int = 1
    criteria: list[Criterion] = Field(default_factory=list)
    dependency_ids: list[int] = Field(default_factory=list)

    # Provenance tracking fields
    source_repo: str | None = None
    source_files: list[str] | None = None
    source_url: str | None = None
    confidence: float | None = None
    encoding_agent: str | None = None
    encoding_version: str | None = None
    agent_id: str | None = None
    agent_version: str | None = None
    agent_model: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """Lightweight task model for list operations."""
    id: int
    title: str
    plan_id: int
    state: TaskState
    priority: TaskPriority
    assigned_agent: str | None = None
    version: int = 1
    criteria_met: int = 0
    criteria_total: int = 0
    blocked: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
