"""Composition root for the Forgetful runtime.

Extracted from main.lifespan() (docs/dev/cli_plan.md phase 1) so every front door —
MCP server, REST API, and CLI — builds the identical adapter/repo/service/registry
stack from one place. Heavy imports stay inside functions to keep module import cheap.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config.logging_config import logging
from app.config.settings import settings
from app.routes.mcp.tool_metadata_registry import register_all_tools_metadata
from app.routes.mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def get_embedding_adapter():
    """Create embedding adapter based on settings."""
    from app.repositories.embeddings.embedding_adapter import (
        AzureOpenAIAdapter,
        FastEmbeddingAdapter,
        GoogleEmbeddingsAdapter,
        OllamaEmbeddingsAdapter,
        OpenAIEmbeddingsAdapter,
    )

    if settings.EMBEDDING_PROVIDER == "Azure":
        return AzureOpenAIAdapter()
    if settings.EMBEDDING_PROVIDER == "Google":
        return GoogleEmbeddingsAdapter()
    if settings.EMBEDDING_PROVIDER == "OpenAI":
        return OpenAIEmbeddingsAdapter()
    if settings.EMBEDDING_PROVIDER == "Ollama":
        return OllamaEmbeddingsAdapter()
    return FastEmbeddingAdapter()


def get_reranker_adapter():
    """Create reranker adapter if enabled."""
    if not settings.RERANKING_ENABLED:
        return None
    if settings.RERANKING_PROVIDER == "HTTP":
        from app.repositories.embeddings.reranker_adapter import HttpRerankAdapter
        return HttpRerankAdapter()
    # Default: FastEmbed
    from app.repositories.embeddings.reranker_adapter import (
        FastEmbedCrossEncoderAdapter,
    )
    return FastEmbedCrossEncoderAdapter(
        cache_dir=settings.FASTEMBED_CACHE_DIR,
    )


def check_first_run_models():
    """Log message on first run when models need to be downloaded."""
    cache_dir = Path(settings.FASTEMBED_CACHE_DIR)
    if not cache_dir.exists() or not any(cache_dir.iterdir()):
        if settings.FASTEMBED_LOCAL_FILES_ONLY:
            logger.info(
                "FastEmbed local-files-only mode enabled - models must already exist in cache",
                extra={"cache_dir": settings.FASTEMBED_CACHE_DIR},
            )
            return
        logger.info("First run detected - downloading embedding models. This may take a minute...")


def create_db_adapter():
    """Create database adapter based on settings."""
    if settings.DATABASE == "Postgres":
        from app.repositories.postgres.postgres_adapter import PostgresDatabaseAdapter
        return PostgresDatabaseAdapter()
    if settings.DATABASE == "SQLite":
        from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
        return SqliteDatabaseAdapter()
    raise ValueError(f"Unsupported DATABASE setting: {settings.DATABASE}. Must be 'Postgres' or 'SQLite'")


def create_repositories(db_adapter, embeddings_adapter, reranker_adapter):
    """Create all repositories based on database setting."""
    if settings.DATABASE == "Postgres":
        from app.repositories.postgres.activity_repository import (
            PostgresActivityRepository,
        )
        from app.repositories.postgres.code_artifact_repository import (
            PostgresCodeArtifactRepository,
        )
        from app.repositories.postgres.document_repository import (
            PostgresDocumentRepository,
        )
        from app.repositories.postgres.entity_repository import PostgresEntityRepository
        from app.repositories.postgres.memory_repository import PostgresMemoryRepository
        from app.repositories.postgres.project_repository import (
            PostgresProjectRepository,
        )
        from app.repositories.postgres.user_repository import PostgresUserRepository

        repos = {
            "user": PostgresUserRepository(db_adapter=db_adapter),
            "memory": PostgresMemoryRepository(
                db_adapter=db_adapter,
                embedding_adapter=embeddings_adapter,
                rerank_adapter=reranker_adapter,
            ),
            "project": PostgresProjectRepository(db_adapter=db_adapter),
            "code_artifact": PostgresCodeArtifactRepository(db_adapter=db_adapter),
            "document": PostgresDocumentRepository(db_adapter=db_adapter),
            "entity": PostgresEntityRepository(db_adapter=db_adapter),
            "activity": PostgresActivityRepository(db_adapter=db_adapter),
        }

        if settings.FILES_ENABLED:
            from app.repositories.postgres.file_repository import PostgresFileRepository
            repos["file"] = PostgresFileRepository(db_adapter=db_adapter)

        if settings.SKILLS_ENABLED:
            from app.repositories.postgres.skill_repository import (
                PostgresSkillRepository,
            )
            repos["skill"] = PostgresSkillRepository(
                db_adapter=db_adapter,
                embedding_adapter=embeddings_adapter,
                rerank_adapter=reranker_adapter,
            )

        if settings.PLANNING_ENABLED:
            from app.repositories.postgres.plan_repository import PostgresPlanRepository
            from app.repositories.postgres.task_repository import PostgresTaskRepository
            repos["plan"] = PostgresPlanRepository(db_adapter=db_adapter)
            repos["task"] = PostgresTaskRepository(db_adapter=db_adapter)

        return repos
    if settings.DATABASE == "SQLite":
        from app.repositories.sqlite.activity_repository import SqliteActivityRepository
        from app.repositories.sqlite.code_artifact_repository import (
            SqliteCodeArtifactRepository,
        )
        from app.repositories.sqlite.document_repository import SqliteDocumentRepository
        from app.repositories.sqlite.entity_repository import SqliteEntityRepository
        from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
        from app.repositories.sqlite.project_repository import SqliteProjectRepository
        from app.repositories.sqlite.user_repository import SqliteUserRepository

        repos = {
            "user": SqliteUserRepository(db_adapter=db_adapter),
            "memory": SqliteMemoryRepository(
                db_adapter=db_adapter,
                embedding_adapter=embeddings_adapter,
                rerank_adapter=reranker_adapter,
            ),
            "project": SqliteProjectRepository(db_adapter=db_adapter),
            "code_artifact": SqliteCodeArtifactRepository(db_adapter=db_adapter),
            "document": SqliteDocumentRepository(db_adapter=db_adapter),
            "entity": SqliteEntityRepository(db_adapter=db_adapter),
            "activity": SqliteActivityRepository(db_adapter=db_adapter),
        }

        if settings.FILES_ENABLED:
            from app.repositories.sqlite.file_repository import SqliteFileRepository
            repos["file"] = SqliteFileRepository(db_adapter=db_adapter)

        if settings.SKILLS_ENABLED:
            from app.repositories.sqlite.skill_repository import SqliteSkillRepository
            repos["skill"] = SqliteSkillRepository(
                db_adapter=db_adapter,
                embedding_adapter=embeddings_adapter,
                rerank_adapter=reranker_adapter,
            )

        if settings.PLANNING_ENABLED:
            from app.repositories.sqlite.plan_repository import SqlitePlanRepository
            from app.repositories.sqlite.task_repository import SqliteTaskRepository
            repos["plan"] = SqlitePlanRepository(db_adapter=db_adapter)
            repos["task"] = SqliteTaskRepository(db_adapter=db_adapter)

        return repos
    raise ValueError(f"Unsupported DATABASE setting: {settings.DATABASE}. Must be 'Postgres' or 'SQLite'")


@dataclass
class Services:
    """Service layer instances; feature-flagged services are None when disabled."""

    user: Any
    memory: Any
    project: Any
    code_artifact: Any
    document: Any
    entity: Any
    graph: Any
    activity: Any
    file: Any | None = None
    skill: Any | None = None
    plan: Any | None = None
    task: Any | None = None


@dataclass
class Runtime:
    """Everything a front door needs to execute tools against the registry."""

    db_adapter: Any
    repos: dict[str, Any]
    services: Services
    registry: ToolRegistry
    permitted_tools: set[str]
    instance_scopes: frozenset[str]
    event_bus: Any | None


async def build_runtime() -> Runtime:
    """Build the full runtime stack: adapters -> repos -> services -> registry -> scopes."""
    check_first_run_models()

    embeddings_adapter = get_embedding_adapter()
    reranker_adapter = get_reranker_adapter()
    logger.info("Embedding adapters initialized")

    db_adapter = create_db_adapter()

    if settings.DATABASE == "SQLite" and not settings.SQLITE_MEMORY:
        data_dir = Path(settings.SQLITE_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory ensured: {data_dir}")

    await db_adapter.init_db()
    logger.info("Database initialized")

    repos = create_repositories(db_adapter, embeddings_adapter, reranker_adapter)

    from app.events import EventBus
    from app.services.activity_service import ActivityService
    from app.services.code_artifact_service import CodeArtifactService
    from app.services.document_service import DocumentService
    from app.services.entity_service import EntityService
    from app.services.graph_service import GraphService
    from app.services.memory_service import MemoryService
    from app.services.project_service import ProjectService
    from app.services.user_service import UserService

    # Create activity service (always available for API queries)
    # Event bus only created when activity tracking is enabled
    activity_service = ActivityService(repos["activity"])
    event_bus = None

    if settings.ACTIVITY_ENABLED:
        event_bus = EventBus()
        event_bus.subscribe("*.*", activity_service.handle_event)
        logger.info("Activity tracking enabled - event bus initialized")
    else:
        logger.info("Activity tracking disabled (ACTIVITY_ENABLED=false) - API available but no events emitted")

    user_service = UserService(repos["user"])
    memory_service = MemoryService(repos["memory"], event_bus=event_bus)
    project_service = ProjectService(repos["project"], event_bus=event_bus)
    code_artifact_service = CodeArtifactService(repos["code_artifact"], event_bus=event_bus)
    document_service = DocumentService(repos["document"], event_bus=event_bus)
    entity_service = EntityService(repos["entity"], event_bus=event_bus)
    # Conditionally create file service behind FILES_ENABLED
    file_service = None

    if settings.FILES_ENABLED:
        from app.services.file_service import FileService
        file_service = FileService(repos["file"], event_bus=event_bus)
        logger.info("Files feature enabled")
    else:
        logger.info("Files feature disabled (FILES_ENABLED=false)")

    # Conditionally create skill service behind SKILLS_ENABLED
    skill_service = None

    if settings.SKILLS_ENABLED:
        from app.services.skill_service import SkillService
        skill_service = SkillService(repos["skill"], event_bus=event_bus)
        logger.info("Skills feature enabled")
    else:
        logger.info("Skills feature disabled (SKILLS_ENABLED=false)")

    # Conditionally create plan/task services behind PLANNING_ENABLED (built before GraphService
    # so they can be passed in as optional services)
    plan_service = None
    task_service = None

    if settings.PLANNING_ENABLED:
        from app.services.plan_service import PlanService
        from app.services.task_service import TaskService

        plan_service = PlanService(repos["plan"], event_bus=event_bus)
        task_service = TaskService(repos["task"], plan_service=plan_service, event_bus=event_bus)
        logger.info("Planning feature enabled")
    else:
        logger.info("Planning feature disabled (PLANNING_ENABLED=false)")

    graph_service = GraphService(
        repos["memory"],
        repos["entity"],
        project_service=project_service,
        document_service=document_service,
        code_artifact_service=code_artifact_service,
        file_service=file_service,
        skill_service=skill_service,
        plan_service=plan_service,
        task_service=task_service,
    )

    registry = ToolRegistry()
    register_all_tools_metadata(
        registry=registry,
        user_service=user_service,
        memory_service=memory_service,
        project_service=project_service,
        code_artifact_service=code_artifact_service,
        document_service=document_service,
        entity_service=entity_service,
        plan_service=plan_service,
        task_service=task_service,
        file_service=file_service,
        skill_service=skill_service,
    )

    categories = registry.list_categories()
    total_tools = sum(categories.values())
    logger.info(f"Tool registration complete: {total_tools} tools across {len(categories)} categories")
    logger.info(f"Categories: {categories}")

    # Resolve instance-level scope ceiling
    from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools
    instance_scopes = parse_scopes(settings.FORGETFUL_SCOPES)
    permitted_tools = resolve_permitted_tools(instance_scopes, registry)
    logger.info(f"Scoped permissions: scopes={list(instance_scopes)}, permitted_tools={len(permitted_tools)}")

    services = Services(
        user=user_service,
        memory=memory_service,
        project=project_service,
        code_artifact=code_artifact_service,
        document=document_service,
        entity=entity_service,
        graph=graph_service,
        activity=activity_service,
        file=file_service,
        skill=skill_service,
        plan=plan_service,
        task=task_service,
    )

    return Runtime(
        db_adapter=db_adapter,
        repos=repos,
        services=services,
        registry=registry,
        permitted_tools=permitted_tools,
        instance_scopes=instance_scopes,
        event_bus=event_bus,
    )


async def dispose_runtime(runtime: Runtime) -> None:
    """Drain in-flight events, then close the DB. Safe to call more than once.

    Draining matters for one-shot consumers (the CLI): activity handlers are
    fire-and-forget tasks, and asyncio.run() would cancel any still pending.
    """
    if runtime.event_bus is not None:
        await runtime.event_bus.wait_for_pending()
    await runtime.db_adapter.dispose()
