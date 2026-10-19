"""Vulture whitelist: names that look unused but are used dynamically.

Each group needs a comment saying who consumes the names (framework hook, pydantic field,
ORM mapper ...). Prefer deleting genuinely dead code over listing it here, and prefer
``[tool.vulture]`` in pyproject.toml for hook names that apply to a whole class of code
(validators, route decorators, alembic/SQLAlchemy/stdlib hooks). Vulture does not scan
``tests/``, so a name only the tests read cannot be a vulture "use".

This file is only parsed by vulture and never imported or executed (pydantic fields are
not class attributes at runtime); the real imports keep each entry tied to its owner.
"""
from app.config.settings import Settings
from app.events.event_bus import EventBus
from app.middleware.auth import TokenCache
from app.models.activity_models import ActorType
from app.models.activity_models import EntityType as ActivityEntityType
from app.models.entity_models import EntityType
from app.models.graph_models import SubgraphMeta
from app.models.memory_models import Memory, MemoryScore, MemorySummary, ObsoleteMatch
from app.models.plan_models import TaskPriority
from app.models.project_models import ProjectType
from app.models.user_models import UserCreate, UserUpdate
from app.repositories.postgres import postgres_tables
from app.repositories.sqlite import sqlite_tables
from app.routes.cli.remote_executor import RemoteExecutor
from test_harness.report import ReportIssue, ReportStep, WalkthroughReport

# --- pydantic-settings fields, populated from the environment / .env files ------------
# ENCODING_* and AGENT_* are read by name through getattr(settings, ...) via
# PROVENANCE_ENV_MAP in app/utils/provenance.py. SERVICE_DESCRIPTION and
# OAUTH_STORAGE_PATH are documented in docs/configuration.md and pinned by the
# test_settings_defaults snapshot; no application code reads them.
Settings.SERVICE_DESCRIPTION
Settings.OAUTH_STORAGE_PATH
Settings.ENCODING_AGENT
Settings.ENCODING_VERSION
Settings.AGENT_ID
Settings.AGENT_VERSION
Settings.AGENT_MODEL

# --- StrEnum members: the stored / API vocabulary (a value domain, not code paths) ----
# Members are persisted in the database and accepted or returned by the REST and MCP
# interfaces, so removing an unreferenced one would change what clients may send.
ActivityEntityType.CRITERION
ActivityEntityType.TASK_DEPENDENCY
ActorType.SYSTEM
ActorType.LLM_MAINTENANCE
EntityType.ORGANIZATION
EntityType.INDIVIDUAL
EntityType.TEAM
EntityType.DEVICE
EntityType.SYSTEM
TaskPriority.P0
TaskPriority.P1
TaskPriority.P3
ProjectType.PERSONAL
ProjectType.WORK
ProjectType.LEARNING
ProjectType.DEVELOPMENT
ProjectType.INFRASTRUCTURE
ProjectType.TEMPLATE
ProjectType.PRODUCT
ProjectType.MARKETING
ProjectType.FINANCE
ProjectType.DOCUMENTATION
ProjectType.DEVELOPMENT_ENVIRONMENT
ProjectType.THIRD_PARTY_LIBRARY
ProjectType.OPEN_SOURCE

# --- pydantic model fields, serialised in REST / MCP responses and report files -------
# SubgraphMeta.edge_count is passed by keyword in graph_service and returned in the response.
# The test_harness report models are validated from the agent-written report.json.
SubgraphMeta.edge_count
Memory.last_accessed_at
MemorySummary.similarity
MemoryScore.similarity
MemoryScore.rerank_score
ObsoleteMatch.similarity
UserCreate.idp_metadata
UserUpdate.idp_metadata
ReportStep.commands
ReportStep.observed
ReportIssue.severity
ReportIssue.what
ReportIssue.evidence
WalkthroughReport.steps

# --- SQLAlchemy ORM columns and relationships ------------------------------------------
# Columns are the table schema (pinned by the schema snapshots and the alembic revisions);
# values are written through mapped keyword arguments and read by the mapper. The
# relationship names are the back_populates targets of the other side of the mapping.
sqlite_tables.UsersTable.idp_metadata
sqlite_tables.MemoryTable.last_accessed_at
sqlite_tables.EntitiesTable.outgoing_relationships
sqlite_tables.EntitiesTable.incoming_relationships
postgres_tables.UsersTable.idp_metadata
postgres_tables.MemoryTable.last_accessed_at
postgres_tables.EntitiesTable.outgoing_relationships
postgres_tables.EntitiesTable.incoming_relationships

# --- Read-only observation accessors that the tests of live behaviour assert on -------
# Nothing in production calls these; they expose state that tests/ read to prove the
# cache hit/miss counts, the SSE subscriber clean-up, the per-user sequence counter and
# which bearer token the CLI selected. vulture does not scan tests/.
TokenCache.stats
EventBus.stream_subscriber_count
EventBus.get_current_seq
RemoteExecutor._token
