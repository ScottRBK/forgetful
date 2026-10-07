# Mermaid class diagrams

Declared types and signatures; unknown types are `unknown`. Receivers are omitted.
Fields are associations, not lifetime ownership. Calls are static heuristic estimates.
Members and connections within each view are uncapped.
Parallel arrows are summarized.
Cross-diagram relationships are retained in the complete relationship list.

Included: 295 boxes. Calls without in-scope endpoints: 0.

## Test filtering

Mode: exclude.
Saved detector version: 2.
Test paths: `test_harness/runs`, `tests`.
Keep paths: none.
Calls removed by test filtering: 4502. Type relationships removed: 119.

-
  `test_harness/runs/20260710-211850-opencode/forgetful-encode-repo/workspace/fixture-repo/src/calc.
  py`: 3 source occurrences (test-path).
- `test_harness/runs/20260710-223528-opencode/harness/runner.py`: 6 source occurrences (test-path).
- `test_harness/runs/20260711-085317-opencode/harness/runner.py`: 6 source occurrences (test-path).
-
  `test_harness/runs/20260711-085317-opencode/skills/forgetful-encode-repo/workspace/fixture-repo/sr
  c/calc.py`: 3 source occurrences (test-path).
- `tests/e2e/conftest.py`: 21 source occurrences (test-path).
- `tests/e2e/test_api_activity.py`: 45 source occurrences (test-path).
- `tests/e2e/test_api_memories_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_auth_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_auto_link_threshold_e2e.py`: 6 source occurrences (test-path).
- `tests/e2e/test_cli_postgres_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_code_artifact_tools_e2e.py`: 8 source occurrences (test-path).
- `tests/e2e/test_document_tools_e2e.py`: 8 source occurrences (test-path).
- `tests/e2e/test_entity_tools_e2e.py`: 36 source occurrences (test-path).
- `tests/e2e/test_file_tools_e2e.py`: 12 source occurrences (test-path).
- `tests/e2e/test_graph_e2e.py`: 47 source occurrences (test-path).
- `tests/e2e/test_health_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_link_memories_no_autolink_e2e.py`: 9 source occurrences (test-path).
- `tests/e2e/test_memory_tools_e2e.py`: 39 source occurrences (test-path).
- `tests/e2e/test_memory_usage_e2e.py`: 3 source occurrences (test-path).
- `tests/e2e/test_memory_usage_tracking_disabled_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_meta_tools_e2e.py`: 17 source occurrences (test-path).
- `tests/e2e/test_obsolete_matches_e2e.py`: 2 source occurrences (test-path).
- `tests/e2e/test_plan_tools_e2e.py`: 11 source occurrences (test-path).
- `tests/e2e/test_project_tools_e2e.py`: 21 source occurrences (test-path).
- `tests/e2e/test_provenance_e2e.py`: 13 source occurrences (test-path).
- `tests/e2e/test_re_embedding_e2e.py`: 11 source occurrences (test-path).
- `tests/e2e/test_reranking_e2e.py`: 4 source occurrences (test-path).
- `tests/e2e/test_retrieval_scores_e2e.py`: 3 source occurrences (test-path).
- `tests/e2e/test_skill_tools_e2e.py`: 24 source occurrences (test-path).
- `tests/e2e/test_task_tools_e2e.py`: 19 source occurrences (test-path).
- `tests/e2e/test_user_tools_e2e.py`: 4 source occurrences (test-path).
- `tests/e2e/test_zz_backup_restore_e2e.py`: 8 source occurrences (test-path).
- `tests/e2e_sqlite/conftest.py`: 12 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_activity_sqlite.py`: 25 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_auth.py`: 14 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_code_artifacts.py`: 17 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_documents.py`: 17 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_entities.py`: 33 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_files.py`: 18 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_graph.py`: 128 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_graph_limit_settings.py`: 4 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_memories.py`: 47 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_plans.py`: 2 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_projects.py`: 21 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_skills.py`: 42 source occurrences (test-path).
- `tests/e2e_sqlite/test_api_tasks.py`: 2 source occurrences (test-path).
- `tests/e2e_sqlite/test_auth_cache_sqlite.py`: 8 source occurrences (test-path).
- `tests/e2e_sqlite/test_auth_sqlite.py`: 6 source occurrences (test-path).
- `tests/e2e_sqlite/test_auto_link_threshold_sqlite.py`: 7 source occurrences (test-path).
- `tests/e2e_sqlite/test_cli_passthrough.py`: 12 source occurrences (test-path).
- `tests/e2e_sqlite/test_cli_remote.py`: 10 source occurrences (test-path).
- `tests/e2e_sqlite/test_cli_verbs.py`: 12 source occurrences (test-path).
- `tests/e2e_sqlite/test_code_artifact_tools_sqlite.py`: 8 source occurrences (test-path).
- `tests/e2e_sqlite/test_document_tools_sqlite.py`: 9 source occurrences (test-path).
- `tests/e2e_sqlite/test_entity_tools_sqlite.py`: 48 source occurrences (test-path).
- `tests/e2e_sqlite/test_feature_flags_sqlite.py`: 7 source occurrences (test-path).
- `tests/e2e_sqlite/test_file_tools_sqlite.py`: 10 source occurrences (test-path).
- `tests/e2e_sqlite/test_harness_server.py`: 2 source occurrences (test-path).
- `tests/e2e_sqlite/test_health_sqlite.py`: 2 source occurrences (test-path).
- `tests/e2e_sqlite/test_link_memories_no_autolink_sqlite.py`: 11 source occurrences (test-path).
- `tests/e2e_sqlite/test_memory_file_ids_sqlite.py`: 13 source occurrences (test-path).
- `tests/e2e_sqlite/test_memory_tools_sqlite.py`: 42 source occurrences (test-path).
- `tests/e2e_sqlite/test_meta_tools_sqlite.py`: 18 source occurrences (test-path).
- `tests/e2e_sqlite/test_obsolete_matches_sqlite.py`: 8 source occurrences (test-path).
- `tests/e2e_sqlite/test_plan_tools_sqlite.py`: 12 source occurrences (test-path).
- `tests/e2e_sqlite/test_project_tools_sqlite.py`: 21 source occurrences (test-path).
- `tests/e2e_sqlite/test_provenance_sqlite.py`: 16 source occurrences (test-path).
- `tests/e2e_sqlite/test_re_embedding_sqlite.py`: 15 source occurrences (test-path).
- `tests/e2e_sqlite/test_reranking_concurrency_sqlite.py`: 3 source occurrences (test-path).
- `tests/e2e_sqlite/test_reranking_sqlite.py`: 5 source occurrences (test-path).
- `tests/e2e_sqlite/test_retrieval_scores_sqlite.py`: 6 source occurrences (test-path).
- `tests/e2e_sqlite/test_scoped_permissions_sqlite.py`: 15 source occurrences (test-path).
- `tests/e2e_sqlite/test_skill_tools_sqlite.py`: 19 source occurrences (test-path).
- `tests/e2e_sqlite/test_task_tools_sqlite.py`: 21 source occurrences (test-path).
- `tests/e2e_sqlite/test_user_tools_sqlite.py`: 4 source occurrences (test-path).
- `tests/integration/conftest.py`: 230 source occurrences (test-path).
- `tests/integration/test_auth.py`: 23 source occurrences (test-path).
- `tests/integration/test_auth_cache.py`: 23 source occurrences (test-path).
- `tests/integration/test_auth_factory.py`: 24 source occurrences (test-path).
- `tests/integration/test_auth_info.py`: 27 source occurrences (test-path).
- `tests/integration/test_backup_service.py`: 8 source occurrences (test-path).
- `tests/integration/test_bootstrap.py`: 6 source occurrences (test-path).
- `tests/integration/test_cli_dispatch.py`: 14 source occurrences (test-path).
- `tests/integration/test_cli_local_executor.py`: 6 source occurrences (test-path).
- `tests/integration/test_cli_remote_executor.py`: 49 source occurrences (test-path).
- `tests/integration/test_cli_verbs_mapping.py`: 16 source occurrences (test-path).
- `tests/integration/test_code_artifact_service.py`: 9 source occurrences (test-path).
- `tests/integration/test_config_precedence.py`: 4 source occurrences (test-path).
- `tests/integration/test_document_service.py`: 9 source occurrences (test-path).
- `tests/integration/test_entity_service.py`: 51 source occurrences (test-path).
- `tests/integration/test_event_bus.py`: 22 source occurrences (test-path).
- `tests/integration/test_fastembed_offline.py`: 12 source occurrences (test-path).
- `tests/integration/test_file_service.py`: 15 source occurrences (test-path).
- `tests/integration/test_graph_service_plan_task.py`: 33 source occurrences (test-path).
- `tests/integration/test_harness_cli.py`: 5 source occurrences (test-path).
- `tests/integration/test_harness_config.py`: 8 source occurrences (test-path).
- `tests/integration/test_harness_container.py`: 10 source occurrences (test-path).
- `tests/integration/test_harness_report.py`: 11 source occurrences (test-path).
- `tests/integration/test_harness_walkthrough.py`: 24 source occurrences (test-path).
- `tests/integration/test_http_reranker_adapter.py`: 12 source occurrences (test-path).
- `tests/integration/test_local_reranker_concurrency.py`: 19 source occurrences (test-path).
- `tests/integration/test_memory_service.py`: 25 source occurrences (test-path).
- `tests/integration/test_memory_usage_tracking.py`: 5 source occurrences (test-path).
- `tests/integration/test_meta_tools_docstrings.py`: 32 source occurrences (test-path).
- `tests/integration/test_obsolete_warning_gate.py`: 5 source occurrences (test-path).
- `tests/integration/test_obsolete_warning_settings.py`: 6 source occurrences (test-path).
- `tests/integration/test_ollama_embeddings_adapter.py`: 8 source occurrences (test-path).
- `tests/integration/test_onnx_providers.py`: 21 source occurrences (test-path).
- `tests/integration/test_openai_embeddings_adapter.py`: 12 source occurrences (test-path).
- `tests/integration/test_plan_service.py`: 12 source occurrences (test-path).
- `tests/integration/test_project_service.py`: 27 source occurrences (test-path).
- `tests/integration/test_provenance.py`: 21 source occurrences (test-path).
- `tests/integration/test_re_embedding_service.py`: 18 source occurrences (test-path).
- `tests/integration/test_rest_auth.py`: 23 source occurrences (test-path).
- `tests/integration/test_scope_resolver.py`: 41 source occurrences (test-path).
- `tests/integration/test_service_activity_events.py`: 18 source occurrences (test-path).
- `tests/integration/test_skill_frontmatter_quoting.py`: 8 source occurrences (test-path).
- `tests/integration/test_skill_service.py`: 38 source occurrences (test-path).
- `tests/integration/test_targeted_rebuild_sqlite.py`: 22 source occurrences (test-path).
- `tests/integration/test_task_service.py`: 22 source occurrences (test-path).
- `tests/integration/test_tool_registry.py`: 32 source occurrences (test-path).
- `tests/integration/test_user_service.py`: 7 source occurrences (test-path).

## Diagram 1

```mermaid
classDiagram
    direction TB
    class c0000["alembic/_db_helpers/db_postgres_impl.py"] {
        <<module>>
        +upgrade_postgres() None
        +downgrade_postgres() None
    }
    class c0001["alembic/_db_helpers/db_sqlite_impl.py"] {
        <<module>>
        +upgrade_sqlite() None
        +downgrade_sqlite() None
    }
    class c0002["alembic/env.py"] {
        <<module>>
        +run_migrations_offline() None
        +do_run_migrations(connection: Connection) None
        +run_async_migrations() None
        +run_migrations_online() None
    }
    class c0003["alembic/versions/0c7b964dd1e7_initial_schema_with_entity_many_to_many.py"] {
        <<module>>
        -_load_helper_module(module_name: str) unknown
        +upgrade() None
        +downgrade() None
    }
    class c0004["alembic/versions/20251216143413_add_aka_to_entities.py"] {
        <<module>>
        +upgrade() None
        +downgrade() None
    }
    class c0005["alembic/versions/20260106_add_activity_log_table.py"] {
        <<module>>
        -_get_user_id_type() unknown
        +upgrade() None
        +downgrade() None
    }
    class c0006["alembic/versions/20260106_add_provenance_tracking_to_memories.py"] {
        <<module>>
        +upgrade() None
        +downgrade() None
    }
    class c0007["alembic/versions/20260312_add_plans_tasks_criteria_dependencies.py"] {
        <<module>>
        -_get_user_id_type() unknown
        +upgrade() None
        +downgrade() None
    }
    class c0008["alembic/versions/20260315_add_files_table.py"] {
        <<module>>
        -_get_user_id_type() unknown
        -_get_tags_column() unknown
        +upgrade() None
        +downgrade() None
    }
    class c0009["alembic/versions/20260321_add_skills_table.py"] {
        <<module>>
        -_get_user_id_type() unknown
        -_get_tags_column() unknown
        -_get_allowed_tools_column() unknown
        -_get_metadata_column() unknown
        +upgrade() None
        +downgrade() None
    }
    class c0010["alembic/versions/20260408_add_provenance_to_all_object_types.py"] {
        <<module>>
        -_add_source_files_column(table_name: str) None
        -_add_full_provenance(table_name: str) None
        -_drop_full_provenance(table_name: str) None
        +upgrade() None
        +downgrade() None
    }
    class c0011["alembic/versions/20260704_add_memory_usage_tracking.py"] {
        <<module>>
        +upgrade() None
        +downgrade() None
    }
    class c0012["alembic/versions/20260822_add_project_last_encoding_point.py"] {
        <<module>>
        +upgrade() None
        +downgrade() None
    }
    class c0013["Runtime"] {
        <<class>>
        +db_adapter: Any
        +repos: Type1
        +services: Services
        +registry: ToolRegistry
        +permitted_tools: set[str]
        +instance_scopes: frozenset[str]
        +event_bus: Type2
    }
    class c0014["Services"] {
        <<class>>
        +user: Any
        +memory: Any
        +project: Any
        +code_artifact: Any
        +document: Any
        +entity: Any
        +graph: Any
        +activity: Any
        +file: Type2
        +skill: Type2
        +plan: Type2
        +task: Type2
    }
    class c0015["app/bootstrap.py"] {
        <<module>>
        +get_embedding_adapter() unknown
        +get_reranker_adapter() unknown
        +check_first_run_models() unknown
        +create_db_adapter() unknown
        +create_repositories(Signature1)
        +build_runtime() Runtime
        +dispose_runtime(runtime: Runtime) None
    }
    class c0016["app/config/auth.py"] {
        <<module>>
        -_register(class_path: str) unknown
        -_required(value: str, field_name: str) str
        -_scopes(raw: str) Type3
        -_build_github() unknown
        -_build_google() unknown
        -_build_jwt() unknown
        -_build_introspection() unknown
        +build_auth_provider() unknown
    }
    class c0017["ConsoleFormatter"] {
        <<class>>
        +COLOURS: unknown
        +RESET: unknown
        +format(record: logging.LogRecord) str
    }
    class c0018["JSONFormatter"] {
        <<class>>
        +format(record: logging.LogRecord) str
    }
    class c0019["SensitiveDataFilter"] {
        <<class>>
        +SENSITIVE_PATTERNS: unknown
        +filter(record: logging.LogRecord) bool
        -_mask_value(value: unknown) unknown
    }
    class c0020["app/config/logging_config.py"] {
        <<module>>
        -_serialise_log_value(obj: unknown) unknown
        +configure_logging(log_level: str, log_format: str) logging.handlers.QueueListener
        +shutdown_logging() unknown
    }
    class c0021["Settings"] {
        <<class>>
        +SERVICE_NAME: str
        +SERVICE_VERSION: str
        +SERVICE_DESCRIPTION: str
        +SERVER_HOST: str
        +SERVER_PORT: int
        +LOG_LEVEL: str
        +LOG_FORMAT: str
        +CORS_ENABLED: bool
        +CORS_ORIGINS: list[str]
        +DATABASE: str
        +POSTGRES_HOST: str
        +PGPORT: int
        +POSTGRES_DB: str
        +POSTGRES_USER: str
        +POSTGRES_PASSWORD: str
        +SQLITE_PATH: str
        +SQLITE_MEMORY: bool
        +DB_LOGGING: bool
        +DEFAULT_USER_ID: str
        +DEFAULT_USER_NAME: str
        +DEFAULT_USER_EMAIL: str
        +FASTMCP_SERVER_AUTH: str
        +FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID: str
        +FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET: str
        +FASTMCP_SERVER_AUTH_GITHUB_BASE_URL: str
        +FASTMCP_SERVER_AUTH_GITHUB_REQUIRED_SCOPES: str
        +FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID: str
        +FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET: str
        +FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL: str
        +FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES: str
        +FASTMCP_SERVER_AUTH_JWT_JWKS_URI: str
        +FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY: str
        +FASTMCP_SERVER_AUTH_JWT_ISSUER: str
        +FASTMCP_SERVER_AUTH_JWT_AUDIENCE: str
        +FASTMCP_SERVER_AUTH_JWT_REQUIRED_SCOPES: str
        +FASTMCP_SERVER_AUTH_INTROSPECTION_URL: str
        +FASTMCP_SERVER_AUTH_INTROSPECTION_CLIENT_ID: str
        +FASTMCP_SERVER_AUTH_INTROSPECTION_CLIENT_SECRET: str
        +FASTMCP_SERVER_AUTH_INTROSPECTION_REQUIRED_SCOPES: str
        +OAUTH_STORAGE_PATH: str
        +TOKEN_CACHE_ENABLED: bool
        +TOKEN_CACHE_TTL_SECONDS: int
        +TOKEN_CACHE_MAX_SIZE: int
        +FORGETFUL_SCOPES: str
        +FORGETFUL_SERVER: str
        +MCP_DESCRIPTOR_MODE: str
        +MEMORY_TITLE_MAX_LENGTH: int
        +MEMORY_CONTENT_MAX_LENGTH: int
        +MEMORY_CONTEXT_MAX_LENGTH: int
        +MEMORY_KEYWORDS_MAX_COUNT: int
        +MEMORY_TAGS_MAX_COUNT: int
        +MEMORY_TOKEN_BUDGET: int
        +MEMORY_MAX_MEMORIES: int
        +MEMORY_NUM_AUTO_LINK: int
        +MEMORY_SIMILARITY_THRESHOLD: float
        +OBSOLETE_WARNING_ENABLED: bool
        +OBSOLETE_WARNING_THRESHOLD: float
        +PROJECT_DESCRIPTION_MAX_LENGTH: int
        +PROJECT_NOTES_MAX_LENGTH: int
        +CODE_ARTIFACT_TITLE_MAX_LENGTH: int
        +CODE_ARTIFACT_DESCRIPTION_MAX_LENGTH: int
        +CODE_ARTIFACT_CODE_MAX_LENGTH: int
        +CODE_ARTIFACT_TAGS_MAX_COUNT: int
        +DOCUMENT_TITLE_MAX_LENGTH: int
        +DOCUMENT_DESCRIPTION_MAX_LENGTH: int
        +DOCUMENT_CONTENT_MAX_LENGTH: int
        +DOCUMENT_TAGS_MAX_COUNT: int
        +FILES_ENABLED: bool
        +FILE_MAX_SIZE_BYTES: int
        +FILE_FILENAME_MAX_LENGTH: int
        +FILE_DESCRIPTION_MAX_LENGTH: int
        +FILE_TAGS_MAX_COUNT: int
        +ENTITY_NAME_MAX_LENGTH: int
        +ENTITY_TYPE_MAX_LENGTH: int
        +ENTITY_NOTES_MAX_LENGTH: int
        +ENTITY_TAGS_MAX_COUNT: int
        +ENTITY_AKA_MAX_COUNT: int
        +ENTITY_RELATIONSHIP_TYPE_MAX_LENGTH: int
        +PLANNING_ENABLED: bool
        +PLAN_TITLE_MAX_LENGTH: int
        +PLAN_GOAL_MAX_LENGTH: int
        +PLAN_CONTEXT_MAX_LENGTH: int
        +TASK_TITLE_MAX_LENGTH: int
        +TASK_DESCRIPTION_MAX_LENGTH: int
        +TASK_AGENT_MAX_LENGTH: int
        +CRITERION_DESCRIPTION_MAX_LENGTH: int
        +SKILLS_ENABLED: bool
        +SKILL_NAME_MAX_LENGTH: int
        +SKILL_DESCRIPTION_MAX_LENGTH: int
        +SKILL_CONTENT_MAX_LENGTH: int
        +SKILL_LICENSE_MAX_LENGTH: int
        +SKILL_COMPATIBILITY_MAX_LENGTH: int
        +SKILL_ALLOWED_TOOLS_MAX_LENGTH: int
        +SKILL_TAGS_MAX_COUNT: int
        +ENCODING_AGENT: str
        +ENCODING_VERSION: str
        +AGENT_ID: str
        +AGENT_VERSION: str
        +AGENT_MODEL: str
        +ENFORCE_ENV_OVERWRITE: bool
        +ACTIVITY_ENABLED: bool
        +ACTIVITY_RETENTION_DAYS: Type4
        +ACTIVITY_TRACK_READS: bool
        +SSE_MAX_QUEUE_SIZE: int
        +MAX_GRAPH_LIMIT: int
        +EMBEDDING_PROVIDER: str
        +EMBEDDING_MODEL: str
        +EMBEDDING_DIMENSIONS: int
        +EMBEDDING_ONNX_PROVIDERS: str
        +AZURE_ENDPOINT: str
        +AZURE_DEPLOYMENT: str
        +AZURE_API_VERSION: str
        +AZURE_API_KEY: str
        +GOOGLE_AI_API_KEY: str
        +OPENAI_API_KEY: str
        +OPENAI_BASE_URL: str
        +OPENAI_SUPPORTS_DIMENSIONS: bool
        +OLLAMA_BASE_URL: str
        +RERANKING_ENABLED: bool
        +RERANKING_PROVIDER: str
        +RERANKING_URL: str
        +RERANKING_API_KEY: str
        +RERANKING_MODEL: str
        +RERANKING_THREADS: int
        +RERANKING_WORKERS: int
        +RERANKING_ONNX_PROVIDERS: str
        +DENSE_SEARCH_CANDIDATES: int
        +FASTEMBED_CACHE_DIR: str
        +FASTEMBED_LOCAL_FILES_ONLY: bool
        -_validate_obsolete_warning_threshold(value: float) float
        -_validate_onnx_providers(value: str) str
        +embedding_onnx_providers: Type3
        +reranking_onnx_providers: Type3
        +model_config: unknown
    }
    class c0022["app/config/settings.py"] {
        <<module>>
        +parse_onnx_providers(value: Type5) Type3
    }
    class c0023["EventBus"] {
        <<class>>
        -__init__(max_queue_size: int) None
        -_subscribers: Type6
        -_pending_tasks: set[asyncio.Task[None]]
        -_stream_subscribers: Type7
        -_sequences: Type8
        -_stream_lock: unknown
        -_max_queue_size: unknown
        +subscribe(pattern: str, handler: EventHandler) None
        -_subscribers#91;pattern#93;: unknown
        +unsubscribe(pattern: str, handler: EventHandler) bool
        +emit(event: ActivityEvent) None
        -_safe_dispatch(handler: EventHandler, event: ActivityEvent) None
        +wait_for_pending(timeout: Type9) None
        +subscriber_count(pattern: Type5) int
        +clear() None
        +subscribe_stream(user_id: UUID) Type10
        -_stream_subscribers#91;user_id_str#93;: unknown
        -_emit_to_streams(event: ActivityEvent) None
        -_next_seq(user_id: str) int
        -_sequences#91;user_id#93;: unknown
        +stream_subscriber_count(user_id: Type5) int
        +get_current_seq(user_id: str) int
    }
    class c0024["ConflictError"] {
        <<class>>
    }
    class c0025["CyclicDependencyError"] {
        <<class>>
    }
    class c0026["DependencyNotMetError"] {
        <<class>>
    }
    class c0027["InvalidStateTransitionError"] {
        <<class>>
    }
    class c0028["NotFoundError"] {
        <<class>>
    }
    class c0029["CacheEntry"] {
        <<class>>
        +user: User
        +expires_at: float
    }
    class c0030["TokenCache"] {
        <<class>>
        -__init__(ttl_seconds: int, max_size: int) unknown
        -_cache: Type11
        -_lock: unknown
        -_ttl: unknown
        -_max_size: unknown
        -_hits: unknown
        -_misses: unknown
        -_hash_token(token: str) str
        +get(token: str) Type12
        +set(token: str, user: User) None
        -_cache#91;key#93;: unknown
        +invalidate(token: str) None
        +clear() None
        +stats: dict
    }
    class c0031["app/middleware/auth.py"] {
        <<module>>
        +get_user_from_auth(ctx: Context) User
        +get_user_from_request(request: Request, mcp: FastMCP) User
    }
    class c0032["app/middleware/logging_middleware.py"] {
        <<module>>
        +get_request_id() Type5
        +set_request_id(request_id: str) None
        +get_user_id() Type5
        +set_user_id(user_id: str) None
    }
    class c0033["ActionType"] {
        <<class>>
        +CREATED: unknown
        +UPDATED: unknown
        +DELETED: unknown
        +READ: unknown
        +QUERIED: unknown
    }
    class c0034["ActivityEvent"] {
        <<class>>
        +entity_type: EntityType
        +entity_id: int
        +action: ActionType
        +changes: Type13
        +snapshot: Type1
        +actor: ActorType
        +actor_id: Type5
        +metadata: Type14
        +created_at: datetime
        +user_id: Type5
        +model_config: unknown
    }
    class c0035["ActivityListResponse"] {
        <<class>>
        +events: list[ActivityLogEntry]
        +total: int
        +limit: int
        +offset: int
        +model_config: unknown
    }
    class c0036["ActivityLogEntry"] {
        <<class>>
        +id: int
        +user_id: str
        +entity_type: EntityType
        +entity_id: int
        +action: ActionType
        +changes: Type13
        +snapshot: Type1
        +actor: ActorType
        +actor_id: Type5
        +metadata: Type14
        +created_at: datetime
        +model_config: unknown
    }
    class c0037["ActorType"] {
        <<class>>
        +USER: unknown
        +SYSTEM: unknown
        +LLM_MAINTENANCE: unknown
    }
    class c0038["EntityType"] {
        <<class>>
        +MEMORY: unknown
        +PROJECT: unknown
        +DOCUMENT: unknown
        +CODE_ARTIFACT: unknown
        +ENTITY: unknown
        +LINK: unknown
        +ENTITY_MEMORY_LINK: unknown
        +ENTITY_RELATIONSHIP: unknown
        +ENTITY_PROJECT_LINK: unknown
        +PLAN: unknown
        +TASK: unknown
        +CRITERION: unknown
        +TASK_DEPENDENCY: unknown
        +FILE: unknown
        +SKILL: unknown
    }
    class c0039["CodeArtifact"] {
        <<class>>
        +id: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0040["CodeArtifactCreate"] {
        <<class>>
        +title: str
        +description: str
        +code: str
        +language: str
        +tags: list[str]
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +lowercase_language(v: unknown) unknown
        +validate_tags(v: unknown) unknown
    }
    class c0041["CodeArtifactSummary"] {
        <<class>>
        +id: int
        +title: str
        +description: str
        +language: str
        +tags: list[str]
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0042["CodeArtifactUpdate"] {
        <<class>>
        +title: Type5
        +description: Type5
        +code: Type5
        +language: Type5
        +tags: Type3
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +lowercase_language(v: unknown) unknown
        +validate_tags(v: unknown) unknown
    }
    class c0043["Document"] {
        <<class>>
        +id: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0044["DocumentCreate"] {
        <<class>>
        +title: str
        +description: str
        +content: str
        +document_type: Type5
        +filename: Type5
        +size_bytes: Type4
        +tags: list[str]
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
        +calculate_size_bytes(v: unknown, info: unknown) unknown
    }
    class c0045["DocumentSummary"] {
        <<class>>
        +id: int
        +title: str
        +description: str
        +document_type: Type5
        +filename: Type5
        +size_bytes: int
        +tags: list[str]
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0046["DocumentUpdate"] {
        <<class>>
        +title: Type5
        +description: Type5
        +content: Type5
        +document_type: Type5
        +filename: Type5
        +size_bytes: Type4
        +tags: Type3
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
    }
    class c0047["Entity"] {
        <<class>>
        +id: int
        +project_ids: Type15
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0048["EntityCreate"] {
        <<class>>
        +name: str
        +entity_type: EntityType
        +custom_type: Type5
        +notes: Type5
        +tags: list[str]
        +aka: list[str]
        +project_ids: Type15
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
        +validate_aka(v: unknown) unknown
        +validate_custom_type() unknown
    }
    class c0049["EntityListResponse"] {
        <<class>>
        +entities: list[EntitySummary]
        +total: int
        +limit: int
        +offset: int
    }
    class c0050["EntityRelationship"] {
        <<class>>
        +id: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0051["EntityRelationshipCreate"] {
        <<class>>
        +source_entity_id: int
        +target_entity_id: int
        +relationship_type: str
        +strength: Type9
        +confidence: Type9
        +metadata: Type14
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown) unknown
        +validate_different_entities() unknown
    }
    class c0052["EntityRelationshipUpdate"] {
        <<class>>
        +relationship_type: Type5
        +strength: Type9
        +confidence: Type9
        +metadata: Type14
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown) unknown
    }
    class c0053["EntitySummary"] {
        <<class>>
        +id: int
        +name: str
        +entity_type: EntityType
        +custom_type: Type5
        +tags: list[str]
        +aka: list[str]
        +project_ids: Type15
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0054["EntityType"] {
        <<class>>
        +ORGANIZATION: unknown
        +INDIVIDUAL: unknown
        +TEAM: unknown
        +DEVICE: unknown
        +SYSTEM: unknown
        +OTHER: unknown
        -_missing_(value: unknown) unknown
    }
    class c0055["EntityUpdate"] {
        <<class>>
        +name: Type5
        +entity_type: Type16
        +custom_type: Type5
        +notes: Type5
        +tags: Type3
        +aka: Type3
        +project_ids: Type15
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
        +validate_aka(v: unknown) unknown
        +validate_custom_type() unknown
    }
    class c0056["File"] {
        <<class>>
        +id: int
        +size_bytes: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0057["FileCreate"] {
        <<class>>
        +filename: str
        +description: str
        +data: str
        +mime_type: str
        +tags: list[str]
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
        +validate_base64_data(v: unknown) unknown
    }
    class c0058["FileSummary"] {
        <<class>>
        +id: int
        +filename: str
        +description: str
        +mime_type: str
        +size_bytes: int
        +tags: list[str]
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0059["FileUpdate"] {
        <<class>>
        +filename: Type5
        +description: Type5
        +data: Type5
        +mime_type: Type5
        +tags: Type3
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
        +validate_tags(v: unknown) unknown
        +validate_base64_data(v: unknown) unknown
    }
    class c0060["SubgraphEdge"] {
        <<class>>
        +id: str
        +source: str
        +target: str
        +type: Type17
        +data: Type14
    }
    class c0061["SubgraphMeta"] {
        <<class>>
        +center_node_id: str
        +depth: int
        +node_types: list[str]
        +max_nodes: int
        +memory_count: int
        +entity_count: int
        +project_count: int
        +document_count: int
        +code_artifact_count: int
        +file_count: int
        +edge_count: int
        +memory_link_count: int
        +entity_relationship_count: int
        +entity_memory_count: int
        +entity_project_count: int
        +memory_project_count: int
        +document_project_count: int
        +code_artifact_project_count: int
        +memory_document_count: int
        +memory_code_artifact_count: int
        +memory_file_count: int
        +file_project_count: int
        +entity_file_count: int
        +skill_count: int
        +memory_skill_count: int
        +skill_project_count: int
        +skill_file_count: int
        +skill_code_artifact_count: int
        +skill_document_count: int
        +plan_count: int
        +task_count: int
        +plan_project_count: int
        +plan_task_count: int
        +truncated: bool
    }
    class c0062["SubgraphNode"] {
        <<class>>
        +id: str
        +type: Type18
        +depth: int
        +label: str
        +data: Type1
    }
    class c0063["SubgraphResponse"] {
        <<class>>
        +nodes: list[SubgraphNode]
        +edges: list[SubgraphEdge]
        +meta: SubgraphMeta
    }
    class c0064["LinkedMemory"] {
        <<class>>
        +memory: Memory
        +link_source_id: int
        +model_config: unknown
    }
    class c0065["Memory"] {
        <<class>>
        +id: int
        +created_at: datetime
        +updated_at: datetime
        +project_ids: list[int]
        +linked_memory_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +is_obsolete: bool
        +obsolete_reason: Type5
        +superseded_by: Type4
        +obsoleted_at: Type19
        +access_count: int
        +last_accessed_at: Type19
        +model_config: unknown
    }
    class c0066["MemoryCreate"] {
        <<class>>
        +title: str
        +content: str
        +context: str
        +keywords: list[str]
        +tags: list[str]
        +importance: int
        +project_ids: Type15
        +code_artifact_ids: Type15
        +document_ids: Type15
        +file_ids: Type15
        +skill_ids: Type15
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_lists(v: unknown, info: unknown) unknown
        +validate_source_files(v: unknown) unknown
    }
    class c0067["MemoryCreateResponse"] {
        <<class>>
        +id: int
        +title: str
        +linked_memory_ids: list[int]
        +project_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +similar_memories: list[MemorySummary]
        +obsolete_matches: list[ObsoleteMatch]
    }
    class c0068["MemoryLinkRequest"] {
        <<class>>
        +memory_id: int
        +related_ids: list[int]
        +validate_related_ids(v: unknown, info: unknown) unknown
    }
    class c0069["MemoryListResponse"] {
        <<class>>
        +memories: list[Memory]
        +total: int
        +limit: int
        +offset: int
    }
    class c0070["MemoryQueryRequest"] {
        <<class>>
        +query: str
        +query_context: str
        +k: int
        +include_links: int
        +token_context_threshold: int
        +max_links_per_primary: int
        +importance_threshold: Type4
        +project_ids: Type15
        +strict_project_filter: bool
    }
    class c0071["MemoryQueryResult"] {
        <<class>>
        +query: str
        +primary_memories: list[Memory]
        +linked_memories: list[LinkedMemory]
        +scores: list[MemoryScore]
        +total_count: int
        +token_count: int
        +truncated: bool
    }
    class c0072["MemoryScore"] {
        <<class>>
        +memory_id: int
        +similarity: float
        +rerank_score: Type9
    }
    class c0073["MemorySummary"] {
        <<class>>
        +id: int
        +title: str
        +keywords: list[str]
        +tags: list[str]
        +importance: int
        +created_at: datetime
        +updated_at: datetime
        +similarity: Type9
        +model_config: unknown
    }
    class c0074["MemoryUpdate"] {
        <<class>>
        +title: Type5
        +content: Type5
        +context: Type5
        +keywords: Type3
        +tags: Type3
        +importance: Type4
        +project_ids: Type15
        +code_artifact_ids: Type15
        +document_ids: Type15
        +file_ids: Type15
        +skill_ids: Type20
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_lists(v: unknown, info: unknown) unknown
        +validate_source_files(v: unknown) unknown
    }
    class c0075["ObsoleteMatch"] {
        <<class>>
        +id: int
        +title: str
        +similarity: float
        +obsolete_reason: Type5
        +superseded_by: Type4
        +obsoleted_at: Type19
        +project_ids: list[int]
    }
    class c0076["HealthStatus"] {
        <<class>>
        +status: str
        +timestamp: datetime
        +service: str
        +version: str
    }
    class c0077["Criterion"] {
        <<class>>
        +id: int
        +task_id: int
        +description: str
        +met: bool
        +met_at: Type19
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0078["CriterionCreate"] {
        <<class>>
        +description: str
        +strip_description(v: str) str
    }
    class c0079["CriterionUpdate"] {
        <<class>>
        +description: Type5
        +met: Type21
        +strip_description(v: Type5) Type5
    }
    class c0080["Plan"] {
        <<class>>
        +id: int
        +task_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0081["PlanCreate"] {
        <<class>>
        +title: str
        +project_id: int
        +goal: Type5
        +context: Type5
        +status: PlanStatus
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_title(v: str) str
        +strip_optional(v: Type5) Type5
    }
    class c0082["PlanStatus"] {
        <<class>>
        +DRAFT: unknown
        +ACTIVE: unknown
        +COMPLETED: unknown
        +ARCHIVED: unknown
    }
    class c0083["PlanSummary"] {
        <<class>>
        +id: int
        +title: str
        +project_id: int
        +status: PlanStatus
        +task_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0084["PlanUpdate"] {
        <<class>>
        +title: Type5
        +goal: Type5
        +context: Type5
        +status: Type22
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_title(v: Type5) Type5
        +strip_optional(v: Type5) Type5
    }
    class c0085["Task"] {
        <<class>>
        +id: int
        +plan_id: int
        +title: str
        +description: Type5
        +state: TaskState
        +priority: TaskPriority
        +assigned_agent: Type5
        +version: int
        +criteria: list[Criterion]
        +dependency_ids: list[int]
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0086["TaskCreate"] {
        <<class>>
        +title: str
        +plan_id: int
        +description: Type5
        +priority: TaskPriority
        +assigned_agent: Type5
        +criteria: Type23
        +dependency_ids: Type15
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_title(v: str) str
        +strip_description(v: Type5) Type5
    }
    class c0087["TaskDependency"] {
        <<class>>
        +id: int
        +task_id: int
        +depends_on_task_id: int
        +created_at: datetime
        +model_config: unknown
    }
    class c0088["TaskDependencyCreate"] {
        <<class>>
        +task_id: int
        +depends_on_task_id: int
        +cannot_depend_on_self(v: int, info: unknown) int
    }
    class c0089["TaskPriority"] {
        <<class>>
        +P0: unknown
        +P1: unknown
        +P2: unknown
        +P3: unknown
    }
    class c0090["TaskState"] {
        <<class>>
        +TODO: unknown
        +DOING: unknown
        +WAITING: unknown
        +DONE: unknown
        +CANCELLED: unknown
    }
    class c0091["TaskSummary"] {
        <<class>>
        +id: int
        +title: str
        +plan_id: int
        +state: TaskState
        +priority: TaskPriority
        +assigned_agent: Type5
        +version: int
        +criteria_met: int
        +criteria_total: int
        +blocked: bool
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0092["TaskUpdate"] {
        <<class>>
        +title: Type5
        +description: Type5
        +priority: Type24
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +strip_title(v: Type5) Type5
        +strip_description(v: Type5) Type5
    }
    class c0093["Project"] {
        <<class>>
        +id: int
        +memory_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0094["ProjectCreate"] {
        <<class>>
        +name: str
        +description: str
        +project_type: ProjectType
        +status: ProjectStatus
        +repo_name: Type5
        +last_encoding_point: Type5
        +notes: Type5
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +preserve_last_encoding_point(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
    }
    class c0095["ProjectStatus"] {
        <<class>>
        +ACTIVE: unknown
        +ARCHIVED: unknown
        +COMPLETED: unknown
    }
    class c0096["ProjectSummary"] {
        <<class>>
        +id: int
        +name: str
        +project_type: ProjectType
        +status: ProjectStatus
        +repo_name: Type5
        +last_encoding_point: Type5
        +memory_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0097["ProjectType"] {
        <<class>>
        +PERSONAL: unknown
        +WORK: unknown
        +LEARNING: unknown
        +DEVELOPMENT: unknown
        +INFRASTRUCTURE: unknown
        +TEMPLATE: unknown
        +PRODUCT: unknown
        +MARKETING: unknown
        +FINANCE: unknown
        +DOCUMENTATION: unknown
        +DEVELOPMENT_ENVIRONMENT: unknown
        +THIRD_PARTY_LIBRARY: unknown
        +OPEN_SOURCE: unknown
    }
    class c0098["ProjectUpdate"] {
        <<class>>
        +name: Type5
        +description: Type5
        +project_type: Type25
        +status: Type26
        +repo_name: Type5
        +last_encoding_point: Type5
        +notes: Type5
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +preserve_last_encoding_point(v: unknown) unknown
        +strip_whitespace(v: unknown, info: unknown) unknown
    }
    class c0099["Skill"] {
        <<class>>
        +id: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0100["SkillCreate"] {
        <<class>>
        +name: str
        +description: str
        +content: str
        +license: Type5
        +compatibility: Type5
        +allowed_tools: Type3
        +metadata: Type27
        +tags: list[str]
        +importance: int
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +validate_name_kebab_case(v: unknown) unknown
        +validate_tags(v: unknown) unknown
    }
    class c0101["SkillLinks"] {
        <<class>>
        +memory_ids: list[int]
        +file_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
    }
    class c0102["SkillSummary"] {
        <<class>>
        +id: int
        +name: str
        +description: str
        +license: Type5
        +tags: list[str]
        +importance: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0103["SkillUpdate"] {
        <<class>>
        +name: Type5
        +description: Type5
        +content: Type5
        +license: Type5
        +compatibility: Type5
        +allowed_tools: Type3
        +metadata: Type27
        +tags: Type3
        +importance: Type4
        +project_id: Type4
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +validate_source_files(v: unknown) unknown
        +validate_name_kebab_case(v: unknown) unknown
        +validate_tags(v: unknown) unknown
    }
    class c0104["ToolCategory"] {
        <<class>>
        +USER: unknown
        +MEMORY: unknown
        +PROJECT: unknown
        +CODE_ARTIFACT: unknown
        +DOCUMENT: unknown
        +ENTITY: unknown
        +LINKING: unknown
        +PLAN: unknown
        +TASK: unknown
        +FILE: unknown
        +SKILL: unknown
    }
    class c0105["ToolDataDetailed"] {
        <<class>>
        +json_schema: Type1
        +further_examples: list[str]
    }
    class c0106["ToolImplementation"] {
        <<class>>
        +metadata: ToolMetadata
        +implementation: Type28
    }
    class c0107["ToolMetadata"] {
        <<class>>
        +name: str
        +category: ToolCategory
        +description: str
        +parameters: list[ToolParameter]
        +returns: str
        +examples: list[str]
        +tags: list[str]
        +mutates: bool
        +to_discovery_dict() Type1
        +to_detailed_dict() Type1
        -_generate_json_schema() Type1
        -_map_python_type_to_json_type(python_type: str) str
    }
    class c0108["ToolParameter"] {
        <<class>>
        +name: str
        +type: str
        +description: str
        +required: bool
        +default: Type2
        +example: Type2
    }
    class c0109["User"] {
        <<class>>
        +id: UUID
        +updated_at: datetime
        +created_at: datetime
        +model_config: unknown
    }
    class c0110["UserCreate"] {
        <<class>>
        +external_id: str
        +name: str
        +email: str
        +idp_metadata: Type27
        +notes: Type5
    }
    class c0111["UserResponse"] {
        <<class>>
        +name: str
        +notes: Type5
        +updated_at: datetime
        +created_at: datetime
        +model_config: unknown
    }
    class c0112["UserUpdate"] {
        <<class>>
        +external_id: Type5
        +name: Type5
        +email: Type5
        +idp_metadata: Type27
        +notes: Type5
    }
    class c0113["ActivityRepository"] {
        <<class>>
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type30) int
    }
    class c0114["CodeArtifactRepository"] {
        <<class>>
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type32
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0115["DocumentRepository"] {
        <<class>>
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type33
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0116["EntityRepository"] {
        <<class>>
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type34
        +list_entities(Signature7)
        +search_entities(Signature8)
        +update_entity(user_id: UUID, entity_id: int, entity_data: EntityUpdate) Entity
        +delete_entity(user_id: UUID, entity_id: int) bool
        +link_entity_to_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +unlink_entity_from_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +link_entity_to_project(user_id: UUID, entity_id: int, project_id: int) bool
        +unlink_entity_from_project(user_id: UUID, entity_id: int, project_id: int) bool
        +create_entity_relationship(Signature9)
        +get_entity_relationships(Signature10)
        +update_entity_relationship(Signature11)
        +delete_entity_relationship(user_id: UUID, relationship_id: int) bool
        +get_all_entity_relationships(user_id: UUID) list[EntityRelationship]
        +get_all_entity_memory_links(user_id: UUID) Type36
        +get_all_entity_project_links(user_id: UUID) Type36
        +get_all_entity_file_links(user_id: UUID) Type36
        +get_entity_memories(user_id: UUID, entity_id: int) Type37
        +get_memory_entities(user_id: UUID, memory_id: int) Type38
    }
    class c0117["ToolExecutor"] {
        <<class>>
        +execute(tool_name: str, arguments: Type1) Any
        +list_tools(category: Type5) Type1
        +tool_info(tool_name: str) Type1
        +close() None
    }
    class c0118["FileRepository"] {
        <<class>>
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type39
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
    }
    class c0119["MemoryRepository"] {
        <<class>>
        +search(Signature13)
        +search_scored(Signature14)
        +create_memory(user_id: UUID, memory: MemoryCreate) Memory
        +create_links_batch(user_id: UUID, source_id: int, target_ids: list[int]) list[int]
        +get_memory_by_id(user_id: UUID, memory_id: int) Memory
        +update_memory(Signature15)
        +mark_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: int) bool
        +get_linked_memories(Signature16)
        +find_similar_memories(user_id: UUID, memory_id: int, max_links: int) list[Memory]
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type42
        +find_obsolete_matches(Signature17)
        +list_memories(Signature18)
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +get_subgraph_nodes(Signature19)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type45) list[int]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type45) None
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0120["ValidationResult"] {
        <<class>>
        +count_ok: bool
        +dimensions_ok: bool
        +search_ok: bool
        +all_passed: bool
    }
    class c0121["PlanRepository"] {
        <<class>>
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type46
        +list_plans(user_id: UUID, project_id: Type4, status: Type22) list[PlanSummary]
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0122["ProjectRepository"] {
        <<class>>
        +list_projects(Signature22)
        +get_project_by_id(user_id: UUID, project_id: int) Type47
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0123["SkillRepository"] {
        <<class>>
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type48
        +list_skills(Signature23)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature24)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type36
        +get_all_skill_code_artifact_links(user_id: UUID) Type36
        +get_all_skill_document_links(user_id: UUID) Type36
    }
    class c0124["TaskRepository"] {
        <<class>>
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type49
        +list_tasks(Signature25)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature26)
        +create_criterion(Signature27)
        +update_criterion(Signature28)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0125["UserRepository"] {
        <<class>>
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0126["AzureOpenAIAdapter"] {
        <<class>>
        -__init__() unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: unknown) list[float]
    }
    class c0127["EmbeddingsAdapter"] {
        <<class>>
        +generate_embedding(text: str) list[float]
    }
    class c0128["FastEmbeddingAdapter"] {
        <<class>>
        -__init__(providers: Type3) unknown
        +providers: unknown
        +model: unknown
        -_create_text_embedding(fastembed_kwargs: Type51) unknown
        +generate_embedding(text: str) list[float]
    }
    class c0129["GoogleEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +model: unknown
        +client: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0130["OllamaEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0131["OpenAIEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +supports_dimensions: unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0132["app/repositories/embeddings/fastembed_offline.py"] {
        <<module>>
        +get_fastembed_kwargs() Type51
        +load_fastembed_model(Signature29)
    }
    class c0133["FastEmbedCrossEncoderAdapter"] {
        <<class>>
        -__init__(Signature30)
        +model_name: unknown
        +threads: unknown
        +cache_dir: unknown
        +providers: unknown
        -_model: unknown
        -_executor: unknown
        -_create_text_cross_encoder(Signature31)
        +rerank(query: str, documents: list[str]) Type53
        -_rerank_sync(query: str, documents: list[str]) Type54
        -__del__() unknown
    }
    class c0134["HttpRerankAdapter"] {
        <<class>>
        -__init__(model: Type5, url: Type5, api_key: Type5) unknown
        +model: unknown
        +url: unknown
        +api_key: unknown
        +rerank(query: str, documents: list[str]) Type53
    }
    class c0135["RerankAdapter"] {
        <<class>>
        +rerank(query: str, documents: list[str]) Type53
    }
    class c0136["app/repositories/helpers.py"] {
        <<module>>
        +build_embedding_text(memory_data: MemoryCreate) str
        +build_memory_text(memory: Memory) str
        +build_skill_embedding_text(skill_data: unknown) str
        +build_contextual_query(query: str, context: str) str
    }
    class c0137["PostgresActivityRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type30) int
    }
    class c0138["PostgresCodeArtifactRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type32
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0139["PostgresDocumentRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type33
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0140["PostgresEntityRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type34
        +list_entities(Signature7)
        +search_entities(Signature8)
        +update_entity(user_id: UUID, entity_id: int, entity_data: EntityUpdate) Entity
        +delete_entity(user_id: UUID, entity_id: int) bool
        +link_entity_to_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +unlink_entity_from_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +link_entity_to_project(user_id: UUID, entity_id: int, project_id: int) bool
        +unlink_entity_from_project(user_id: UUID, entity_id: int, project_id: int) bool
        +create_entity_relationship(Signature9)
        +get_entity_relationships(Signature10)
        +update_entity_relationship(Signature11)
        +delete_entity_relationship(user_id: UUID, relationship_id: int) bool
        +get_all_entity_relationships(user_id: UUID) list[EntityRelationship]
        +get_all_entity_memory_links(user_id: UUID) Type36
        +get_all_entity_project_links(user_id: UUID) Type36
        +get_all_entity_file_links(user_id: UUID) Type36
        +get_memory_entities(user_id: UUID, memory_id: int) Type38
        +get_entity_memories(user_id: UUID, entity_id: int) Type37
    }
    class c0141["PostgresFileRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type39
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
        -_to_file_model(file_table: FilesTable) File
    }
    class c0142["PostgresMemoryRepository"] {
        <<class>>
        -__init__(Signature32)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +search(Signature13)
        +search_scored(Signature14)
        +semantic_search(Signature33)
        +semantic_search_scored(Signature34)
        +create_memory(user_id: UUID, memory: MemoryCreate) Memory
        +update_memory(Signature35)
        +get_memory_by_id(user_id: UUID, memory_id: int) Memory
        +get_memory_table_by_id(user_id: UUID, memory_id: int) MemoryTable
        +mark_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: Type4) bool
        +find_similar_memories(user_id: UUID, memory_id: int, max_links: int) list[Memory]
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type42
        +find_obsolete_matches(Signature17)
        +get_linked_memories(Signature16)
        +create_link(user_id: UUID, source_id: int, target_id: int) MemoryLinkTable
        +create_links_batch(user_id: UUID, source_id: int, target_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +list_memories(Signature18)
        -_link_projects(Signature36)
        -_link_code_artifacts(Signature37)
        -_link_documents(Signature38)
        -_link_files(Signature39)
        -_link_skills(Signature40)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type45) None
        -_build_targeted_rebuild_filter(Signature41)
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type45) list[int]
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        -_generate_embeddings(text: str) list[float]
        +get_subgraph_nodes(Signature42)
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0143["PostgresPlanRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type46
        +list_plans(user_id: UUID, project_id: Type4, status: Type22) list[PlanSummary]
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0144["PostgresDatabaseAdapter"] {
        <<class>>
        -__init__() unknown
        -_engine: AsyncEngine
        -_session_factory: async_sessionmaker[AsyncSession]
        +session(user_id: UUID) AsyncIterator[AsyncSession]
        +system_session() AsyncIterator[AsyncSession]
        +init_db() None
        -_run_migrations(connection: unknown) None
        +dispose() None
        +construct_postgres_connection_string() str
    }
    class c0145["ActivityLogTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +entity_type: Mapped[str]
        +entity_id: Mapped[int]
        +action: Mapped[str]
        +changes: Mapped[dict]
        +snapshot: Mapped[dict]
        +actor: Mapped[str]
        +actor_id: Mapped[str]
        +event_metadata: Mapped[dict]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0146["Base"] {
        <<class>>
    }
    class c0147["CodeArtifactsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +code: Mapped[str]
        +language: Mapped[str]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +skills: Type59
        -__table_args__: unknown
    }
    class c0148["CriteriaTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +task_id: Mapped[int]
        +description: Mapped[str]
        +met: Mapped[bool]
        +met_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +task: Type60
        -__table_args__: unknown
    }
    class c0149["DocumentsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +content: Mapped[str]
        +document_type: Mapped[str]
        +filename: Mapped[str]
        +size_bytes: Mapped[int]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +skills: Type59
        -__table_args__: unknown
    }
    class c0150["EntitiesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +name: Mapped[str]
        +entity_type: Mapped[str]
        +custom_type: Mapped[str]
        +notes: Mapped[str]
        +tags: Mapped[list[str]]
        +aka: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +projects: Type61
        +memories: Type58
        +files: Type62
        +outgoing_relationships: Type63
        +incoming_relationships: Type63
        +project_ids: list[int]
        -__table_args__: unknown
    }
    class c0151["EntityRelationshipsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +source_entity_id: Mapped[int]
        +target_entity_id: Mapped[int]
        +relationship_type: Mapped[str]
        +strength: Mapped[float]
        +confidence: Mapped[float]
        +relationship_metadata: Mapped[dict]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +source_entity: Type64
        +target_entity: Type64
        -__table_args__: unknown
    }
    class c0152["FilesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +filename: Mapped[str]
        +description: Mapped[str]
        +data: Mapped[bytes]
        +mime_type: Mapped[str]
        +size_bytes: Mapped[int]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +entities: Type65
        +skills: Type59
        -__table_args__: unknown
    }
    class c0153["MemoryLinkTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +source_id: Mapped[int]
        +target_id: Mapped[int]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0154["MemoryTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +title: Mapped[str]
        +content: Mapped[str]
        +context: Mapped[str]
        +keywords: Mapped[list[str]]
        +tags: Mapped[list[str]]
        +importance: Mapped[int]
        +embedding: Mapped[Vector]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +is_obsolete: Mapped[bool]
        +obsolete_reason: Mapped[str]
        +superseded_by: Mapped[int]
        +obsoleted_at: Mapped[datetime]
        +access_count: Mapped[int]
        +last_accessed_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +projects: Type61
        +code_artifacts: Type66
        +documents: Type67
        +files: Type62
        +skills: Type59
        +entities: Type65
        +linked_memories: Type58
        +linking_memories: Type58
        +linked_memory_ids: list[int]
        +project_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +entity_ids: list[int]
        -__table_args__: unknown
    }
    class c0155["PlansTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +goal: Mapped[str]
        +context: Mapped[str]
        +status: Mapped[str]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +tasks: Type68
        +task_count() int
        -__table_args__: unknown
    }
    class c0156["ProjectsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +name: Mapped[str]
        +description: Mapped[str]
        +project_type: Mapped[str]
        +status: Mapped[str]
        +repo_name: Mapped[str]
        +last_encoding_point: Mapped[str]
        +notes: Mapped[str]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +memories: Type58
        +code_artifacts: Type66
        +documents: Type67
        +entities: Type65
        +files: Type62
        +skills: Type59
        +plans: Type69
        +memory_count() int
        -__table_args__: unknown
    }
    class c0157["SkillsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +name: Mapped[str]
        +description: Mapped[str]
        +content: Mapped[str]
        +license: Mapped[str]
        +compatibility: Mapped[str]
        +allowed_tools: Mapped[list[str]]
        +skill_metadata: Mapped[dict]
        +tags: Mapped[list[str]]
        +importance: Mapped[int]
        +embedding: Mapped[Vector]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +files: Type62
        +code_artifacts: Type66
        +documents: Type67
        -__table_args__: unknown
    }
    class c0158["TaskDependenciesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +task_id: Mapped[int]
        +depends_on_task_id: Mapped[int]
        +created_at: Mapped[datetime]
        +task: Type60
        -__table_args__: unknown
    }
    class c0159["TasksTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +plan_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +state: Mapped[str]
        +priority: Mapped[str]
        +assigned_agent: Mapped[str]
        +version: Mapped[int]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +plan: Type70
        +criteria: Type71
        +dependency_ids: list[int]
        +depends_on: Type72
        -__table_args__: unknown
    }
    class c0160["UsersTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[UUID]
        +external_id: Mapped[str]
        +name: Mapped[str]
        +email: Mapped[str]
        +idp_metadata: Mapped[dict]
        +notes: Mapped[str]
        +updated_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +memories: Type58
        +projects: Type61
        +code_artifacts: Type66
        +documents: Type67
        +entities: Type65
        +files: Type62
        +skills: Type59
        +plans: Type69
    }
    class c0161["PostgresProjectRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +list_projects(Signature22)
        +get_project_by_id(user_id: UUID, project_id: int) Type47
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0162["PostgresSkillRepository"] {
        <<class>>
        -__init__(Signature32)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type48
        +list_skills(Signature23)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature24)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type36
        +get_all_skill_code_artifact_links(user_id: UUID) Type36
        +get_all_skill_document_links(user_id: UUID) Type36
        -_to_skill(row: SkillsTable) Skill
    }
    class c0163["PostgresTaskRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type49
        +list_tasks(Signature25)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature26)
        +create_criterion(Signature27)
        +update_criterion(Signature28)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0164["PostgresUserRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0165["SqliteActivityRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type30) int
    }
    class c0166["SqliteCodeArtifactRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type32
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0167["SqliteDocumentRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type33
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0168["SqliteEntityRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type34
        +list_entities(Signature7)
        +search_entities(Signature8)
        +update_entity(user_id: UUID, entity_id: int, entity_data: EntityUpdate) Entity
        +delete_entity(user_id: UUID, entity_id: int) bool
        +link_entity_to_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +unlink_entity_from_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +link_entity_to_project(user_id: UUID, entity_id: int, project_id: int) bool
        +unlink_entity_from_project(user_id: UUID, entity_id: int, project_id: int) bool
        +create_entity_relationship(Signature9)
        +get_entity_relationships(Signature10)
        +update_entity_relationship(Signature11)
        +delete_entity_relationship(user_id: UUID, relationship_id: int) bool
        +get_all_entity_relationships(user_id: UUID) list[EntityRelationship]
        +get_all_entity_memory_links(user_id: UUID) Type36
        +get_all_entity_project_links(user_id: UUID) Type36
        +get_all_entity_file_links(user_id: UUID) Type36
        +get_memory_entities(user_id: UUID, memory_id: int) Type38
        +get_entity_memories(user_id: UUID, entity_id: int) Type37
    }
    class c0169["SqliteFileRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type39
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
        -_to_file_model(file_table: FilesTable) File
    }
    class c0170["SqliteMemoryRepository"] {
        <<class>>
        -__init__(Signature43)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +search(Signature13)
        +search_scored(Signature14)
        +semantic_search(Signature33)
        +semantic_search_scored(Signature34)
        +create_memory(user_id: UUID, memory: MemoryCreate) Memory
        +update_memory(Signature35)
        +get_memory_by_id(user_id: UUID, memory_id: int) Memory
        +get_memory_table_by_id(user_id: UUID, memory_id: int) MemoryTable
        +mark_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: Type4) bool
        +find_similar_memories(user_id: UUID, memory_id: int, max_links: int) list[Memory]
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type42
        +find_obsolete_matches(Signature17)
        +get_linked_memories(Signature16)
        +create_link(user_id: UUID, source_id: int, target_id: int) MemoryLinkTable
        +create_links_batch(user_id: UUID, source_id: int, target_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +list_memories(Signature18)
        -_link_projects(Signature36)
        -_link_code_artifacts(Signature37)
        -_link_documents(Signature38)
        -_link_files(Signature39)
        -_link_skills(Signature40)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type45) None
        -_build_targeted_rebuild_filter(Signature41)
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type45) list[int]
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        -_generate_embeddings(text: str) list[float]
        +get_subgraph_nodes(Signature42)
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0171["SqlitePlanRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type46
        +list_plans(user_id: UUID, project_id: Type4, status: Type22) list[PlanSummary]
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0172["SqliteProjectRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +list_projects(Signature22)
        +get_project_by_id(user_id: UUID, project_id: int) Type47
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0173["SqliteSkillRepository"] {
        <<class>>
        -__init__(Signature44)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type48
        +list_skills(Signature23)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature24)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type36
        +get_all_skill_code_artifact_links(user_id: UUID) Type36
        +get_all_skill_document_links(user_id: UUID) Type36
        -_to_skill(skill_table: SkillsTable) Skill
    }
    class c0174["SqliteDatabaseAdapter"] {
        <<class>>
        -__init__() unknown
        -_engine: AsyncEngine
        -_session_factory: async_sessionmaker[AsyncSession]
        +session(user_id: UUID) AsyncIterator[AsyncSession]
        +system_session() AsyncIterator[AsyncSession]
        +init_db() None
        -_run_migrations(connection: unknown) None
        +dispose() None
        -_construct_connection_string() str
    }
    class c0175["app/repositories/sqlite/sqlite_adapter.py"] {
        <<module>>
        -_sqlite_connection_creator() unknown
    }
    class c0176["ActivityLogTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +entity_type: Mapped[str]
        +entity_id: Mapped[int]
        +action: Mapped[str]
        +changes: Mapped[dict]
        +snapshot: Mapped[dict]
        +actor: Mapped[str]
        +actor_id: Mapped[str]
        +event_metadata: Mapped[dict]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0177["Base"] {
        <<class>>
    }
    class c0178["CodeArtifactsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +code: Mapped[str]
        +language: Mapped[str]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +skills: Type59
        -__table_args__: unknown
    }
    class c0179["CriteriaTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +task_id: Mapped[int]
        +description: Mapped[str]
        +met: Mapped[bool]
        +met_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +task: Type60
        -__table_args__: unknown
    }
    class c0180["DocumentsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +content: Mapped[str]
        +document_type: Mapped[str]
        +filename: Mapped[str]
        +size_bytes: Mapped[int]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +skills: Type59
        -__table_args__: unknown
    }
    class c0181["EntitiesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +name: Mapped[str]
        +entity_type: Mapped[str]
        +custom_type: Mapped[str]
        +notes: Mapped[str]
        +tags: Mapped[list[str]]
        +aka: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +projects: Type61
        +memories: Type58
        +files: Type62
        +outgoing_relationships: Type63
        +incoming_relationships: Type63
        +project_ids: list[int]
        -__table_args__: unknown
    }
    class c0182["EntityRelationshipsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +source_entity_id: Mapped[int]
        +target_entity_id: Mapped[int]
        +relationship_type: Mapped[str]
        +strength: Mapped[float]
        +confidence: Mapped[float]
        +relationship_metadata: Mapped[dict]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +source_entity: Type64
        +target_entity: Type64
        -__table_args__: unknown
    }
    class c0183["FilesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +filename: Mapped[str]
        +description: Mapped[str]
        +data: Mapped[bytes]
        +mime_type: Mapped[str]
        +size_bytes: Mapped[int]
        +tags: Mapped[list[str]]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +entities: Type65
        +skills: Type59
        -__table_args__: unknown
    }
    class c0184["MemoryLinkTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +source_id: Mapped[int]
        +target_id: Mapped[int]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0185["MemoryTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +title: Mapped[str]
        +content: Mapped[str]
        +context: Mapped[str]
        +keywords: Mapped[list[str]]
        +tags: Mapped[list[str]]
        +importance: Mapped[int]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +is_obsolete: Mapped[bool]
        +obsolete_reason: Mapped[str]
        +superseded_by: Mapped[int]
        +obsoleted_at: Mapped[datetime]
        +access_count: Mapped[int]
        +last_accessed_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +projects: Type61
        +code_artifacts: Type66
        +documents: Type67
        +files: Type62
        +skills: Type59
        +entities: Type65
        +linked_memories: Type58
        +linking_memories: Type58
        +linked_memory_ids: list[int]
        +project_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +entity_ids: list[int]
        -__table_args__: unknown
    }
    class c0186["PlansTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +goal: Mapped[str]
        +context: Mapped[str]
        +status: Mapped[str]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +tasks: Type68
        +task_count() int
        -__table_args__: unknown
    }
    class c0187["ProjectsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +name: Mapped[str]
        +description: Mapped[str]
        +project_type: Mapped[str]
        +status: Mapped[str]
        +repo_name: Mapped[str]
        +last_encoding_point: Mapped[str]
        +notes: Mapped[str]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +memories: Type58
        +code_artifacts: Type66
        +documents: Type67
        +entities: Type65
        +files: Type62
        +skills: Type59
        +plans: Type69
        +memory_count() int
        -__table_args__: unknown
    }
    class c0188["SkillsTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +name: Mapped[str]
        +description: Mapped[str]
        +content: Mapped[str]
        +license: Mapped[str]
        +compatibility: Mapped[str]
        +allowed_tools: Mapped[list[str]]
        +skill_metadata: Mapped[dict]
        +tags: Mapped[list[str]]
        +importance: Mapped[int]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +user: Type56
        +project: Type57
        +memories: Type58
        +files: Type62
        +code_artifacts: Type66
        +documents: Type67
        -__table_args__: unknown
    }
    class c0189["TaskDependenciesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +task_id: Mapped[int]
        +depends_on_task_id: Mapped[int]
        +created_at: Mapped[datetime]
        +task: Type60
        -__table_args__: unknown
    }
    class c0190["TasksTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +plan_id: Mapped[int]
        +title: Mapped[str]
        +description: Mapped[str]
        +state: Mapped[str]
        +priority: Mapped[str]
        +assigned_agent: Mapped[str]
        +version: Mapped[int]
        +source_repo: Mapped[str]
        +source_files: Mapped[list[str]]
        +source_url: Mapped[str]
        +confidence: Mapped[float]
        +encoding_agent: Mapped[str]
        +encoding_version: Mapped[str]
        +agent_id: Mapped[str]
        +agent_version: Mapped[str]
        +agent_model: Mapped[str]
        +created_at: Mapped[datetime]
        +updated_at: Mapped[datetime]
        +plan: Type70
        +criteria: Type71
        +dependency_ids: list[int]
        +depends_on: Type72
        -__table_args__: unknown
    }
    class c0191["UsersTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[str]
        +external_id: Mapped[str]
        +name: Mapped[str]
        +email: Mapped[str]
        +idp_metadata: Mapped[dict]
        +notes: Mapped[str]
        +updated_at: Mapped[datetime]
        +created_at: Mapped[datetime]
        +memories: Type58
        +projects: Type61
        +code_artifacts: Type66
        +documents: Type67
        +entities: Type65
        +files: Type62
        +skills: Type59
        +plans: Type69
    }
    class c0192["SqliteTaskRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type49
        +list_tasks(Signature25)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature26)
        +create_criterion(Signature27)
        +update_criterion(Signature28)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0193["SqliteUserRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0194["app/routes/api/activity.py"] {
        <<module>>
        +parse_int_param(params: unknown, key: str, default: int) int
        +parse_datetime_param(params: unknown, key: str) Type19
        +register(mcp: FastMCP) unknown
    }
    class c0195["app/routes/api/auth.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0196["app/routes/api/code_artifacts.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0197["app/routes/api/documents.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0198["app/routes/api/entities.py"] {
        <<module>>
        +parse_int_param(params: Any, name: str, default: Type4) Type4
        +register(mcp: FastMCP) unknown
    }
    class c0199["app/routes/api/files.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0200["app/routes/api/graph.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0201["app/routes/api/health.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0202["app/routes/api/memories.py"] {
        <<module>>
        +parse_int_param(params: Any, name: str, default: Type4) Type4
        +register(mcp: FastMCP) unknown
    }
    class c0203["app/routes/api/plans.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0204["app/routes/api/projects.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0205["app/routes/api/skills.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0206["app/routes/api/tasks.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0207["app/routes/cli/auth_commands.py"] {
        <<module>>
        +upsert_env_var(env_file: Path, key: str, value: str) None
        -_oauth_client_factory(url: str, token_dir: Path) unknown
        -_plain_client_factory(url: str, _token: Type5) unknown
        -_has_cached_credentials(url: str, token_dir: Path) bool
        +login(server: str, env_file: Type73, token_dir: Type73, client_factory: unknown) int
        +status(server: Type5) int
        +logout(token_dir: Type73) int
    }
    class c0208["CliContext"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        +fastmcp: unknown
    }
    class c0209["_CliRuntime"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        +user_service: unknown
        +auth: unknown
    }
    class c0210["LocalExecutor"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        -_runtime: unknown
        -_ctx: unknown
        +create() Type74
        +execute(tool_name: str, arguments: Type1) Any
        +list_tools(category: Type5) Type1
        +tool_info(tool_name: str) Type1
        +close() None
    }
    class c0211["app/routes/cli/parser.py"] {
        <<module>>
        -_json_object(value: str) dict
        +build_parser() argparse.ArgumentParser
        -_build_executor(args: unknown) unknown
        -_run_tool_command(args: unknown) int
        +dispatch(argv: unknown, serve_runner: unknown, reembed_runner: unknown) unknown
        -_run_auth_command(args: unknown) int
    }
    class c0212["app/routes/cli/paths.py"] {
        <<module>>
        +config_dir() Path
        +user_env_file() Path
        +token_cache_dir() Path
    }
    class c0213["RemoteExecutor"] {
        <<class>>
        -__init__(server_url: str, token: Type5, client_factory: unknown) unknown
        +server_url: unknown
        -_token: unknown
        -_client: unknown
        -_call(meta_tool: str, payload: Type1) Any
        +execute(tool_name: str, arguments: Type1) Any
        +list_tools(category: Type5) Type1
        +tool_info(tool_name: str) Type1
        +close() None
    }
    class c0214["app/routes/cli/remote_executor.py"] {
        <<module>>
        +normalize_server_url(url: str) str
        -_default_client_factory(url: str, token: Type5) unknown
    }
    class c0215["app/routes/cli/render.py"] {
        <<module>>
        +to_jsonable(value: Any) Any
        +render_result(value: Any, as_json: bool) str
        +emit_error(message: str, as_json: bool) None
        +render_memory_lines(memories: list[dict]) str
        +render_memory_detail(memory: dict) str
        +render_project_lines(projects: list[dict]) str
    }
    class c0216["CliError"] {
        <<class>>
    }
    class c0217["app/routes/cli/verbs.py"] {
        <<module>>
        +resolve_project(executor: unknown, value: str) int
        +run(executor: unknown, args: unknown) Type75
        -_memory_search(executor: unknown, args: unknown) Type75
        -_memory_save(executor: unknown, args: unknown) Type75
        -_memory_get(executor: unknown, args: unknown) Type75
        -_memory_recent(executor: unknown, args: unknown) Type75
        -_project_list(executor: unknown) Type75
    }
    class c0218["app/routes/mcp/code_artifact_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0219["app/routes/mcp/document_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0220["app/routes/mcp/entity_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0221["app/routes/mcp/memory_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0222["app/routes/mcp/meta_tools.py"] {
        <<module>>
        -_build_category_list() str
        -_build_tool_categories_line() str
        -_get_mcp_descriptor_mode() str
        -_build_compact_discover_docstring(categories: str) str
        -_build_compact_execute_docstring(tool_categories: str) str
        -_build_discover_docstring() str
        -_build_execute_docstring() str
        +build_discovery_payload(registry: unknown, permitted: set, category: Type5) Type1
        +build_tool_documentation(registry: unknown, permitted: set, tool_name: str) Type1
        +ensure_tool_executable(registry: unknown, permitted: set, tool_name: str) None
        +register(mcp: FastMCP) unknown
    }
    class c0223["app/routes/mcp/pagination.py"] {
        <<module>>
        +clamp_list_pagination(limit: int, offset: int) Type76
    }
    class c0224["app/routes/mcp/project_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0225["app/routes/mcp/scope_resolver.py"] {
        <<module>>
        +parse_scopes(scope_string: str) frozenset[str]
        +resolve_permitted_tools(scopes: frozenset[str], registry: ToolRegistry) set[str]
        +get_required_scope(tool_name: str, registry: ToolRegistry) str
        +get_effective_scopes(ctx: Context) Type77
        -_extract_token_scopes(ctx: Context) Type78
    }
    class c0226["app/routes/mcp/skill_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0227["CodeArtifactToolAdapters"] {
        <<class>>
        -__init__(code_artifact_service: CodeArtifactService, user_service: UserService) unknown
        +code_artifact_service: unknown
        +user_service: unknown
        +create_code_artifact(Signature45)
        +get_code_artifact(artifact_id: int, ctx: Context) CodeArtifact
        +list_code_artifacts(ctx: Context, project_id: Type4, language: Type5, tags: Type3) dict
        +update_code_artifact(Signature46)
        +delete_code_artifact(artifact_id: int, ctx: Context) dict
    }
    class c0228["DocumentToolAdapters"] {
        <<class>>
        -__init__(document_service: DocumentService, user_service: UserService) unknown
        +document_service: unknown
        +user_service: unknown
        +create_document(Signature47)
        +get_document(document_id: int, ctx: Context) Document
        +list_documents(ctx: Context, project_id: Type4, document_type: Type5, tags: Type3) dict
        +update_document(Signature48)
        +delete_document(document_id: int, ctx: Context) dict
    }
    class c0229["EntityToolAdapters"] {
        <<class>>
        -__init__(entity_service: EntityService, user_service: UserService) unknown
        +entity_service: unknown
        +user_service: unknown
        +create_entity(Signature49)
        +get_entity(entity_id: int, ctx: Context) Entity
        +list_entities(ctx: Context, project_ids: Type15, entity_type: Type5, tags: Type3) dict
        +search_entities(Signature50)
        +update_entity(Signature51)
        +delete_entity(entity_id: int, ctx: Context) dict
        +link_entity_to_memory(entity_id: int, memory_id: int, ctx: Context) dict
        +unlink_entity_from_memory(entity_id: int, memory_id: int, ctx: Context) dict
        +link_entity_to_project(entity_id: int, project_id: int, ctx: Context) dict
        +unlink_entity_from_project(entity_id: int, project_id: int, ctx: Context) dict
        +create_entity_relationship(Signature52)
        +get_entity_relationships(Signature53)
        +update_entity_relationship(Signature54)
        +delete_entity_relationship(relationship_id: int, ctx: Context) dict
        +get_entity_memories(entity_id: int, ctx: Context) dict
        +get_memory_entities(memory_id: int, ctx: Context) dict
    }
    class c0230["FileToolAdapters"] {
        <<class>>
        -__init__(file_service: unknown, user_service: UserService) unknown
        +file_service: unknown
        +user_service: unknown
        +create_file(Signature55)
        +get_file(file_id: int, ctx: Context) unknown
        +list_files(ctx: Context, project_id: Type4, mime_type: Type5, tags: Type3) dict
        +update_file(Signature56)
        +delete_file(file_id: int, ctx: Context) dict
    }
    class c0231["MemoryToolAdapters"] {
        <<class>>
        -__init__(memory_service: MemoryService, user_service: UserService) unknown
        +memory_service: unknown
        +user_service: unknown
        -_build_re_embedding_service() ReEmbeddingService
        -_validate_rebuild_scope(user_id: unknown, memory_ids: Type15, project_id: Type4) None
        +create_memory(Signature57)
        +query_memory(Signature58)
        +update_memory(Signature59)
        +link_memories(Signature60)
        +unlink_memories(Signature61)
        +get_memory(ctx: Context, memory_id: Type4, id: Type4, kwargs: unknown) Memory
        +mark_memory_obsolete(Signature62)
        +get_recent_memories(Signature63)
        +rebuild_embeddings(ctx: Context, memory_ids: Type15, project_id: Type4) Type1
    }
    class c0232["PlanToolAdapters"] {
        <<class>>
        -__init__(plan_service: unknown, user_service: unknown) unknown
        +plan_service: unknown
        +user_service: unknown
        +create_plan(Signature64)
        +update_plan(Signature65)
        +get_plan(plan_id: int, ctx: Context) unknown
        +list_plans(ctx: Context, project_id: Type4, status: Type5) unknown
    }
    class c0233["ProjectToolAdapters"] {
        <<class>>
        -__init__(project_service: ProjectService, user_service: UserService) unknown
        +project_service: unknown
        +user_service: unknown
        +create_project(Signature66)
        +update_project(Signature67)
        +delete_project(project_id: int, ctx: Context) dict
        +list_projects(ctx: Context, status: Type5, repo_name: Type5, name: Type5) dict
        +get_project(project_id: int, ctx: Context) Project
    }
    class c0234["SkillToolAdapters"] {
        <<class>>
        -__init__(skill_service: unknown, user_service: UserService) unknown
        +skill_service: unknown
        +user_service: unknown
        +create_skill(Signature68)
        +get_skill(skill_id: int, ctx: Context) unknown
        +list_skills(Signature69)
        +update_skill(Signature70)
        +delete_skill(skill_id: int, ctx: Context) dict
        +search_skills(query: str, ctx: Context, k: int, project_id: Type4) dict
        +import_skill(Signature71)
        +export_skill(skill_id: int, ctx: Context) str
        +link_skill_to_memory(skill_id: int, memory_id: int, ctx: Context) dict
        +unlink_skill_from_memory(skill_id: int, memory_id: int, ctx: Context) dict
        +link_skill_to_file(skill_id: int, file_id: int, ctx: Context) dict
        +unlink_skill_from_file(skill_id: int, file_id: int, ctx: Context) dict
        +link_skill_to_code_artifact(skill_id: int, code_artifact_id: int, ctx: Context) dict
        +unlink_skill_from_code_artifact(Signature72)
        +link_skill_to_document(skill_id: int, document_id: int, ctx: Context) dict
        +unlink_skill_from_document(skill_id: int, document_id: int, ctx: Context) dict
        +get_skill_links(skill_id: int, ctx: Context) dict
    }
    class c0235["TaskToolAdapters"] {
        <<class>>
        -__init__(task_service: unknown, user_service: unknown) unknown
        +task_service: unknown
        +user_service: unknown
        +create_task(Signature73)
        +update_task(Signature74)
        +get_task(task_id: int, ctx: Context) unknown
        +query_tasks(Signature75)
        +claim_task(task_id: int, agent_id: str, version: int, ctx: Context) unknown
        +transition_task(task_id: int, state: str, version: int, ctx: Context) unknown
        +add_criterion(task_id: int, description: str, ctx: Context) unknown
        +verify_criterion(criterion_id: int, met: bool, ctx: Context) unknown
        +delete_criterion(criterion_id: int, ctx: Context) unknown
        +add_dependency(task_id: int, depends_on_task_id: int, ctx: Context) unknown
        +remove_dependency(task_id: int, depends_on_task_id: int, ctx: Context) unknown
    }
    class c0236["UserToolAdapters"] {
        <<class>>
        -__init__(user_service: UserService) unknown
        +user_service: unknown
        +get_current_user(ctx: Context) UserResponse
        +update_user_notes(user_notes: str, ctx: Context) UserResponse
    }
    class c0237["app/routes/mcp/tool_adapters.py"] {
        <<module>>
        -_coerce_int_id(val: Any, param_name: str) int
        -_coerce_int_ids(vals: Any, param_name: str) list[int]
        +create_user_adapters(user_service: UserService) Type1
        +create_memory_adapters(memory_service: MemoryService, user_service: UserService) Type1
        +create_project_adapters(Signature76)
        +create_code_artifact_adapters(Signature77)
        +create_document_adapters(Signature78)
        +create_entity_adapters(entity_service: EntityService, user_service: UserService) Type1
        +create_plan_adapters(plan_service: unknown, user_service: unknown) Type1
        +create_task_adapters(task_service: unknown, user_service: unknown) Type1
        +create_file_adapters(file_service: unknown, user_service: UserService) Type1
        +create_skill_adapters(skill_service: unknown, user_service: UserService) Type1
    }
    class c0238["app/routes/mcp/tool_metadata_registry.py"] {
        <<module>>
        +register_simplified_tool(Signature79)
        +register_user_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_memory_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_all_tools_metadata(Signature80)
        +register_project_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_code_artifact_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_document_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_entity_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_plan_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_task_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_file_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_skill_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
    }
    class c0239["ToolRegistry"] {
        <<class>>
        -__init__() unknown
        -_tools: Type81
        +register(Signature81)
        -_tools#91;name#93;: unknown
        +get_tool(name: str) Type82
        +list_all_tools() list[ToolMetadata]
        +list_by_category(category: ToolCategory) list[ToolMetadata]
        +list_categories() Type8
        +tool_exists(name: str) bool
        +get_permitted_tools(permitted: set) list[ToolMetadata]
        +get_permitted_by_category(category: ToolCategory, permitted: set) list[ToolMetadata]
        +get_permitted_categories(permitted: set) Type8
        +is_permitted(name: str, permitted: set) bool
        +execute(name: str, arguments: Type1, context: unknown) Any
    }
    class c0240["app/routes/mcp/user_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0241["ActivityService"] {
        <<class>>
        -__init__(activity_repo: ActivityRepository) unknown
        +activity_repo: unknown
        +handle_event(event: ActivityEvent) None
        +get_activity(Signature82)
        +get_entity_history(Signature83)
        +count_activity(user_id: UUID, entity_type: Type16, action: Type30) int
        -_cleanup_if_configured(user_id: UUID) None
    }
    class c0242["BackupService"] {
        <<class>>
        -__init__(database_type: Type5) unknown
        +database_type: unknown
        +create_backup() Path
        +restore_backup(backup_path: Path) None
        -_backup_sqlite(timestamp: str) Path
        -_restore_sqlite(backup_path: Path) None
        -_backup_postgres(timestamp: str) Path
        -_restore_postgres(backup_path: Path) None
    }
    class c0243["CodeArtifactService"] {
        <<class>>
        -__init__(artifact_repo: CodeArtifactRepository, event_bus: Type83) unknown
        +artifact_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact(user_id: UUID, artifact_id: int) CodeArtifact
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0244["DocumentService"] {
        <<class>>
        -__init__(document_repo: DocumentRepository, event_bus: Type83) unknown
        +document_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document(user_id: UUID, document_id: int) Document
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0245["EntityService"] {
        <<class>>
        -__init__(entity_repo: EntityRepository, event_bus: Type83) unknown
        +entity_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity(user_id: UUID, entity_id: int) Entity
        +list_entities(Signature7)
        +search_entities(Signature8)
        +update_entity(user_id: UUID, entity_id: int, entity_data: EntityUpdate) Entity
        +delete_entity(user_id: UUID, entity_id: int) bool
        +link_entity_to_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +unlink_entity_from_memory(user_id: UUID, entity_id: int, memory_id: int) bool
        +link_entity_to_project(user_id: UUID, entity_id: int, project_id: int) bool
        +unlink_entity_from_project(user_id: UUID, entity_id: int, project_id: int) bool
        +create_entity_relationship(Signature9)
        +get_entity_relationships(Signature10)
        +update_entity_relationship(Signature11)
        +delete_entity_relationship(user_id: UUID, relationship_id: int) bool
        +get_all_entity_relationships(user_id: UUID) list[EntityRelationship]
        +get_all_entity_memory_links(user_id: UUID) Type36
        +get_all_entity_project_links(user_id: UUID) Type36
        +get_all_entity_file_links(user_id: UUID) Type36
        +get_entity_memories(user_id: UUID, entity_id: int) Type84
        +get_memory_entities(user_id: UUID, memory_id: int) Type85
    }
    class c0246["FileService"] {
        <<class>>
        -__init__(file_repo: FileRepository, event_bus: Type83) unknown
        +file_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        -_snapshot_without_data(file: File) dict
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file(user_id: UUID, file_id: int) File
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
    }
    class c0247["CodeArtifactServiceProtocol"] {
        <<class>>
        +get_code_artifact(user_id: UUID, artifact_id: int) Any
    }
    class c0248["DocumentServiceProtocol"] {
        <<class>>
        +get_document(user_id: UUID, document_id: int) Any
    }
    class c0249["FileServiceProtocol"] {
        <<class>>
        +get_file(user_id: UUID, file_id: int) Any
        +list_files(user_id: UUID, kwargs: unknown) Any
    }
    class c0250["GraphService"] {
        <<class>>
        -__init__(Signature86)
        +memory_repo: unknown
        +entity_repo: unknown
        +project_service: unknown
        +document_service: unknown
        +code_artifact_service: unknown
        +file_service: unknown
        +skill_service: unknown
        +plan_service: unknown
        +task_service: unknown
        +parse_node_id(node_id: str) Type93
        +get_subgraph(Signature87)
        -_validate_center_node(user_id: UUID, center_type: str, center_id: int) None
        -_fetch_node_data(Signature88)
        -_fetch_edges(Signature89)
    }
    class c0251["PlanServiceProtocol"] {
        <<class>>
        +get_plan(user_id: UUID, plan_id: int) Any
        +list_plans(user_id: UUID, kwargs: unknown) Any
    }
    class c0252["ProjectServiceProtocol"] {
        <<class>>
        +get_project(user_id: UUID, project_id: int) Any
    }
    class c0253["SkillServiceProtocol"] {
        <<class>>
        +get_skill(user_id: UUID, skill_id: int) Any
        +get_all_skill_file_links(user_id: UUID) Type36
        +get_all_skill_code_artifact_links(user_id: UUID) Type36
        +get_all_skill_document_links(user_id: UUID) Type36
    }
    class c0254["TaskServiceProtocol"] {
        <<class>>
        +get_task(user_id: UUID, task_id: int) Any
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) Any
    }
    class c0255["MemoryService"] {
        <<class>>
        -__init__(memory_repo: MemoryRepository, event_bus: Type83) unknown
        +memory_repo: unknown
        -_event_bus: unknown
        +register_access_tracking_handlers(event_bus: Type95) None
        +query_memory(user_id: UUID, memory_query: MemoryQueryRequest) MemoryQueryResult
        +create_memory(user_id: UUID, memory_data: MemoryCreate) Type96
        +update_memory(user_id: UUID, memory_id: int, updated_memory: MemoryUpdate) Type41
        +mark_memory_obsolete(Signature90)
        +get_memory(user_id: UUID, memory_id: int) Type41
        +find_obsolete_matches(user_id: UUID, memory_id: int) list[ObsoleteMatch]
        +list_memories(Signature18)
        +link_memories(user_id: UUID, memory_id: int, related_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, memory_id: int, target_id: int) bool
        -_fetch_linked_memories(Signature91)
        -_apply_token_budget(Signature92)
        -_count_memory_tokens(memory: Memory) int
        +truncate_memories_by_budget(Signature93)
        +handle_memory_access_event(event: ActivityEvent) None
        -_emit_event(Signature84)
    }
    class c0256["PlanService"] {
        <<class>>
        -__init__(plan_repo: PlanRepository, event_bus: Type83) unknown
        +plan_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan(user_id: UUID, plan_id: int) Plan
        +list_plans(user_id: UUID, project_id: Type4, status: Type22) list[PlanSummary]
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Type46
        +delete_plan(user_id: UUID, plan_id: int) bool
        +check_plan_completion(user_id: UUID, plan_id: int) bool
    }
    class c0257["ProjectService"] {
        <<class>>
        -__init__(project_repo: ProjectRepository, event_bus: Type83) unknown
        +project_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +list_projects(Signature22)
        +get_project(user_id: UUID, project_id: int) Project
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Type47
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0258["ReEmbedResult"] {
        <<class>>
        +total_processed: int
        +total_memories: int
        +validation: Type99
    }
    class c0259["ReEmbeddingService"] {
        <<class>>
        -__init__(Signature94)
        +memory_repository: unknown
        +embedding_adapter: unknown
        +batch_size: unknown
        +re_embed_all(progress_callback: Type100) ReEmbedResult
        +rebuild_targeted(Signature95)
        -_record_unresolved_memory_ids(Signature96)
        -_recompute_auto_links(Signature97)
        +validate() ValidationResult
    }
    class c0260["TargetedRebuildResult"] {
        <<class>>
        +rebuilt_ids: list[int]
        +skipped_ids: list[int]
        +failed: list[dict]
    }
    class c0261["SkillService"] {
        <<class>>
        -__init__(skill_repo: SkillRepository, event_bus: Type83) unknown
        +skill_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +get_skill(user_id: UUID, skill_id: int) Skill
        +list_skills(Signature23)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +import_skill(Signature98)
        +export_skill(user_id: UUID, skill_id: int) str
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature24)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type36
        +get_all_skill_code_artifact_links(user_id: UUID) Type36
        +get_all_skill_document_links(user_id: UUID) Type36
    }
    class c0262["app/services/skill_service.py"] {
        <<module>>
        -_quote_unquoted_frontmatter_scalars(raw: str) str
    }
    class c0263["TaskService"] {
        <<class>>
        -__init__(Signature99)
        +task_repo: unknown
        +plan_service: unknown
        -_event_bus: unknown
        -_emit_event(Signature84)
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task(user_id: UUID, task_id: int) Task
        +list_tasks(Signature25)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Type49
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task(Signature100)
        +claim_task(user_id: UUID, task_id: int, agent_id: str, expected_version: int) Task
        +add_criterion(user_id: UUID, task_id: int, criterion_data: CriterionCreate) Criterion
        +update_criterion(Signature28)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) unknown
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        -_validate_dependencies_met(user_id: UUID, task: Task) None
        -_validate_all_criteria_met(user_id: UUID, task: Task) None
        -_validate_no_cycle(user_id: UUID, task_id: int, new_dep_id: int) None
        -_validate_same_plan(Signature101)
        -_check_plan_auto_completion(user_id: UUID, plan_id: int) None
    }
    class c0264["UserService"] {
        <<class>>
        -__init__(user_repo: UserRepository) unknown
        +user_repo: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_or_create_user(user: UserCreate) Type12
        +update_user(user_update: UserUpdate) Type12
    }
    class c0265["app/utils/provenance.py"] {
        <<module>>
        +apply_provenance_defaults(data: unknown) unknown
        +apply_provenance_defaults_for_update(data: unknown) unknown
    }
    class c0266["app/utils/pydantic_helper.py"] {
        <<module>>
        +get_changed_fields(input_model: BaseModel, existing_model: BaseModel) Type101
        +filter_none_values(kwargs: unknown) unknown
    }
    class c0267["app/utils/repository_identity.py"] {
        <<module>>
        +repository_identity(value: str) Type102
    }
    class c0268["TokenCounter"] {
        <<class>>
        -__init__(model: str) unknown
        +encoding: unknown
        +count_tokens(text: str) int
    }
    class c0269["app/version.py"] {
        <<module>>
        +get_version() str
    }
    class c0270["debug/reranker-test.py"] {
        <<module>>
        +main() unknown
        +jina() unknown
        +fast_embed_rank() unknown
        +http_rank() unknown
    }
    class c0271["debug/sqlite_vec_poc.py"] {
        <<module>>
        +test_sqlite_vec_sync() unknown
        +test_sqlite_vec_async() unknown
    }
    class c0272["debug/test_google_embeddings.py"] {
        <<module>>
        +test_embeddings() unknown
    }
    class c0273["debug/test_mcp_connection.py"] {
        <<module>>
        +main() unknown
    }
    class c0274["debug/test_sqlite_init.py"] {
        <<module>>
        +test_sqlite_init() unknown
    }
    class c0275["main.py"] {
        <<module>>
        +lifespan(app: unknown) unknown
        +root(request: Request) JSONResponse
        -_run_reembed(args: unknown) unknown
        -_serve(transport: unknown, host: unknown, port: unknown) unknown
        -_legacy_launcher(argv: unknown) unknown
        +cli() unknown
    }
    class c0276["test_harness/__main__.py"] {
        <<module>>
        +config_from_argv(argv: list[str]) HarnessConfig
        -_print_summary(results: list[SkillRunResult], run_dir: Path) None
        -_run(config: HarnessConfig) int
        +main(argv: Type3) int
    }
    class c0277["HarnessConfig"] {
        <<class>>
        +model_config: unknown
        +agent_type: str
        +model: str
        +effort: Type5
        +surface: Type103
        +skills: list[str]
        +skill_timeout: float
        +skill_timeouts: Type104
        +skills_dir: Path
        +output_dir: Path
        +rebuild_image: bool
        -_only_cli_is_implemented(value: str) str
        -_subset_of_walkthrough_order(value: list[str]) list[str]
        +timeout_for(skill: str) float
    }
    class c0278["AgentContainer"] {
        <<class>>
        -__init__(config: HarnessConfig, run_dir: Path, server_url: str) unknown
        +config: unknown
        +run_dir: unknown
        +server_url: unknown
        -_staged: list[Path]
        -_client: unknown
        -_container: unknown
        +start() None
        +health_check() None
        +run_session(Signature102)
        -_exec(cmd: list[str], log_path: Type73) Type105
        +stop() None
    }
    class c0279["test_harness/container.py"] {
        <<module>>
        +build_container_env(server_url: str) Type106
        +exec_command(timeout: float, skill: str) list[str]
        +staged_mount(files: list[Path], container_dir: str, staged: list[Path]) Type107
        +provision_agent(agent_type: str, staged: list[Path], auth_path: Path) Type107
        +export_requirements() str
        +requirements_hash(requirements: str) str
        -_docker_client() unknown
        +ensure_image(rebuild: bool, log: unknown) None
        -_prepare_harness_mount(run_dir: Path) Path
    }
    class c0280["test_harness/docker/runner.py"] {
        <<module>>
        -_shell() unknown
        +health() None
        -_attach_debug_log(path: Path) None
        +run_session(skill_dir: Path) None
        +main() int
    }
    class c0281["test_harness/prompts.py"] {
        <<module>>
        +build_prompt(skill: str) str
    }
    class c0282["ReportIssue"] {
        <<class>>
        +model_config: unknown
        +severity: Type108
        +where: str
        +what: str
        +evidence: str
        -_normalize_severity: unknown
    }
    class c0283["ReportLoad"] {
        <<class>>
        +status: Type109
        +report: Type110
        +detail: str
    }
    class c0284["ReportStep"] {
        <<class>>
        +model_config: unknown
        +step: str
        +commands: list[str]
        +observed: str
        +verdict: Type111
        -_normalize_verdict: unknown
    }
    class c0285["WalkthroughReport"] {
        <<class>>
        +model_config: unknown
        +skill: str
        +verdict: Type112
        +steps: list[ReportStep]
        +issues: list[ReportIssue]
        -_normalize_verdict: unknown
    }
    class c0286["test_harness/report.py"] {
        <<module>>
        -_lowercase(value: Any) Any
        -_normalize_step_verdict(value: Any) Any
        -_normalize_report_verdict(value: Any) Any
        -_normalize_severity(value: Any) Any
        +report_contract_example() str
        +load_report(path: Path) ReportLoad
    }
    class c0291["HarnessInfraError"] {
        <<class>>
    }
    class c0292["ThrowawayForgetful"] {
        <<class>>
        -__init__(run_dir: Path, boot_timeout: float) unknown
        +run_dir: unknown
        +boot_timeout: unknown
        +port: Type4
        +process: Type113
        -_log_file: unknown
        +url: str
        +mcp_url: str
        -_child_env() Type106
        +start() None
        -_wait_until_healthy() None
        +stop() None
        +execute(tool_name: str, arguments: Type1) Any
        +seed_skills(skills_dir: Path, names: Iterable[str]) list[dict]
    }
    class c0293["test_harness/server.py"] {
        <<module>>
        -_plain_client_factory(url: str, token: Type5) unknown
        -_ephemeral_port() int
    }
    class c0294["SessionOutcome"] {
        <<class>>
        +kind: Type114
        +detail: str
    }
    class c0295["SessionRunner"] {
        <<class>>
        +run_session(Signature102)
    }
    class c0296["SkillRunResult"] {
        <<class>>
        +skill: str
        +status: str
        +report_load: ReportLoad
        +breaches: list[str]
        +cost: float
        +duration: float
        +output_tokens: int
        +session_id: Type5
        +error: str
    }
    class c0297["Walkthrough"] {
        <<class>>
        -__init__(Signature103)
        +config: unknown
        +runner: unknown
        +server_url: unknown
        +run_dir: unknown
        +run() list[SkillRunResult]
        +run_skill(skill: str) SkillRunResult
        -_meta(result: SkillRunResult, started: float) Type1
        +write_summary(results: list[SkillRunResult]) None
    }
    class c0298["test_harness/walkthrough.py"] {
        <<module>>
        +prepare_workspace(skill_dir: Path, skill: str, skills_dir: Path) Path
        -_build_fixture_repo(root: Path) None
        +load_events(path: Path) Type115
        +scan_for_breaches(events: Type115) list[str]
    }
    c0002 ..> c0002 : 2 relationships (see list)
    c0002 ..> c0030 : run_migrations_online() calls get()
    c0002 ..> c0144 : run_async_migrations() calls dispose()
    c0002 ..> c0217 : run_migrations_online() calls run()
    c0003 ..> c0000 : 2 relationships (see list)
    c0003 ..> c0001 : 2 relationships (see list)
    c0003 ..> c0003 : 2 relationships (see list)
    c0005 ..> c0005 : upgrade() calls _get_user_id_type()
    c0007 ..> c0007 : upgrade() calls _get_user_id_type()
    c0008 ..> c0008 : 2 relationships (see list)
    c0009 ..> c0009 : 4 relationships (see list)
    c0010 ..> c0010 : 4 relationships (see list)
    c0013 --> c0014 : field services
    c0013 --> c0239 : field registry
    c0015 ..> c0013 : 3 relationships (see list)
    c0015 ..> c0014 : build_runtime() constructs Services
    c0015 ..> c0015 : 5 relationships (see list)
    c0015 ..> c0023 : 3 relationships (see list)
    c0015 ..> c0126 : get_embedding_adapter() constructs AzureOpenAIAdapter
    c0015 ..> c0128 : get_embedding_adapter() constructs FastEmbeddingAdapter
    c0015 ..> c0129 : get_embedding_adapter() constructs GoogleEmbeddingsAdapter
    c0015 ..> c0130 : get_embedding_adapter() constructs OllamaEmbeddingsAdapter
    c0015 ..> c0131 : get_embedding_adapter() constructs OpenAIEmbeddingsAdapter
    c0015 ..> c0133 : get_reranker_adapter() constructs FastEmbedCrossEncoderAdapter
    c0015 ..> c0134 : get_reranker_adapter() constructs HttpRerankAdapter
    c0015 ..> c0137 : create_repositories() constructs PostgresActivityRepository
    c0015 ..> c0138 : create_repositories() constructs PostgresCodeArtifactRepository
    c0015 ..> c0139 : create_repositories() constructs PostgresDocumentRepository
    c0015 ..> c0140 : create_repositories() constructs PostgresEntityRepository
    c0015 ..> c0141 : create_repositories() constructs PostgresFileRepository
    c0015 ..> c0142 : create_repositories() constructs PostgresMemoryRepository
    c0015 ..> c0143 : create_repositories() constructs PostgresPlanRepository
    c0015 ..> c0144 : 3 relationships (see list)
    c0015 ..> c0161 : create_repositories() constructs PostgresProjectRepository
    c0015 ..> c0162 : create_repositories() constructs PostgresSkillRepository
    c0015 ..> c0163 : create_repositories() constructs PostgresTaskRepository
    c0015 ..> c0164 : create_repositories() constructs PostgresUserRepository
    c0015 ..> c0165 : create_repositories() constructs SqliteActivityRepository
    c0015 ..> c0166 : create_repositories() constructs SqliteCodeArtifactRepository
    c0015 ..> c0167 : create_repositories() constructs SqliteDocumentRepository
    c0015 ..> c0168 : create_repositories() constructs SqliteEntityRepository
    c0015 ..> c0169 : create_repositories() constructs SqliteFileRepository
    c0015 ..> c0170 : create_repositories() constructs SqliteMemoryRepository
    c0015 ..> c0171 : create_repositories() constructs SqlitePlanRepository
    c0015 ..> c0172 : create_repositories() constructs SqliteProjectRepository
    c0015 ..> c0173 : create_repositories() constructs SqliteSkillRepository
    c0015 ..> c0174 : create_db_adapter() constructs SqliteDatabaseAdapter
    c0015 ..> c0192 : create_repositories() constructs SqliteTaskRepository
    c0015 ..> c0193 : create_repositories() constructs SqliteUserRepository
    c0015 ..> c0225 : 2 relationships (see list)
    c0015 ..> c0238 : build_runtime() calls register_all_tools_metadata()
    c0015 ..> c0239 : 2 relationships (see list)
    c0015 ..> c0241 : build_runtime() constructs ActivityService
    c0015 ..> c0243 : build_runtime() constructs CodeArtifactService
    c0015 ..> c0244 : build_runtime() constructs DocumentService
    c0015 ..> c0245 : build_runtime() constructs EntityService
    c0015 ..> c0246 : build_runtime() constructs FileService
    c0015 ..> c0250 : build_runtime() constructs GraphService
    c0015 ..> c0255 : 2 relationships (see list)
    c0015 ..> c0256 : build_runtime() constructs PlanService
    c0015 ..> c0257 : build_runtime() constructs ProjectService
    c0015 ..> c0261 : build_runtime() constructs SkillService
    c0015 ..> c0263 : build_runtime() constructs TaskService
    c0015 ..> c0264 : build_runtime() constructs UserService
    c0016 ..> c0016 : 7 relationships (see list)
    c0016 ..> c0030 : build_auth_provider() calls get()
    c0018 ..> c0030 : format() calls get()
    c0018 ..> c0032 : 2 relationships (see list)
    c0019 ..> c0019 : filter() calls _mask_value()
    c0020 ..> c0017 : configure_logging() constructs ConsoleFormatter
    c0020 ..> c0018 : configure_logging() constructs JSONFormatter
    c0020 ..> c0019 : configure_logging() constructs SensitiveDataFilter
    c0020 ..> c0023 : configure_logging() calls clear()
    c0020 ..> c0278 : 2 relationships (see list)
    c0021 ..> c0022 : 3 relationships (see list)
    c0023 ..> c0023 : 3 relationships (see list)
    c0023 ..> c0030 : 6 relationships (see list)
    c0023 ..> c0034 : 3 relationships (see list)
    c0023 ..> c0124 : emit() calls create_task()
    c0029 --> c0109 : field user
    c0030 ..> c0023 : clear() calls clear()
    c0030 --> c0029 : field _cache
    c0030 ..> c0029 : set() constructs CacheEntry
    c0030 ..> c0030 : 3 relationships (see list)
    c0030 ..> c0109 : 2 relationships (see list)
    c0031 ..> c0030 : 2 relationships (see list)
    c0031 ..> c0109 : 2 relationships (see list)
    c0031 ..> c0110 : 2 relationships (see list)
    c0031 ..> c0264 : 2 relationships (see list)
    c0032 ..> c0030 : 2 relationships (see list)
    c0034 --> c0033 : field action
    c0034 --> c0037 : field actor
    c0034 --> c0038 : field entity_type
    c0035 --> c0036 : field events
    c0036 --> c0033 : field action
    c0036 --> c0037 : field actor
    c0036 --> c0038 : field entity_type
    c0039 --|> c0040 : inherits
    c0043 --|> c0044 : inherits
    c0044 ..> c0030 : calculate_size_bytes() calls get()
    c0047 --|> c0048 : inherits
    c0048 --> c0054 : field entity_type
    c0049 --> c0053 : field entities
    c0050 --|> c0051 : inherits
    c0053 --> c0054 : field entity_type
    c0055 --> c0054 : field entity_type
    c0056 --|> c0057 : inherits
    c0063 --> c0060 : field edges
    c0063 --> c0061 : field meta
    c0063 --> c0062 : field nodes
    c0064 --> c0065 : field memory
    c0065 --|> c0066 : inherits
    c0067 --> c0073 : field similar_memories
    c0067 --> c0075 : field obsolete_matches
    c0069 --> c0065 : field memories
    c0071 --> c0064 : field linked_memories
    c0071 --> c0065 : field primary_memories
    c0071 --> c0072 : field scores
    c0080 --|> c0081 : inherits
    c0081 --> c0082 : field status
    c0083 --> c0082 : field status
    c0084 --> c0082 : field status
    c0085 --> c0077 : field criteria
    c0085 --> c0089 : field priority
    c0085 --> c0090 : field state
    c0086 --> c0078 : field criteria
    c0086 --> c0089 : field priority
    c0088 ..> c0030 : cannot_depend_on_self() calls get()
    c0091 --> c0089 : field priority
    c0091 --> c0090 : field state
    c0092 --> c0089 : field priority
    c0093 --|> c0094 : inherits
    c0094 --> c0095 : field status
    c0094 --> c0097 : field project_type
    c0096 --> c0095 : field status
    c0096 --> c0097 : field project_type
    c0098 --> c0095 : field status
    c0098 --> c0097 : field project_type
    c0099 --|> c0100 : inherits
    c0105 --|> c0107 : inherits
    c0106 --> c0107 : field metadata
    c0107 ..> c0030 : _map_python_type_to_json_type() calls get()
    c0107 --> c0104 : field category
    c0107 ..> c0107 : 2 relationships (see list)
    c0107 --> c0108 : field parameters
    c0109 --|> c0110 : inherits
    c0113 ..> c0033 : 2 relationships (see list)
    c0113 ..> c0034 : type in save_event
    c0113 ..> c0036 : 2 relationships (see list)
    c0113 ..> c0037 : type in query_events
    c0113 ..> c0038 : 2 relationships (see list)
    c0114 ..> c0039 : 3 relationships (see list)
    c0114 ..> c0040 : type in create_code_artifact
    c0114 ..> c0041 : type in list_code_artifacts
    c0114 ..> c0042 : type in update_code_artifact
    c0115 ..> c0043 : 3 relationships (see list)
    c0115 ..> c0044 : type in create_document
    c0115 ..> c0045 : type in list_documents
    c0115 ..> c0046 : type in update_document
    c0116 ..> c0047 : 3 relationships (see list)
    c0116 ..> c0048 : type in create_entity
    c0116 ..> c0050 : 4 relationships (see list)
    c0116 ..> c0051 : type in create_entity_relationship
    c0116 ..> c0052 : type in update_entity_relationship
    c0116 ..> c0053 : 2 relationships (see list)
    c0116 ..> c0054 : 2 relationships (see list)
    c0116 ..> c0055 : type in update_entity
    c0118 ..> c0056 : 3 relationships (see list)
    c0118 ..> c0057 : type in create_file
    c0118 ..> c0058 : type in list_files
    c0118 ..> c0059 : type in update_file
    c0119 ..> c0065 : 12 relationships (see list)
    c0119 ..> c0066 : type in create_memory
    c0119 ..> c0072 : type in search_scored
    c0119 ..> c0074 : type in update_memory
    c0121 ..> c0080 : 3 relationships (see list)
    c0121 ..> c0081 : type in create_plan
    c0121 ..> c0082 : type in list_plans
    c0121 ..> c0083 : type in list_plans
    c0121 ..> c0084 : type in update_plan
    c0122 ..> c0093 : 3 relationships (see list)
    c0122 ..> c0094 : type in create_project
    c0122 ..> c0095 : type in list_projects
    c0122 ..> c0096 : type in list_projects
    c0122 ..> c0098 : type in update_project
    c0123 ..> c0099 : 3 relationships (see list)
    c0123 ..> c0100 : type in create_skill
    c0123 ..> c0101 : type in get_skill_links
    c0123 ..> c0102 : 2 relationships (see list)
    c0123 ..> c0103 : type in update_skill
    c0124 ..> c0077 : 3 relationships (see list)
    c0124 ..> c0078 : type in create_criterion
    c0124 ..> c0079 : type in update_criterion
    c0124 ..> c0085 : 4 relationships (see list)
    c0124 ..> c0086 : type in create_task
    c0124 ..> c0087 : type in add_dependency
    c0124 ..> c0089 : type in list_tasks
    c0124 ..> c0090 : 2 relationships (see list)
    c0124 ..> c0091 : 2 relationships (see list)
    c0124 ..> c0092 : type in update_task
    c0125 ..> c0109 : 4 relationships (see list)
    c0125 ..> c0110 : type in create_user
    c0125 ..> c0112 : type in update_user
    c0126 --|> c0127 : inherits
    c0128 --|> c0127 : inherits
    c0129 --|> c0127 : inherits
    c0130 --|> c0127 : inherits
    c0130 ..> c0128 : __init__() calls _create_text_embedding()
    c0130 ..> c0132 : __init__() calls load_fastembed_model()
    c0130 ..> c0210 : generate_embedding() calls create()
    c0131 --|> c0127 : inherits
    c0132 ..> c0132 : load_fastembed_model() calls get_fastembed_kwargs()
    c0133 ..> c0134 : _rerank_sync() calls rerank()
    c0134 ..> c0132 : __init__() calls load_fastembed_model()
    c0134 ..> c0133 : __init__() calls _create_text_cross_encoder()
    c0136 ..> c0065 : type in build_memory_text
    c0136 ..> c0066 : type in build_embedding_text
    c0137 ..> c0033 : 2 relationships (see list)
    c0137 ..> c0034 : type in save_event
    c0137 ..> c0036 : 4 relationships (see list)
    c0137 ..> c0037 : type in query_events
    c0137 ..> c0038 : 2 relationships (see list)
    c0137 ..> c0117 : 3 relationships (see list)
    c0137 ..> c0144 : 5 relationships (see list)
    c0137 ..> c0145 : save_event() constructs ActivityLogTable
    c0138 ..> c0028 : update_code_artifact() constructs NotFoundError
    c0138 ..> c0030 : update_code_artifact() calls get()
    c0138 ..> c0039 : 3 relationships (see list)
    c0138 ..> c0040 : type in create_code_artifact
    c0138 ..> c0041 : type in list_code_artifacts
    c0138 ..> c0042 : type in update_code_artifact
    c0138 ..> c0117 : 4 relationships (see list)
    c0138 ..> c0144 : 6 relationships (see list)
    c0138 ..> c0147 : create_code_artifact() constructs CodeArtifactsTable
    c0139 ..> c0028 : update_document() constructs NotFoundError
    c0139 ..> c0030 : update_document() calls get()
    c0139 ..> c0043 : 3 relationships (see list)
    c0139 ..> c0044 : type in create_document
    c0139 ..> c0045 : type in list_documents
    c0139 ..> c0046 : type in update_document
    c0139 ..> c0117 : 4 relationships (see list)
    c0139 ..> c0144 : 6 relationships (see list)
    c0139 ..> c0149 : create_document() constructs DocumentsTable
    c0140 ..> c0028 : 8 relationships (see list)
    c0140 ..> c0030 : update_entity() calls get()
    c0140 ..> c0047 : 3 relationships (see list)
    c0140 ..> c0048 : type in create_entity
    c0140 ..> c0050 : 8 relationships (see list)
    c0140 ..> c0051 : type in create_entity_relationship
    c0140 ..> c0052 : type in update_entity_relationship
    c0140 ..> c0053 : 2 relationships (see list)
    c0140 ..> c0054 : 2 relationships (see list)
    c0140 ..> c0055 : type in update_entity
    c0140 ..> c0117 : 20 relationships (see list)
    c0140 ..> c0144 : 21 relationships (see list)
    c0140 ..> c0150 : create_entity() constructs EntitiesTable
    c0140 ..> c0151 : create_entity_relationship() constructs EntityRelationshipsTable
    c0141 ..> c0028 : update_file() constructs NotFoundError
    c0141 ..> c0056 : 5 relationships (see list)
    c0141 ..> c0057 : type in create_file
    c0141 ..> c0058 : type in list_files
    c0141 ..> c0059 : type in update_file
    c0141 ..> c0117 : 4 relationships (see list)
    c0141 ..> c0141 : 3 relationships (see list)
    c0141 ..> c0144 : 6 relationships (see list)
    c0141 ..> c0152 : 2 relationships (see list)
    c0142 ..> c0023 : update_memory() calls clear()
    c0142 ..> c0028 : 11 relationships (see list)
    c0142 ..> c0030 : 2 relationships (see list)
    c0142 ..> c0065 : 14 relationships (see list)
    c0142 ..> c0066 : type in create_memory
    c0142 ..> c0072 : 2 relationships (see list)
    c0142 ..> c0074 : type in update_memory
    c0142 ..> c0117 : 25 relationships (see list)
    c0142 ..> c0127 : type in __init__
    c0142 ..> c0130 : _generate_embeddings() calls generate_embedding()
    c0142 ..> c0134 : search_scored() calls rerank()
    c0142 ..> c0135 : type in __init__
    c0142 ..> c0136 : 4 relationships (see list)
    c0142 ..> c0142 : 23 relationships (see list)
    c0142 ..> c0144 : 24 relationships (see list)
    c0142 ..> c0153 : 2 relationships (see list)
    c0142 ..> c0154 : 7 relationships (see list)
    c0143 ..> c0028 : update_plan() constructs NotFoundError
    c0143 ..> c0080 : 3 relationships (see list)
    c0143 ..> c0081 : type in create_plan
    c0143 ..> c0082 : type in list_plans
    c0143 ..> c0083 : type in list_plans
    c0143 ..> c0084 : type in update_plan
    c0143 ..> c0117 : 4 relationships (see list)
    c0143 ..> c0144 : 6 relationships (see list)
    c0143 ..> c0155 : create_plan() constructs PlansTable
    c0144 ..> c0003 : _run_migrations() calls upgrade()
    c0144 ..> c0117 : 4 relationships (see list)
    c0144 ..> c0144 : 2 relationships (see list)
    c0144 ..> c0174 : dispose() calls dispose()
    c0145 --|> c0146 : inherits
    c0147 --|> c0146 : inherits
    c0147 --> c0154 : field memories
    c0147 --> c0156 : field project
    c0147 --> c0157 : field skills
    c0147 --> c0160 : field user
    c0148 --|> c0146 : inherits
    c0148 --> c0159 : field task
    c0149 --|> c0146 : inherits
    c0149 --> c0154 : field memories
    c0149 --> c0156 : field project
    c0149 --> c0157 : field skills
    c0149 --> c0160 : field user
    c0150 --|> c0146 : inherits
    c0150 --> c0151 : 2 relationships (see list)
    c0150 --> c0152 : field files
    c0150 --> c0154 : field memories
    c0150 --> c0156 : field projects
    c0150 --> c0160 : field user
    c0151 --|> c0146 : inherits
    c0151 --> c0150 : 2 relationships (see list)
    c0152 --|> c0146 : inherits
    c0152 --> c0150 : field entities
    c0152 --> c0154 : field memories
    c0152 --> c0156 : field project
    c0152 --> c0157 : field skills
    c0152 --> c0160 : field user
    c0153 --|> c0146 : inherits
    c0154 --|> c0146 : inherits
    c0154 --> c0147 : field code_artifacts
    c0154 --> c0149 : field documents
    c0154 --> c0150 : field entities
    c0154 --> c0152 : field files
    c0154 --> c0156 : field projects
    c0154 --> c0157 : field skills
    c0154 --> c0160 : field user
    c0155 --|> c0146 : inherits
    c0155 --> c0156 : field project
    c0155 --> c0159 : field tasks
    c0155 --> c0160 : field user
    c0156 --|> c0146 : inherits
    c0156 --> c0147 : field code_artifacts
    c0156 --> c0149 : field documents
    c0156 --> c0150 : field entities
    c0156 --> c0152 : field files
    c0156 --> c0154 : field memories
    c0156 --> c0155 : field plans
    c0156 --> c0157 : field skills
    c0156 --> c0160 : field user
    c0157 --|> c0146 : inherits
    c0157 --> c0147 : field code_artifacts
    c0157 --> c0149 : field documents
    c0157 --> c0152 : field files
    c0157 --> c0154 : field memories
    c0157 --> c0156 : field project
    c0157 --> c0160 : field user
    c0158 --|> c0146 : inherits
    c0158 --> c0159 : field task
    c0159 --|> c0146 : inherits
    c0159 --> c0148 : field criteria
    c0159 --> c0155 : field plan
    c0159 --> c0158 : field depends_on
    c0160 --|> c0146 : inherits
    c0160 --> c0147 : field code_artifacts
    c0160 --> c0149 : field documents
    c0160 --> c0150 : field entities
    c0160 --> c0152 : field files
    c0160 --> c0154 : field memories
    c0160 --> c0155 : field plans
    c0160 --> c0156 : field projects
    c0160 --> c0157 : field skills
    c0161 ..> c0028 : update_project() constructs NotFoundError
    c0161 ..> c0093 : 3 relationships (see list)
    c0161 ..> c0094 : type in create_project
    c0161 ..> c0095 : type in list_projects
    c0161 ..> c0096 : type in list_projects
    c0161 ..> c0098 : type in update_project
    c0161 ..> c0117 : 4 relationships (see list)
    c0161 ..> c0144 : 6 relationships (see list)
    c0161 ..> c0156 : create_project() constructs ProjectsTable
    c0161 ..> c0267 : list_projects() calls repository_identity()
    c0162 ..> c0028 : 6 relationships (see list)
    c0162 ..> c0099 : 5 relationships (see list)
    c0162 ..> c0100 : type in create_skill
    c0162 ..> c0101 : 2 relationships (see list)
    c0162 ..> c0102 : 2 relationships (see list)
    c0162 ..> c0103 : type in update_skill
    c0162 ..> c0117 : 18 relationships (see list)
    c0162 ..> c0127 : type in __init__
    c0162 ..> c0130 : 3 relationships (see list)
    c0162 ..> c0134 : search_skills() calls rerank()
    c0162 ..> c0135 : type in __init__
    c0162 ..> c0136 : 2 relationships (see list)
    c0162 ..> c0144 : 20 relationships (see list)
    c0162 ..> c0157 : 2 relationships (see list)
    c0162 ..> c0162 : 3 relationships (see list)
    c0163 ..> c0024 : transition_task_state() constructs ConflictError
    c0163 ..> c0028 : 3 relationships (see list)
    c0163 ..> c0030 : update_criterion() calls get()
    c0163 ..> c0077 : 3 relationships (see list)
    c0163 ..> c0078 : type in create_criterion
    c0163 ..> c0079 : type in update_criterion
    c0163 ..> c0085 : 4 relationships (see list)
    c0163 ..> c0086 : type in create_task
    c0163 ..> c0087 : type in add_dependency
    c0163 ..> c0089 : 3 relationships (see list)
    c0163 ..> c0090 : 4 relationships (see list)
    c0163 ..> c0091 : 4 relationships (see list)
    c0163 ..> c0092 : type in update_task
    c0163 ..> c0117 : 12 relationships (see list)
    c0163 ..> c0144 : 16 relationships (see list)
    c0163 ..> c0148 : create_criterion() constructs CriteriaTable
    c0163 ..> c0158 : add_dependency() constructs TaskDependenciesTable
    c0163 ..> c0159 : create_task() constructs TasksTable
    c0163 ..> c0163 : update_task() calls get_task_by_id()
    c0164 ..> c0028 : update_user() constructs NotFoundError
    c0164 ..> c0109 : 4 relationships (see list)
    c0164 ..> c0110 : type in create_user
    c0164 ..> c0112 : type in update_user
    c0164 ..> c0117 : 3 relationships (see list)
    c0164 ..> c0144 : 5 relationships (see list)
    c0164 ..> c0160 : create_user() constructs UsersTable
    c0165 ..> c0033 : 2 relationships (see list)
    c0165 ..> c0034 : type in save_event
    c0165 ..> c0036 : 4 relationships (see list)
    c0165 ..> c0037 : type in query_events
    c0165 ..> c0038 : 2 relationships (see list)
    c0165 ..> c0117 : 3 relationships (see list)
    c0165 ..> c0174 : 5 relationships (see list)
    c0165 ..> c0176 : save_event() constructs ActivityLogTable
    c0166 ..> c0028 : update_code_artifact() constructs NotFoundError
    c0166 ..> c0030 : update_code_artifact() calls get()
    c0166 ..> c0039 : 3 relationships (see list)
    c0166 ..> c0040 : type in create_code_artifact
    c0166 ..> c0041 : type in list_code_artifacts
    c0166 ..> c0042 : type in update_code_artifact
    c0166 ..> c0117 : 4 relationships (see list)
    c0166 ..> c0174 : 6 relationships (see list)
    c0166 ..> c0178 : create_code_artifact() constructs CodeArtifactsTable
    c0167 ..> c0028 : update_document() constructs NotFoundError
    c0167 ..> c0030 : update_document() calls get()
    c0167 ..> c0043 : 3 relationships (see list)
    c0167 ..> c0044 : type in create_document
    c0167 ..> c0045 : type in list_documents
    c0167 ..> c0046 : type in update_document
    c0167 ..> c0117 : 4 relationships (see list)
    c0167 ..> c0174 : 6 relationships (see list)
    c0167 ..> c0180 : create_document() constructs DocumentsTable
    c0168 ..> c0028 : 8 relationships (see list)
    c0168 ..> c0030 : update_entity() calls get()
    c0168 ..> c0047 : 3 relationships (see list)
    c0168 ..> c0048 : type in create_entity
    c0168 ..> c0050 : 8 relationships (see list)
    c0168 ..> c0051 : type in create_entity_relationship
    c0168 ..> c0052 : type in update_entity_relationship
    c0168 ..> c0053 : 2 relationships (see list)
    c0168 ..> c0054 : 2 relationships (see list)
    c0168 ..> c0055 : type in update_entity
    c0168 ..> c0117 : 20 relationships (see list)
    c0168 ..> c0174 : 21 relationships (see list)
    c0168 ..> c0181 : create_entity() constructs EntitiesTable
    c0168 ..> c0182 : create_entity_relationship() constructs EntityRelationshipsTable
    c0169 ..> c0028 : update_file() constructs NotFoundError
    c0169 ..> c0056 : 5 relationships (see list)
    c0169 ..> c0057 : type in create_file
    c0169 ..> c0058 : type in list_files
    c0169 ..> c0059 : type in update_file
    c0169 ..> c0117 : 4 relationships (see list)
    c0169 ..> c0169 : 3 relationships (see list)
    c0169 ..> c0174 : 6 relationships (see list)
    c0169 ..> c0183 : 2 relationships (see list)
    c0170 ..> c0023 : update_memory() calls clear()
    c0170 ..> c0028 : 12 relationships (see list)
    c0170 ..> c0030 : 2 relationships (see list)
    c0170 ..> c0065 : 14 relationships (see list)
    c0170 ..> c0066 : type in create_memory
    c0170 ..> c0072 : 2 relationships (see list)
    c0170 ..> c0074 : type in update_memory
    c0170 ..> c0117 : 27 relationships (see list)
    c0170 ..> c0127 : type in __init__
    c0170 ..> c0130 : _generate_embeddings() calls generate_embedding()
    c0170 ..> c0134 : search_scored() calls rerank()
    c0170 ..> c0135 : type in __init__
    c0170 ..> c0136 : 4 relationships (see list)
    c0170 ..> c0170 : 21 relationships (see list)
    c0170 ..> c0174 : 24 relationships (see list)
    c0170 ..> c0184 : 2 relationships (see list)
    c0170 ..> c0185 : 7 relationships (see list)
    c0171 ..> c0028 : update_plan() constructs NotFoundError
    c0171 ..> c0080 : 3 relationships (see list)
    c0171 ..> c0081 : type in create_plan
    c0171 ..> c0082 : type in list_plans
    c0171 ..> c0083 : type in list_plans
    c0171 ..> c0084 : type in update_plan
    c0171 ..> c0117 : 4 relationships (see list)
    c0171 ..> c0174 : 6 relationships (see list)
    c0171 ..> c0186 : create_plan() constructs PlansTable
    c0172 ..> c0028 : update_project() constructs NotFoundError
    c0172 ..> c0093 : 3 relationships (see list)
    c0172 ..> c0094 : type in create_project
    c0172 ..> c0095 : type in list_projects
    c0172 ..> c0096 : type in list_projects
    c0172 ..> c0098 : type in update_project
    c0172 ..> c0117 : 4 relationships (see list)
    c0172 ..> c0174 : 6 relationships (see list)
    c0172 ..> c0187 : create_project() constructs ProjectsTable
    c0172 ..> c0267 : list_projects() calls repository_identity()
    c0173 ..> c0028 : 6 relationships (see list)
    c0173 ..> c0099 : 5 relationships (see list)
    c0173 ..> c0100 : type in create_skill
    c0173 ..> c0101 : 2 relationships (see list)
    c0173 ..> c0102 : 2 relationships (see list)
    c0173 ..> c0103 : type in update_skill
    c0173 ..> c0117 : 19 relationships (see list)
    c0173 ..> c0127 : type in __init__
    c0173 ..> c0130 : 3 relationships (see list)
    c0173 ..> c0134 : search_skills() calls rerank()
    c0173 ..> c0135 : type in __init__
    c0173 ..> c0136 : 2 relationships (see list)
    c0173 ..> c0173 : 3 relationships (see list)
    c0173 ..> c0174 : 20 relationships (see list)
    c0173 ..> c0188 : 2 relationships (see list)
    c0174 ..> c0003 : _run_migrations() calls upgrade()
    c0174 ..> c0117 : 3 relationships (see list)
    c0174 ..> c0144 : dispose() calls dispose()
    c0174 ..> c0174 : 2 relationships (see list)
    c0175 ..> c0117 : _sqlite_connection_creator() calls execute()
    c0176 --|> c0177 : inherits
    c0178 --|> c0177 : inherits
    c0178 --> c0185 : field memories
    c0178 --> c0187 : field project
    c0178 --> c0188 : field skills
    c0178 --> c0191 : field user
    c0179 --|> c0177 : inherits
    c0179 --> c0190 : field task
    c0180 --|> c0177 : inherits
    c0180 --> c0185 : field memories
    c0180 --> c0187 : field project
    c0180 --> c0188 : field skills
    c0180 --> c0191 : field user
    c0181 --|> c0177 : inherits
    c0181 --> c0182 : 2 relationships (see list)
    c0181 --> c0183 : field files
    c0181 --> c0185 : field memories
    c0181 --> c0187 : field projects
    c0181 --> c0191 : field user
    c0182 --|> c0177 : inherits
    c0182 --> c0181 : 2 relationships (see list)
    c0183 --|> c0177 : inherits
    c0183 --> c0181 : field entities
    c0183 --> c0185 : field memories
    c0183 --> c0187 : field project
    c0183 --> c0188 : field skills
    c0183 --> c0191 : field user
    c0184 --|> c0177 : inherits
    c0185 --|> c0177 : inherits
    c0185 --> c0178 : field code_artifacts
    c0185 --> c0180 : field documents
    c0185 --> c0181 : field entities
    c0185 --> c0183 : field files
    c0185 --> c0187 : field projects
    c0185 --> c0188 : field skills
    c0185 --> c0191 : field user
    c0186 --|> c0177 : inherits
    c0186 --> c0187 : field project
    c0186 --> c0190 : field tasks
    c0186 --> c0191 : field user
    c0187 --|> c0177 : inherits
    c0187 --> c0178 : field code_artifacts
    c0187 --> c0180 : field documents
    c0187 --> c0181 : field entities
    c0187 --> c0183 : field files
    c0187 --> c0185 : field memories
    c0187 --> c0186 : field plans
    c0187 --> c0188 : field skills
    c0187 --> c0191 : field user
    c0188 --|> c0177 : inherits
    c0188 --> c0178 : field code_artifacts
    c0188 --> c0180 : field documents
    c0188 --> c0183 : field files
    c0188 --> c0185 : field memories
    c0188 --> c0187 : field project
    c0188 --> c0191 : field user
    c0189 --|> c0177 : inherits
    c0189 --> c0190 : field task
    c0190 --|> c0177 : inherits
    c0190 --> c0179 : field criteria
    c0190 --> c0186 : field plan
    c0190 --> c0189 : field depends_on
    c0191 --|> c0177 : inherits
    c0191 --> c0178 : field code_artifacts
    c0191 --> c0180 : field documents
    c0191 --> c0181 : field entities
    c0191 --> c0183 : field files
    c0191 --> c0185 : field memories
    c0191 --> c0186 : field plans
    c0191 --> c0187 : field projects
    c0191 --> c0188 : field skills
    c0192 ..> c0024 : transition_task_state() constructs ConflictError
    c0192 ..> c0028 : 3 relationships (see list)
    c0192 ..> c0030 : update_criterion() calls get()
    c0192 ..> c0077 : 3 relationships (see list)
    c0192 ..> c0078 : type in create_criterion
    c0192 ..> c0079 : type in update_criterion
    c0192 ..> c0085 : 4 relationships (see list)
    c0192 ..> c0086 : type in create_task
    c0192 ..> c0087 : type in add_dependency
    c0192 ..> c0089 : 3 relationships (see list)
    c0192 ..> c0090 : 4 relationships (see list)
    c0192 ..> c0091 : 4 relationships (see list)
    c0192 ..> c0092 : type in update_task
    c0192 ..> c0117 : 12 relationships (see list)
    c0192 ..> c0174 : 16 relationships (see list)
    c0192 ..> c0179 : create_criterion() constructs CriteriaTable
    c0192 ..> c0189 : add_dependency() constructs TaskDependenciesTable
    c0192 ..> c0190 : create_task() constructs TasksTable
    c0192 ..> c0192 : update_task() calls get_task_by_id()
    c0193 ..> c0028 : update_user() constructs NotFoundError
    c0193 ..> c0109 : 4 relationships (see list)
    c0193 ..> c0110 : type in create_user
    c0193 ..> c0112 : type in update_user
    c0193 ..> c0117 : 3 relationships (see list)
    c0193 ..> c0174 : 5 relationships (see list)
    c0193 ..> c0191 : create_user() constructs UsersTable
    c0194 ..> c0030 : 2 relationships (see list)
    c0198 ..> c0030 : parse_int_param() calls get()
    c0202 ..> c0030 : parse_int_param() calls get()
    c0207 ..> c0030 : status() calls get()
    c0207 ..> c0207 : 2 relationships (see list)
    c0207 ..> c0212 : 4 relationships (see list)
    c0207 ..> c0213 : 3 relationships (see list)
    c0207 ..> c0214 : 2 relationships (see list)
    c0208 ..> c0013 : type in __init__
    c0208 ..> c0209 : __init__() constructs _CliRuntime
    c0209 ..> c0013 : type in __init__
    c0210 ..> c0013 : type in __init__
    c0210 ..> c0015 : 2 relationships (see list)
    c0210 ..> c0117 : execute() calls execute()
    c0210 ..> c0208 : __init__() constructs CliContext
    c0210 ..> c0222 : 3 relationships (see list)
    c0211 ..> c0030 : _build_executor() calls get()
    c0211 ..> c0117 : 4 relationships (see list)
    c0211 ..> c0207 : 3 relationships (see list)
    c0211 ..> c0210 : _build_executor() calls create()
    c0211 ..> c0211 : 4 relationships (see list)
    c0211 ..> c0213 : _build_executor() constructs RemoteExecutor
    c0211 ..> c0215 : 3 relationships (see list)
    c0211 ..> c0217 : 2 relationships (see list)
    c0211 ..> c0269 : build_parser() calls get_version()
    c0212 ..> c0212 : 2 relationships (see list)
    c0213 ..> c0117 : close() calls close()
    c0213 ..> c0213 : 3 relationships (see list)
    c0213 ..> c0214 : __init__() calls normalize_server_url()
    c0214 ..> c0212 : _default_client_factory() calls token_cache_dir()
    c0215 ..> c0030 : 3 relationships (see list)
    c0215 ..> c0215 : render_result() calls to_jsonable()
    c0217 ..> c0030 : 4 relationships (see list)
    c0217 ..> c0117 : 6 relationships (see list)
    c0217 ..> c0215 : 10 relationships (see list)
    c0217 ..> c0216 : resolve_project() constructs CliError
    c0217 ..> c0217 : 4 relationships (see list)
    c0222 ..> c0104 : build_discovery_payload() constructs ToolCategory
    c0222 ..> c0107 : 2 relationships (see list)
    c0222 ..> c0222 : 8 relationships (see list)
    c0222 ..> c0225 : 2 relationships (see list)
    c0222 ..> c0239 : 8 relationships (see list)
    c0225 ..> c0030 : 3 relationships (see list)
    c0225 ..> c0225 : 3 relationships (see list)
    c0225 ..> c0239 : 5 relationships (see list)
    c0227 ..> c0031 : 5 relationships (see list)
    c0227 ..> c0039 : 3 relationships (see list)
    c0227 ..> c0040 : create_code_artifact() constructs CodeArtifactCreate
    c0227 ..> c0042 : update_code_artifact() constructs CodeArtifactUpdate
    c0227 ..> c0243 : 6 relationships (see list)
    c0227 ..> c0264 : type in __init__
    c0227 ..> c0266 : update_code_artifact() calls filter_none_values()
    c0228 ..> c0031 : 5 relationships (see list)
    c0228 ..> c0043 : 3 relationships (see list)
    c0228 ..> c0044 : create_document() constructs DocumentCreate
    c0228 ..> c0046 : update_document() constructs DocumentUpdate
    c0228 ..> c0244 : 6 relationships (see list)
    c0228 ..> c0264 : type in __init__
    c0228 ..> c0266 : update_document() calls filter_none_values()
    c0229 ..> c0031 : 16 relationships (see list)
    c0229 ..> c0047 : 3 relationships (see list)
    c0229 ..> c0048 : create_entity() constructs EntityCreate
    c0229 ..> c0050 : 2 relationships (see list)
    c0229 ..> c0051 : create_entity_relationship() constructs EntityRelationshipCreate
    c0229 ..> c0052 : update_entity_relationship() constructs EntityRelationshipUpdate
    c0229 ..> c0054 : 2 relationships (see list)
    c0229 ..> c0055 : update_entity() constructs EntityUpdate
    c0229 ..> c0245 : 17 relationships (see list)
    c0229 ..> c0264 : type in __init__
    c0229 ..> c0266 : 3 relationships (see list)
    c0230 ..> c0031 : 5 relationships (see list)
    c0230 ..> c0057 : create_file() constructs FileCreate
    c0230 ..> c0059 : update_file() constructs FileUpdate
    c0230 ..> c0118 : 4 relationships (see list)
    c0230 ..> c0246 : get_file() calls get_file()
    c0230 ..> c0264 : type in __init__
    c0230 ..> c0266 : update_file() calls filter_none_values()
    c0231 ..> c0031 : 9 relationships (see list)
    c0231 ..> c0065 : 2 relationships (see list)
    c0231 ..> c0066 : create_memory() constructs MemoryCreate
    c0231 ..> c0067 : 2 relationships (see list)
    c0231 ..> c0070 : query_memory() constructs MemoryQueryRequest
    c0231 ..> c0071 : type in query_memory
    c0231 ..> c0074 : update_memory() constructs MemoryUpdate
    c0231 ..> c0119 : Relation116
    c0231 ..> c0223 : get_recent_memories() calls clamp_list_pagination()
    c0231 ..> c0231 : 2 relationships (see list)
    c0231 ..> c0237 : 13 relationships (see list)
    c0231 ..> c0255 : 10 relationships (see list)
    c0231 ..> c0259 : 3 relationships (see list)
    c0231 ..> c0264 : type in __init__
    c0231 ..> c0266 : update_memory() calls filter_none_values()
    c0232 ..> c0031 : 4 relationships (see list)
    c0232 ..> c0081 : create_plan() constructs PlanCreate
    c0232 ..> c0082 : 3 relationships (see list)
    c0232 ..> c0084 : update_plan() constructs PlanUpdate
    c0232 ..> c0121 : 3 relationships (see list)
    c0232 ..> c0251 : get_plan() calls get_plan()
    c0232 ..> c0266 : update_plan() calls filter_none_values()
    c0233 ..> c0031 : 5 relationships (see list)
    c0233 ..> c0093 : 3 relationships (see list)
    c0233 ..> c0094 : create_project() constructs ProjectCreate
    c0233 ..> c0095 : 3 relationships (see list)
    c0233 ..> c0097 : 2 relationships (see list)
    c0233 ..> c0098 : update_project() constructs ProjectUpdate
    c0233 ..> c0257 : 6 relationships (see list)
    c0233 ..> c0264 : type in __init__
    c0233 ..> c0266 : update_project() calls filter_none_values()
    c0234 ..> c0031 : 17 relationships (see list)
    c0234 ..> c0100 : create_skill() constructs SkillCreate
    c0234 ..> c0103 : update_skill() constructs SkillUpdate
    c0234 ..> c0123 : 14 relationships (see list)
    c0234 ..> c0253 : get_skill() calls get_skill()
    c0234 ..> c0261 : 2 relationships (see list)
    c0234 ..> c0264 : type in __init__
    c0234 ..> c0266 : update_skill() calls filter_none_values()
    c0235 ..> c0031 : 11 relationships (see list)
    c0235 ..> c0078 : 2 relationships (see list)
    c0235 ..> c0079 : verify_criterion() constructs CriterionUpdate
    c0235 ..> c0086 : create_task() constructs TaskCreate
    c0235 ..> c0089 : 3 relationships (see list)
    c0235 ..> c0090 : 2 relationships (see list)
    c0235 ..> c0092 : update_task() constructs TaskUpdate
    c0235 ..> c0124 : 7 relationships (see list)
    c0235 ..> c0254 : get_task() calls get_task()
    c0235 ..> c0263 : 3 relationships (see list)
    c0235 ..> c0266 : update_task() calls filter_none_values()
    c0236 ..> c0031 : 2 relationships (see list)
    c0236 ..> c0111 : 4 relationships (see list)
    c0236 ..> c0112 : update_user_notes() constructs UserUpdate
    c0236 ..> c0264 : 2 relationships (see list)
    c0237 ..> c0227 : Relation117
    c0237 ..> c0228 : create_document_adapters() constructs DocumentToolAdapters
    c0237 ..> c0229 : create_entity_adapters() constructs EntityToolAdapters
    c0237 ..> c0230 : create_file_adapters() constructs FileToolAdapters
    c0237 ..> c0231 : create_memory_adapters() constructs MemoryToolAdapters
    c0237 ..> c0232 : create_plan_adapters() constructs PlanToolAdapters
    c0237 ..> c0233 : create_project_adapters() constructs ProjectToolAdapters
    c0237 ..> c0234 : create_skill_adapters() constructs SkillToolAdapters
    c0237 ..> c0235 : create_task_adapters() constructs TaskToolAdapters
    c0237 ..> c0236 : create_user_adapters() constructs UserToolAdapters
    c0237 ..> c0237 : _coerce_int_ids() calls _coerce_int_id()
    c0237 ..> c0243 : type in create_code_artifact_adapters
    c0237 ..> c0244 : type in create_document_adapters
    c0237 ..> c0245 : type in create_entity_adapters
    c0237 ..> c0255 : type in create_memory_adapters
    c0237 ..> c0257 : type in create_project_adapters
    c0237 ..> c0264 : 8 relationships (see list)
    c0238 ..> c0030 : 11 relationships (see list)
    c0238 ..> c0104 : type in register_simplified_tool
    c0238 ..> c0108 : register_simplified_tool() constructs ToolParameter
    c0238 ..> c0237 : 10 relationships (see list)
    c0238 ..> c0238 : 20 relationships (see list)
    c0238 ..> c0239 : 14 relationships (see list)
    c0238 ..> c0255 : type in register_all_tools_metadata
    c0238 ..> c0264 : type in register_all_tools_metadata
    c0239 ..> c0030 : 3 relationships (see list)
    c0239 ..> c0104 : 3 relationships (see list)
    c0239 --> c0106 : field _tools
    c0239 ..> c0106 : 2 relationships (see list)
    c0239 ..> c0107 : 5 relationships (see list)
    c0239 ..> c0108 : type in register
    c0239 ..> c0239 : execute() calls get_tool()
    c0241 ..> c0033 : 2 relationships (see list)
    c0241 ..> c0034 : type in handle_event
    c0241 ..> c0035 : 3 relationships (see list)
    c0241 ..> c0037 : type in get_activity
    c0241 ..> c0038 : 3 relationships (see list)
    c0241 ..> c0113 : 5 relationships (see list)
    c0241 ..> c0241 : 2 relationships (see list)
    c0242 ..> c0217 : 2 relationships (see list)
    c0242 ..> c0242 : 4 relationships (see list)
    c0243 ..> c0023 : 2 relationships (see list)
    c0243 ..> c0028 : 2 relationships (see list)
    c0243 ..> c0033 : type in _emit_event
    c0243 ..> c0034 : _emit_event() constructs ActivityEvent
    c0243 ..> c0038 : type in _emit_event
    c0243 ..> c0039 : 3 relationships (see list)
    c0243 ..> c0040 : type in create_code_artifact
    c0243 ..> c0041 : type in list_code_artifacts
    c0243 ..> c0042 : type in update_code_artifact
    c0243 ..> c0114 : 8 relationships (see list)
    c0243 ..> c0243 : 5 relationships (see list)
    c0243 ..> c0265 : 2 relationships (see list)
    c0243 ..> c0266 : update_code_artifact() calls get_changed_fields()
    c0244 ..> c0023 : 2 relationships (see list)
    c0244 ..> c0028 : 2 relationships (see list)
    c0244 ..> c0033 : type in _emit_event
    c0244 ..> c0034 : _emit_event() constructs ActivityEvent
    c0244 ..> c0038 : type in _emit_event
    c0244 ..> c0043 : 3 relationships (see list)
    c0244 ..> c0044 : type in create_document
    c0244 ..> c0045 : type in list_documents
    c0244 ..> c0046 : type in update_document
    c0244 ..> c0115 : 8 relationships (see list)
    c0244 ..> c0244 : 5 relationships (see list)
    c0244 ..> c0265 : 2 relationships (see list)
    c0244 ..> c0266 : update_document() calls get_changed_fields()
    c0245 ..> c0023 : 2 relationships (see list)
    c0245 ..> c0028 : 2 relationships (see list)
    c0245 ..> c0033 : type in _emit_event
    c0245 ..> c0034 : _emit_event() constructs ActivityEvent
    c0245 ..> c0038 : type in _emit_event
    c0245 ..> c0047 : 3 relationships (see list)
    c0245 ..> c0048 : type in create_entity
    c0245 ..> c0050 : 4 relationships (see list)
    c0245 ..> c0051 : type in create_entity_relationship
    c0245 ..> c0052 : type in update_entity_relationship
    c0245 ..> c0053 : 2 relationships (see list)
    c0245 ..> c0054 : 2 relationships (see list)
    c0245 ..> c0055 : type in update_entity
    c0245 ..> c0116 : 23 relationships (see list)
    c0245 ..> c0245 : 13 relationships (see list)
    c0245 ..> c0265 : 4 relationships (see list)
    c0245 ..> c0266 : update_entity() calls get_changed_fields()
    c0246 ..> c0023 : 2 relationships (see list)
    c0246 ..> c0028 : 2 relationships (see list)
    c0246 ..> c0033 : type in _emit_event
    c0246 ..> c0034 : _emit_event() constructs ActivityEvent
    c0246 ..> c0038 : type in _emit_event
    c0246 ..> c0056 : 4 relationships (see list)
    c0246 ..> c0057 : type in create_file
    c0246 ..> c0058 : type in list_files
    c0246 ..> c0059 : type in update_file
    c0246 ..> c0118 : 8 relationships (see list)
    c0246 ..> c0246 : 9 relationships (see list)
    c0246 ..> c0265 : 2 relationships (see list)
    c0246 ..> c0266 : update_file() calls get_changed_fields()
    c0250 ..> c0028 : _validate_center_node() constructs NotFoundError
    c0250 ..> c0030 : _fetch_node_data() calls get()
    c0250 ..> c0060 : 2 relationships (see list)
    c0250 ..> c0061 : get_subgraph() constructs SubgraphMeta
    c0250 ..> c0062 : 2 relationships (see list)
    c0250 ..> c0063 : 2 relationships (see list)
    c0250 ..> c0116 : 7 relationships (see list)
    c0250 ..> c0119 : 5 relationships (see list)
    c0250 ..> c0247 : 4 relationships (see list)
    c0250 ..> c0248 : 4 relationships (see list)
    c0250 ..> c0249 : 4 relationships (see list)
    c0250 ..> c0250 : 4 relationships (see list)
    c0250 ..> c0251 : 4 relationships (see list)
    c0250 ..> c0252 : 3 relationships (see list)
    c0250 ..> c0253 : 7 relationships (see list)
    c0250 ..> c0254 : 3 relationships (see list)
    c0255 ..> c0023 : 4 relationships (see list)
    c0255 ..> c0030 : handle_memory_access_event() calls get()
    c0255 ..> c0033 : type in _emit_event
    c0255 ..> c0034 : 2 relationships (see list)
    c0255 ..> c0038 : type in _emit_event
    c0255 ..> c0064 : 3 relationships (see list)
    c0255 ..> c0065 : 8 relationships (see list)
    c0255 ..> c0066 : type in create_memory
    c0255 ..> c0070 : type in query_memory
    c0255 ..> c0071 : 2 relationships (see list)
    c0255 ..> c0073 : 2 relationships (see list)
    c0255 ..> c0074 : type in update_memory
    c0255 ..> c0075 : 2 relationships (see list)
    c0255 ..> c0119 : 17 relationships (see list)
    c0255 ..> c0255 : 12 relationships (see list)
    c0255 ..> c0265 : 2 relationships (see list)
    c0255 ..> c0266 : update_memory() calls get_changed_fields()
    c0255 ..> c0268 : 2 relationships (see list)
    c0256 ..> c0023 : 2 relationships (see list)
    c0256 ..> c0027 : update_plan() constructs InvalidStateTransitionError
    c0256 ..> c0028 : get_plan() constructs NotFoundError
    c0256 ..> c0030 : update_plan() calls get()
    c0256 ..> c0033 : type in _emit_event
    c0256 ..> c0034 : _emit_event() constructs ActivityEvent
    c0256 ..> c0038 : type in _emit_event
    c0256 ..> c0080 : 3 relationships (see list)
    c0256 ..> c0081 : type in create_plan
    c0256 ..> c0082 : 3 relationships (see list)
    c0256 ..> c0083 : type in list_plans
    c0256 ..> c0084 : type in update_plan
    c0256 ..> c0121 : 9 relationships (see list)
    c0256 ..> c0256 : 4 relationships (see list)
    c0256 ..> c0265 : 2 relationships (see list)
    c0256 ..> c0266 : update_plan() calls get_changed_fields()
    c0257 ..> c0023 : 2 relationships (see list)
    c0257 ..> c0028 : get_project() constructs NotFoundError
    c0257 ..> c0033 : type in _emit_event
    c0257 ..> c0034 : _emit_event() constructs ActivityEvent
    c0257 ..> c0038 : type in _emit_event
    c0257 ..> c0093 : 3 relationships (see list)
    c0257 ..> c0094 : type in create_project
    c0257 ..> c0095 : type in list_projects
    c0257 ..> c0096 : type in list_projects
    c0257 ..> c0098 : type in update_project
    c0257 ..> c0122 : 8 relationships (see list)
    c0257 ..> c0257 : 5 relationships (see list)
    c0257 ..> c0265 : 2 relationships (see list)
    c0257 ..> c0266 : update_project() calls get_changed_fields()
    c0258 --> c0120 : field validation
    c0259 ..> c0119 : 13 relationships (see list)
    c0259 ..> c0120 : 3 relationships (see list)
    c0259 ..> c0127 : type in __init__
    c0259 ..> c0130 : 2 relationships (see list)
    c0259 ..> c0136 : 2 relationships (see list)
    c0259 ..> c0258 : 2 relationships (see list)
    c0259 ..> c0259 : 3 relationships (see list)
    c0259 ..> c0260 : 4 relationships (see list)
    c0261 ..> c0023 : 2 relationships (see list)
    c0261 ..> c0028 : 2 relationships (see list)
    c0261 ..> c0030 : import_skill() calls get()
    c0261 ..> c0033 : type in _emit_event
    c0261 ..> c0034 : _emit_event() constructs ActivityEvent
    c0261 ..> c0038 : type in _emit_event
    c0261 ..> c0099 : 4 relationships (see list)
    c0261 ..> c0100 : 2 relationships (see list)
    c0261 ..> c0101 : type in get_skill_links
    c0261 ..> c0102 : 2 relationships (see list)
    c0261 ..> c0103 : type in update_skill
    c0261 ..> c0123 : 23 relationships (see list)
    c0261 ..> c0261 : 14 relationships (see list)
    c0261 ..> c0262 : import_skill() calls _quote_unquoted_frontmatter_scalars()
    c0261 ..> c0265 : 2 relationships (see list)
    c0261 ..> c0266 : update_skill() calls get_changed_fields()
    c0263 ..> c0023 : 2 relationships (see list)
    c0263 ..> c0024 : 2 relationships (see list)
    c0263 ..> c0025 : _validate_no_cycle() constructs CyclicDependencyError
    c0263 ..> c0026 : _validate_dependencies_met() constructs DependencyNotMetError
    c0263 ..> c0027 : 5 relationships (see list)
    c0263 ..> c0028 : 6 relationships (see list)
    c0263 ..> c0030 : transition_task() calls get()
    c0263 ..> c0033 : type in _emit_event
    c0263 ..> c0034 : _emit_event() constructs ActivityEvent
    c0263 ..> c0038 : type in _emit_event
    c0263 ..> c0077 : 2 relationships (see list)
    c0263 ..> c0078 : type in add_criterion
    c0263 ..> c0079 : type in update_criterion
    c0263 ..> c0082 : 2 relationships (see list)
    c0263 ..> c0084 : _check_plan_auto_completion() constructs PlanUpdate
    c0263 ..> c0085 : 7 relationships (see list)
    c0263 ..> c0086 : type in create_task
    c0263 ..> c0089 : type in list_tasks
    c0263 ..> c0090 : 7 relationships (see list)
    c0263 ..> c0091 : 2 relationships (see list)
    c0263 ..> c0092 : type in update_task
    c0263 ..> c0124 : 28 relationships (see list)
    c0263 ..> c0256 : 9 relationships (see list)
    c0263 ..> c0263 : 9 relationships (see list)
    c0263 ..> c0265 : 2 relationships (see list)
    c0263 ..> c0266 : update_task() calls get_changed_fields()
    c0264 ..> c0109 : 3 relationships (see list)
    c0264 ..> c0110 : 2 relationships (see list)
    c0264 ..> c0112 : 2 relationships (see list)
    c0264 ..> c0125 : 8 relationships (see list)
    c0264 ..> c0266 : 2 relationships (see list)
    c0270 ..> c0133 : fast_embed_rank() constructs FastEmbedCrossEncoderAdapter
    c0270 ..> c0134 : 3 relationships (see list)
    c0271 ..> c0117 : 4 relationships (see list)
    c0272 ..> c0129 : test_embeddings() constructs GoogleEmbeddingsAdapter
    c0272 ..> c0130 : test_embeddings() calls generate_embedding()
    c0273 ..> c0117 : main() calls list_tools()
    c0274 ..> c0117 : test_sqlite_init() calls execute()
    c0274 ..> c0174 : 5 relationships (see list)
    c0275 ..> c0015 : 5 relationships (see list)
    c0275 ..> c0020 : 2 relationships (see list)
    c0275 ..> c0030 : lifespan() constructs TokenCache
    c0275 ..> c0119 : 2 relationships (see list)
    c0275 ..> c0144 : 2 relationships (see list)
    c0275 ..> c0194 : 2 relationships (see list)
    c0275 ..> c0211 : cli() calls dispatch()
    c0275 ..> c0217 : 2 relationships (see list)
    c0275 ..> c0242 : 3 relationships (see list)
    c0275 ..> c0259 : 2 relationships (see list)
    c0275 ..> c0269 : _legacy_launcher() calls get_version()
    c0275 ..> c0275 : 3 relationships (see list)
    c0276 ..> c0276 : 3 relationships (see list)
    c0276 ..> c0277 : 3 relationships (see list)
    c0276 ..> c0278 : 3 relationships (see list)
    c0276 ..> c0279 : _run() calls ensure_image()
    c0276 ..> c0292 : 2 relationships (see list)
    c0276 ..> c0296 : type in _print_summary
    c0276 ..> c0297 : 4 relationships (see list)
    c0277 ..> c0030 : timeout_for() calls get()
    c0278 ..> c0023 : stop() calls clear()
    c0278 ..> c0030 : start() calls get()
    c0278 ..> c0117 : _exec() calls close()
    c0278 ..> c0277 : type in __init__
    c0278 ..> c0278 : 2 relationships (see list)
    c0278 ..> c0279 : 5 relationships (see list)
    c0278 ..> c0291 : 3 relationships (see list)
    c0278 ..> c0292 : stop() calls stop()
    c0278 ..> c0294 : 2 relationships (see list)
    c0278 ..> c0297 : start() calls run()
    c0279 ..> c0030 : ensure_image() calls get()
    c0279 ..> c0279 : 4 relationships (see list)
    c0279 ..> c0291 : 4 relationships (see list)
    c0279 ..> c0297 : 3 relationships (see list)
    c0280 ..> c0030 : 2 relationships (see list)
    c0280 ..> c0217 : main() calls run()
    c0280 ..> c0278 : health() calls health_check()
    c0280 ..> c0280 : 5 relationships (see list)
    c0281 ..> c0030 : build_prompt() calls get()
    c0281 ..> c0286 : build_prompt() calls report_contract_example()
    c0283 --> c0285 : field report
    c0285 --> c0282 : field issues
    c0285 --> c0284 : field steps
    c0286 ..> c0030 : _normalize_severity() calls get()
    c0286 ..> c0283 : 2 relationships (see list)
    c0286 ..> c0286 : 3 relationships (see list)
    c0292 ..> c0030 : _wait_until_healthy() calls get()
    c0292 ..> c0213 : 5 relationships (see list)
    c0292 ..> c0291 : 3 relationships (see list)
    c0292 ..> c0292 : 3 relationships (see list)
    c0292 ..> c0293 : start() calls _ephemeral_port()
    c0295 ..> c0294 : type in run_session
    c0296 --> c0283 : field report_load
    c0297 ..> c0030 : run_skill() calls get()
    c0297 ..> c0277 : 2 relationships (see list)
    c0297 ..> c0281 : run_skill() calls build_prompt()
    c0297 ..> c0286 : run_skill() calls load_report()
    c0297 ..> c0295 : 2 relationships (see list)
    c0297 ..> c0296 : 5 relationships (see list)
    c0297 ..> c0297 : 3 relationships (see list)
    c0297 ..> c0298 : 3 relationships (see list)
    c0298 ..> c0030 : scan_for_breaches() calls get()
    c0298 ..> c0298 : prepare_workspace() calls _build_fixture_repo()
```

## Source index

- c0000: `alembic/_db_helpers/db_postgres_impl.py` — `alembic/_db_helpers/db_postgres_impl.py`:1
- c0001: `alembic/_db_helpers/db_sqlite_impl.py` — `alembic/_db_helpers/db_sqlite_impl.py`:1
- c0002: `alembic/env.py` — `alembic/env.py`:1
- c0003: `alembic/versions/0c7b964dd1e7_initial_schema_with_entity_many_to_many.py` —
  `alembic/versions/0c7b964dd1e7_initial_schema_with_entity_many_to_many.py`:1
- c0004: `alembic/versions/20251216143413_add_aka_to_entities.py` —
  `alembic/versions/20251216143413_add_aka_to_entities.py`:1
- c0005: `alembic/versions/20260106_add_activity_log_table.py` —
  `alembic/versions/20260106_add_activity_log_table.py`:1
- c0006: `alembic/versions/20260106_add_provenance_tracking_to_memories.py` —
  `alembic/versions/20260106_add_provenance_tracking_to_memories.py`:1
- c0007: `alembic/versions/20260312_add_plans_tasks_criteria_dependencies.py` —
  `alembic/versions/20260312_add_plans_tasks_criteria_dependencies.py`:1
- c0008: `alembic/versions/20260315_add_files_table.py` —
  `alembic/versions/20260315_add_files_table.py`:1
- c0009: `alembic/versions/20260321_add_skills_table.py` —
  `alembic/versions/20260321_add_skills_table.py`:1
- c0010: `alembic/versions/20260408_add_provenance_to_all_object_types.py` —
  `alembic/versions/20260408_add_provenance_to_all_object_types.py`:1
- c0011: `alembic/versions/20260704_add_memory_usage_tracking.py` —
  `alembic/versions/20260704_add_memory_usage_tracking.py`:1
- c0012: `alembic/versions/20260822_add_project_last_encoding_point.py` —
  `alembic/versions/20260822_add_project_last_encoding_point.py`:1
- c0013: `Runtime` — `app/bootstrap.py`:203
- c0014: `Services` — `app/bootstrap.py`:185
- c0015: `app/bootstrap.py` — `app/bootstrap.py`:1
- c0016: `app/config/auth.py` — `app/config/auth.py`:1
- c0017: `ConsoleFormatter` — `app/config/logging_config.py`:21
- c0018: `JSONFormatter` — `app/config/logging_config.py`:104
- c0019: `SensitiveDataFilter` — `app/config/logging_config.py`:56
- c0020: `app/config/logging_config.py` — `app/config/logging_config.py`:1
- c0021: `Settings` — `app/config/settings.py`:33
- c0022: `app/config/settings.py` — `app/config/settings.py`:1
- c0023: `EventBus` — `app/events/event_bus.py`:28
- c0024: `ConflictError` — `app/exceptions.py`:7
- c0025: `CyclicDependencyError` — `app/exceptions.py`:19
- c0026: `DependencyNotMetError` — `app/exceptions.py`:15
- c0027: `InvalidStateTransitionError` — `app/exceptions.py`:11
- c0028: `NotFoundError` — `app/exceptions.py`:4
- c0029: `CacheEntry` — `app/middleware/auth.py`:23
- c0030: `TokenCache` — `app/middleware/auth.py`:29
- c0031: `app/middleware/auth.py` — `app/middleware/auth.py`:1
- c0032: `app/middleware/logging_middleware.py` — `app/middleware/logging_middleware.py`:1
- c0033: `ActionType` — `app/models/activity_models.py`:33
- c0034: `ActivityEvent` — `app/models/activity_models.py`:49
- c0035: `ActivityListResponse` — `app/models/activity_models.py`:126
- c0036: `ActivityLogEntry` — `app/models/activity_models.py`:102
- c0037: `ActorType` — `app/models/activity_models.py`:42
- c0038: `EntityType` — `app/models/activity_models.py`:14
- c0039: `CodeArtifact` — `app/models/code_artifact_models.py`:222
- c0040: `CodeArtifactCreate` — `app/models/code_artifact_models.py`:13
- c0041: `CodeArtifactSummary` — `app/models/code_artifact_models.py`:253
- c0042: `CodeArtifactUpdate` — `app/models/code_artifact_models.py`:116
- c0043: `Document` — `app/models/document_models.py`:238
- c0044: `DocumentCreate` — `app/models/document_models.py`:13
- c0045: `DocumentSummary` — `app/models/document_models.py`:269
- c0046: `DocumentUpdate` — `app/models/document_models.py`:130
- c0047: `Entity` — `app/models/entity_models.py`:285
- c0048: `EntityCreate` — `app/models/entity_models.py`:34
- c0049: `EntityListResponse` — `app/models/entity_models.py`:365
- c0050: `EntityRelationship` — `app/models/entity_models.py`:537
- c0051: `EntityRelationshipCreate` — `app/models/entity_models.py`:391
- c0052: `EntityRelationshipUpdate` — `app/models/entity_models.py`:473
- c0053: `EntitySummary` — `app/models/entity_models.py`:316
- c0054: `EntityType` — `app/models/entity_models.py`:15
- c0055: `EntityUpdate` — `app/models/entity_models.py`:158
- c0056: `File` — `app/models/file_models.py`:233
- c0057: `FileCreate` — `app/models/file_models.py`:14
- c0058: `FileSummary` — `app/models/file_models.py`:263
- c0059: `FileUpdate` — `app/models/file_models.py`:124
- c0060: `SubgraphEdge` — `app/models/graph_models.py`:36
- c0061: `SubgraphMeta` — `app/models/graph_models.py`:81
- c0062: `SubgraphNode` — `app/models/graph_models.py`:10
- c0063: `SubgraphResponse` — `app/models/graph_models.py`:253
- c0064: `LinkedMemory` — `app/models/memory_models.py`:421
- c0065: `Memory` — `app/models/memory_models.py`:272
- c0066: `MemoryCreate` — `app/models/memory_models.py`:8
- c0067: `MemoryCreateResponse` — `app/models/memory_models.py`:340
- c0068: `MemoryLinkRequest` — `app/models/memory_models.py`:441
- c0069: `MemoryListResponse` — `app/models/memory_models.py`:363
- c0070: `MemoryQueryRequest` — `app/models/memory_models.py`:370
- c0071: `MemoryQueryResult` — `app/models/memory_models.py`:428
- c0072: `MemoryScore` — `app/models/memory_models.py`:317
- c0073: `MemorySummary` — `app/models/memory_models.py`:300
- c0074: `MemoryUpdate` — `app/models/memory_models.py`:143
- c0075: `ObsoleteMatch` — `app/models/memory_models.py`:328
- c0076: `HealthStatus` — `app/models/models.py`:8
- c0077: `Criterion` — `app/models/plan_models.py`:92
- c0078: `CriterionCreate` — `app/models/plan_models.py`:71
- c0079: `CriterionUpdate` — `app/models/plan_models.py`:81
- c0080: `Plan` — `app/models/plan_models.py`:211
- c0081: `PlanCreate` — `app/models/plan_models.py`:138
- c0082: `PlanStatus` — `app/models/plan_models.py`:20
- c0083: `PlanSummary` — `app/models/plan_models.py`:221
- c0084: `PlanUpdate` — `app/models/plan_models.py`:175
- c0085: `Task` — `app/models/plan_models.py`:313
- c0086: `TaskCreate` — `app/models/plan_models.py`:239
- c0087: `TaskDependency` — `app/models/plan_models.py`:123
- c0088: `TaskDependencyCreate` — `app/models/plan_models.py`:110
- c0089: `TaskPriority` — `app/models/plan_models.py`:37
- c0090: `TaskState` — `app/models/plan_models.py`:28
- c0091: `TaskSummary` — `app/models/plan_models.py`:343
- c0092: `TaskUpdate` — `app/models/plan_models.py`:278
- c0093: `Project` — `app/models/project_models.py`:223
- c0094: `ProjectCreate` — `app/models/project_models.py`:33
- c0095: `ProjectStatus` — `app/models/project_models.py`:26
- c0096: `ProjectSummary` — `app/models/project_models.py`:254
- c0097: `ProjectType` — `app/models/project_models.py`:9
- c0098: `ProjectUpdate` — `app/models/project_models.py`:129
- c0099: `Skill` — `app/models/skill_models.py`:202
- c0100: `SkillCreate` — `app/models/skill_models.py`:16
- c0101: `SkillLinks` — `app/models/skill_models.py`:234
- c0102: `SkillSummary` — `app/models/skill_models.py`:215
- c0103: `SkillUpdate` — `app/models/skill_models.py`:132
- c0104: `ToolCategory` — `app/models/tool_registry_models.py`:11
- c0105: `ToolDataDetailed` — `app/models/tool_registry_models.py`:147
- c0106: `ToolImplementation` — `app/models/tool_registry_models.py`:154
- c0107: `ToolMetadata` — `app/models/tool_registry_models.py`:34
- c0108: `ToolParameter` — `app/models/tool_registry_models.py`:25
- c0109: `User` — `app/models/user_models.py`:21
- c0110: `UserCreate` — `app/models/user_models.py`:7
- c0111: `UserResponse` — `app/models/user_models.py`:28
- c0112: `UserUpdate` — `app/models/user_models.py`:14
- c0113: `ActivityRepository` — `app/protocols/activity_protocol.py`:20
- c0114: `CodeArtifactRepository` — `app/protocols/code_artifact_protocol.py`:17
- c0115: `DocumentRepository` — `app/protocols/document_protocol.py`:17
- c0116: `EntityRepository` — `app/protocols/entity_protocol.py`:21
- c0117: `ToolExecutor` — `app/protocols/executor.py`:10
- c0118: `FileRepository` — `app/protocols/file_protocol.py`:17
- c0119: `MemoryRepository` — `app/protocols/memory_protocol.py`:21
- c0120: `ValidationResult` — `app/protocols/memory_protocol.py`:10
- c0121: `PlanRepository` — `app/protocols/plan_protocol.py`:13
- c0122: `ProjectRepository` — `app/protocols/project_protocol.py`:13
- c0123: `SkillRepository` — `app/protocols/skill_protocol.py`:18
- c0124: `TaskRepository` — `app/protocols/task_protocol.py`:18
- c0125: `UserRepository` — `app/protocols/user_protocol.py`:7
- c0126: `AzureOpenAIAdapter` — `app/repositories/embeddings/embedding_adapter.py`:71
- c0127: `EmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:16
- c0128: `FastEmbeddingAdapter` — `app/repositories/embeddings/embedding_adapter.py`:21
- c0129: `GoogleEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:106
- c0130: `OllamaEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:201
- c0131: `OpenAIEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:143
- c0132: `app/repositories/embeddings/fastembed_offline.py` —
  `app/repositories/embeddings/fastembed_offline.py`:1
- c0133: `FastEmbedCrossEncoderAdapter` — `app/repositories/embeddings/reranker_adapter.py`:21
- c0134: `HttpRerankAdapter` — `app/repositories/embeddings/reranker_adapter.py`:111
- c0135: `RerankAdapter` — `app/repositories/embeddings/reranker_adapter.py`:13
- c0136: `app/repositories/helpers.py` — `app/repositories/helpers.py`:1
- c0137: `PostgresActivityRepository` — `app/repositories/postgres/activity_repository.py`:26
- c0138: `PostgresCodeArtifactRepository` —
  `app/repositories/postgres/code_artifact_repository.py`:22
- c0139: `PostgresDocumentRepository` — `app/repositories/postgres/document_repository.py`:22
- c0140: `PostgresEntityRepository` — `app/repositories/postgres/entity_repository.py`:34
- c0141: `PostgresFileRepository` — `app/repositories/postgres/file_repository.py`:18
- c0142: `PostgresMemoryRepository` — `app/repositories/postgres/memory_repository.py`:36
- c0143: `PostgresPlanRepository` — `app/repositories/postgres/plan_repository.py`:24
- c0144: `PostgresDatabaseAdapter` — `app/repositories/postgres/postgres_adapter.py`:18
- c0145: `ActivityLogTable` — `app/repositories/postgres/postgres_tables.py`:1175
- c0146: `Base` — `app/repositories/postgres/postgres_tables.py`:26
- c0147: `CodeArtifactsTable` — `app/repositories/postgres/postgres_tables.py`:519
- c0148: `CriteriaTable` — `app/repositories/postgres/postgres_tables.py`:1113
- c0149: `DocumentsTable` — `app/repositories/postgres/postgres_tables.py`:584
- c0150: `EntitiesTable` — `app/repositories/postgres/postgres_tables.py`:813
- c0151: `EntityRelationshipsTable` — `app/repositories/postgres/postgres_tables.py`:916
- c0152: `FilesTable` — `app/repositories/postgres/postgres_tables.py`:651
- c0153: `MemoryLinkTable` — `app/repositories/postgres/postgres_tables.py`:412
- c0154: `MemoryTable` — `app/repositories/postgres/postgres_tables.py`:178
- c0155: `PlansTable` — `app/repositories/postgres/postgres_tables.py`:982
- c0156: `ProjectsTable` — `app/repositories/postgres/postgres_tables.py`:433
- c0157: `SkillsTable` — `app/repositories/postgres/postgres_tables.py`:724
- c0158: `TaskDependenciesTable` — `app/repositories/postgres/postgres_tables.py`:1147
- c0159: `TasksTable` — `app/repositories/postgres/postgres_tables.py`:1040
- c0160: `UsersTable` — `app/repositories/postgres/postgres_tables.py`:112
- c0161: `PostgresProjectRepository` — `app/repositories/postgres/project_repository.py`:27
- c0162: `PostgresSkillRepository` — `app/repositories/postgres/skill_repository.py`:36
- c0163: `PostgresTaskRepository` — `app/repositories/postgres/task_repository.py`:33
- c0164: `PostgresUserRepository` — `app/repositories/postgres/user_repository.py`:15
- c0165: `SqliteActivityRepository` — `app/repositories/sqlite/activity_repository.py`:26
- c0166: `SqliteCodeArtifactRepository` — `app/repositories/sqlite/code_artifact_repository.py`:22
- c0167: `SqliteDocumentRepository` — `app/repositories/sqlite/document_repository.py`:22
- c0168: `SqliteEntityRepository` — `app/repositories/sqlite/entity_repository.py`:36
- c0169: `SqliteFileRepository` — `app/repositories/sqlite/file_repository.py`:18
- c0170: `SqliteMemoryRepository` — `app/repositories/sqlite/memory_repository.py`:37
- c0171: `SqlitePlanRepository` — `app/repositories/sqlite/plan_repository.py`:24
- c0172: `SqliteProjectRepository` — `app/repositories/sqlite/project_repository.py`:27
- c0173: `SqliteSkillRepository` — `app/repositories/sqlite/skill_repository.py`:37
- c0174: `SqliteDatabaseAdapter` — `app/repositories/sqlite/sqlite_adapter.py`:46
- c0175: `app/repositories/sqlite/sqlite_adapter.py` — `app/repositories/sqlite/sqlite_adapter.py`:1
- c0176: `ActivityLogTable` — `app/repositories/sqlite/sqlite_tables.py`:1182
- c0177: `Base` — `app/repositories/sqlite/sqlite_tables.py`:31
- c0178: `CodeArtifactsTable` — `app/repositories/sqlite/sqlite_tables.py`:524
- c0179: `CriteriaTable` — `app/repositories/sqlite/sqlite_tables.py`:1122
- c0180: `DocumentsTable` — `app/repositories/sqlite/sqlite_tables.py`:591
- c0181: `EntitiesTable` — `app/repositories/sqlite/sqlite_tables.py`:822
- c0182: `EntityRelationshipsTable` — `app/repositories/sqlite/sqlite_tables.py`:925
- c0183: `FilesTable` — `app/repositories/sqlite/sqlite_tables.py`:659
- c0184: `MemoryLinkTable` — `app/repositories/sqlite/sqlite_tables.py`:414
- c0185: `MemoryTable` — `app/repositories/sqlite/sqlite_tables.py`:177
- c0186: `PlansTable` — `app/repositories/sqlite/sqlite_tables.py`:994
- c0187: `ProjectsTable` — `app/repositories/sqlite/sqlite_tables.py`:437
- c0188: `SkillsTable` — `app/repositories/sqlite/sqlite_tables.py`:733
- c0189: `TaskDependenciesTable` — `app/repositories/sqlite/sqlite_tables.py`:1155
- c0190: `TasksTable` — `app/repositories/sqlite/sqlite_tables.py`:1050
- c0191: `UsersTable` — `app/repositories/sqlite/sqlite_tables.py`:124
- c0192: `SqliteTaskRepository` — `app/repositories/sqlite/task_repository.py`:33
- c0193: `SqliteUserRepository` — `app/repositories/sqlite/user_repository.py`:15
- c0194: `app/routes/api/activity.py` — `app/routes/api/activity.py`:1
- c0195: `app/routes/api/auth.py` — `app/routes/api/auth.py`:1
- c0196: `app/routes/api/code_artifacts.py` — `app/routes/api/code_artifacts.py`:1
- c0197: `app/routes/api/documents.py` — `app/routes/api/documents.py`:1
- c0198: `app/routes/api/entities.py` — `app/routes/api/entities.py`:1
- c0199: `app/routes/api/files.py` — `app/routes/api/files.py`:1
- c0200: `app/routes/api/graph.py` — `app/routes/api/graph.py`:1
- c0201: `app/routes/api/health.py` — `app/routes/api/health.py`:1
- c0202: `app/routes/api/memories.py` — `app/routes/api/memories.py`:1
- c0203: `app/routes/api/plans.py` — `app/routes/api/plans.py`:1
- c0204: `app/routes/api/projects.py` — `app/routes/api/projects.py`:1
- c0205: `app/routes/api/skills.py` — `app/routes/api/skills.py`:1
- c0206: `app/routes/api/tasks.py` — `app/routes/api/tasks.py`:1
- c0207: `app/routes/cli/auth_commands.py` — `app/routes/cli/auth_commands.py`:1
- c0208: `CliContext` — `app/routes/cli/context.py`:19
- c0209: `_CliRuntime` — `app/routes/cli/context.py`:11
- c0210: `LocalExecutor` — `app/routes/cli/local_executor.py`:18
- c0211: `app/routes/cli/parser.py` — `app/routes/cli/parser.py`:1
- c0212: `app/routes/cli/paths.py` — `app/routes/cli/paths.py`:1
- c0213: `RemoteExecutor` — `app/routes/cli/remote_executor.py`:67
- c0214: `app/routes/cli/remote_executor.py` — `app/routes/cli/remote_executor.py`:1
- c0215: `app/routes/cli/render.py` — `app/routes/cli/render.py`:1
- c0216: `CliError` — `app/routes/cli/verbs.py`:20
- c0217: `app/routes/cli/verbs.py` — `app/routes/cli/verbs.py`:1
- c0218: `app/routes/mcp/code_artifact_tools.py` — `app/routes/mcp/code_artifact_tools.py`:1
- c0219: `app/routes/mcp/document_tools.py` — `app/routes/mcp/document_tools.py`:1
- c0220: `app/routes/mcp/entity_tools.py` — `app/routes/mcp/entity_tools.py`:1
- c0221: `app/routes/mcp/memory_tools.py` — `app/routes/mcp/memory_tools.py`:1
- c0222: `app/routes/mcp/meta_tools.py` — `app/routes/mcp/meta_tools.py`:1
- c0223: `app/routes/mcp/pagination.py` — `app/routes/mcp/pagination.py`:1
- c0224: `app/routes/mcp/project_tools.py` — `app/routes/mcp/project_tools.py`:1
- c0225: `app/routes/mcp/scope_resolver.py` — `app/routes/mcp/scope_resolver.py`:1
- c0226: `app/routes/mcp/skill_tools.py` — `app/routes/mcp/skill_tools.py`:1
- c0227: `CodeArtifactToolAdapters` — `app/routes/mcp/tool_adapters.py`:1039
- c0228: `DocumentToolAdapters` — `app/routes/mcp/tool_adapters.py`:1206
- c0229: `EntityToolAdapters` — `app/routes/mcp/tool_adapters.py`:1375
- c0230: `FileToolAdapters` — `app/routes/mcp/tool_adapters.py`:2136
- c0231: `MemoryToolAdapters` — `app/routes/mcp/tool_adapters.py`:145
- c0232: `PlanToolAdapters` — `app/routes/mcp/tool_adapters.py`:1792
- c0233: `ProjectToolAdapters` — `app/routes/mcp/tool_adapters.py`:861
- c0234: `SkillToolAdapters` — `app/routes/mcp/tool_adapters.py`:2303
- c0235: `TaskToolAdapters` — `app/routes/mcp/tool_adapters.py`:1913
- c0236: `UserToolAdapters` — `app/routes/mcp/tool_adapters.py`:102
- c0237: `app/routes/mcp/tool_adapters.py` — `app/routes/mcp/tool_adapters.py`:1
- c0238: `app/routes/mcp/tool_metadata_registry.py` — `app/routes/mcp/tool_metadata_registry.py`:1
- c0239: `ToolRegistry` — `app/routes/mcp/tool_registry.py`:19
- c0240: `app/routes/mcp/user_tools.py` — `app/routes/mcp/user_tools.py`:1
- c0241: `ActivityService` — `app/services/activity_service.py`:24
- c0242: `BackupService` — `app/services/backup_service.py`:16
- c0243: `CodeArtifactService` — `app/services/code_artifact_service.py`:40
- c0244: `DocumentService` — `app/services/document_service.py`:40
- c0245: `EntityService` — `app/services/entity_service.py`:47
- c0246: `FileService` — `app/services/file_service.py`:40
- c0247: `CodeArtifactServiceProtocol` — `app/services/graph_service.py`:41
- c0248: `DocumentServiceProtocol` — `app/services/graph_service.py`:36
- c0249: `FileServiceProtocol` — `app/services/graph_service.py`:46
- c0250: `GraphService` — `app/services/graph_service.py`:73
- c0251: `PlanServiceProtocol` — `app/services/graph_service.py`:60
- c0252: `ProjectServiceProtocol` — `app/services/graph_service.py`:31
- c0253: `SkillServiceProtocol` — `app/services/graph_service.py`:52
- c0254: `TaskServiceProtocol` — `app/services/graph_service.py`:66
- c0255: `MemoryService` — `app/services/memory_service.py`:42
- c0256: `PlanService` — `app/services/plan_service.py`:34
- c0257: `ProjectService` — `app/services/project_service.py`:33
- c0258: `ReEmbedResult` — `app/services/re_embedding_service.py`:20
- c0259: `ReEmbeddingService` — `app/services/re_embedding_service.py`:40
- c0260: `TargetedRebuildResult` — `app/services/re_embedding_service.py`:28
- c0261: `SkillService` — `app/services/skill_service.py`:72
- c0262: `app/services/skill_service.py` — `app/services/skill_service.py`:1
- c0263: `TaskService` — `app/services/task_service.py`:46
- c0264: `UserService` — `app/services/user_service.py`:14
- c0265: `app/utils/provenance.py` — `app/utils/provenance.py`:1
- c0266: `app/utils/pydantic_helper.py` — `app/utils/pydantic_helper.py`:1
- c0267: `app/utils/repository_identity.py` — `app/utils/repository_identity.py`:1
- c0268: `TokenCounter` — `app/utils/token_counter.py`:10
- c0269: `app/version.py` — `app/version.py`:1
- c0270: `debug/reranker-test.py` — `debug/reranker-test.py`:1
- c0271: `debug/sqlite_vec_poc.py` — `debug/sqlite_vec_poc.py`:1
- c0272: `debug/test_google_embeddings.py` — `debug/test_google_embeddings.py`:1
- c0273: `debug/test_mcp_connection.py` — `debug/test_mcp_connection.py`:1
- c0274: `debug/test_sqlite_init.py` — `debug/test_sqlite_init.py`:1
- c0275: `main.py` — `main.py`:1
- c0276: `test_harness/__main__.py` — `test_harness/__main__.py`:1
- c0277: `HarnessConfig` — `test_harness/config.py`:29
- c0278: `AgentContainer` — `test_harness/container.py`:174
- c0279: `test_harness/container.py` — `test_harness/container.py`:1
- c0280: `test_harness/docker/runner.py` — `test_harness/docker/runner.py`:1
- c0281: `test_harness/prompts.py` — `test_harness/prompts.py`:1
- c0282: `ReportIssue` — `test_harness/report.py`:71
- c0283: `ReportLoad` — `test_harness/report.py`:94
- c0284: `ReportStep` — `test_harness/report.py`:60
- c0285: `WalkthroughReport` — `test_harness/report.py`:82
- c0286: `test_harness/report.py` — `test_harness/report.py`:1
- c0291: `HarnessInfraError` — `test_harness/server.py`:27
- c0292: `ThrowawayForgetful` — `test_harness/server.py`:43
- c0293: `test_harness/server.py` — `test_harness/server.py`:1
- c0294: `SessionOutcome` — `test_harness/walkthrough.py`:43
- c0295: `SessionRunner` — `test_harness/walkthrough.py`:51
- c0296: `SkillRunResult` — `test_harness/walkthrough.py`:58
- c0297: `Walkthrough` — `test_harness/walkthrough.py`:128
- c0298: `test_harness/walkthrough.py` — `test_harness/walkthrough.py`:1

## Relationships

- c0002 ..> c0002: `run_migrations_online() calls do_run_migrations()`
- c0002 ..> c0002: `run_migrations_online() calls run_async_migrations()`
- c0002 ..> c0030: `run_migrations_online() calls get()`
- c0002 ..> c0144: `run_async_migrations() calls dispose()`
- c0002 ..> c0217: `run_migrations_online() calls run()`
- c0003 ..> c0000: `downgrade() calls downgrade_postgres()`
- c0003 ..> c0000: `upgrade() calls upgrade_postgres()`
- c0003 ..> c0001: `downgrade() calls downgrade_sqlite()`
- c0003 ..> c0001: `upgrade() calls upgrade_sqlite()`
- c0003 ..> c0003: `downgrade() calls _load_helper_module()`
- c0003 ..> c0003: `upgrade() calls _load_helper_module()`
- c0005 ..> c0005: `upgrade() calls _get_user_id_type()`
- c0007 ..> c0007: `upgrade() calls _get_user_id_type()`
- c0008 ..> c0008: `upgrade() calls _get_tags_column()`
- c0008 ..> c0008: `upgrade() calls _get_user_id_type()`
- c0009 ..> c0009: `upgrade() calls _get_allowed_tools_column()`
- c0009 ..> c0009: `upgrade() calls _get_metadata_column()`
- c0009 ..> c0009: `upgrade() calls _get_tags_column()`
- c0009 ..> c0009: `upgrade() calls _get_user_id_type()`
- c0010 ..> c0010: `_add_full_provenance() calls _add_source_files_column()`
- c0010 ..> c0010: `downgrade() calls _drop_full_provenance()`
- c0010 ..> c0010: `upgrade() calls _add_full_provenance()`
- c0010 ..> c0010: `upgrade() calls _add_source_files_column()`
- c0013 --> c0014: `field services`
- c0013 --> c0239: `field registry`
- c0015 ..> c0013: `build_runtime() constructs Runtime`
- c0015 ..> c0013: `type in build_runtime`
- c0015 ..> c0013: `type in dispose_runtime`
- c0015 ..> c0014: `build_runtime() constructs Services`
- c0015 ..> c0015: `build_runtime() calls check_first_run_models()`
- c0015 ..> c0015: `build_runtime() calls create_db_adapter()`
- c0015 ..> c0015: `build_runtime() calls create_repositories()`
- c0015 ..> c0015: `build_runtime() calls get_embedding_adapter()`
- c0015 ..> c0015: `build_runtime() calls get_reranker_adapter()`
- c0015 ..> c0023: `build_runtime() calls subscribe()`
- c0015 ..> c0023: `build_runtime() constructs EventBus`
- c0015 ..> c0023: `dispose_runtime() calls wait_for_pending()`
- c0015 ..> c0126: `get_embedding_adapter() constructs AzureOpenAIAdapter`
- c0015 ..> c0128: `get_embedding_adapter() constructs FastEmbeddingAdapter`
- c0015 ..> c0129: `get_embedding_adapter() constructs GoogleEmbeddingsAdapter`
- c0015 ..> c0130: `get_embedding_adapter() constructs OllamaEmbeddingsAdapter`
- c0015 ..> c0131: `get_embedding_adapter() constructs OpenAIEmbeddingsAdapter`
- c0015 ..> c0133: `get_reranker_adapter() constructs FastEmbedCrossEncoderAdapter`
- c0015 ..> c0134: `get_reranker_adapter() constructs HttpRerankAdapter`
- c0015 ..> c0137: `create_repositories() constructs PostgresActivityRepository`
- c0015 ..> c0138: `create_repositories() constructs PostgresCodeArtifactRepository`
- c0015 ..> c0139: `create_repositories() constructs PostgresDocumentRepository`
- c0015 ..> c0140: `create_repositories() constructs PostgresEntityRepository`
- c0015 ..> c0141: `create_repositories() constructs PostgresFileRepository`
- c0015 ..> c0142: `create_repositories() constructs PostgresMemoryRepository`
- c0015 ..> c0143: `create_repositories() constructs PostgresPlanRepository`
- c0015 ..> c0144: `build_runtime() calls init_db()`
- c0015 ..> c0144: `create_db_adapter() constructs PostgresDatabaseAdapter`
- c0015 ..> c0144: `dispose_runtime() calls dispose()`
- c0015 ..> c0161: `create_repositories() constructs PostgresProjectRepository`
- c0015 ..> c0162: `create_repositories() constructs PostgresSkillRepository`
- c0015 ..> c0163: `create_repositories() constructs PostgresTaskRepository`
- c0015 ..> c0164: `create_repositories() constructs PostgresUserRepository`
- c0015 ..> c0165: `create_repositories() constructs SqliteActivityRepository`
- c0015 ..> c0166: `create_repositories() constructs SqliteCodeArtifactRepository`
- c0015 ..> c0167: `create_repositories() constructs SqliteDocumentRepository`
- c0015 ..> c0168: `create_repositories() constructs SqliteEntityRepository`
- c0015 ..> c0169: `create_repositories() constructs SqliteFileRepository`
- c0015 ..> c0170: `create_repositories() constructs SqliteMemoryRepository`
- c0015 ..> c0171: `create_repositories() constructs SqlitePlanRepository`
- c0015 ..> c0172: `create_repositories() constructs SqliteProjectRepository`
- c0015 ..> c0173: `create_repositories() constructs SqliteSkillRepository`
- c0015 ..> c0174: `create_db_adapter() constructs SqliteDatabaseAdapter`
- c0015 ..> c0192: `create_repositories() constructs SqliteTaskRepository`
- c0015 ..> c0193: `create_repositories() constructs SqliteUserRepository`
- c0015 ..> c0225: `build_runtime() calls parse_scopes()`
- c0015 ..> c0225: `build_runtime() calls resolve_permitted_tools()`
- c0015 ..> c0238: `build_runtime() calls register_all_tools_metadata()`
- c0015 ..> c0239: `build_runtime() calls list_categories()`
- c0015 ..> c0239: `build_runtime() constructs ToolRegistry`
- c0015 ..> c0241: `build_runtime() constructs ActivityService`
- c0015 ..> c0243: `build_runtime() constructs CodeArtifactService`
- c0015 ..> c0244: `build_runtime() constructs DocumentService`
- c0015 ..> c0245: `build_runtime() constructs EntityService`
- c0015 ..> c0246: `build_runtime() constructs FileService`
- c0015 ..> c0250: `build_runtime() constructs GraphService`
- c0015 ..> c0255: `build_runtime() calls register_access_tracking_handlers()`
- c0015 ..> c0255: `build_runtime() constructs MemoryService`
- c0015 ..> c0256: `build_runtime() constructs PlanService`
- c0015 ..> c0257: `build_runtime() constructs ProjectService`
- c0015 ..> c0261: `build_runtime() constructs SkillService`
- c0015 ..> c0263: `build_runtime() constructs TaskService`
- c0015 ..> c0264: `build_runtime() constructs UserService`
- c0016 ..> c0016: `_build_github() calls _required()`
- c0016 ..> c0016: `_build_github() calls _scopes()`
- c0016 ..> c0016: `_build_google() calls _required()`
- c0016 ..> c0016: `_build_google() calls _scopes()`
- c0016 ..> c0016: `_build_introspection() calls _required()`
- c0016 ..> c0016: `_build_introspection() calls _scopes()`
- c0016 ..> c0016: `_build_jwt() calls _scopes()`
- c0016 ..> c0030: `build_auth_provider() calls get()`
- c0018 ..> c0030: `format() calls get()`
- c0018 ..> c0032: `format() calls get_request_id()`
- c0018 ..> c0032: `format() calls get_user_id()`
- c0019 ..> c0019: `filter() calls _mask_value()`
- c0020 ..> c0017: `configure_logging() constructs ConsoleFormatter`
- c0020 ..> c0018: `configure_logging() constructs JSONFormatter`
- c0020 ..> c0019: `configure_logging() constructs SensitiveDataFilter`
- c0020 ..> c0023: `configure_logging() calls clear()`
- c0020 ..> c0278: `configure_logging() calls start()`
- c0020 ..> c0278: `shutdown_logging() calls stop()`
- c0021 ..> c0022: `_validate_onnx_providers() calls parse_onnx_providers()`
- c0021 ..> c0022: `embedding_onnx_providers() calls parse_onnx_providers()`
- c0021 ..> c0022: `reranking_onnx_providers() calls parse_onnx_providers()`
- c0023 ..> c0023: `_emit_to_streams() calls _next_seq()`
- c0023 ..> c0023: `emit() calls _emit_to_streams()`
- c0023 ..> c0023: `emit() calls _safe_dispatch()`
- c0023 ..> c0030: `_emit_to_streams() calls get()`
- c0023 ..> c0030: `clear() calls clear()`
- c0023 ..> c0030: `get_current_seq() calls get()`
- c0023 ..> c0030: `stream_subscriber_count() calls get()`
- c0023 ..> c0030: `subscribe_stream() calls get()`
- c0023 ..> c0030: `subscriber_count() calls get()`
- c0023 ..> c0034: `type in _emit_to_streams`
- c0023 ..> c0034: `type in _safe_dispatch`
- c0023 ..> c0034: `type in emit`
- c0023 ..> c0124: `emit() calls create_task()`
- c0029 --> c0109: `field user`
- c0030 ..> c0023: `clear() calls clear()`
- c0030 --> c0029: `field _cache`
- c0030 ..> c0029: `set() constructs CacheEntry`
- c0030 ..> c0030: `get() calls _hash_token()`
- c0030 ..> c0030: `invalidate() calls _hash_token()`
- c0030 ..> c0030: `set() calls _hash_token()`
- c0030 ..> c0109: `type in get`
- c0030 ..> c0109: `type in set`
- c0031 ..> c0030: `get_user_from_auth() calls get()`
- c0031 ..> c0030: `get_user_from_request() calls get()`
- c0031 ..> c0109: `type in get_user_from_auth`
- c0031 ..> c0109: `type in get_user_from_request`
- c0031 ..> c0110: `get_user_from_auth() constructs UserCreate`
- c0031 ..> c0110: `get_user_from_request() constructs UserCreate`
- c0031 ..> c0264: `get_user_from_auth() calls get_or_create_user()`
- c0031 ..> c0264: `get_user_from_request() calls get_or_create_user()`
- c0032 ..> c0030: `get_request_id() calls get()`
- c0032 ..> c0030: `get_user_id() calls get()`
- c0034 --> c0033: `field action`
- c0034 --> c0037: `field actor`
- c0034 --> c0038: `field entity_type`
- c0035 --> c0036: `field events`
- c0036 --> c0033: `field action`
- c0036 --> c0037: `field actor`
- c0036 --> c0038: `field entity_type`
- c0039 --|> c0040: `inherits`
- c0043 --|> c0044: `inherits`
- c0044 ..> c0030: `calculate_size_bytes() calls get()`
- c0047 --|> c0048: `inherits`
- c0048 --> c0054: `field entity_type`
- c0049 --> c0053: `field entities`
- c0050 --|> c0051: `inherits`
- c0053 --> c0054: `field entity_type`
- c0055 --> c0054: `field entity_type`
- c0056 --|> c0057: `inherits`
- c0063 --> c0060: `field edges`
- c0063 --> c0061: `field meta`
- c0063 --> c0062: `field nodes`
- c0064 --> c0065: `field memory`
- c0065 --|> c0066: `inherits`
- c0067 --> c0073: `field similar_memories`
- c0067 --> c0075: `field obsolete_matches`
- c0069 --> c0065: `field memories`
- c0071 --> c0064: `field linked_memories`
- c0071 --> c0065: `field primary_memories`
- c0071 --> c0072: `field scores`
- c0080 --|> c0081: `inherits`
- c0081 --> c0082: `field status`
- c0083 --> c0082: `field status`
- c0084 --> c0082: `field status`
- c0085 --> c0077: `field criteria`
- c0085 --> c0089: `field priority`
- c0085 --> c0090: `field state`
- c0086 --> c0078: `field criteria`
- c0086 --> c0089: `field priority`
- c0088 ..> c0030: `cannot_depend_on_self() calls get()`
- c0091 --> c0089: `field priority`
- c0091 --> c0090: `field state`
- c0092 --> c0089: `field priority`
- c0093 --|> c0094: `inherits`
- c0094 --> c0095: `field status`
- c0094 --> c0097: `field project_type`
- c0096 --> c0095: `field status`
- c0096 --> c0097: `field project_type`
- c0098 --> c0095: `field status`
- c0098 --> c0097: `field project_type`
- c0099 --|> c0100: `inherits`
- c0105 --|> c0107: `inherits`
- c0106 --> c0107: `field metadata`
- c0107 ..> c0030: `_map_python_type_to_json_type() calls get()`
- c0107 --> c0104: `field category`
- c0107 ..> c0107: `_generate_json_schema() calls _map_python_type_to_json_type()`
- c0107 ..> c0107: `to_detailed_dict() calls _generate_json_schema()`
- c0107 --> c0108: `field parameters`
- c0109 --|> c0110: `inherits`
- c0113 ..> c0033: `type in count_events`
- c0113 ..> c0033: `type in query_events`
- c0113 ..> c0034: `type in save_event`
- c0113 ..> c0036: `type in query_events`
- c0113 ..> c0036: `type in save_event`
- c0113 ..> c0037: `type in query_events`
- c0113 ..> c0038: `type in count_events`
- c0113 ..> c0038: `type in query_events`
- c0114 ..> c0039: `type in create_code_artifact`
- c0114 ..> c0039: `type in get_code_artifact_by_id`
- c0114 ..> c0039: `type in update_code_artifact`
- c0114 ..> c0040: `type in create_code_artifact`
- c0114 ..> c0041: `type in list_code_artifacts`
- c0114 ..> c0042: `type in update_code_artifact`
- c0115 ..> c0043: `type in create_document`
- c0115 ..> c0043: `type in get_document_by_id`
- c0115 ..> c0043: `type in update_document`
- c0115 ..> c0044: `type in create_document`
- c0115 ..> c0045: `type in list_documents`
- c0115 ..> c0046: `type in update_document`
- c0116 ..> c0047: `type in create_entity`
- c0116 ..> c0047: `type in get_entity_by_id`
- c0116 ..> c0047: `type in update_entity`
- c0116 ..> c0048: `type in create_entity`
- c0116 ..> c0050: `type in create_entity_relationship`
- c0116 ..> c0050: `type in get_all_entity_relationships`
- c0116 ..> c0050: `type in get_entity_relationships`
- c0116 ..> c0050: `type in update_entity_relationship`
- c0116 ..> c0051: `type in create_entity_relationship`
- c0116 ..> c0052: `type in update_entity_relationship`
- c0116 ..> c0053: `type in list_entities`
- c0116 ..> c0053: `type in search_entities`
- c0116 ..> c0054: `type in list_entities`
- c0116 ..> c0054: `type in search_entities`
- c0116 ..> c0055: `type in update_entity`
- c0118 ..> c0056: `type in create_file`
- c0118 ..> c0056: `type in get_file_by_id`
- c0118 ..> c0056: `type in update_file`
- c0118 ..> c0057: `type in create_file`
- c0118 ..> c0058: `type in list_files`
- c0118 ..> c0059: `type in update_file`
- c0119 ..> c0065: `type in create_memory`
- c0119 ..> c0065: `type in find_obsolete_matches`
- c0119 ..> c0065: `type in find_similar_memories`
- c0119 ..> c0065: `type in find_similar_memories_scored`
- c0119 ..> c0065: `type in get_linked_memories`
- c0119 ..> c0065: `type in get_memories_for_reembedding`
- c0119 ..> c0065: `type in get_memories_for_targeted_rebuild`
- c0119 ..> c0065: `type in get_memory_by_id`
- c0119 ..> c0065: `type in list_memories`
- c0119 ..> c0065: `type in search`
- c0119 ..> c0065: `type in search_scored`
- c0119 ..> c0065: `type in update_memory`
- c0119 ..> c0066: `type in create_memory`
- c0119 ..> c0072: `type in search_scored`
- c0119 ..> c0074: `type in update_memory`
- c0121 ..> c0080: `type in create_plan`
- c0121 ..> c0080: `type in get_plan_by_id`
- c0121 ..> c0080: `type in update_plan`
- c0121 ..> c0081: `type in create_plan`
- c0121 ..> c0082: `type in list_plans`
- c0121 ..> c0083: `type in list_plans`
- c0121 ..> c0084: `type in update_plan`
- c0122 ..> c0093: `type in create_project`
- c0122 ..> c0093: `type in get_project_by_id`
- c0122 ..> c0093: `type in update_project`
- c0122 ..> c0094: `type in create_project`
- c0122 ..> c0095: `type in list_projects`
- c0122 ..> c0096: `type in list_projects`
- c0122 ..> c0098: `type in update_project`
- c0123 ..> c0099: `type in create_skill`
- c0123 ..> c0099: `type in get_skill_by_id`
- c0123 ..> c0099: `type in update_skill`
- c0123 ..> c0100: `type in create_skill`
- c0123 ..> c0101: `type in get_skill_links`
- c0123 ..> c0102: `type in list_skills`
- c0123 ..> c0102: `type in search_skills`
- c0123 ..> c0103: `type in update_skill`
- c0124 ..> c0077: `type in create_criterion`
- c0124 ..> c0077: `type in get_criteria_for_task`
- c0124 ..> c0077: `type in update_criterion`
- c0124 ..> c0078: `type in create_criterion`
- c0124 ..> c0079: `type in update_criterion`
- c0124 ..> c0085: `type in create_task`
- c0124 ..> c0085: `type in get_task_by_id`
- c0124 ..> c0085: `type in transition_task_state`
- c0124 ..> c0085: `type in update_task`
- c0124 ..> c0086: `type in create_task`
- c0124 ..> c0087: `type in add_dependency`
- c0124 ..> c0089: `type in list_tasks`
- c0124 ..> c0090: `type in list_tasks`
- c0124 ..> c0090: `type in transition_task_state`
- c0124 ..> c0091: `type in list_tasks`
- c0124 ..> c0091: `type in list_tasks_for_user`
- c0124 ..> c0092: `type in update_task`
- c0125 ..> c0109: `type in create_user`
- c0125 ..> c0109: `type in get_user_by_external_id`
- c0125 ..> c0109: `type in get_user_by_id`
- c0125 ..> c0109: `type in update_user`
- c0125 ..> c0110: `type in create_user`
- c0125 ..> c0112: `type in update_user`
- c0126 --|> c0127: `inherits`
- c0128 --|> c0127: `inherits`
- c0129 --|> c0127: `inherits`
- c0130 --|> c0127: `inherits`
- c0130 ..> c0128: `__init__() calls _create_text_embedding()`
- c0130 ..> c0132: `__init__() calls load_fastembed_model()`
- c0130 ..> c0210: `generate_embedding() calls create()`
- c0131 --|> c0127: `inherits`
- c0132 ..> c0132: `load_fastembed_model() calls get_fastembed_kwargs()`
- c0133 ..> c0134: `_rerank_sync() calls rerank()`
- c0134 ..> c0132: `__init__() calls load_fastembed_model()`
- c0134 ..> c0133: `__init__() calls _create_text_cross_encoder()`
- c0136 ..> c0065: `type in build_memory_text`
- c0136 ..> c0066: `type in build_embedding_text`
- c0137 ..> c0033: `type in count_events`
- c0137 ..> c0033: `type in query_events`
- c0137 ..> c0034: `type in save_event`
- c0137 ..> c0036: `query_events() constructs ActivityLogEntry`
- c0137 ..> c0036: `save_event() constructs ActivityLogEntry`
- c0137 ..> c0036: `type in query_events`
- c0137 ..> c0036: `type in save_event`
- c0137 ..> c0037: `type in query_events`
- c0137 ..> c0038: `type in count_events`
- c0137 ..> c0038: `type in query_events`
- c0137 ..> c0117: `cleanup_expired() calls execute()`
- c0137 ..> c0117: `count_events() calls execute()`
- c0137 ..> c0117: `query_events() calls execute()`
- c0137 ..> c0144: `cleanup_expired() calls session()`
- c0137 ..> c0144: `count_events() calls session()`
- c0137 ..> c0144: `query_events() calls session()`
- c0137 ..> c0144: `save_event() calls session()`
- c0137 ..> c0144: `type in __init__`
- c0137 ..> c0145: `save_event() constructs ActivityLogTable`
- c0138 ..> c0028: `update_code_artifact() constructs NotFoundError`
- c0138 ..> c0030: `update_code_artifact() calls get()`
- c0138 ..> c0039: `type in create_code_artifact`
- c0138 ..> c0039: `type in get_code_artifact_by_id`
- c0138 ..> c0039: `type in update_code_artifact`
- c0138 ..> c0040: `type in create_code_artifact`
- c0138 ..> c0041: `type in list_code_artifacts`
- c0138 ..> c0042: `type in update_code_artifact`
- c0138 ..> c0117: `delete_code_artifact() calls execute()`
- c0138 ..> c0117: `get_code_artifact_by_id() calls execute()`
- c0138 ..> c0117: `list_code_artifacts() calls execute()`
- c0138 ..> c0117: `update_code_artifact() calls execute()`
- c0138 ..> c0144: `create_code_artifact() calls session()`
- c0138 ..> c0144: `delete_code_artifact() calls session()`
- c0138 ..> c0144: `get_code_artifact_by_id() calls session()`
- c0138 ..> c0144: `list_code_artifacts() calls session()`
- c0138 ..> c0144: `type in __init__`
- c0138 ..> c0144: `update_code_artifact() calls session()`
- c0138 ..> c0147: `create_code_artifact() constructs CodeArtifactsTable`
- c0139 ..> c0028: `update_document() constructs NotFoundError`
- c0139 ..> c0030: `update_document() calls get()`
- c0139 ..> c0043: `type in create_document`
- c0139 ..> c0043: `type in get_document_by_id`
- c0139 ..> c0043: `type in update_document`
- c0139 ..> c0044: `type in create_document`
- c0139 ..> c0045: `type in list_documents`
- c0139 ..> c0046: `type in update_document`
- c0139 ..> c0117: `delete_document() calls execute()`
- c0139 ..> c0117: `get_document_by_id() calls execute()`
- c0139 ..> c0117: `list_documents() calls execute()`
- c0139 ..> c0117: `update_document() calls execute()`
- c0139 ..> c0144: `create_document() calls session()`
- c0139 ..> c0144: `delete_document() calls session()`
- c0139 ..> c0144: `get_document_by_id() calls session()`
- c0139 ..> c0144: `list_documents() calls session()`
- c0139 ..> c0144: `type in __init__`
- c0139 ..> c0144: `update_document() calls session()`
- c0139 ..> c0149: `create_document() constructs DocumentsTable`
- c0140 ..> c0028: `create_entity_relationship() constructs NotFoundError`
- c0140 ..> c0028: `get_entity_memories() constructs NotFoundError`
- c0140 ..> c0028: `get_entity_relationships() constructs NotFoundError`
- c0140 ..> c0028: `get_memory_entities() constructs NotFoundError`
- c0140 ..> c0028: `link_entity_to_memory() constructs NotFoundError`
- c0140 ..> c0028: `link_entity_to_project() constructs NotFoundError`
- c0140 ..> c0028: `update_entity() constructs NotFoundError`
- c0140 ..> c0028: `update_entity_relationship() constructs NotFoundError`
- c0140 ..> c0030: `update_entity() calls get()`
- c0140 ..> c0047: `type in create_entity`
- c0140 ..> c0047: `type in get_entity_by_id`
- c0140 ..> c0047: `type in update_entity`
- c0140 ..> c0048: `type in create_entity`
- c0140 ..> c0050: `create_entity_relationship() constructs EntityRelationship`
- c0140 ..> c0050: `get_all_entity_relationships() constructs EntityRelationship`
- c0140 ..> c0050: `get_entity_relationships() constructs EntityRelationship`
- c0140 ..> c0050: `type in create_entity_relationship`
- c0140 ..> c0050: `type in get_all_entity_relationships`
- c0140 ..> c0050: `type in get_entity_relationships`
- c0140 ..> c0050: `type in update_entity_relationship`
- c0140 ..> c0050: `update_entity_relationship() constructs EntityRelationship`
- c0140 ..> c0051: `type in create_entity_relationship`
- c0140 ..> c0052: `type in update_entity_relationship`
- c0140 ..> c0053: `type in list_entities`
- c0140 ..> c0053: `type in search_entities`
- c0140 ..> c0054: `type in list_entities`
- c0140 ..> c0054: `type in search_entities`
- c0140 ..> c0055: `type in update_entity`
- c0140 ..> c0117: `create_entity() calls execute()`
- c0140 ..> c0117: `create_entity_relationship() calls execute()`
- c0140 ..> c0117: `delete_entity() calls execute()`
- c0140 ..> c0117: `delete_entity_relationship() calls execute()`
- c0140 ..> c0117: `get_all_entity_file_links() calls execute()`
- c0140 ..> c0117: `get_all_entity_memory_links() calls execute()`
- c0140 ..> c0117: `get_all_entity_project_links() calls execute()`
- c0140 ..> c0117: `get_all_entity_relationships() calls execute()`
- c0140 ..> c0117: `get_entity_by_id() calls execute()`
- c0140 ..> c0117: `get_entity_memories() calls execute()`
- c0140 ..> c0117: `get_entity_relationships() calls execute()`
- c0140 ..> c0117: `get_memory_entities() calls execute()`
- c0140 ..> c0117: `link_entity_to_memory() calls execute()`
- c0140 ..> c0117: `link_entity_to_project() calls execute()`
- c0140 ..> c0117: `list_entities() calls execute()`
- c0140 ..> c0117: `search_entities() calls execute()`
- c0140 ..> c0117: `unlink_entity_from_memory() calls execute()`
- c0140 ..> c0117: `unlink_entity_from_project() calls execute()`
- c0140 ..> c0117: `update_entity() calls execute()`
- c0140 ..> c0117: `update_entity_relationship() calls execute()`
- c0140 ..> c0144: `create_entity() calls session()`
- c0140 ..> c0144: `create_entity_relationship() calls session()`
- c0140 ..> c0144: `delete_entity() calls session()`
- c0140 ..> c0144: `delete_entity_relationship() calls session()`
- c0140 ..> c0144: `get_all_entity_file_links() calls session()`
- c0140 ..> c0144: `get_all_entity_memory_links() calls session()`
- c0140 ..> c0144: `get_all_entity_project_links() calls session()`
- c0140 ..> c0144: `get_all_entity_relationships() calls session()`
- c0140 ..> c0144: `get_entity_by_id() calls session()`
- c0140 ..> c0144: `get_entity_memories() calls session()`
- c0140 ..> c0144: `get_entity_relationships() calls session()`
- c0140 ..> c0144: `get_memory_entities() calls session()`
- c0140 ..> c0144: `link_entity_to_memory() calls session()`
- c0140 ..> c0144: `link_entity_to_project() calls session()`
- c0140 ..> c0144: `list_entities() calls session()`
- c0140 ..> c0144: `search_entities() calls session()`
- c0140 ..> c0144: `type in __init__`
- c0140 ..> c0144: `unlink_entity_from_memory() calls session()`
- c0140 ..> c0144: `unlink_entity_from_project() calls session()`
- c0140 ..> c0144: `update_entity() calls session()`
- c0140 ..> c0144: `update_entity_relationship() calls session()`
- c0140 ..> c0150: `create_entity() constructs EntitiesTable`
- c0140 ..> c0151: `create_entity_relationship() constructs EntityRelationshipsTable`
- c0141 ..> c0028: `update_file() constructs NotFoundError`
- c0141 ..> c0056: `_to_file_model() constructs File`
- c0141 ..> c0056: `type in _to_file_model`
- c0141 ..> c0056: `type in create_file`
- c0141 ..> c0056: `type in get_file_by_id`
- c0141 ..> c0056: `type in update_file`
- c0141 ..> c0057: `type in create_file`
- c0141 ..> c0058: `type in list_files`
- c0141 ..> c0059: `type in update_file`
- c0141 ..> c0117: `delete_file() calls execute()`
- c0141 ..> c0117: `get_file_by_id() calls execute()`
- c0141 ..> c0117: `list_files() calls execute()`
- c0141 ..> c0117: `update_file() calls execute()`
- c0141 ..> c0141: `create_file() calls _to_file_model()`
- c0141 ..> c0141: `get_file_by_id() calls _to_file_model()`
- c0141 ..> c0141: `update_file() calls _to_file_model()`
- c0141 ..> c0144: `create_file() calls session()`
- c0141 ..> c0144: `delete_file() calls session()`
- c0141 ..> c0144: `get_file_by_id() calls session()`
- c0141 ..> c0144: `list_files() calls session()`
- c0141 ..> c0144: `type in __init__`
- c0141 ..> c0144: `update_file() calls session()`
- c0141 ..> c0152: `create_file() constructs FilesTable`
- c0141 ..> c0152: `type in _to_file_model`
- c0142 ..> c0023: `update_memory() calls clear()`
- c0142 ..> c0028: `_link_code_artifacts() constructs NotFoundError`
- c0142 ..> c0028: `_link_documents() constructs NotFoundError`
- c0142 ..> c0028: `_link_files() constructs NotFoundError`
- c0142 ..> c0028: `_link_projects() constructs NotFoundError`
- c0142 ..> c0028: `_link_skills() constructs NotFoundError`
- c0142 ..> c0028: `create_link() constructs NotFoundError`
- c0142 ..> c0028: `get_linked_memories() constructs NotFoundError`
- c0142 ..> c0028: `get_memory_by_id() constructs NotFoundError`
- c0142 ..> c0028: `get_memory_table_by_id() constructs NotFoundError`
- c0142 ..> c0028: `mark_obsolete() constructs NotFoundError`
- c0142 ..> c0028: `update_memory() constructs NotFoundError`
- c0142 ..> c0030: `create_link() calls get()`
- c0142 ..> c0030: `list_memories() calls get()`
- c0142 ..> c0065: `type in create_memory`
- c0142 ..> c0065: `type in find_obsolete_matches`
- c0142 ..> c0065: `type in find_similar_memories`
- c0142 ..> c0065: `type in find_similar_memories_scored`
- c0142 ..> c0065: `type in get_linked_memories`
- c0142 ..> c0065: `type in get_memories_for_reembedding`
- c0142 ..> c0065: `type in get_memories_for_targeted_rebuild`
- c0142 ..> c0065: `type in get_memory_by_id`
- c0142 ..> c0065: `type in list_memories`
- c0142 ..> c0065: `type in search`
- c0142 ..> c0065: `type in search_scored`
- c0142 ..> c0065: `type in semantic_search`
- c0142 ..> c0065: `type in semantic_search_scored`
- c0142 ..> c0065: `type in update_memory`
- c0142 ..> c0066: `type in create_memory`
- c0142 ..> c0072: `search_scored() constructs MemoryScore`
- c0142 ..> c0072: `type in search_scored`
- c0142 ..> c0074: `type in update_memory`
- c0142 ..> c0117: `_link_code_artifacts() calls execute()`
- c0142 ..> c0117: `_link_documents() calls execute()`
- c0142 ..> c0117: `_link_files() calls execute()`
- c0142 ..> c0117: `_link_projects() calls execute()`
- c0142 ..> c0117: `_link_skills() calls execute()`
- c0142 ..> c0117: `bulk_update_embeddings() calls execute()`
- c0142 ..> c0117: `count_memories_for_targeted_rebuild() calls execute()`
- c0142 ..> c0117: `create_memory() calls execute()`
- c0142 ..> c0117: `find_obsolete_matches() calls execute()`
- c0142 ..> c0117: `find_similar_memories_scored() calls execute()`
- c0142 ..> c0117: `get_linked_memories() calls execute()`
- c0142 ..> c0117: `get_memories_for_reembedding() calls execute()`
- c0142 ..> c0117: `get_memories_for_targeted_rebuild() calls execute()`
- c0142 ..> c0117: `get_memory_table_by_id() calls execute()`
- c0142 ..> c0117: `get_subgraph_nodes() calls execute()`
- c0142 ..> c0117: `list_memories() calls execute()`
- c0142 ..> c0117: `mark_obsolete() calls execute()`
- c0142 ..> c0117: `record_memory_access() calls execute()`
- c0142 ..> c0117: `reset_embedding_storage() calls execute()`
- c0142 ..> c0117: `semantic_search_scored() calls execute()`
- c0142 ..> c0117: `unlink_memories() calls execute()`
- c0142 ..> c0117: `update_memory() calls execute()`
- c0142 ..> c0117: `upsert_targeted_embeddings() calls execute()`
- c0142 ..> c0117: `validate_embedding_dimensions() calls execute()`
- c0142 ..> c0117: `validate_search_works() calls execute()`
- c0142 ..> c0127: `type in __init__`
- c0142 ..> c0130: `_generate_embeddings() calls generate_embedding()`
- c0142 ..> c0134: `search_scored() calls rerank()`
- c0142 ..> c0135: `type in __init__`
- c0142 ..> c0136: `create_memory() calls build_embedding_text()`
- c0142 ..> c0136: `search_scored() calls build_contextual_query()`
- c0142 ..> c0136: `search_scored() calls build_memory_text()`
- c0142 ..> c0136: `update_memory() calls build_embedding_text()`
- c0142 ..> c0142: `count_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0142 ..> c0142: `create_links_batch() calls create_link()`
- c0142 ..> c0142: `create_memory() calls _generate_embeddings()`
- c0142 ..> c0142: `create_memory() calls _link_code_artifacts()`
- c0142 ..> c0142: `create_memory() calls _link_documents()`
- c0142 ..> c0142: `create_memory() calls _link_files()`
- c0142 ..> c0142: `create_memory() calls _link_projects()`
- c0142 ..> c0142: `create_memory() calls _link_skills()`
- c0142 ..> c0142: `find_obsolete_matches() calls get_memory_table_by_id()`
- c0142 ..> c0142: `find_similar_memories() calls find_similar_memories_scored()`
- c0142 ..> c0142: `find_similar_memories_scored() calls get_memory_table_by_id()`
- c0142 ..> c0142: `get_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0142 ..> c0142: `get_memory_by_id() calls get_memory_table_by_id()`
- c0142 ..> c0142: `search() calls search_scored()`
- c0142 ..> c0142: `search_scored() calls semantic_search_scored()`
- c0142 ..> c0142: `semantic_search() calls semantic_search_scored()`
- c0142 ..> c0142: `semantic_search_scored() calls _generate_embeddings()`
- c0142 ..> c0142: `update_memory() calls _generate_embeddings()`
- c0142 ..> c0142: `update_memory() calls _link_code_artifacts()`
- c0142 ..> c0142: `update_memory() calls _link_documents()`
- c0142 ..> c0142: `update_memory() calls _link_files()`
- c0142 ..> c0142: `update_memory() calls _link_projects()`
- c0142 ..> c0142: `validate_search_works() calls _generate_embeddings()`
- c0142 ..> c0144: `bulk_update_embeddings() calls system_session()`
- c0142 ..> c0144: `count_all_memories() calls system_session()`
- c0142 ..> c0144: `count_memories_for_targeted_rebuild() calls system_session()`
- c0142 ..> c0144: `create_link() calls session()`
- c0142 ..> c0144: `create_memory() calls session()`
- c0142 ..> c0144: `find_obsolete_matches() calls session()`
- c0142 ..> c0144: `find_similar_memories_scored() calls session()`
- c0142 ..> c0144: `get_linked_memories() calls session()`
- c0142 ..> c0144: `get_memories_for_reembedding() calls system_session()`
- c0142 ..> c0144: `get_memories_for_targeted_rebuild() calls system_session()`
- c0142 ..> c0144: `get_memory_table_by_id() calls session()`
- c0142 ..> c0144: `get_subgraph_nodes() calls session()`
- c0142 ..> c0144: `list_memories() calls session()`
- c0142 ..> c0144: `mark_obsolete() calls session()`
- c0142 ..> c0144: `record_memory_access() calls system_session()`
- c0142 ..> c0144: `reset_embedding_storage() calls system_session()`
- c0142 ..> c0144: `semantic_search_scored() calls session()`
- c0142 ..> c0144: `type in __init__`
- c0142 ..> c0144: `unlink_memories() calls session()`
- c0142 ..> c0144: `update_memory() calls session()`
- c0142 ..> c0144: `upsert_targeted_embeddings() calls system_session()`
- c0142 ..> c0144: `validate_embedding_count() calls system_session()`
- c0142 ..> c0144: `validate_embedding_dimensions() calls system_session()`
- c0142 ..> c0144: `validate_search_works() calls system_session()`
- c0142 ..> c0153: `create_link() constructs MemoryLinkTable`
- c0142 ..> c0153: `type in create_link`
- c0142 ..> c0154: `create_memory() constructs MemoryTable`
- c0142 ..> c0154: `type in _link_code_artifacts`
- c0142 ..> c0154: `type in _link_documents`
- c0142 ..> c0154: `type in _link_files`
- c0142 ..> c0154: `type in _link_projects`
- c0142 ..> c0154: `type in _link_skills`
- c0142 ..> c0154: `type in get_memory_table_by_id`
- c0143 ..> c0028: `update_plan() constructs NotFoundError`
- c0143 ..> c0080: `type in create_plan`
- c0143 ..> c0080: `type in get_plan_by_id`
- c0143 ..> c0080: `type in update_plan`
- c0143 ..> c0081: `type in create_plan`
- c0143 ..> c0082: `type in list_plans`
- c0143 ..> c0083: `type in list_plans`
- c0143 ..> c0084: `type in update_plan`
- c0143 ..> c0117: `delete_plan() calls execute()`
- c0143 ..> c0117: `get_plan_by_id() calls execute()`
- c0143 ..> c0117: `list_plans() calls execute()`
- c0143 ..> c0117: `update_plan() calls execute()`
- c0143 ..> c0144: `create_plan() calls session()`
- c0143 ..> c0144: `delete_plan() calls session()`
- c0143 ..> c0144: `get_plan_by_id() calls session()`
- c0143 ..> c0144: `list_plans() calls session()`
- c0143 ..> c0144: `type in __init__`
- c0143 ..> c0144: `update_plan() calls session()`
- c0143 ..> c0155: `create_plan() constructs PlansTable`
- c0144 ..> c0003: `_run_migrations() calls upgrade()`
- c0144 ..> c0117: `init_db() calls execute()`
- c0144 ..> c0117: `session() calls close()`
- c0144 ..> c0117: `session() calls execute()`
- c0144 ..> c0117: `system_session() calls close()`
- c0144 ..> c0144: `__init__() calls construct_postgres_connection_string()`
- c0144 ..> c0144: `_run_migrations() calls construct_postgres_connection_string()`
- c0144 ..> c0174: `dispose() calls dispose()`
- c0145 --|> c0146: `inherits`
- c0147 --|> c0146: `inherits`
- c0147 --> c0154: `field memories`
- c0147 --> c0156: `field project`
- c0147 --> c0157: `field skills`
- c0147 --> c0160: `field user`
- c0148 --|> c0146: `inherits`
- c0148 --> c0159: `field task`
- c0149 --|> c0146: `inherits`
- c0149 --> c0154: `field memories`
- c0149 --> c0156: `field project`
- c0149 --> c0157: `field skills`
- c0149 --> c0160: `field user`
- c0150 --|> c0146: `inherits`
- c0150 --> c0151: `field incoming_relationships`
- c0150 --> c0151: `field outgoing_relationships`
- c0150 --> c0152: `field files`
- c0150 --> c0154: `field memories`
- c0150 --> c0156: `field projects`
- c0150 --> c0160: `field user`
- c0151 --|> c0146: `inherits`
- c0151 --> c0150: `field source_entity`
- c0151 --> c0150: `field target_entity`
- c0152 --|> c0146: `inherits`
- c0152 --> c0150: `field entities`
- c0152 --> c0154: `field memories`
- c0152 --> c0156: `field project`
- c0152 --> c0157: `field skills`
- c0152 --> c0160: `field user`
- c0153 --|> c0146: `inherits`
- c0154 --|> c0146: `inherits`
- c0154 --> c0147: `field code_artifacts`
- c0154 --> c0149: `field documents`
- c0154 --> c0150: `field entities`
- c0154 --> c0152: `field files`
- c0154 --> c0156: `field projects`
- c0154 --> c0157: `field skills`
- c0154 --> c0160: `field user`
- c0155 --|> c0146: `inherits`
- c0155 --> c0156: `field project`
- c0155 --> c0159: `field tasks`
- c0155 --> c0160: `field user`
- c0156 --|> c0146: `inherits`
- c0156 --> c0147: `field code_artifacts`
- c0156 --> c0149: `field documents`
- c0156 --> c0150: `field entities`
- c0156 --> c0152: `field files`
- c0156 --> c0154: `field memories`
- c0156 --> c0155: `field plans`
- c0156 --> c0157: `field skills`
- c0156 --> c0160: `field user`
- c0157 --|> c0146: `inherits`
- c0157 --> c0147: `field code_artifacts`
- c0157 --> c0149: `field documents`
- c0157 --> c0152: `field files`
- c0157 --> c0154: `field memories`
- c0157 --> c0156: `field project`
- c0157 --> c0160: `field user`
- c0158 --|> c0146: `inherits`
- c0158 --> c0159: `field task`
- c0159 --|> c0146: `inherits`
- c0159 --> c0148: `field criteria`
- c0159 --> c0155: `field plan`
- c0159 --> c0158: `field depends_on`
- c0160 --|> c0146: `inherits`
- c0160 --> c0147: `field code_artifacts`
- c0160 --> c0149: `field documents`
- c0160 --> c0150: `field entities`
- c0160 --> c0152: `field files`
- c0160 --> c0154: `field memories`
- c0160 --> c0155: `field plans`
- c0160 --> c0156: `field projects`
- c0160 --> c0157: `field skills`
- c0161 ..> c0028: `update_project() constructs NotFoundError`
- c0161 ..> c0093: `type in create_project`
- c0161 ..> c0093: `type in get_project_by_id`
- c0161 ..> c0093: `type in update_project`
- c0161 ..> c0094: `type in create_project`
- c0161 ..> c0095: `type in list_projects`
- c0161 ..> c0096: `type in list_projects`
- c0161 ..> c0098: `type in update_project`
- c0161 ..> c0117: `delete_project() calls execute()`
- c0161 ..> c0117: `get_project_by_id() calls execute()`
- c0161 ..> c0117: `list_projects() calls execute()`
- c0161 ..> c0117: `update_project() calls execute()`
- c0161 ..> c0144: `create_project() calls session()`
- c0161 ..> c0144: `delete_project() calls session()`
- c0161 ..> c0144: `get_project_by_id() calls session()`
- c0161 ..> c0144: `list_projects() calls session()`
- c0161 ..> c0144: `type in __init__`
- c0161 ..> c0144: `update_project() calls session()`
- c0161 ..> c0156: `create_project() constructs ProjectsTable`
- c0161 ..> c0267: `list_projects() calls repository_identity()`
- c0162 ..> c0028: `get_skill_links() constructs NotFoundError`
- c0162 ..> c0028: `link_skill_to_code_artifact() constructs NotFoundError`
- c0162 ..> c0028: `link_skill_to_document() constructs NotFoundError`
- c0162 ..> c0028: `link_skill_to_file() constructs NotFoundError`
- c0162 ..> c0028: `link_skill_to_memory() constructs NotFoundError`
- c0162 ..> c0028: `update_skill() constructs NotFoundError`
- c0162 ..> c0099: `_to_skill() constructs Skill`
- c0162 ..> c0099: `type in _to_skill`
- c0162 ..> c0099: `type in create_skill`
- c0162 ..> c0099: `type in get_skill_by_id`
- c0162 ..> c0099: `type in update_skill`
- c0162 ..> c0100: `type in create_skill`
- c0162 ..> c0101: `get_skill_links() constructs SkillLinks`
- c0162 ..> c0101: `type in get_skill_links`
- c0162 ..> c0102: `type in list_skills`
- c0162 ..> c0102: `type in search_skills`
- c0162 ..> c0103: `type in update_skill`
- c0162 ..> c0117: `delete_skill() calls execute()`
- c0162 ..> c0117: `get_all_skill_code_artifact_links() calls execute()`
- c0162 ..> c0117: `get_all_skill_document_links() calls execute()`
- c0162 ..> c0117: `get_all_skill_file_links() calls execute()`
- c0162 ..> c0117: `get_skill_by_id() calls execute()`
- c0162 ..> c0117: `get_skill_links() calls execute()`
- c0162 ..> c0117: `link_skill_to_code_artifact() calls execute()`
- c0162 ..> c0117: `link_skill_to_document() calls execute()`
- c0162 ..> c0117: `link_skill_to_file() calls execute()`
- c0162 ..> c0117: `link_skill_to_memory() calls execute()`
- c0162 ..> c0117: `list_skills() calls execute()`
- c0162 ..> c0117: `search_skills() calls execute()`
- c0162 ..> c0117: `skill_name_exists() calls execute()`
- c0162 ..> c0117: `unlink_skill_from_code_artifact() calls execute()`
- c0162 ..> c0117: `unlink_skill_from_document() calls execute()`
- c0162 ..> c0117: `unlink_skill_from_file() calls execute()`
- c0162 ..> c0117: `unlink_skill_from_memory() calls execute()`
- c0162 ..> c0117: `update_skill() calls execute()`
- c0162 ..> c0127: `type in __init__`
- c0162 ..> c0130: `create_skill() calls generate_embedding()`
- c0162 ..> c0130: `search_skills() calls generate_embedding()`
- c0162 ..> c0130: `update_skill() calls generate_embedding()`
- c0162 ..> c0134: `search_skills() calls rerank()`
- c0162 ..> c0135: `type in __init__`
- c0162 ..> c0136: `create_skill() calls build_skill_embedding_text()`
- c0162 ..> c0136: `update_skill() calls build_skill_embedding_text()`
- c0162 ..> c0144: `create_skill() calls session()`
- c0162 ..> c0144: `delete_skill() calls session()`
- c0162 ..> c0144: `get_all_skill_code_artifact_links() calls session()`
- c0162 ..> c0144: `get_all_skill_document_links() calls session()`
- c0162 ..> c0144: `get_all_skill_file_links() calls session()`
- c0162 ..> c0144: `get_skill_by_id() calls session()`
- c0162 ..> c0144: `get_skill_links() calls session()`
- c0162 ..> c0144: `link_skill_to_code_artifact() calls session()`
- c0162 ..> c0144: `link_skill_to_document() calls session()`
- c0162 ..> c0144: `link_skill_to_file() calls session()`
- c0162 ..> c0144: `link_skill_to_memory() calls session()`
- c0162 ..> c0144: `list_skills() calls session()`
- c0162 ..> c0144: `search_skills() calls session()`
- c0162 ..> c0144: `skill_name_exists() calls session()`
- c0162 ..> c0144: `type in __init__`
- c0162 ..> c0144: `unlink_skill_from_code_artifact() calls session()`
- c0162 ..> c0144: `unlink_skill_from_document() calls session()`
- c0162 ..> c0144: `unlink_skill_from_file() calls session()`
- c0162 ..> c0144: `unlink_skill_from_memory() calls session()`
- c0162 ..> c0144: `update_skill() calls session()`
- c0162 ..> c0157: `create_skill() constructs SkillsTable`
- c0162 ..> c0157: `type in _to_skill`
- c0162 ..> c0162: `create_skill() calls _to_skill()`
- c0162 ..> c0162: `get_skill_by_id() calls _to_skill()`
- c0162 ..> c0162: `update_skill() calls _to_skill()`
- c0163 ..> c0024: `transition_task_state() constructs ConflictError`
- c0163 ..> c0028: `transition_task_state() constructs NotFoundError`
- c0163 ..> c0028: `update_criterion() constructs NotFoundError`
- c0163 ..> c0028: `update_task() constructs NotFoundError`
- c0163 ..> c0030: `update_criterion() calls get()`
- c0163 ..> c0077: `type in create_criterion`
- c0163 ..> c0077: `type in get_criteria_for_task`
- c0163 ..> c0077: `type in update_criterion`
- c0163 ..> c0078: `type in create_criterion`
- c0163 ..> c0079: `type in update_criterion`
- c0163 ..> c0085: `type in create_task`
- c0163 ..> c0085: `type in get_task_by_id`
- c0163 ..> c0085: `type in transition_task_state`
- c0163 ..> c0085: `type in update_task`
- c0163 ..> c0086: `type in create_task`
- c0163 ..> c0087: `type in add_dependency`
- c0163 ..> c0089: `list_tasks() constructs TaskPriority`
- c0163 ..> c0089: `list_tasks_for_user() constructs TaskPriority`
- c0163 ..> c0089: `type in list_tasks`
- c0163 ..> c0090: `list_tasks() constructs TaskState`
- c0163 ..> c0090: `list_tasks_for_user() constructs TaskState`
- c0163 ..> c0090: `type in list_tasks`
- c0163 ..> c0090: `type in transition_task_state`
- c0163 ..> c0091: `list_tasks() constructs TaskSummary`
- c0163 ..> c0091: `list_tasks_for_user() constructs TaskSummary`
- c0163 ..> c0091: `type in list_tasks`
- c0163 ..> c0091: `type in list_tasks_for_user`
- c0163 ..> c0092: `type in update_task`
- c0163 ..> c0117: `delete_criterion() calls execute()`
- c0163 ..> c0117: `delete_task() calls execute()`
- c0163 ..> c0117: `get_criteria_for_task() calls execute()`
- c0163 ..> c0117: `get_dependencies() calls execute()`
- c0163 ..> c0117: `get_dependents() calls execute()`
- c0163 ..> c0117: `get_task_by_id() calls execute()`
- c0163 ..> c0117: `list_tasks() calls execute()`
- c0163 ..> c0117: `list_tasks_for_user() calls execute()`
- c0163 ..> c0117: `remove_dependency() calls execute()`
- c0163 ..> c0117: `transition_task_state() calls execute()`
- c0163 ..> c0117: `update_criterion() calls execute()`
- c0163 ..> c0117: `update_task() calls execute()`
- c0163 ..> c0144: `add_dependency() calls session()`
- c0163 ..> c0144: `create_criterion() calls session()`
- c0163 ..> c0144: `create_task() calls session()`
- c0163 ..> c0144: `delete_criterion() calls session()`
- c0163 ..> c0144: `delete_task() calls session()`
- c0163 ..> c0144: `get_criteria_for_task() calls session()`
- c0163 ..> c0144: `get_dependencies() calls session()`
- c0163 ..> c0144: `get_dependents() calls session()`
- c0163 ..> c0144: `get_task_by_id() calls session()`
- c0163 ..> c0144: `list_tasks() calls session()`
- c0163 ..> c0144: `list_tasks_for_user() calls session()`
- c0163 ..> c0144: `remove_dependency() calls session()`
- c0163 ..> c0144: `transition_task_state() calls session()`
- c0163 ..> c0144: `type in __init__`
- c0163 ..> c0144: `update_criterion() calls session()`
- c0163 ..> c0144: `update_task() calls session()`
- c0163 ..> c0148: `create_criterion() constructs CriteriaTable`
- c0163 ..> c0158: `add_dependency() constructs TaskDependenciesTable`
- c0163 ..> c0159: `create_task() constructs TasksTable`
- c0163 ..> c0163: `update_task() calls get_task_by_id()`
- c0164 ..> c0028: `update_user() constructs NotFoundError`
- c0164 ..> c0109: `type in create_user`
- c0164 ..> c0109: `type in get_user_by_external_id`
- c0164 ..> c0109: `type in get_user_by_id`
- c0164 ..> c0109: `type in update_user`
- c0164 ..> c0110: `type in create_user`
- c0164 ..> c0112: `type in update_user`
- c0164 ..> c0117: `get_user_by_external_id() calls execute()`
- c0164 ..> c0117: `get_user_by_id() calls execute()`
- c0164 ..> c0117: `update_user() calls execute()`
- c0164 ..> c0144: `create_user() calls system_session()`
- c0164 ..> c0144: `get_user_by_external_id() calls system_session()`
- c0164 ..> c0144: `get_user_by_id() calls system_session()`
- c0164 ..> c0144: `type in __init__`
- c0164 ..> c0144: `update_user() calls system_session()`
- c0164 ..> c0160: `create_user() constructs UsersTable`
- c0165 ..> c0033: `type in count_events`
- c0165 ..> c0033: `type in query_events`
- c0165 ..> c0034: `type in save_event`
- c0165 ..> c0036: `query_events() constructs ActivityLogEntry`
- c0165 ..> c0036: `save_event() constructs ActivityLogEntry`
- c0165 ..> c0036: `type in query_events`
- c0165 ..> c0036: `type in save_event`
- c0165 ..> c0037: `type in query_events`
- c0165 ..> c0038: `type in count_events`
- c0165 ..> c0038: `type in query_events`
- c0165 ..> c0117: `cleanup_expired() calls execute()`
- c0165 ..> c0117: `count_events() calls execute()`
- c0165 ..> c0117: `query_events() calls execute()`
- c0165 ..> c0174: `cleanup_expired() calls session()`
- c0165 ..> c0174: `count_events() calls session()`
- c0165 ..> c0174: `query_events() calls session()`
- c0165 ..> c0174: `save_event() calls session()`
- c0165 ..> c0174: `type in __init__`
- c0165 ..> c0176: `save_event() constructs ActivityLogTable`
- c0166 ..> c0028: `update_code_artifact() constructs NotFoundError`
- c0166 ..> c0030: `update_code_artifact() calls get()`
- c0166 ..> c0039: `type in create_code_artifact`
- c0166 ..> c0039: `type in get_code_artifact_by_id`
- c0166 ..> c0039: `type in update_code_artifact`
- c0166 ..> c0040: `type in create_code_artifact`
- c0166 ..> c0041: `type in list_code_artifacts`
- c0166 ..> c0042: `type in update_code_artifact`
- c0166 ..> c0117: `delete_code_artifact() calls execute()`
- c0166 ..> c0117: `get_code_artifact_by_id() calls execute()`
- c0166 ..> c0117: `list_code_artifacts() calls execute()`
- c0166 ..> c0117: `update_code_artifact() calls execute()`
- c0166 ..> c0174: `create_code_artifact() calls session()`
- c0166 ..> c0174: `delete_code_artifact() calls session()`
- c0166 ..> c0174: `get_code_artifact_by_id() calls session()`
- c0166 ..> c0174: `list_code_artifacts() calls session()`
- c0166 ..> c0174: `type in __init__`
- c0166 ..> c0174: `update_code_artifact() calls session()`
- c0166 ..> c0178: `create_code_artifact() constructs CodeArtifactsTable`
- c0167 ..> c0028: `update_document() constructs NotFoundError`
- c0167 ..> c0030: `update_document() calls get()`
- c0167 ..> c0043: `type in create_document`
- c0167 ..> c0043: `type in get_document_by_id`
- c0167 ..> c0043: `type in update_document`
- c0167 ..> c0044: `type in create_document`
- c0167 ..> c0045: `type in list_documents`
- c0167 ..> c0046: `type in update_document`
- c0167 ..> c0117: `delete_document() calls execute()`
- c0167 ..> c0117: `get_document_by_id() calls execute()`
- c0167 ..> c0117: `list_documents() calls execute()`
- c0167 ..> c0117: `update_document() calls execute()`
- c0167 ..> c0174: `create_document() calls session()`
- c0167 ..> c0174: `delete_document() calls session()`
- c0167 ..> c0174: `get_document_by_id() calls session()`
- c0167 ..> c0174: `list_documents() calls session()`
- c0167 ..> c0174: `type in __init__`
- c0167 ..> c0174: `update_document() calls session()`
- c0167 ..> c0180: `create_document() constructs DocumentsTable`
- c0168 ..> c0028: `create_entity_relationship() constructs NotFoundError`
- c0168 ..> c0028: `get_entity_memories() constructs NotFoundError`
- c0168 ..> c0028: `get_entity_relationships() constructs NotFoundError`
- c0168 ..> c0028: `get_memory_entities() constructs NotFoundError`
- c0168 ..> c0028: `link_entity_to_memory() constructs NotFoundError`
- c0168 ..> c0028: `link_entity_to_project() constructs NotFoundError`
- c0168 ..> c0028: `update_entity() constructs NotFoundError`
- c0168 ..> c0028: `update_entity_relationship() constructs NotFoundError`
- c0168 ..> c0030: `update_entity() calls get()`
- c0168 ..> c0047: `type in create_entity`
- c0168 ..> c0047: `type in get_entity_by_id`
- c0168 ..> c0047: `type in update_entity`
- c0168 ..> c0048: `type in create_entity`
- c0168 ..> c0050: `create_entity_relationship() constructs EntityRelationship`
- c0168 ..> c0050: `get_all_entity_relationships() constructs EntityRelationship`
- c0168 ..> c0050: `get_entity_relationships() constructs EntityRelationship`
- c0168 ..> c0050: `type in create_entity_relationship`
- c0168 ..> c0050: `type in get_all_entity_relationships`
- c0168 ..> c0050: `type in get_entity_relationships`
- c0168 ..> c0050: `type in update_entity_relationship`
- c0168 ..> c0050: `update_entity_relationship() constructs EntityRelationship`
- c0168 ..> c0051: `type in create_entity_relationship`
- c0168 ..> c0052: `type in update_entity_relationship`
- c0168 ..> c0053: `type in list_entities`
- c0168 ..> c0053: `type in search_entities`
- c0168 ..> c0054: `type in list_entities`
- c0168 ..> c0054: `type in search_entities`
- c0168 ..> c0055: `type in update_entity`
- c0168 ..> c0117: `create_entity() calls execute()`
- c0168 ..> c0117: `create_entity_relationship() calls execute()`
- c0168 ..> c0117: `delete_entity() calls execute()`
- c0168 ..> c0117: `delete_entity_relationship() calls execute()`
- c0168 ..> c0117: `get_all_entity_file_links() calls execute()`
- c0168 ..> c0117: `get_all_entity_memory_links() calls execute()`
- c0168 ..> c0117: `get_all_entity_project_links() calls execute()`
- c0168 ..> c0117: `get_all_entity_relationships() calls execute()`
- c0168 ..> c0117: `get_entity_by_id() calls execute()`
- c0168 ..> c0117: `get_entity_memories() calls execute()`
- c0168 ..> c0117: `get_entity_relationships() calls execute()`
- c0168 ..> c0117: `get_memory_entities() calls execute()`
- c0168 ..> c0117: `link_entity_to_memory() calls execute()`
- c0168 ..> c0117: `link_entity_to_project() calls execute()`
- c0168 ..> c0117: `list_entities() calls execute()`
- c0168 ..> c0117: `search_entities() calls execute()`
- c0168 ..> c0117: `unlink_entity_from_memory() calls execute()`
- c0168 ..> c0117: `unlink_entity_from_project() calls execute()`
- c0168 ..> c0117: `update_entity() calls execute()`
- c0168 ..> c0117: `update_entity_relationship() calls execute()`
- c0168 ..> c0174: `create_entity() calls session()`
- c0168 ..> c0174: `create_entity_relationship() calls session()`
- c0168 ..> c0174: `delete_entity() calls session()`
- c0168 ..> c0174: `delete_entity_relationship() calls session()`
- c0168 ..> c0174: `get_all_entity_file_links() calls session()`
- c0168 ..> c0174: `get_all_entity_memory_links() calls session()`
- c0168 ..> c0174: `get_all_entity_project_links() calls session()`
- c0168 ..> c0174: `get_all_entity_relationships() calls session()`
- c0168 ..> c0174: `get_entity_by_id() calls session()`
- c0168 ..> c0174: `get_entity_memories() calls session()`
- c0168 ..> c0174: `get_entity_relationships() calls session()`
- c0168 ..> c0174: `get_memory_entities() calls session()`
- c0168 ..> c0174: `link_entity_to_memory() calls session()`
- c0168 ..> c0174: `link_entity_to_project() calls session()`
- c0168 ..> c0174: `list_entities() calls session()`
- c0168 ..> c0174: `search_entities() calls session()`
- c0168 ..> c0174: `type in __init__`
- c0168 ..> c0174: `unlink_entity_from_memory() calls session()`
- c0168 ..> c0174: `unlink_entity_from_project() calls session()`
- c0168 ..> c0174: `update_entity() calls session()`
- c0168 ..> c0174: `update_entity_relationship() calls session()`
- c0168 ..> c0181: `create_entity() constructs EntitiesTable`
- c0168 ..> c0182: `create_entity_relationship() constructs EntityRelationshipsTable`
- c0169 ..> c0028: `update_file() constructs NotFoundError`
- c0169 ..> c0056: `_to_file_model() constructs File`
- c0169 ..> c0056: `type in _to_file_model`
- c0169 ..> c0056: `type in create_file`
- c0169 ..> c0056: `type in get_file_by_id`
- c0169 ..> c0056: `type in update_file`
- c0169 ..> c0057: `type in create_file`
- c0169 ..> c0058: `type in list_files`
- c0169 ..> c0059: `type in update_file`
- c0169 ..> c0117: `delete_file() calls execute()`
- c0169 ..> c0117: `get_file_by_id() calls execute()`
- c0169 ..> c0117: `list_files() calls execute()`
- c0169 ..> c0117: `update_file() calls execute()`
- c0169 ..> c0169: `create_file() calls _to_file_model()`
- c0169 ..> c0169: `get_file_by_id() calls _to_file_model()`
- c0169 ..> c0169: `update_file() calls _to_file_model()`
- c0169 ..> c0174: `create_file() calls session()`
- c0169 ..> c0174: `delete_file() calls session()`
- c0169 ..> c0174: `get_file_by_id() calls session()`
- c0169 ..> c0174: `list_files() calls session()`
- c0169 ..> c0174: `type in __init__`
- c0169 ..> c0174: `update_file() calls session()`
- c0169 ..> c0183: `create_file() constructs FilesTable`
- c0169 ..> c0183: `type in _to_file_model`
- c0170 ..> c0023: `update_memory() calls clear()`
- c0170 ..> c0028: `_link_code_artifacts() constructs NotFoundError`
- c0170 ..> c0028: `_link_documents() constructs NotFoundError`
- c0170 ..> c0028: `_link_files() constructs NotFoundError`
- c0170 ..> c0028: `_link_projects() constructs NotFoundError`
- c0170 ..> c0028: `_link_skills() constructs NotFoundError`
- c0170 ..> c0028: `create_link() constructs NotFoundError`
- c0170 ..> c0028: `find_similar_memories_scored() constructs NotFoundError`
- c0170 ..> c0028: `get_linked_memories() constructs NotFoundError`
- c0170 ..> c0028: `get_memory_by_id() constructs NotFoundError`
- c0170 ..> c0028: `get_memory_table_by_id() constructs NotFoundError`
- c0170 ..> c0028: `mark_obsolete() constructs NotFoundError`
- c0170 ..> c0028: `update_memory() constructs NotFoundError`
- c0170 ..> c0030: `create_link() calls get()`
- c0170 ..> c0030: `list_memories() calls get()`
- c0170 ..> c0065: `type in create_memory`
- c0170 ..> c0065: `type in find_obsolete_matches`
- c0170 ..> c0065: `type in find_similar_memories`
- c0170 ..> c0065: `type in find_similar_memories_scored`
- c0170 ..> c0065: `type in get_linked_memories`
- c0170 ..> c0065: `type in get_memories_for_reembedding`
- c0170 ..> c0065: `type in get_memories_for_targeted_rebuild`
- c0170 ..> c0065: `type in get_memory_by_id`
- c0170 ..> c0065: `type in list_memories`
- c0170 ..> c0065: `type in search`
- c0170 ..> c0065: `type in search_scored`
- c0170 ..> c0065: `type in semantic_search`
- c0170 ..> c0065: `type in semantic_search_scored`
- c0170 ..> c0065: `type in update_memory`
- c0170 ..> c0066: `type in create_memory`
- c0170 ..> c0072: `search_scored() constructs MemoryScore`
- c0170 ..> c0072: `type in search_scored`
- c0170 ..> c0074: `type in update_memory`
- c0170 ..> c0117: `_link_code_artifacts() calls execute()`
- c0170 ..> c0117: `_link_documents() calls execute()`
- c0170 ..> c0117: `_link_files() calls execute()`
- c0170 ..> c0117: `_link_projects() calls execute()`
- c0170 ..> c0117: `_link_skills() calls execute()`
- c0170 ..> c0117: `bulk_update_embeddings() calls execute()`
- c0170 ..> c0117: `count_all_memories() calls execute()`
- c0170 ..> c0117: `count_memories_for_targeted_rebuild() calls execute()`
- c0170 ..> c0117: `create_memory() calls execute()`
- c0170 ..> c0117: `find_obsolete_matches() calls execute()`
- c0170 ..> c0117: `find_similar_memories_scored() calls execute()`
- c0170 ..> c0117: `get_linked_memories() calls execute()`
- c0170 ..> c0117: `get_memories_for_reembedding() calls execute()`
- c0170 ..> c0117: `get_memories_for_targeted_rebuild() calls execute()`
- c0170 ..> c0117: `get_memory_table_by_id() calls execute()`
- c0170 ..> c0117: `get_subgraph_nodes() calls execute()`
- c0170 ..> c0117: `list_memories() calls execute()`
- c0170 ..> c0117: `mark_obsolete() calls execute()`
- c0170 ..> c0117: `record_memory_access() calls execute()`
- c0170 ..> c0117: `reset_embedding_storage() calls execute()`
- c0170 ..> c0117: `semantic_search_scored() calls execute()`
- c0170 ..> c0117: `unlink_memories() calls execute()`
- c0170 ..> c0117: `update_memory() calls execute()`
- c0170 ..> c0117: `upsert_targeted_embeddings() calls execute()`
- c0170 ..> c0117: `validate_embedding_count() calls execute()`
- c0170 ..> c0117: `validate_embedding_dimensions() calls execute()`
- c0170 ..> c0117: `validate_search_works() calls execute()`
- c0170 ..> c0127: `type in __init__`
- c0170 ..> c0130: `_generate_embeddings() calls generate_embedding()`
- c0170 ..> c0134: `search_scored() calls rerank()`
- c0170 ..> c0135: `type in __init__`
- c0170 ..> c0136: `create_memory() calls build_embedding_text()`
- c0170 ..> c0136: `search_scored() calls build_contextual_query()`
- c0170 ..> c0136: `search_scored() calls build_memory_text()`
- c0170 ..> c0136: `update_memory() calls build_embedding_text()`
- c0170 ..> c0170: `count_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0170 ..> c0170: `create_links_batch() calls create_link()`
- c0170 ..> c0170: `create_memory() calls _generate_embeddings()`
- c0170 ..> c0170: `create_memory() calls _link_code_artifacts()`
- c0170 ..> c0170: `create_memory() calls _link_documents()`
- c0170 ..> c0170: `create_memory() calls _link_files()`
- c0170 ..> c0170: `create_memory() calls _link_projects()`
- c0170 ..> c0170: `create_memory() calls _link_skills()`
- c0170 ..> c0170: `find_similar_memories() calls find_similar_memories_scored()`
- c0170 ..> c0170: `get_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0170 ..> c0170: `get_memory_by_id() calls get_memory_table_by_id()`
- c0170 ..> c0170: `search() calls search_scored()`
- c0170 ..> c0170: `search_scored() calls semantic_search_scored()`
- c0170 ..> c0170: `semantic_search() calls semantic_search_scored()`
- c0170 ..> c0170: `semantic_search_scored() calls _generate_embeddings()`
- c0170 ..> c0170: `update_memory() calls _generate_embeddings()`
- c0170 ..> c0170: `update_memory() calls _link_code_artifacts()`
- c0170 ..> c0170: `update_memory() calls _link_documents()`
- c0170 ..> c0170: `update_memory() calls _link_files()`
- c0170 ..> c0170: `update_memory() calls _link_projects()`
- c0170 ..> c0170: `validate_search_works() calls _generate_embeddings()`
- c0170 ..> c0174: `bulk_update_embeddings() calls system_session()`
- c0170 ..> c0174: `count_all_memories() calls system_session()`
- c0170 ..> c0174: `count_memories_for_targeted_rebuild() calls system_session()`
- c0170 ..> c0174: `create_link() calls session()`
- c0170 ..> c0174: `create_memory() calls session()`
- c0170 ..> c0174: `find_obsolete_matches() calls session()`
- c0170 ..> c0174: `find_similar_memories_scored() calls session()`
- c0170 ..> c0174: `get_linked_memories() calls session()`
- c0170 ..> c0174: `get_memories_for_reembedding() calls system_session()`
- c0170 ..> c0174: `get_memories_for_targeted_rebuild() calls system_session()`
- c0170 ..> c0174: `get_memory_table_by_id() calls session()`
- c0170 ..> c0174: `get_subgraph_nodes() calls session()`
- c0170 ..> c0174: `list_memories() calls session()`
- c0170 ..> c0174: `mark_obsolete() calls session()`
- c0170 ..> c0174: `record_memory_access() calls system_session()`
- c0170 ..> c0174: `reset_embedding_storage() calls system_session()`
- c0170 ..> c0174: `semantic_search_scored() calls session()`
- c0170 ..> c0174: `type in __init__`
- c0170 ..> c0174: `unlink_memories() calls session()`
- c0170 ..> c0174: `update_memory() calls session()`
- c0170 ..> c0174: `upsert_targeted_embeddings() calls system_session()`
- c0170 ..> c0174: `validate_embedding_count() calls system_session()`
- c0170 ..> c0174: `validate_embedding_dimensions() calls system_session()`
- c0170 ..> c0174: `validate_search_works() calls system_session()`
- c0170 ..> c0184: `create_link() constructs MemoryLinkTable`
- c0170 ..> c0184: `type in create_link`
- c0170 ..> c0185: `create_memory() constructs MemoryTable`
- c0170 ..> c0185: `type in _link_code_artifacts`
- c0170 ..> c0185: `type in _link_documents`
- c0170 ..> c0185: `type in _link_files`
- c0170 ..> c0185: `type in _link_projects`
- c0170 ..> c0185: `type in _link_skills`
- c0170 ..> c0185: `type in get_memory_table_by_id`
- c0171 ..> c0028: `update_plan() constructs NotFoundError`
- c0171 ..> c0080: `type in create_plan`
- c0171 ..> c0080: `type in get_plan_by_id`
- c0171 ..> c0080: `type in update_plan`
- c0171 ..> c0081: `type in create_plan`
- c0171 ..> c0082: `type in list_plans`
- c0171 ..> c0083: `type in list_plans`
- c0171 ..> c0084: `type in update_plan`
- c0171 ..> c0117: `delete_plan() calls execute()`
- c0171 ..> c0117: `get_plan_by_id() calls execute()`
- c0171 ..> c0117: `list_plans() calls execute()`
- c0171 ..> c0117: `update_plan() calls execute()`
- c0171 ..> c0174: `create_plan() calls session()`
- c0171 ..> c0174: `delete_plan() calls session()`
- c0171 ..> c0174: `get_plan_by_id() calls session()`
- c0171 ..> c0174: `list_plans() calls session()`
- c0171 ..> c0174: `type in __init__`
- c0171 ..> c0174: `update_plan() calls session()`
- c0171 ..> c0186: `create_plan() constructs PlansTable`
- c0172 ..> c0028: `update_project() constructs NotFoundError`
- c0172 ..> c0093: `type in create_project`
- c0172 ..> c0093: `type in get_project_by_id`
- c0172 ..> c0093: `type in update_project`
- c0172 ..> c0094: `type in create_project`
- c0172 ..> c0095: `type in list_projects`
- c0172 ..> c0096: `type in list_projects`
- c0172 ..> c0098: `type in update_project`
- c0172 ..> c0117: `delete_project() calls execute()`
- c0172 ..> c0117: `get_project_by_id() calls execute()`
- c0172 ..> c0117: `list_projects() calls execute()`
- c0172 ..> c0117: `update_project() calls execute()`
- c0172 ..> c0174: `create_project() calls session()`
- c0172 ..> c0174: `delete_project() calls session()`
- c0172 ..> c0174: `get_project_by_id() calls session()`
- c0172 ..> c0174: `list_projects() calls session()`
- c0172 ..> c0174: `type in __init__`
- c0172 ..> c0174: `update_project() calls session()`
- c0172 ..> c0187: `create_project() constructs ProjectsTable`
- c0172 ..> c0267: `list_projects() calls repository_identity()`
- c0173 ..> c0028: `get_skill_links() constructs NotFoundError`
- c0173 ..> c0028: `link_skill_to_code_artifact() constructs NotFoundError`
- c0173 ..> c0028: `link_skill_to_document() constructs NotFoundError`
- c0173 ..> c0028: `link_skill_to_file() constructs NotFoundError`
- c0173 ..> c0028: `link_skill_to_memory() constructs NotFoundError`
- c0173 ..> c0028: `update_skill() constructs NotFoundError`
- c0173 ..> c0099: `_to_skill() constructs Skill`
- c0173 ..> c0099: `type in _to_skill`
- c0173 ..> c0099: `type in create_skill`
- c0173 ..> c0099: `type in get_skill_by_id`
- c0173 ..> c0099: `type in update_skill`
- c0173 ..> c0100: `type in create_skill`
- c0173 ..> c0101: `get_skill_links() constructs SkillLinks`
- c0173 ..> c0101: `type in get_skill_links`
- c0173 ..> c0102: `type in list_skills`
- c0173 ..> c0102: `type in search_skills`
- c0173 ..> c0103: `type in update_skill`
- c0173 ..> c0117: `create_skill() calls execute()`
- c0173 ..> c0117: `delete_skill() calls execute()`
- c0173 ..> c0117: `get_all_skill_code_artifact_links() calls execute()`
- c0173 ..> c0117: `get_all_skill_document_links() calls execute()`
- c0173 ..> c0117: `get_all_skill_file_links() calls execute()`
- c0173 ..> c0117: `get_skill_by_id() calls execute()`
- c0173 ..> c0117: `get_skill_links() calls execute()`
- c0173 ..> c0117: `link_skill_to_code_artifact() calls execute()`
- c0173 ..> c0117: `link_skill_to_document() calls execute()`
- c0173 ..> c0117: `link_skill_to_file() calls execute()`
- c0173 ..> c0117: `link_skill_to_memory() calls execute()`
- c0173 ..> c0117: `list_skills() calls execute()`
- c0173 ..> c0117: `search_skills() calls execute()`
- c0173 ..> c0117: `skill_name_exists() calls execute()`
- c0173 ..> c0117: `unlink_skill_from_code_artifact() calls execute()`
- c0173 ..> c0117: `unlink_skill_from_document() calls execute()`
- c0173 ..> c0117: `unlink_skill_from_file() calls execute()`
- c0173 ..> c0117: `unlink_skill_from_memory() calls execute()`
- c0173 ..> c0117: `update_skill() calls execute()`
- c0173 ..> c0127: `type in __init__`
- c0173 ..> c0130: `create_skill() calls generate_embedding()`
- c0173 ..> c0130: `search_skills() calls generate_embedding()`
- c0173 ..> c0130: `update_skill() calls generate_embedding()`
- c0173 ..> c0134: `search_skills() calls rerank()`
- c0173 ..> c0135: `type in __init__`
- c0173 ..> c0136: `create_skill() calls build_skill_embedding_text()`
- c0173 ..> c0136: `update_skill() calls build_skill_embedding_text()`
- c0173 ..> c0173: `create_skill() calls _to_skill()`
- c0173 ..> c0173: `get_skill_by_id() calls _to_skill()`
- c0173 ..> c0173: `update_skill() calls _to_skill()`
- c0173 ..> c0174: `create_skill() calls session()`
- c0173 ..> c0174: `delete_skill() calls session()`
- c0173 ..> c0174: `get_all_skill_code_artifact_links() calls session()`
- c0173 ..> c0174: `get_all_skill_document_links() calls session()`
- c0173 ..> c0174: `get_all_skill_file_links() calls session()`
- c0173 ..> c0174: `get_skill_by_id() calls session()`
- c0173 ..> c0174: `get_skill_links() calls session()`
- c0173 ..> c0174: `link_skill_to_code_artifact() calls session()`
- c0173 ..> c0174: `link_skill_to_document() calls session()`
- c0173 ..> c0174: `link_skill_to_file() calls session()`
- c0173 ..> c0174: `link_skill_to_memory() calls session()`
- c0173 ..> c0174: `list_skills() calls session()`
- c0173 ..> c0174: `search_skills() calls session()`
- c0173 ..> c0174: `skill_name_exists() calls session()`
- c0173 ..> c0174: `type in __init__`
- c0173 ..> c0174: `unlink_skill_from_code_artifact() calls session()`
- c0173 ..> c0174: `unlink_skill_from_document() calls session()`
- c0173 ..> c0174: `unlink_skill_from_file() calls session()`
- c0173 ..> c0174: `unlink_skill_from_memory() calls session()`
- c0173 ..> c0174: `update_skill() calls session()`
- c0173 ..> c0188: `create_skill() constructs SkillsTable`
- c0173 ..> c0188: `type in _to_skill`
- c0174 ..> c0003: `_run_migrations() calls upgrade()`
- c0174 ..> c0117: `init_db() calls execute()`
- c0174 ..> c0117: `session() calls close()`
- c0174 ..> c0117: `system_session() calls close()`
- c0174 ..> c0144: `dispose() calls dispose()`
- c0174 ..> c0174: `__init__() calls _construct_connection_string()`
- c0174 ..> c0174: `_run_migrations() calls _construct_connection_string()`
- c0175 ..> c0117: `_sqlite_connection_creator() calls execute()`
- c0176 --|> c0177: `inherits`
- c0178 --|> c0177: `inherits`
- c0178 --> c0185: `field memories`
- c0178 --> c0187: `field project`
- c0178 --> c0188: `field skills`
- c0178 --> c0191: `field user`
- c0179 --|> c0177: `inherits`
- c0179 --> c0190: `field task`
- c0180 --|> c0177: `inherits`
- c0180 --> c0185: `field memories`
- c0180 --> c0187: `field project`
- c0180 --> c0188: `field skills`
- c0180 --> c0191: `field user`
- c0181 --|> c0177: `inherits`
- c0181 --> c0182: `field incoming_relationships`
- c0181 --> c0182: `field outgoing_relationships`
- c0181 --> c0183: `field files`
- c0181 --> c0185: `field memories`
- c0181 --> c0187: `field projects`
- c0181 --> c0191: `field user`
- c0182 --|> c0177: `inherits`
- c0182 --> c0181: `field source_entity`
- c0182 --> c0181: `field target_entity`
- c0183 --|> c0177: `inherits`
- c0183 --> c0181: `field entities`
- c0183 --> c0185: `field memories`
- c0183 --> c0187: `field project`
- c0183 --> c0188: `field skills`
- c0183 --> c0191: `field user`
- c0184 --|> c0177: `inherits`
- c0185 --|> c0177: `inherits`
- c0185 --> c0178: `field code_artifacts`
- c0185 --> c0180: `field documents`
- c0185 --> c0181: `field entities`
- c0185 --> c0183: `field files`
- c0185 --> c0187: `field projects`
- c0185 --> c0188: `field skills`
- c0185 --> c0191: `field user`
- c0186 --|> c0177: `inherits`
- c0186 --> c0187: `field project`
- c0186 --> c0190: `field tasks`
- c0186 --> c0191: `field user`
- c0187 --|> c0177: `inherits`
- c0187 --> c0178: `field code_artifacts`
- c0187 --> c0180: `field documents`
- c0187 --> c0181: `field entities`
- c0187 --> c0183: `field files`
- c0187 --> c0185: `field memories`
- c0187 --> c0186: `field plans`
- c0187 --> c0188: `field skills`
- c0187 --> c0191: `field user`
- c0188 --|> c0177: `inherits`
- c0188 --> c0178: `field code_artifacts`
- c0188 --> c0180: `field documents`
- c0188 --> c0183: `field files`
- c0188 --> c0185: `field memories`
- c0188 --> c0187: `field project`
- c0188 --> c0191: `field user`
- c0189 --|> c0177: `inherits`
- c0189 --> c0190: `field task`
- c0190 --|> c0177: `inherits`
- c0190 --> c0179: `field criteria`
- c0190 --> c0186: `field plan`
- c0190 --> c0189: `field depends_on`
- c0191 --|> c0177: `inherits`
- c0191 --> c0178: `field code_artifacts`
- c0191 --> c0180: `field documents`
- c0191 --> c0181: `field entities`
- c0191 --> c0183: `field files`
- c0191 --> c0185: `field memories`
- c0191 --> c0186: `field plans`
- c0191 --> c0187: `field projects`
- c0191 --> c0188: `field skills`
- c0192 ..> c0024: `transition_task_state() constructs ConflictError`
- c0192 ..> c0028: `transition_task_state() constructs NotFoundError`
- c0192 ..> c0028: `update_criterion() constructs NotFoundError`
- c0192 ..> c0028: `update_task() constructs NotFoundError`
- c0192 ..> c0030: `update_criterion() calls get()`
- c0192 ..> c0077: `type in create_criterion`
- c0192 ..> c0077: `type in get_criteria_for_task`
- c0192 ..> c0077: `type in update_criterion`
- c0192 ..> c0078: `type in create_criterion`
- c0192 ..> c0079: `type in update_criterion`
- c0192 ..> c0085: `type in create_task`
- c0192 ..> c0085: `type in get_task_by_id`
- c0192 ..> c0085: `type in transition_task_state`
- c0192 ..> c0085: `type in update_task`
- c0192 ..> c0086: `type in create_task`
- c0192 ..> c0087: `type in add_dependency`
- c0192 ..> c0089: `list_tasks() constructs TaskPriority`
- c0192 ..> c0089: `list_tasks_for_user() constructs TaskPriority`
- c0192 ..> c0089: `type in list_tasks`
- c0192 ..> c0090: `list_tasks() constructs TaskState`
- c0192 ..> c0090: `list_tasks_for_user() constructs TaskState`
- c0192 ..> c0090: `type in list_tasks`
- c0192 ..> c0090: `type in transition_task_state`
- c0192 ..> c0091: `list_tasks() constructs TaskSummary`
- c0192 ..> c0091: `list_tasks_for_user() constructs TaskSummary`
- c0192 ..> c0091: `type in list_tasks`
- c0192 ..> c0091: `type in list_tasks_for_user`
- c0192 ..> c0092: `type in update_task`
- c0192 ..> c0117: `delete_criterion() calls execute()`
- c0192 ..> c0117: `delete_task() calls execute()`
- c0192 ..> c0117: `get_criteria_for_task() calls execute()`
- c0192 ..> c0117: `get_dependencies() calls execute()`
- c0192 ..> c0117: `get_dependents() calls execute()`
- c0192 ..> c0117: `get_task_by_id() calls execute()`
- c0192 ..> c0117: `list_tasks() calls execute()`
- c0192 ..> c0117: `list_tasks_for_user() calls execute()`
- c0192 ..> c0117: `remove_dependency() calls execute()`
- c0192 ..> c0117: `transition_task_state() calls execute()`
- c0192 ..> c0117: `update_criterion() calls execute()`
- c0192 ..> c0117: `update_task() calls execute()`
- c0192 ..> c0174: `add_dependency() calls session()`
- c0192 ..> c0174: `create_criterion() calls session()`
- c0192 ..> c0174: `create_task() calls session()`
- c0192 ..> c0174: `delete_criterion() calls session()`
- c0192 ..> c0174: `delete_task() calls session()`
- c0192 ..> c0174: `get_criteria_for_task() calls session()`
- c0192 ..> c0174: `get_dependencies() calls session()`
- c0192 ..> c0174: `get_dependents() calls session()`
- c0192 ..> c0174: `get_task_by_id() calls session()`
- c0192 ..> c0174: `list_tasks() calls session()`
- c0192 ..> c0174: `list_tasks_for_user() calls session()`
- c0192 ..> c0174: `remove_dependency() calls session()`
- c0192 ..> c0174: `transition_task_state() calls session()`
- c0192 ..> c0174: `type in __init__`
- c0192 ..> c0174: `update_criterion() calls session()`
- c0192 ..> c0174: `update_task() calls session()`
- c0192 ..> c0179: `create_criterion() constructs CriteriaTable`
- c0192 ..> c0189: `add_dependency() constructs TaskDependenciesTable`
- c0192 ..> c0190: `create_task() constructs TasksTable`
- c0192 ..> c0192: `update_task() calls get_task_by_id()`
- c0193 ..> c0028: `update_user() constructs NotFoundError`
- c0193 ..> c0109: `type in create_user`
- c0193 ..> c0109: `type in get_user_by_external_id`
- c0193 ..> c0109: `type in get_user_by_id`
- c0193 ..> c0109: `type in update_user`
- c0193 ..> c0110: `type in create_user`
- c0193 ..> c0112: `type in update_user`
- c0193 ..> c0117: `get_user_by_external_id() calls execute()`
- c0193 ..> c0117: `get_user_by_id() calls execute()`
- c0193 ..> c0117: `update_user() calls execute()`
- c0193 ..> c0174: `create_user() calls system_session()`
- c0193 ..> c0174: `get_user_by_external_id() calls system_session()`
- c0193 ..> c0174: `get_user_by_id() calls system_session()`
- c0193 ..> c0174: `type in __init__`
- c0193 ..> c0174: `update_user() calls system_session()`
- c0193 ..> c0191: `create_user() constructs UsersTable`
- c0194 ..> c0030: `parse_datetime_param() calls get()`
- c0194 ..> c0030: `parse_int_param() calls get()`
- c0198 ..> c0030: `parse_int_param() calls get()`
- c0202 ..> c0030: `parse_int_param() calls get()`
- c0207 ..> c0030: `status() calls get()`
- c0207 ..> c0207: `login() calls upsert_env_var()`
- c0207 ..> c0207: `status() calls _has_cached_credentials()`
- c0207 ..> c0212: `login() calls token_cache_dir()`
- c0207 ..> c0212: `login() calls user_env_file()`
- c0207 ..> c0212: `logout() calls token_cache_dir()`
- c0207 ..> c0212: `status() calls token_cache_dir()`
- c0207 ..> c0213: `status() calls close()`
- c0207 ..> c0213: `status() calls execute()`
- c0207 ..> c0213: `status() constructs RemoteExecutor`
- c0207 ..> c0214: `login() calls normalize_server_url()`
- c0207 ..> c0214: `status() calls normalize_server_url()`
- c0208 ..> c0013: `type in __init__`
- c0208 ..> c0209: `__init__() constructs _CliRuntime`
- c0209 ..> c0013: `type in __init__`
- c0210 ..> c0013: `type in __init__`
- c0210 ..> c0015: `close() calls dispose_runtime()`
- c0210 ..> c0015: `create() calls build_runtime()`
- c0210 ..> c0117: `execute() calls execute()`
- c0210 ..> c0208: `__init__() constructs CliContext`
- c0210 ..> c0222: `execute() calls ensure_tool_executable()`
- c0210 ..> c0222: `list_tools() calls build_discovery_payload()`
- c0210 ..> c0222: `tool_info() calls build_tool_documentation()`
- c0211 ..> c0030: `_build_executor() calls get()`
- c0211 ..> c0117: `_run_tool_command() calls close()`
- c0211 ..> c0117: `_run_tool_command() calls execute()`
- c0211 ..> c0117: `_run_tool_command() calls list_tools()`
- c0211 ..> c0117: `_run_tool_command() calls tool_info()`
- c0211 ..> c0207: `_run_auth_command() calls login()`
- c0211 ..> c0207: `_run_auth_command() calls logout()`
- c0211 ..> c0207: `_run_auth_command() calls status()`
- c0211 ..> c0210: `_build_executor() calls create()`
- c0211 ..> c0211: `_run_tool_command() calls _build_executor()`
- c0211 ..> c0211: `dispatch() calls _run_auth_command()`
- c0211 ..> c0211: `dispatch() calls _run_tool_command()`
- c0211 ..> c0211: `dispatch() calls build_parser()`
- c0211 ..> c0213: `_build_executor() constructs RemoteExecutor`
- c0211 ..> c0215: `_run_auth_command() calls emit_error()`
- c0211 ..> c0215: `_run_tool_command() calls emit_error()`
- c0211 ..> c0215: `_run_tool_command() calls render_result()`
- c0211 ..> c0217: `_run_tool_command() calls run()`
- c0211 ..> c0217: `dispatch() calls run()`
- c0211 ..> c0269: `build_parser() calls get_version()`
- c0212 ..> c0212: `token_cache_dir() calls config_dir()`
- c0212 ..> c0212: `user_env_file() calls config_dir()`
- c0213 ..> c0117: `close() calls close()`
- c0213 ..> c0213: `execute() calls _call()`
- c0213 ..> c0213: `list_tools() calls _call()`
- c0213 ..> c0213: `tool_info() calls _call()`
- c0213 ..> c0214: `__init__() calls normalize_server_url()`
- c0214 ..> c0212: `_default_client_factory() calls token_cache_dir()`
- c0215 ..> c0030: `render_memory_detail() calls get()`
- c0215 ..> c0030: `render_memory_lines() calls get()`
- c0215 ..> c0030: `render_project_lines() calls get()`
- c0215 ..> c0215: `render_result() calls to_jsonable()`
- c0217 ..> c0030: `_memory_recent() calls get()`
- c0217 ..> c0030: `_memory_search() calls get()`
- c0217 ..> c0030: `_project_list() calls get()`
- c0217 ..> c0030: `resolve_project() calls get()`
- c0217 ..> c0117: `_memory_get() calls execute()`
- c0217 ..> c0117: `_memory_recent() calls execute()`
- c0217 ..> c0117: `_memory_save() calls execute()`
- c0217 ..> c0117: `_memory_search() calls execute()`
- c0217 ..> c0117: `_project_list() calls execute()`
- c0217 ..> c0117: `resolve_project() calls execute()`
- c0217 ..> c0215: `_memory_get() calls render_memory_detail()`
- c0217 ..> c0215: `_memory_get() calls to_jsonable()`
- c0217 ..> c0215: `_memory_recent() calls render_memory_lines()`
- c0217 ..> c0215: `_memory_recent() calls to_jsonable()`
- c0217 ..> c0215: `_memory_save() calls to_jsonable()`
- c0217 ..> c0215: `_memory_search() calls render_memory_lines()`
- c0217 ..> c0215: `_memory_search() calls to_jsonable()`
- c0217 ..> c0215: `_project_list() calls render_project_lines()`
- c0217 ..> c0215: `_project_list() calls to_jsonable()`
- c0217 ..> c0215: `resolve_project() calls to_jsonable()`
- c0217 ..> c0216: `resolve_project() constructs CliError`
- c0217 ..> c0217: `_memory_recent() calls resolve_project()`
- c0217 ..> c0217: `_memory_save() calls resolve_project()`
- c0217 ..> c0217: `_memory_search() calls resolve_project()`
- c0217 ..> c0217: `run() calls _project_list()`
- c0222 ..> c0104: `build_discovery_payload() constructs ToolCategory`
- c0222 ..> c0107: `build_discovery_payload() calls to_discovery_dict()`
- c0222 ..> c0107: `build_tool_documentation() calls to_detailed_dict()`
- c0222 ..> c0222: `_build_discover_docstring() calls _build_category_list()`
- c0222 ..> c0222: `_build_discover_docstring() calls _build_compact_discover_docstring()`
- c0222 ..> c0222: `_build_discover_docstring() calls _get_mcp_descriptor_mode()`
- c0222 ..> c0222: `_build_execute_docstring() calls _build_compact_execute_docstring()`
- c0222 ..> c0222: `_build_execute_docstring() calls _build_tool_categories_line()`
- c0222 ..> c0222: `_build_execute_docstring() calls _get_mcp_descriptor_mode()`
- c0222 ..> c0222: `register() calls _build_discover_docstring()`
- c0222 ..> c0222: `register() calls _build_execute_docstring()`
- c0222 ..> c0225: `build_tool_documentation() calls get_required_scope()`
- c0222 ..> c0225: `ensure_tool_executable() calls get_required_scope()`
- c0222 ..> c0239: `build_discovery_payload() calls get_permitted_by_category()`
- c0222 ..> c0239: `build_discovery_payload() calls get_permitted_categories()`
- c0222 ..> c0239: `build_discovery_payload() calls get_permitted_tools()`
- c0222 ..> c0239: `build_tool_documentation() calls get_permitted_tools()`
- c0222 ..> c0239: `build_tool_documentation() calls get_tool()`
- c0222 ..> c0239: `build_tool_documentation() calls is_permitted()`
- c0222 ..> c0239: `ensure_tool_executable() calls get_permitted_tools()`
- c0222 ..> c0239: `ensure_tool_executable() calls tool_exists()`
- c0225 ..> c0030: `_extract_token_scopes() calls get()`
- c0225 ..> c0030: `get_required_scope() calls get()`
- c0225 ..> c0030: `resolve_permitted_tools() calls get()`
- c0225 ..> c0225: `_extract_token_scopes() calls parse_scopes()`
- c0225 ..> c0225: `get_effective_scopes() calls _extract_token_scopes()`
- c0225 ..> c0225: `get_effective_scopes() calls resolve_permitted_tools()`
- c0225 ..> c0239: `get_effective_scopes() calls list_all_tools()`
- c0225 ..> c0239: `get_required_scope() calls get_tool()`
- c0225 ..> c0239: `resolve_permitted_tools() calls list_all_tools()`
- c0225 ..> c0239: `type in get_required_scope`
- c0225 ..> c0239: `type in resolve_permitted_tools`
- c0227 ..> c0031: `create_code_artifact() calls get_user_from_auth()`
- c0227 ..> c0031: `delete_code_artifact() calls get_user_from_auth()`
- c0227 ..> c0031: `get_code_artifact() calls get_user_from_auth()`
- c0227 ..> c0031: `list_code_artifacts() calls get_user_from_auth()`
- c0227 ..> c0031: `update_code_artifact() calls get_user_from_auth()`
- c0227 ..> c0039: `type in create_code_artifact`
- c0227 ..> c0039: `type in get_code_artifact`
- c0227 ..> c0039: `type in update_code_artifact`
- c0227 ..> c0040: `create_code_artifact() constructs CodeArtifactCreate`
- c0227 ..> c0042: `update_code_artifact() constructs CodeArtifactUpdate`
- c0227 ..> c0243: `create_code_artifact() calls create_code_artifact()`
- c0227 ..> c0243: `delete_code_artifact() calls delete_code_artifact()`
- c0227 ..> c0243: `get_code_artifact() calls get_code_artifact()`
- c0227 ..> c0243: `list_code_artifacts() calls list_code_artifacts()`
- c0227 ..> c0243: `type in __init__`
- c0227 ..> c0243: `update_code_artifact() calls update_code_artifact()`
- c0227 ..> c0264: `type in __init__`
- c0227 ..> c0266: `update_code_artifact() calls filter_none_values()`
- c0228 ..> c0031: `create_document() calls get_user_from_auth()`
- c0228 ..> c0031: `delete_document() calls get_user_from_auth()`
- c0228 ..> c0031: `get_document() calls get_user_from_auth()`
- c0228 ..> c0031: `list_documents() calls get_user_from_auth()`
- c0228 ..> c0031: `update_document() calls get_user_from_auth()`
- c0228 ..> c0043: `type in create_document`
- c0228 ..> c0043: `type in get_document`
- c0228 ..> c0043: `type in update_document`
- c0228 ..> c0044: `create_document() constructs DocumentCreate`
- c0228 ..> c0046: `update_document() constructs DocumentUpdate`
- c0228 ..> c0244: `create_document() calls create_document()`
- c0228 ..> c0244: `delete_document() calls delete_document()`
- c0228 ..> c0244: `get_document() calls get_document()`
- c0228 ..> c0244: `list_documents() calls list_documents()`
- c0228 ..> c0244: `type in __init__`
- c0228 ..> c0244: `update_document() calls update_document()`
- c0228 ..> c0264: `type in __init__`
- c0228 ..> c0266: `update_document() calls filter_none_values()`
- c0229 ..> c0031: `create_entity() calls get_user_from_auth()`
- c0229 ..> c0031: `create_entity_relationship() calls get_user_from_auth()`
- c0229 ..> c0031: `delete_entity() calls get_user_from_auth()`
- c0229 ..> c0031: `delete_entity_relationship() calls get_user_from_auth()`
- c0229 ..> c0031: `get_entity() calls get_user_from_auth()`
- c0229 ..> c0031: `get_entity_memories() calls get_user_from_auth()`
- c0229 ..> c0031: `get_entity_relationships() calls get_user_from_auth()`
- c0229 ..> c0031: `get_memory_entities() calls get_user_from_auth()`
- c0229 ..> c0031: `link_entity_to_memory() calls get_user_from_auth()`
- c0229 ..> c0031: `link_entity_to_project() calls get_user_from_auth()`
- c0229 ..> c0031: `list_entities() calls get_user_from_auth()`
- c0229 ..> c0031: `search_entities() calls get_user_from_auth()`
- c0229 ..> c0031: `unlink_entity_from_memory() calls get_user_from_auth()`
- c0229 ..> c0031: `unlink_entity_from_project() calls get_user_from_auth()`
- c0229 ..> c0031: `update_entity() calls get_user_from_auth()`
- c0229 ..> c0031: `update_entity_relationship() calls get_user_from_auth()`
- c0229 ..> c0047: `type in create_entity`
- c0229 ..> c0047: `type in get_entity`
- c0229 ..> c0047: `type in update_entity`
- c0229 ..> c0048: `create_entity() constructs EntityCreate`
- c0229 ..> c0050: `type in create_entity_relationship`
- c0229 ..> c0050: `type in update_entity_relationship`
- c0229 ..> c0051: `create_entity_relationship() constructs EntityRelationshipCreate`
- c0229 ..> c0052: `update_entity_relationship() constructs EntityRelationshipUpdate`
- c0229 ..> c0054: `list_entities() constructs EntityType`
- c0229 ..> c0054: `search_entities() constructs EntityType`
- c0229 ..> c0055: `update_entity() constructs EntityUpdate`
- c0229 ..> c0245: `create_entity() calls create_entity()`
- c0229 ..> c0245: `create_entity_relationship() calls create_entity_relationship()`
- c0229 ..> c0245: `delete_entity() calls delete_entity()`
- c0229 ..> c0245: `delete_entity_relationship() calls delete_entity_relationship()`
- c0229 ..> c0245: `get_entity() calls get_entity()`
- c0229 ..> c0245: `get_entity_memories() calls get_entity_memories()`
- c0229 ..> c0245: `get_entity_relationships() calls get_entity_relationships()`
- c0229 ..> c0245: `get_memory_entities() calls get_memory_entities()`
- c0229 ..> c0245: `link_entity_to_memory() calls link_entity_to_memory()`
- c0229 ..> c0245: `link_entity_to_project() calls link_entity_to_project()`
- c0229 ..> c0245: `list_entities() calls list_entities()`
- c0229 ..> c0245: `search_entities() calls search_entities()`
- c0229 ..> c0245: `type in __init__`
- c0229 ..> c0245: `unlink_entity_from_memory() calls unlink_entity_from_memory()`
- c0229 ..> c0245: `unlink_entity_from_project() calls unlink_entity_from_project()`
- c0229 ..> c0245: `update_entity() calls update_entity()`
- c0229 ..> c0245: `update_entity_relationship() calls update_entity_relationship()`
- c0229 ..> c0264: `type in __init__`
- c0229 ..> c0266: `create_entity() calls filter_none_values()`
- c0229 ..> c0266: `update_entity() calls filter_none_values()`
- c0229 ..> c0266: `update_entity_relationship() calls filter_none_values()`
- c0230 ..> c0031: `create_file() calls get_user_from_auth()`
- c0230 ..> c0031: `delete_file() calls get_user_from_auth()`
- c0230 ..> c0031: `get_file() calls get_user_from_auth()`
- c0230 ..> c0031: `list_files() calls get_user_from_auth()`
- c0230 ..> c0031: `update_file() calls get_user_from_auth()`
- c0230 ..> c0057: `create_file() constructs FileCreate`
- c0230 ..> c0059: `update_file() constructs FileUpdate`
- c0230 ..> c0118: `create_file() calls create_file()`
- c0230 ..> c0118: `delete_file() calls delete_file()`
- c0230 ..> c0118: `list_files() calls list_files()`
- c0230 ..> c0118: `update_file() calls update_file()`
- c0230 ..> c0246: `get_file() calls get_file()`
- c0230 ..> c0264: `type in __init__`
- c0230 ..> c0266: `update_file() calls filter_none_values()`
- c0231 ..> c0031: `create_memory() calls get_user_from_auth()`
- c0231 ..> c0031: `get_memory() calls get_user_from_auth()`
- c0231 ..> c0031: `get_recent_memories() calls get_user_from_auth()`
- c0231 ..> c0031: `link_memories() calls get_user_from_auth()`
- c0231 ..> c0031: `mark_memory_obsolete() calls get_user_from_auth()`
- c0231 ..> c0031: `query_memory() calls get_user_from_auth()`
- c0231 ..> c0031: `rebuild_embeddings() calls get_user_from_auth()`
- c0231 ..> c0031: `unlink_memories() calls get_user_from_auth()`
- c0231 ..> c0031: `update_memory() calls get_user_from_auth()`
- c0231 ..> c0065: `type in get_memory`
- c0231 ..> c0065: `type in update_memory`
- c0231 ..> c0066: `create_memory() constructs MemoryCreate`
- c0231 ..> c0067: `create_memory() constructs MemoryCreateResponse`
- c0231 ..> c0067: `type in create_memory`
- c0231 ..> c0070: `query_memory() constructs MemoryQueryRequest`
- c0231 ..> c0071: `type in query_memory`
- c0231 ..> c0074: `update_memory() constructs MemoryUpdate`
- c0231 ..> c0119: `_validate_rebuild_scope() calls count_memories_for_targeted_rebuild()`
- c0231 ..> c0223: `get_recent_memories() calls clamp_list_pagination()`
- c0231 ..> c0231: `rebuild_embeddings() calls _build_re_embedding_service()`
- c0231 ..> c0231: `rebuild_embeddings() calls _validate_rebuild_scope()`
- c0231 ..> c0237: `create_memory() calls _coerce_int_id()`
- c0231 ..> c0237: `create_memory() calls _coerce_int_ids()`
- c0231 ..> c0237: `get_memory() calls _coerce_int_id()`
- c0231 ..> c0237: `get_recent_memories() calls _coerce_int_id()`
- c0231 ..> c0237: `link_memories() calls _coerce_int_id()`
- c0231 ..> c0237: `link_memories() calls _coerce_int_ids()`
- c0231 ..> c0237: `mark_memory_obsolete() calls _coerce_int_id()`
- c0231 ..> c0237: `query_memory() calls _coerce_int_id()`
- c0231 ..> c0237: `rebuild_embeddings() calls _coerce_int_id()`
- c0231 ..> c0237: `unlink_memories() calls _coerce_int_id()`
- c0231 ..> c0237: `unlink_memories() calls _coerce_int_ids()`
- c0231 ..> c0237: `update_memory() calls _coerce_int_id()`
- c0231 ..> c0237: `update_memory() calls _coerce_int_ids()`
- c0231 ..> c0255: `create_memory() calls create_memory()`
- c0231 ..> c0255: `create_memory() calls find_obsolete_matches()`
- c0231 ..> c0255: `get_memory() calls get_memory()`
- c0231 ..> c0255: `get_recent_memories() calls list_memories()`
- c0231 ..> c0255: `link_memories() calls link_memories()`
- c0231 ..> c0255: `mark_memory_obsolete() calls mark_memory_obsolete()`
- c0231 ..> c0255: `query_memory() calls query_memory()`
- c0231 ..> c0255: `type in __init__`
- c0231 ..> c0255: `unlink_memories() calls unlink_memories()`
- c0231 ..> c0255: `update_memory() calls update_memory()`
- c0231 ..> c0259: `_build_re_embedding_service() constructs ReEmbeddingService`
- c0231 ..> c0259: `rebuild_embeddings() calls rebuild_targeted()`
- c0231 ..> c0259: `type in _build_re_embedding_service`
- c0231 ..> c0264: `type in __init__`
- c0231 ..> c0266: `update_memory() calls filter_none_values()`
- c0232 ..> c0031: `create_plan() calls get_user_from_auth()`
- c0232 ..> c0031: `get_plan() calls get_user_from_auth()`
- c0232 ..> c0031: `list_plans() calls get_user_from_auth()`
- c0232 ..> c0031: `update_plan() calls get_user_from_auth()`
- c0232 ..> c0081: `create_plan() constructs PlanCreate`
- c0232 ..> c0082: `create_plan() constructs PlanStatus`
- c0232 ..> c0082: `list_plans() constructs PlanStatus`
- c0232 ..> c0082: `update_plan() constructs PlanStatus`
- c0232 ..> c0084: `update_plan() constructs PlanUpdate`
- c0232 ..> c0121: `create_plan() calls create_plan()`
- c0232 ..> c0121: `list_plans() calls list_plans()`
- c0232 ..> c0121: `update_plan() calls update_plan()`
- c0232 ..> c0251: `get_plan() calls get_plan()`
- c0232 ..> c0266: `update_plan() calls filter_none_values()`
- c0233 ..> c0031: `create_project() calls get_user_from_auth()`
- c0233 ..> c0031: `delete_project() calls get_user_from_auth()`
- c0233 ..> c0031: `get_project() calls get_user_from_auth()`
- c0233 ..> c0031: `list_projects() calls get_user_from_auth()`
- c0233 ..> c0031: `update_project() calls get_user_from_auth()`
- c0233 ..> c0093: `type in create_project`
- c0233 ..> c0093: `type in get_project`
- c0233 ..> c0093: `type in update_project`
- c0233 ..> c0094: `create_project() constructs ProjectCreate`
- c0233 ..> c0095: `list_projects() constructs ProjectStatus`
- c0233 ..> c0095: `type in create_project`
- c0233 ..> c0095: `type in update_project`
- c0233 ..> c0097: `type in create_project`
- c0233 ..> c0097: `type in update_project`
- c0233 ..> c0098: `update_project() constructs ProjectUpdate`
- c0233 ..> c0257: `create_project() calls create_project()`
- c0233 ..> c0257: `delete_project() calls delete_project()`
- c0233 ..> c0257: `get_project() calls get_project()`
- c0233 ..> c0257: `list_projects() calls list_projects()`
- c0233 ..> c0257: `type in __init__`
- c0233 ..> c0257: `update_project() calls update_project()`
- c0233 ..> c0264: `type in __init__`
- c0233 ..> c0266: `update_project() calls filter_none_values()`
- c0234 ..> c0031: `create_skill() calls get_user_from_auth()`
- c0234 ..> c0031: `delete_skill() calls get_user_from_auth()`
- c0234 ..> c0031: `export_skill() calls get_user_from_auth()`
- c0234 ..> c0031: `get_skill() calls get_user_from_auth()`
- c0234 ..> c0031: `get_skill_links() calls get_user_from_auth()`
- c0234 ..> c0031: `import_skill() calls get_user_from_auth()`
- c0234 ..> c0031: `link_skill_to_code_artifact() calls get_user_from_auth()`
- c0234 ..> c0031: `link_skill_to_document() calls get_user_from_auth()`
- c0234 ..> c0031: `link_skill_to_file() calls get_user_from_auth()`
- c0234 ..> c0031: `link_skill_to_memory() calls get_user_from_auth()`
- c0234 ..> c0031: `list_skills() calls get_user_from_auth()`
- c0234 ..> c0031: `search_skills() calls get_user_from_auth()`
- c0234 ..> c0031: `unlink_skill_from_code_artifact() calls get_user_from_auth()`
- c0234 ..> c0031: `unlink_skill_from_document() calls get_user_from_auth()`
- c0234 ..> c0031: `unlink_skill_from_file() calls get_user_from_auth()`
- c0234 ..> c0031: `unlink_skill_from_memory() calls get_user_from_auth()`
- c0234 ..> c0031: `update_skill() calls get_user_from_auth()`
- c0234 ..> c0100: `create_skill() constructs SkillCreate`
- c0234 ..> c0103: `update_skill() constructs SkillUpdate`
- c0234 ..> c0123: `create_skill() calls create_skill()`
- c0234 ..> c0123: `delete_skill() calls delete_skill()`
- c0234 ..> c0123: `get_skill_links() calls get_skill_links()`
- c0234 ..> c0123: `link_skill_to_code_artifact() calls link_skill_to_code_artifact()`
- c0234 ..> c0123: `link_skill_to_document() calls link_skill_to_document()`
- c0234 ..> c0123: `link_skill_to_file() calls link_skill_to_file()`
- c0234 ..> c0123: `link_skill_to_memory() calls link_skill_to_memory()`
- c0234 ..> c0123: `list_skills() calls list_skills()`
- c0234 ..> c0123: `search_skills() calls search_skills()`
- c0234 ..> c0123: `unlink_skill_from_code_artifact() calls unlink_skill_from_code_artifact()`
- c0234 ..> c0123: `unlink_skill_from_document() calls unlink_skill_from_document()`
- c0234 ..> c0123: `unlink_skill_from_file() calls unlink_skill_from_file()`
- c0234 ..> c0123: `unlink_skill_from_memory() calls unlink_skill_from_memory()`
- c0234 ..> c0123: `update_skill() calls update_skill()`
- c0234 ..> c0253: `get_skill() calls get_skill()`
- c0234 ..> c0261: `export_skill() calls export_skill()`
- c0234 ..> c0261: `import_skill() calls import_skill()`
- c0234 ..> c0264: `type in __init__`
- c0234 ..> c0266: `update_skill() calls filter_none_values()`
- c0235 ..> c0031: `add_criterion() calls get_user_from_auth()`
- c0235 ..> c0031: `add_dependency() calls get_user_from_auth()`
- c0235 ..> c0031: `claim_task() calls get_user_from_auth()`
- c0235 ..> c0031: `create_task() calls get_user_from_auth()`
- c0235 ..> c0031: `delete_criterion() calls get_user_from_auth()`
- c0235 ..> c0031: `get_task() calls get_user_from_auth()`
- c0235 ..> c0031: `query_tasks() calls get_user_from_auth()`
- c0235 ..> c0031: `remove_dependency() calls get_user_from_auth()`
- c0235 ..> c0031: `transition_task() calls get_user_from_auth()`
- c0235 ..> c0031: `update_task() calls get_user_from_auth()`
- c0235 ..> c0031: `verify_criterion() calls get_user_from_auth()`
- c0235 ..> c0078: `add_criterion() constructs CriterionCreate`
- c0235 ..> c0078: `create_task() constructs CriterionCreate`
- c0235 ..> c0079: `verify_criterion() constructs CriterionUpdate`
- c0235 ..> c0086: `create_task() constructs TaskCreate`
- c0235 ..> c0089: `create_task() constructs TaskPriority`
- c0235 ..> c0089: `query_tasks() constructs TaskPriority`
- c0235 ..> c0089: `update_task() constructs TaskPriority`
- c0235 ..> c0090: `query_tasks() constructs TaskState`
- c0235 ..> c0090: `transition_task() constructs TaskState`
- c0235 ..> c0092: `update_task() constructs TaskUpdate`
- c0235 ..> c0124: `add_dependency() calls add_dependency()`
- c0235 ..> c0124: `create_task() calls create_task()`
- c0235 ..> c0124: `delete_criterion() calls delete_criterion()`
- c0235 ..> c0124: `query_tasks() calls list_tasks()`
- c0235 ..> c0124: `remove_dependency() calls remove_dependency()`
- c0235 ..> c0124: `update_task() calls update_task()`
- c0235 ..> c0124: `verify_criterion() calls update_criterion()`
- c0235 ..> c0254: `get_task() calls get_task()`
- c0235 ..> c0263: `add_criterion() calls add_criterion()`
- c0235 ..> c0263: `claim_task() calls claim_task()`
- c0235 ..> c0263: `transition_task() calls transition_task()`
- c0235 ..> c0266: `update_task() calls filter_none_values()`
- c0236 ..> c0031: `get_current_user() calls get_user_from_auth()`
- c0236 ..> c0031: `update_user_notes() calls get_user_from_auth()`
- c0236 ..> c0111: `get_current_user() constructs UserResponse`
- c0236 ..> c0111: `type in get_current_user`
- c0236 ..> c0111: `type in update_user_notes`
- c0236 ..> c0111: `update_user_notes() constructs UserResponse`
- c0236 ..> c0112: `update_user_notes() constructs UserUpdate`
- c0236 ..> c0264: `type in __init__`
- c0236 ..> c0264: `update_user_notes() calls update_user()`
- c0237 ..> c0227: `create_code_artifact_adapters() constructs CodeArtifactToolAdapters`
- c0237 ..> c0228: `create_document_adapters() constructs DocumentToolAdapters`
- c0237 ..> c0229: `create_entity_adapters() constructs EntityToolAdapters`
- c0237 ..> c0230: `create_file_adapters() constructs FileToolAdapters`
- c0237 ..> c0231: `create_memory_adapters() constructs MemoryToolAdapters`
- c0237 ..> c0232: `create_plan_adapters() constructs PlanToolAdapters`
- c0237 ..> c0233: `create_project_adapters() constructs ProjectToolAdapters`
- c0237 ..> c0234: `create_skill_adapters() constructs SkillToolAdapters`
- c0237 ..> c0235: `create_task_adapters() constructs TaskToolAdapters`
- c0237 ..> c0236: `create_user_adapters() constructs UserToolAdapters`
- c0237 ..> c0237: `_coerce_int_ids() calls _coerce_int_id()`
- c0237 ..> c0243: `type in create_code_artifact_adapters`
- c0237 ..> c0244: `type in create_document_adapters`
- c0237 ..> c0245: `type in create_entity_adapters`
- c0237 ..> c0255: `type in create_memory_adapters`
- c0237 ..> c0257: `type in create_project_adapters`
- c0237 ..> c0264: `type in create_code_artifact_adapters`
- c0237 ..> c0264: `type in create_document_adapters`
- c0237 ..> c0264: `type in create_entity_adapters`
- c0237 ..> c0264: `type in create_file_adapters`
- c0237 ..> c0264: `type in create_memory_adapters`
- c0237 ..> c0264: `type in create_project_adapters`
- c0237 ..> c0264: `type in create_skill_adapters`
- c0237 ..> c0264: `type in create_user_adapters`
- c0238 ..> c0030: `register_code_artifact_tools_metadata() calls get()`
- c0238 ..> c0030: `register_document_tools_metadata() calls get()`
- c0238 ..> c0030: `register_entity_tools_metadata() calls get()`
- c0238 ..> c0030: `register_file_tools_metadata() calls get()`
- c0238 ..> c0030: `register_memory_tools_metadata() calls get()`
- c0238 ..> c0030: `register_plan_tools_metadata() calls get()`
- c0238 ..> c0030: `register_project_tools_metadata() calls get()`
- c0238 ..> c0030: `register_simplified_tool() calls get()`
- c0238 ..> c0030: `register_skill_tools_metadata() calls get()`
- c0238 ..> c0030: `register_task_tools_metadata() calls get()`
- c0238 ..> c0030: `register_user_tools_metadata() calls get()`
- c0238 ..> c0104: `type in register_simplified_tool`
- c0238 ..> c0108: `register_simplified_tool() constructs ToolParameter`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_code_artifact_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_document_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_entity_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_file_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_memory_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_plan_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_project_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_skill_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_task_adapters()`
- c0238 ..> c0237: `register_all_tools_metadata() calls create_user_adapters()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_code_artifact_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_document_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_entity_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_file_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_memory_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_plan_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_project_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_skill_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_task_tools_metadata()`
- c0238 ..> c0238: `register_all_tools_metadata() calls register_user_tools_metadata()`
- c0238 ..> c0238: `register_code_artifact_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_document_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_entity_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_file_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_memory_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_plan_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_project_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_skill_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_task_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0238: `register_user_tools_metadata() calls register_simplified_tool()`
- c0238 ..> c0239: `register_all_tools_metadata() calls list_categories()`
- c0238 ..> c0239: `register_simplified_tool() calls register()`
- c0238 ..> c0239: `type in register_all_tools_metadata`
- c0238 ..> c0239: `type in register_code_artifact_tools_metadata`
- c0238 ..> c0239: `type in register_document_tools_metadata`
- c0238 ..> c0239: `type in register_entity_tools_metadata`
- c0238 ..> c0239: `type in register_file_tools_metadata`
- c0238 ..> c0239: `type in register_memory_tools_metadata`
- c0238 ..> c0239: `type in register_plan_tools_metadata`
- c0238 ..> c0239: `type in register_project_tools_metadata`
- c0238 ..> c0239: `type in register_simplified_tool`
- c0238 ..> c0239: `type in register_skill_tools_metadata`
- c0238 ..> c0239: `type in register_task_tools_metadata`
- c0238 ..> c0239: `type in register_user_tools_metadata`
- c0238 ..> c0255: `type in register_all_tools_metadata`
- c0238 ..> c0264: `type in register_all_tools_metadata`
- c0239 ..> c0030: `get_permitted_categories() calls get()`
- c0239 ..> c0030: `get_tool() calls get()`
- c0239 ..> c0030: `list_categories() calls get()`
- c0239 ..> c0104: `type in get_permitted_by_category`
- c0239 ..> c0104: `type in list_by_category`
- c0239 ..> c0104: `type in register`
- c0239 --> c0106: `field _tools`
- c0239 ..> c0106: `register() constructs ToolImplementation`
- c0239 ..> c0106: `type in get_tool`
- c0239 ..> c0107: `register() constructs ToolMetadata`
- c0239 ..> c0107: `type in get_permitted_by_category`
- c0239 ..> c0107: `type in get_permitted_tools`
- c0239 ..> c0107: `type in list_all_tools`
- c0239 ..> c0107: `type in list_by_category`
- c0239 ..> c0108: `type in register`
- c0239 ..> c0239: `execute() calls get_tool()`
- c0241 ..> c0033: `type in count_activity`
- c0241 ..> c0033: `type in get_activity`
- c0241 ..> c0034: `type in handle_event`
- c0241 ..> c0035: `get_activity() constructs ActivityListResponse`
- c0241 ..> c0035: `type in get_activity`
- c0241 ..> c0035: `type in get_entity_history`
- c0241 ..> c0037: `type in get_activity`
- c0241 ..> c0038: `type in count_activity`
- c0241 ..> c0038: `type in get_activity`
- c0241 ..> c0038: `type in get_entity_history`
- c0241 ..> c0113: `_cleanup_if_configured() calls cleanup_expired()`
- c0241 ..> c0113: `count_activity() calls count_events()`
- c0241 ..> c0113: `get_activity() calls query_events()`
- c0241 ..> c0113: `handle_event() calls save_event()`
- c0241 ..> c0113: `type in __init__`
- c0241 ..> c0241: `get_activity() calls _cleanup_if_configured()`
- c0241 ..> c0241: `get_entity_history() calls get_activity()`
- c0242 ..> c0217: `_backup_postgres() calls run()`
- c0242 ..> c0217: `_restore_postgres() calls run()`
- c0242 ..> c0242: `create_backup() calls _backup_postgres()`
- c0242 ..> c0242: `create_backup() calls _backup_sqlite()`
- c0242 ..> c0242: `restore_backup() calls _restore_postgres()`
- c0242 ..> c0242: `restore_backup() calls _restore_sqlite()`
- c0243 ..> c0023: `_emit_event() calls emit()`
- c0243 ..> c0023: `type in __init__`
- c0243 ..> c0028: `get_code_artifact() constructs NotFoundError`
- c0243 ..> c0028: `update_code_artifact() constructs NotFoundError`
- c0243 ..> c0033: `type in _emit_event`
- c0243 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0243 ..> c0038: `type in _emit_event`
- c0243 ..> c0039: `type in create_code_artifact`
- c0243 ..> c0039: `type in get_code_artifact`
- c0243 ..> c0039: `type in update_code_artifact`
- c0243 ..> c0040: `type in create_code_artifact`
- c0243 ..> c0041: `type in list_code_artifacts`
- c0243 ..> c0042: `type in update_code_artifact`
- c0243 ..> c0114: `create_code_artifact() calls create_code_artifact()`
- c0243 ..> c0114: `delete_code_artifact() calls delete_code_artifact()`
- c0243 ..> c0114: `delete_code_artifact() calls get_code_artifact_by_id()`
- c0243 ..> c0114: `get_code_artifact() calls get_code_artifact_by_id()`
- c0243 ..> c0114: `list_code_artifacts() calls list_code_artifacts()`
- c0243 ..> c0114: `type in __init__`
- c0243 ..> c0114: `update_code_artifact() calls get_code_artifact_by_id()`
- c0243 ..> c0114: `update_code_artifact() calls update_code_artifact()`
- c0243 ..> c0243: `create_code_artifact() calls _emit_event()`
- c0243 ..> c0243: `delete_code_artifact() calls _emit_event()`
- c0243 ..> c0243: `get_code_artifact() calls _emit_event()`
- c0243 ..> c0243: `list_code_artifacts() calls _emit_event()`
- c0243 ..> c0243: `update_code_artifact() calls _emit_event()`
- c0243 ..> c0265: `create_code_artifact() calls apply_provenance_defaults()`
- c0243 ..> c0265: `update_code_artifact() calls apply_provenance_defaults_for_update()`
- c0243 ..> c0266: `update_code_artifact() calls get_changed_fields()`
- c0244 ..> c0023: `_emit_event() calls emit()`
- c0244 ..> c0023: `type in __init__`
- c0244 ..> c0028: `get_document() constructs NotFoundError`
- c0244 ..> c0028: `update_document() constructs NotFoundError`
- c0244 ..> c0033: `type in _emit_event`
- c0244 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0244 ..> c0038: `type in _emit_event`
- c0244 ..> c0043: `type in create_document`
- c0244 ..> c0043: `type in get_document`
- c0244 ..> c0043: `type in update_document`
- c0244 ..> c0044: `type in create_document`
- c0244 ..> c0045: `type in list_documents`
- c0244 ..> c0046: `type in update_document`
- c0244 ..> c0115: `create_document() calls create_document()`
- c0244 ..> c0115: `delete_document() calls delete_document()`
- c0244 ..> c0115: `delete_document() calls get_document_by_id()`
- c0244 ..> c0115: `get_document() calls get_document_by_id()`
- c0244 ..> c0115: `list_documents() calls list_documents()`
- c0244 ..> c0115: `type in __init__`
- c0244 ..> c0115: `update_document() calls get_document_by_id()`
- c0244 ..> c0115: `update_document() calls update_document()`
- c0244 ..> c0244: `create_document() calls _emit_event()`
- c0244 ..> c0244: `delete_document() calls _emit_event()`
- c0244 ..> c0244: `get_document() calls _emit_event()`
- c0244 ..> c0244: `list_documents() calls _emit_event()`
- c0244 ..> c0244: `update_document() calls _emit_event()`
- c0244 ..> c0265: `create_document() calls apply_provenance_defaults()`
- c0244 ..> c0265: `update_document() calls apply_provenance_defaults_for_update()`
- c0244 ..> c0266: `update_document() calls get_changed_fields()`
- c0245 ..> c0023: `_emit_event() calls emit()`
- c0245 ..> c0023: `type in __init__`
- c0245 ..> c0028: `get_entity() constructs NotFoundError`
- c0245 ..> c0028: `update_entity() constructs NotFoundError`
- c0245 ..> c0033: `type in _emit_event`
- c0245 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0245 ..> c0038: `type in _emit_event`
- c0245 ..> c0047: `type in create_entity`
- c0245 ..> c0047: `type in get_entity`
- c0245 ..> c0047: `type in update_entity`
- c0245 ..> c0048: `type in create_entity`
- c0245 ..> c0050: `type in create_entity_relationship`
- c0245 ..> c0050: `type in get_all_entity_relationships`
- c0245 ..> c0050: `type in get_entity_relationships`
- c0245 ..> c0050: `type in update_entity_relationship`
- c0245 ..> c0051: `type in create_entity_relationship`
- c0245 ..> c0052: `type in update_entity_relationship`
- c0245 ..> c0053: `type in list_entities`
- c0245 ..> c0053: `type in search_entities`
- c0245 ..> c0054: `type in list_entities`
- c0245 ..> c0054: `type in search_entities`
- c0245 ..> c0055: `type in update_entity`
- c0245 ..> c0116: `create_entity() calls create_entity()`
- c0245 ..> c0116: `create_entity_relationship() calls create_entity_relationship()`
- c0245 ..> c0116: `delete_entity() calls delete_entity()`
- c0245 ..> c0116: `delete_entity() calls get_entity_by_id()`
- c0245 ..> c0116: `delete_entity_relationship() calls delete_entity_relationship()`
- c0245 ..> c0116: `get_all_entity_file_links() calls get_all_entity_file_links()`
- c0245 ..> c0116: `get_all_entity_memory_links() calls get_all_entity_memory_links()`
- c0245 ..> c0116: `get_all_entity_project_links() calls get_all_entity_project_links()`
- c0245 ..> c0116: `get_all_entity_relationships() calls get_all_entity_relationships()`
- c0245 ..> c0116: `get_entity() calls get_entity_by_id()`
- c0245 ..> c0116: `get_entity_memories() calls get_entity_memories()`
- c0245 ..> c0116: `get_entity_relationships() calls get_entity_relationships()`
- c0245 ..> c0116: `get_memory_entities() calls get_memory_entities()`
- c0245 ..> c0116: `link_entity_to_memory() calls link_entity_to_memory()`
- c0245 ..> c0116: `link_entity_to_project() calls link_entity_to_project()`
- c0245 ..> c0116: `list_entities() calls list_entities()`
- c0245 ..> c0116: `search_entities() calls search_entities()`
- c0245 ..> c0116: `type in __init__`
- c0245 ..> c0116: `unlink_entity_from_memory() calls unlink_entity_from_memory()`
- c0245 ..> c0116: `unlink_entity_from_project() calls unlink_entity_from_project()`
- c0245 ..> c0116: `update_entity() calls get_entity_by_id()`
- c0245 ..> c0116: `update_entity() calls update_entity()`
- c0245 ..> c0116: `update_entity_relationship() calls update_entity_relationship()`
- c0245 ..> c0245: `create_entity() calls _emit_event()`
- c0245 ..> c0245: `create_entity_relationship() calls _emit_event()`
- c0245 ..> c0245: `delete_entity() calls _emit_event()`
- c0245 ..> c0245: `delete_entity_relationship() calls _emit_event()`
- c0245 ..> c0245: `get_entity() calls _emit_event()`
- c0245 ..> c0245: `link_entity_to_memory() calls _emit_event()`
- c0245 ..> c0245: `link_entity_to_project() calls _emit_event()`
- c0245 ..> c0245: `list_entities() calls _emit_event()`
- c0245 ..> c0245: `search_entities() calls _emit_event()`
- c0245 ..> c0245: `unlink_entity_from_memory() calls _emit_event()`
- c0245 ..> c0245: `unlink_entity_from_project() calls _emit_event()`
- c0245 ..> c0245: `update_entity() calls _emit_event()`
- c0245 ..> c0245: `update_entity_relationship() calls _emit_event()`
- c0245 ..> c0265: `create_entity() calls apply_provenance_defaults()`
- c0245 ..> c0265: `create_entity_relationship() calls apply_provenance_defaults()`
- c0245 ..> c0265: `update_entity() calls apply_provenance_defaults_for_update()`
- c0245 ..> c0265: `update_entity_relationship() calls apply_provenance_defaults_for_update()`
- c0245 ..> c0266: `update_entity() calls get_changed_fields()`
- c0246 ..> c0023: `_emit_event() calls emit()`
- c0246 ..> c0023: `type in __init__`
- c0246 ..> c0028: `get_file() constructs NotFoundError`
- c0246 ..> c0028: `update_file() constructs NotFoundError`
- c0246 ..> c0033: `type in _emit_event`
- c0246 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0246 ..> c0038: `type in _emit_event`
- c0246 ..> c0056: `type in _snapshot_without_data`
- c0246 ..> c0056: `type in create_file`
- c0246 ..> c0056: `type in get_file`
- c0246 ..> c0056: `type in update_file`
- c0246 ..> c0057: `type in create_file`
- c0246 ..> c0058: `type in list_files`
- c0246 ..> c0059: `type in update_file`
- c0246 ..> c0118: `create_file() calls create_file()`
- c0246 ..> c0118: `delete_file() calls delete_file()`
- c0246 ..> c0118: `delete_file() calls get_file_by_id()`
- c0246 ..> c0118: `get_file() calls get_file_by_id()`
- c0246 ..> c0118: `list_files() calls list_files()`
- c0246 ..> c0118: `type in __init__`
- c0246 ..> c0118: `update_file() calls get_file_by_id()`
- c0246 ..> c0118: `update_file() calls update_file()`
- c0246 ..> c0246: `create_file() calls _emit_event()`
- c0246 ..> c0246: `create_file() calls _snapshot_without_data()`
- c0246 ..> c0246: `delete_file() calls _emit_event()`
- c0246 ..> c0246: `delete_file() calls _snapshot_without_data()`
- c0246 ..> c0246: `get_file() calls _emit_event()`
- c0246 ..> c0246: `get_file() calls _snapshot_without_data()`
- c0246 ..> c0246: `list_files() calls _emit_event()`
- c0246 ..> c0246: `update_file() calls _emit_event()`
- c0246 ..> c0246: `update_file() calls _snapshot_without_data()`
- c0246 ..> c0265: `create_file() calls apply_provenance_defaults()`
- c0246 ..> c0265: `update_file() calls apply_provenance_defaults_for_update()`
- c0246 ..> c0266: `update_file() calls get_changed_fields()`
- c0250 ..> c0028: `_validate_center_node() constructs NotFoundError`
- c0250 ..> c0030: `_fetch_node_data() calls get()`
- c0250 ..> c0060: `_fetch_edges() constructs SubgraphEdge`
- c0250 ..> c0060: `type in _fetch_edges`
- c0250 ..> c0061: `get_subgraph() constructs SubgraphMeta`
- c0250 ..> c0062: `_fetch_node_data() constructs SubgraphNode`
- c0250 ..> c0062: `type in _fetch_node_data`
- c0250 ..> c0063: `get_subgraph() constructs SubgraphResponse`
- c0250 ..> c0063: `type in get_subgraph`
- c0250 ..> c0116: `_fetch_edges() calls get_all_entity_file_links()`
- c0250 ..> c0116: `_fetch_edges() calls get_all_entity_memory_links()`
- c0250 ..> c0116: `_fetch_edges() calls get_all_entity_project_links()`
- c0250 ..> c0116: `_fetch_edges() calls get_all_entity_relationships()`
- c0250 ..> c0116: `_fetch_node_data() calls get_entity_by_id()`
- c0250 ..> c0116: `_validate_center_node() calls get_entity_by_id()`
- c0250 ..> c0116: `type in __init__`
- c0250 ..> c0119: `_fetch_edges() calls get_memory_by_id()`
- c0250 ..> c0119: `_fetch_node_data() calls get_memory_by_id()`
- c0250 ..> c0119: `_validate_center_node() calls get_memory_by_id()`
- c0250 ..> c0119: `get_subgraph() calls get_subgraph_nodes()`
- c0250 ..> c0119: `type in __init__`
- c0250 ..> c0247: `_fetch_edges() calls get_code_artifact()`
- c0250 ..> c0247: `_fetch_node_data() calls get_code_artifact()`
- c0250 ..> c0247: `_validate_center_node() calls get_code_artifact()`
- c0250 ..> c0247: `type in __init__`
- c0250 ..> c0248: `_fetch_edges() calls get_document()`
- c0250 ..> c0248: `_fetch_node_data() calls get_document()`
- c0250 ..> c0248: `_validate_center_node() calls get_document()`
- c0250 ..> c0248: `type in __init__`
- c0250 ..> c0249: `_fetch_edges() calls list_files()`
- c0250 ..> c0249: `_fetch_node_data() calls list_files()`
- c0250 ..> c0249: `_validate_center_node() calls get_file()`
- c0250 ..> c0249: `type in __init__`
- c0250 ..> c0250: `get_subgraph() calls _fetch_edges()`
- c0250 ..> c0250: `get_subgraph() calls _fetch_node_data()`
- c0250 ..> c0250: `get_subgraph() calls _validate_center_node()`
- c0250 ..> c0250: `get_subgraph() calls parse_node_id()`
- c0250 ..> c0251: `_fetch_edges() calls get_plan()`
- c0250 ..> c0251: `_fetch_node_data() calls get_plan()`
- c0250 ..> c0251: `_validate_center_node() calls get_plan()`
- c0250 ..> c0251: `type in __init__`
- c0250 ..> c0252: `_fetch_node_data() calls get_project()`
- c0250 ..> c0252: `_validate_center_node() calls get_project()`
- c0250 ..> c0252: `type in __init__`
- c0250 ..> c0253: `_fetch_edges() calls get_all_skill_code_artifact_links()`
- c0250 ..> c0253: `_fetch_edges() calls get_all_skill_document_links()`
- c0250 ..> c0253: `_fetch_edges() calls get_all_skill_file_links()`
- c0250 ..> c0253: `_fetch_edges() calls get_skill()`
- c0250 ..> c0253: `_fetch_node_data() calls get_skill()`
- c0250 ..> c0253: `_validate_center_node() calls get_skill()`
- c0250 ..> c0253: `type in __init__`
- c0250 ..> c0254: `_validate_center_node() calls get_task()`
- c0250 ..> c0254: `get_subgraph() calls list_tasks_for_user()`
- c0250 ..> c0254: `type in __init__`
- c0255 ..> c0023: `_emit_event() calls emit()`
- c0255 ..> c0023: `register_access_tracking_handlers() calls subscribe()`
- c0255 ..> c0023: `type in __init__`
- c0255 ..> c0023: `type in register_access_tracking_handlers`
- c0255 ..> c0030: `handle_memory_access_event() calls get()`
- c0255 ..> c0033: `type in _emit_event`
- c0255 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0255 ..> c0034: `type in handle_memory_access_event`
- c0255 ..> c0038: `type in _emit_event`
- c0255 ..> c0064: `_fetch_linked_memories() constructs LinkedMemory`
- c0255 ..> c0064: `type in _apply_token_budget`
- c0255 ..> c0064: `type in _fetch_linked_memories`
- c0255 ..> c0065: `type in _apply_token_budget`
- c0255 ..> c0065: `type in _count_memory_tokens`
- c0255 ..> c0065: `type in _fetch_linked_memories`
- c0255 ..> c0065: `type in create_memory`
- c0255 ..> c0065: `type in get_memory`
- c0255 ..> c0065: `type in list_memories`
- c0255 ..> c0065: `type in truncate_memories_by_budget`
- c0255 ..> c0065: `type in update_memory`
- c0255 ..> c0066: `type in create_memory`
- c0255 ..> c0070: `type in query_memory`
- c0255 ..> c0071: `query_memory() constructs MemoryQueryResult`
- c0255 ..> c0071: `type in query_memory`
- c0255 ..> c0073: `create_memory() constructs MemorySummary`
- c0255 ..> c0073: `type in create_memory`
- c0255 ..> c0074: `type in update_memory`
- c0255 ..> c0075: `find_obsolete_matches() constructs ObsoleteMatch`
- c0255 ..> c0075: `type in find_obsolete_matches`
- c0255 ..> c0119: `_fetch_linked_memories() calls get_linked_memories()`
- c0255 ..> c0119: `create_memory() calls create_links_batch()`
- c0255 ..> c0119: `create_memory() calls create_memory()`
- c0255 ..> c0119: `create_memory() calls find_similar_memories_scored()`
- c0255 ..> c0119: `find_obsolete_matches() calls find_obsolete_matches()`
- c0255 ..> c0119: `get_memory() calls get_memory_by_id()`
- c0255 ..> c0119: `handle_memory_access_event() calls record_memory_access()`
- c0255 ..> c0119: `link_memories() calls create_links_batch()`
- c0255 ..> c0119: `link_memories() calls get_memory_by_id()`
- c0255 ..> c0119: `list_memories() calls list_memories()`
- c0255 ..> c0119: `mark_memory_obsolete() calls get_memory_by_id()`
- c0255 ..> c0119: `mark_memory_obsolete() calls mark_obsolete()`
- c0255 ..> c0119: `query_memory() calls search_scored()`
- c0255 ..> c0119: `type in __init__`
- c0255 ..> c0119: `unlink_memories() calls unlink_memories()`
- c0255 ..> c0119: `update_memory() calls get_memory_by_id()`
- c0255 ..> c0119: `update_memory() calls update_memory()`
- c0255 ..> c0255: `_apply_token_budget() calls truncate_memories_by_budget()`
- c0255 ..> c0255: `create_memory() calls _emit_event()`
- c0255 ..> c0255: `get_memory() calls _emit_event()`
- c0255 ..> c0255: `link_memories() calls _emit_event()`
- c0255 ..> c0255: `mark_memory_obsolete() calls _emit_event()`
- c0255 ..> c0255: `query_memory() calls _apply_token_budget()`
- c0255 ..> c0255: `query_memory() calls _emit_event()`
- c0255 ..> c0255: `query_memory() calls _fetch_linked_memories()`
- c0255 ..> c0255: `truncate_memories_by_budget() calls _count_memory_tokens()`
- c0255 ..> c0255: `unlink_memories() calls _emit_event()`
- c0255 ..> c0255: `unlink_memories() calls get_memory()`
- c0255 ..> c0255: `update_memory() calls _emit_event()`
- c0255 ..> c0265: `create_memory() calls apply_provenance_defaults()`
- c0255 ..> c0265: `update_memory() calls apply_provenance_defaults_for_update()`
- c0255 ..> c0266: `update_memory() calls get_changed_fields()`
- c0255 ..> c0268: `_count_memory_tokens() calls count_tokens()`
- c0255 ..> c0268: `_count_memory_tokens() constructs TokenCounter`
- c0256 ..> c0023: `_emit_event() calls emit()`
- c0256 ..> c0023: `type in __init__`
- c0256 ..> c0027: `update_plan() constructs InvalidStateTransitionError`
- c0256 ..> c0028: `get_plan() constructs NotFoundError`
- c0256 ..> c0030: `update_plan() calls get()`
- c0256 ..> c0033: `type in _emit_event`
- c0256 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0256 ..> c0038: `type in _emit_event`
- c0256 ..> c0080: `type in create_plan`
- c0256 ..> c0080: `type in get_plan`
- c0256 ..> c0080: `type in update_plan`
- c0256 ..> c0081: `type in create_plan`
- c0256 ..> c0082: `check_plan_completion() constructs PlanStatus`
- c0256 ..> c0082: `type in list_plans`
- c0256 ..> c0082: `update_plan() constructs PlanStatus`
- c0256 ..> c0083: `type in list_plans`
- c0256 ..> c0084: `type in update_plan`
- c0256 ..> c0121: `check_plan_completion() calls get_plan_by_id()`
- c0256 ..> c0121: `create_plan() calls create_plan()`
- c0256 ..> c0121: `delete_plan() calls delete_plan()`
- c0256 ..> c0121: `delete_plan() calls get_plan_by_id()`
- c0256 ..> c0121: `get_plan() calls get_plan_by_id()`
- c0256 ..> c0121: `list_plans() calls list_plans()`
- c0256 ..> c0121: `type in __init__`
- c0256 ..> c0121: `update_plan() calls get_plan_by_id()`
- c0256 ..> c0121: `update_plan() calls update_plan()`
- c0256 ..> c0256: `create_plan() calls _emit_event()`
- c0256 ..> c0256: `delete_plan() calls _emit_event()`
- c0256 ..> c0256: `get_plan() calls _emit_event()`
- c0256 ..> c0256: `update_plan() calls _emit_event()`
- c0256 ..> c0265: `create_plan() calls apply_provenance_defaults()`
- c0256 ..> c0265: `update_plan() calls apply_provenance_defaults_for_update()`
- c0256 ..> c0266: `update_plan() calls get_changed_fields()`
- c0257 ..> c0023: `_emit_event() calls emit()`
- c0257 ..> c0023: `type in __init__`
- c0257 ..> c0028: `get_project() constructs NotFoundError`
- c0257 ..> c0033: `type in _emit_event`
- c0257 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0257 ..> c0038: `type in _emit_event`
- c0257 ..> c0093: `type in create_project`
- c0257 ..> c0093: `type in get_project`
- c0257 ..> c0093: `type in update_project`
- c0257 ..> c0094: `type in create_project`
- c0257 ..> c0095: `type in list_projects`
- c0257 ..> c0096: `type in list_projects`
- c0257 ..> c0098: `type in update_project`
- c0257 ..> c0122: `create_project() calls create_project()`
- c0257 ..> c0122: `delete_project() calls delete_project()`
- c0257 ..> c0122: `delete_project() calls get_project_by_id()`
- c0257 ..> c0122: `get_project() calls get_project_by_id()`
- c0257 ..> c0122: `list_projects() calls list_projects()`
- c0257 ..> c0122: `type in __init__`
- c0257 ..> c0122: `update_project() calls get_project_by_id()`
- c0257 ..> c0122: `update_project() calls update_project()`
- c0257 ..> c0257: `create_project() calls _emit_event()`
- c0257 ..> c0257: `delete_project() calls _emit_event()`
- c0257 ..> c0257: `get_project() calls _emit_event()`
- c0257 ..> c0257: `list_projects() calls _emit_event()`
- c0257 ..> c0257: `update_project() calls _emit_event()`
- c0257 ..> c0265: `create_project() calls apply_provenance_defaults()`
- c0257 ..> c0265: `update_project() calls apply_provenance_defaults_for_update()`
- c0257 ..> c0266: `update_project() calls get_changed_fields()`
- c0258 --> c0120: `field validation`
- c0259 ..> c0119: `_recompute_auto_links() calls create_links_batch()`
- c0259 ..> c0119: `_recompute_auto_links() calls find_similar_memories()`
- c0259 ..> c0119: `re_embed_all() calls bulk_update_embeddings()`
- c0259 ..> c0119: `re_embed_all() calls count_all_memories()`
- c0259 ..> c0119: `re_embed_all() calls get_memories_for_reembedding()`
- c0259 ..> c0119: `re_embed_all() calls reset_embedding_storage()`
- c0259 ..> c0119: `rebuild_targeted() calls count_memories_for_targeted_rebuild()`
- c0259 ..> c0119: `rebuild_targeted() calls get_memories_for_targeted_rebuild()`
- c0259 ..> c0119: `rebuild_targeted() calls upsert_targeted_embeddings()`
- c0259 ..> c0119: `type in __init__`
- c0259 ..> c0119: `validate() calls validate_embedding_count()`
- c0259 ..> c0119: `validate() calls validate_embedding_dimensions()`
- c0259 ..> c0119: `validate() calls validate_search_works()`
- c0259 ..> c0120: `re_embed_all() constructs ValidationResult`
- c0259 ..> c0120: `type in validate`
- c0259 ..> c0120: `validate() constructs ValidationResult`
- c0259 ..> c0127: `type in __init__`
- c0259 ..> c0130: `re_embed_all() calls generate_embedding()`
- c0259 ..> c0130: `rebuild_targeted() calls generate_embedding()`
- c0259 ..> c0136: `re_embed_all() calls build_embedding_text()`
- c0259 ..> c0136: `rebuild_targeted() calls build_embedding_text()`
- c0259 ..> c0258: `re_embed_all() constructs ReEmbedResult`
- c0259 ..> c0258: `type in re_embed_all`
- c0259 ..> c0259: `re_embed_all() calls validate()`
- c0259 ..> c0259: `rebuild_targeted() calls _recompute_auto_links()`
- c0259 ..> c0259: `rebuild_targeted() calls _record_unresolved_memory_ids()`
- c0259 ..> c0260: `rebuild_targeted() constructs TargetedRebuildResult`
- c0259 ..> c0260: `type in _recompute_auto_links`
- c0259 ..> c0260: `type in _record_unresolved_memory_ids`
- c0259 ..> c0260: `type in rebuild_targeted`
- c0261 ..> c0023: `_emit_event() calls emit()`
- c0261 ..> c0023: `type in __init__`
- c0261 ..> c0028: `get_skill() constructs NotFoundError`
- c0261 ..> c0028: `update_skill() constructs NotFoundError`
- c0261 ..> c0030: `import_skill() calls get()`
- c0261 ..> c0033: `type in _emit_event`
- c0261 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0261 ..> c0038: `type in _emit_event`
- c0261 ..> c0099: `type in create_skill`
- c0261 ..> c0099: `type in get_skill`
- c0261 ..> c0099: `type in import_skill`
- c0261 ..> c0099: `type in update_skill`
- c0261 ..> c0100: `import_skill() constructs SkillCreate`
- c0261 ..> c0100: `type in create_skill`
- c0261 ..> c0101: `type in get_skill_links`
- c0261 ..> c0102: `type in list_skills`
- c0261 ..> c0102: `type in search_skills`
- c0261 ..> c0103: `type in update_skill`
- c0261 ..> c0123: `create_skill() calls create_skill()`
- c0261 ..> c0123: `create_skill() calls skill_name_exists()`
- c0261 ..> c0123: `delete_skill() calls delete_skill()`
- c0261 ..> c0123: `delete_skill() calls get_skill_by_id()`
- c0261 ..> c0123: `get_all_skill_code_artifact_links() calls get_all_skill_code_artifact_links()`
- c0261 ..> c0123: `get_all_skill_document_links() calls get_all_skill_document_links()`
- c0261 ..> c0123: `get_all_skill_file_links() calls get_all_skill_file_links()`
- c0261 ..> c0123: `get_skill() calls get_skill_by_id()`
- c0261 ..> c0123: `get_skill_links() calls get_skill_links()`
- c0261 ..> c0123: `import_skill() calls create_skill()`
- c0261 ..> c0123: `link_skill_to_code_artifact() calls link_skill_to_code_artifact()`
- c0261 ..> c0123: `link_skill_to_document() calls link_skill_to_document()`
- c0261 ..> c0123: `link_skill_to_file() calls link_skill_to_file()`
- c0261 ..> c0123: `link_skill_to_memory() calls link_skill_to_memory()`
- c0261 ..> c0123: `list_skills() calls list_skills()`
- c0261 ..> c0123: `search_skills() calls search_skills()`
- c0261 ..> c0123: `type in __init__`
- c0261 ..> c0123: `unlink_skill_from_code_artifact() calls unlink_skill_from_code_artifact()`
- c0261 ..> c0123: `unlink_skill_from_document() calls unlink_skill_from_document()`
- c0261 ..> c0123: `unlink_skill_from_file() calls unlink_skill_from_file()`
- c0261 ..> c0123: `unlink_skill_from_memory() calls unlink_skill_from_memory()`
- c0261 ..> c0123: `update_skill() calls get_skill_by_id()`
- c0261 ..> c0123: `update_skill() calls update_skill()`
- c0261 ..> c0261: `create_skill() calls _emit_event()`
- c0261 ..> c0261: `delete_skill() calls _emit_event()`
- c0261 ..> c0261: `export_skill() calls get_skill()`
- c0261 ..> c0261: `get_skill() calls _emit_event()`
- c0261 ..> c0261: `link_skill_to_code_artifact() calls get_skill()`
- c0261 ..> c0261: `link_skill_to_document() calls get_skill()`
- c0261 ..> c0261: `link_skill_to_file() calls get_skill()`
- c0261 ..> c0261: `link_skill_to_memory() calls get_skill()`
- c0261 ..> c0261: `list_skills() calls _emit_event()`
- c0261 ..> c0261: `unlink_skill_from_code_artifact() calls get_skill()`
- c0261 ..> c0261: `unlink_skill_from_document() calls get_skill()`
- c0261 ..> c0261: `unlink_skill_from_file() calls get_skill()`
- c0261 ..> c0261: `unlink_skill_from_memory() calls get_skill()`
- c0261 ..> c0261: `update_skill() calls _emit_event()`
- c0261 ..> c0262: `import_skill() calls _quote_unquoted_frontmatter_scalars()`
- c0261 ..> c0265: `create_skill() calls apply_provenance_defaults()`
- c0261 ..> c0265: `update_skill() calls apply_provenance_defaults_for_update()`
- c0261 ..> c0266: `update_skill() calls get_changed_fields()`
- c0263 ..> c0023: `_emit_event() calls emit()`
- c0263 ..> c0023: `type in __init__`
- c0263 ..> c0024: `claim_task() constructs ConflictError`
- c0263 ..> c0024: `transition_task() constructs ConflictError`
- c0263 ..> c0025: `_validate_no_cycle() constructs CyclicDependencyError`
- c0263 ..> c0026: `_validate_dependencies_met() constructs DependencyNotMetError`
- c0263 ..> c0027: `_validate_all_criteria_met() constructs InvalidStateTransitionError`
- c0263 ..> c0027: `add_criterion() constructs InvalidStateTransitionError`
- c0263 ..> c0027: `claim_task() constructs InvalidStateTransitionError`
- c0263 ..> c0027: `create_task() constructs InvalidStateTransitionError`
- c0263 ..> c0027: `transition_task() constructs InvalidStateTransitionError`
- c0263 ..> c0028: `_validate_same_plan() constructs NotFoundError`
- c0263 ..> c0028: `add_criterion() constructs NotFoundError`
- c0263 ..> c0028: `add_dependency() constructs NotFoundError`
- c0263 ..> c0028: `claim_task() constructs NotFoundError`
- c0263 ..> c0028: `get_task() constructs NotFoundError`
- c0263 ..> c0028: `transition_task() constructs NotFoundError`
- c0263 ..> c0030: `transition_task() calls get()`
- c0263 ..> c0033: `type in _emit_event`
- c0263 ..> c0034: `_emit_event() constructs ActivityEvent`
- c0263 ..> c0038: `type in _emit_event`
- c0263 ..> c0077: `type in add_criterion`
- c0263 ..> c0077: `type in update_criterion`
- c0263 ..> c0078: `type in add_criterion`
- c0263 ..> c0079: `type in update_criterion`
- c0263 ..> c0082: `_check_plan_auto_completion() constructs PlanStatus`
- c0263 ..> c0082: `create_task() constructs PlanStatus`
- c0263 ..> c0084: `_check_plan_auto_completion() constructs PlanUpdate`
- c0263 ..> c0085: `type in _validate_all_criteria_met`
- c0263 ..> c0085: `type in _validate_dependencies_met`
- c0263 ..> c0085: `type in claim_task`
- c0263 ..> c0085: `type in create_task`
- c0263 ..> c0085: `type in get_task`
- c0263 ..> c0085: `type in transition_task`
- c0263 ..> c0085: `type in update_task`
- c0263 ..> c0086: `type in create_task`
- c0263 ..> c0089: `type in list_tasks`
- c0263 ..> c0090: `_check_plan_auto_completion() constructs TaskState`
- c0263 ..> c0090: `_validate_dependencies_met() constructs TaskState`
- c0263 ..> c0090: `add_criterion() constructs TaskState`
- c0263 ..> c0090: `claim_task() constructs TaskState`
- c0263 ..> c0090: `transition_task() constructs TaskState`
- c0263 ..> c0090: `type in list_tasks`
- c0263 ..> c0090: `type in transition_task`
- c0263 ..> c0091: `type in list_tasks`
- c0263 ..> c0091: `type in list_tasks_for_user`
- c0263 ..> c0092: `type in update_task`
- c0263 ..> c0124: `_check_plan_auto_completion() calls list_tasks()`
- c0263 ..> c0124: `_validate_all_criteria_met() calls get_criteria_for_task()`
- c0263 ..> c0124: `_validate_dependencies_met() calls get_task_by_id()`
- c0263 ..> c0124: `_validate_no_cycle() calls get_dependencies()`
- c0263 ..> c0124: `_validate_same_plan() calls get_task_by_id()`
- c0263 ..> c0124: `add_criterion() calls create_criterion()`
- c0263 ..> c0124: `add_criterion() calls get_task_by_id()`
- c0263 ..> c0124: `add_dependency() calls add_dependency()`
- c0263 ..> c0124: `add_dependency() calls get_task_by_id()`
- c0263 ..> c0124: `claim_task() calls get_task_by_id()`
- c0263 ..> c0124: `claim_task() calls transition_task_state()`
- c0263 ..> c0124: `create_task() calls add_dependency()`
- c0263 ..> c0124: `create_task() calls create_criterion()`
- c0263 ..> c0124: `create_task() calls create_task()`
- c0263 ..> c0124: `create_task() calls get_task_by_id()`
- c0263 ..> c0124: `delete_criterion() calls delete_criterion()`
- c0263 ..> c0124: `delete_task() calls delete_task()`
- c0263 ..> c0124: `delete_task() calls get_task_by_id()`
- c0263 ..> c0124: `get_task() calls get_task_by_id()`
- c0263 ..> c0124: `list_tasks() calls list_tasks()`
- c0263 ..> c0124: `list_tasks_for_user() calls list_tasks_for_user()`
- c0263 ..> c0124: `remove_dependency() calls remove_dependency()`
- c0263 ..> c0124: `transition_task() calls get_task_by_id()`
- c0263 ..> c0124: `transition_task() calls transition_task_state()`
- c0263 ..> c0124: `type in __init__`
- c0263 ..> c0124: `update_criterion() calls update_criterion()`
- c0263 ..> c0124: `update_task() calls get_task_by_id()`
- c0263 ..> c0124: `update_task() calls update_task()`
- c0263 ..> c0256: `_check_plan_auto_completion() calls get_plan()`
- c0263 ..> c0256: `_check_plan_auto_completion() calls update_plan()`
- c0263 ..> c0256: `claim_task() calls _emit_event()`
- c0263 ..> c0256: `create_task() calls _emit_event()`
- c0263 ..> c0256: `create_task() calls get_plan()`
- c0263 ..> c0256: `delete_task() calls _emit_event()`
- c0263 ..> c0256: `transition_task() calls _emit_event()`
- c0263 ..> c0256: `type in __init__`
- c0263 ..> c0256: `update_task() calls _emit_event()`
- c0263 ..> c0263: `add_dependency() calls _validate_no_cycle()`
- c0263 ..> c0263: `add_dependency() calls _validate_same_plan()`
- c0263 ..> c0263: `claim_task() calls _validate_dependencies_met()`
- c0263 ..> c0263: `create_task() calls _validate_no_cycle()`
- c0263 ..> c0263: `create_task() calls _validate_same_plan()`
- c0263 ..> c0263: `delete_task() calls _check_plan_auto_completion()`
- c0263 ..> c0263: `transition_task() calls _check_plan_auto_completion()`
- c0263 ..> c0263: `transition_task() calls _validate_all_criteria_met()`
- c0263 ..> c0263: `transition_task() calls _validate_dependencies_met()`
- c0263 ..> c0265: `create_task() calls apply_provenance_defaults()`
- c0263 ..> c0265: `update_task() calls apply_provenance_defaults_for_update()`
- c0263 ..> c0266: `update_task() calls get_changed_fields()`
- c0264 ..> c0109: `type in get_or_create_user`
- c0264 ..> c0109: `type in get_user_by_id`
- c0264 ..> c0109: `type in update_user`
- c0264 ..> c0110: `type in get_or_create_user`
- c0264 ..> c0110: `update_user() constructs UserCreate`
- c0264 ..> c0112: `get_or_create_user() constructs UserUpdate`
- c0264 ..> c0112: `type in update_user`
- c0264 ..> c0125: `get_or_create_user() calls create_user()`
- c0264 ..> c0125: `get_or_create_user() calls get_user_by_external_id()`
- c0264 ..> c0125: `get_or_create_user() calls update_user()`
- c0264 ..> c0125: `get_user_by_id() calls get_user_by_id()`
- c0264 ..> c0125: `type in __init__`
- c0264 ..> c0125: `update_user() calls create_user()`
- c0264 ..> c0125: `update_user() calls get_user_by_external_id()`
- c0264 ..> c0125: `update_user() calls update_user()`
- c0264 ..> c0266: `get_or_create_user() calls get_changed_fields()`
- c0264 ..> c0266: `update_user() calls get_changed_fields()`
- c0270 ..> c0133: `fast_embed_rank() constructs FastEmbedCrossEncoderAdapter`
- c0270 ..> c0134: `fast_embed_rank() calls rerank()`
- c0270 ..> c0134: `http_rank() calls rerank()`
- c0270 ..> c0134: `http_rank() constructs HttpRerankAdapter`
- c0271 ..> c0117: `test_sqlite_vec_async() calls close()`
- c0271 ..> c0117: `test_sqlite_vec_async() calls execute()`
- c0271 ..> c0117: `test_sqlite_vec_sync() calls close()`
- c0271 ..> c0117: `test_sqlite_vec_sync() calls execute()`
- c0272 ..> c0129: `test_embeddings() constructs GoogleEmbeddingsAdapter`
- c0272 ..> c0130: `test_embeddings() calls generate_embedding()`
- c0273 ..> c0117: `main() calls list_tools()`
- c0274 ..> c0117: `test_sqlite_init() calls execute()`
- c0274 ..> c0174: `test_sqlite_init() calls dispose()`
- c0274 ..> c0174: `test_sqlite_init() calls init_db()`
- c0274 ..> c0174: `test_sqlite_init() calls session()`
- c0274 ..> c0174: `test_sqlite_init() calls system_session()`
- c0274 ..> c0174: `test_sqlite_init() constructs SqliteDatabaseAdapter`
- c0275 ..> c0015: `_run_reembed() calls create_db_adapter()`
- c0275 ..> c0015: `_run_reembed() calls create_repositories()`
- c0275 ..> c0015: `_run_reembed() calls get_embedding_adapter()`
- c0275 ..> c0015: `lifespan() calls build_runtime()`
- c0275 ..> c0015: `lifespan() calls dispose_runtime()`
- c0275 ..> c0020: `_run_reembed() calls configure_logging()`
- c0275 ..> c0020: `lifespan() calls configure_logging()`
- c0275 ..> c0030: `lifespan() constructs TokenCache`
- c0275 ..> c0119: `_run_reembed() calls count_all_memories()`
- c0275 ..> c0119: `_run_reembed() calls reset_embedding_storage()`
- c0275 ..> c0144: `_run_reembed() calls dispose()`
- c0275 ..> c0144: `_run_reembed() calls init_db()`
- c0275 ..> c0194: `_run_reembed() calls register()`
- c0275 ..> c0194: `lifespan() calls register()`
- c0275 ..> c0211: `cli() calls dispatch()`
- c0275 ..> c0217: `_legacy_launcher() calls run()`
- c0275 ..> c0217: `_serve() calls run()`
- c0275 ..> c0242: `_run_reembed() calls create_backup()`
- c0275 ..> c0242: `_run_reembed() calls restore_backup()`
- c0275 ..> c0242: `_run_reembed() constructs BackupService`
- c0275 ..> c0259: `_run_reembed() calls re_embed_all()`
- c0275 ..> c0259: `_run_reembed() constructs ReEmbeddingService`
- c0275 ..> c0269: `_legacy_launcher() calls get_version()`
- c0275 ..> c0275: `_legacy_launcher() calls _run_reembed()`
- c0275 ..> c0275: `_legacy_launcher() calls _serve()`
- c0275 ..> c0275: `cli() calls _legacy_launcher()`
- c0276 ..> c0276: `_run() calls _print_summary()`
- c0276 ..> c0276: `main() calls _run()`
- c0276 ..> c0276: `main() calls config_from_argv()`
- c0276 ..> c0277: `config_from_argv() constructs HarnessConfig`
- c0276 ..> c0277: `type in _run`
- c0276 ..> c0277: `type in config_from_argv`
- c0276 ..> c0278: `_run() calls start()`
- c0276 ..> c0278: `_run() calls stop()`
- c0276 ..> c0278: `_run() constructs AgentContainer`
- c0276 ..> c0279: `_run() calls ensure_image()`
- c0276 ..> c0292: `_run() calls seed_skills()`
- c0276 ..> c0292: `_run() constructs ThrowawayForgetful`
- c0276 ..> c0296: `type in _print_summary`
- c0276 ..> c0297: `_run() calls run_skill()`
- c0276 ..> c0297: `_run() calls write_summary()`
- c0276 ..> c0297: `_run() constructs Walkthrough`
- c0276 ..> c0297: `main() calls run()`
- c0277 ..> c0030: `timeout_for() calls get()`
- c0278 ..> c0023: `stop() calls clear()`
- c0278 ..> c0030: `start() calls get()`
- c0278 ..> c0117: `_exec() calls close()`
- c0278 ..> c0277: `type in __init__`
- c0278 ..> c0278: `health_check() calls _exec()`
- c0278 ..> c0278: `start() calls _exec()`
- c0278 ..> c0279: `run_session() calls exec_command()`
- c0278 ..> c0279: `start() calls _docker_client()`
- c0278 ..> c0279: `start() calls _prepare_harness_mount()`
- c0278 ..> c0279: `start() calls build_container_env()`
- c0278 ..> c0279: `start() calls provision_agent()`
- c0278 ..> c0291: `health_check() constructs HarnessInfraError`
- c0278 ..> c0291: `run_session() constructs HarnessInfraError`
- c0278 ..> c0291: `start() constructs HarnessInfraError`
- c0278 ..> c0292: `stop() calls stop()`
- c0278 ..> c0294: `run_session() constructs SessionOutcome`
- c0278 ..> c0294: `type in run_session`
- c0278 ..> c0297: `start() calls run()`
- c0279 ..> c0030: `ensure_image() calls get()`
- c0279 ..> c0279: `ensure_image() calls _docker_client()`
- c0279 ..> c0279: `ensure_image() calls export_requirements()`
- c0279 ..> c0279: `ensure_image() calls requirements_hash()`
- c0279 ..> c0279: `provision_agent() calls staged_mount()`
- c0279 ..> c0291: `_docker_client() constructs HarnessInfraError`
- c0279 ..> c0291: `_prepare_harness_mount() constructs HarnessInfraError`
- c0279 ..> c0291: `ensure_image() constructs HarnessInfraError`
- c0279 ..> c0291: `provision_agent() constructs HarnessInfraError`
- c0279 ..> c0297: `_prepare_harness_mount() calls run()`
- c0279 ..> c0297: `ensure_image() calls run()`
- c0279 ..> c0297: `export_requirements() calls run()`
- c0280 ..> c0030: `health() calls get()`
- c0280 ..> c0030: `run_session() calls get()`
- c0280 ..> c0217: `main() calls run()`
- c0280 ..> c0278: `health() calls health_check()`
- c0280 ..> c0280: `health() calls _shell()`
- c0280 ..> c0280: `main() calls health()`
- c0280 ..> c0280: `main() calls run_session()`
- c0280 ..> c0280: `run_session() calls _attach_debug_log()`
- c0280 ..> c0280: `run_session() calls _shell()`
- c0281 ..> c0030: `build_prompt() calls get()`
- c0281 ..> c0286: `build_prompt() calls report_contract_example()`
- c0283 --> c0285: `field report`
- c0285 --> c0282: `field issues`
- c0285 --> c0284: `field steps`
- c0286 ..> c0030: `_normalize_severity() calls get()`
- c0286 ..> c0283: `load_report() constructs ReportLoad`
- c0286 ..> c0283: `type in load_report`
- c0286 ..> c0286: `_normalize_report_verdict() calls _lowercase()`
- c0286 ..> c0286: `_normalize_severity() calls _lowercase()`
- c0286 ..> c0286: `_normalize_step_verdict() calls _lowercase()`
- c0292 ..> c0030: `_wait_until_healthy() calls get()`
- c0292 ..> c0213: `execute() calls close()`
- c0292 ..> c0213: `execute() calls execute()`
- c0292 ..> c0213: `execute() constructs RemoteExecutor`
- c0292 ..> c0213: `seed_skills() calls execute()`
- c0292 ..> c0213: `stop() calls close()`
- c0292 ..> c0291: `_wait_until_healthy() constructs HarnessInfraError`
- c0292 ..> c0291: `seed_skills() constructs HarnessInfraError`
- c0292 ..> c0291: `start() constructs HarnessInfraError`
- c0292 ..> c0292: `_wait_until_healthy() calls stop()`
- c0292 ..> c0292: `start() calls _child_env()`
- c0292 ..> c0292: `start() calls _wait_until_healthy()`
- c0292 ..> c0293: `start() calls _ephemeral_port()`
- c0295 ..> c0294: `type in run_session`
- c0296 --> c0283: `field report_load`
- c0297 ..> c0030: `run_skill() calls get()`
- c0297 ..> c0277: `run_skill() calls timeout_for()`
- c0297 ..> c0277: `type in __init__`
- c0297 ..> c0281: `run_skill() calls build_prompt()`
- c0297 ..> c0286: `run_skill() calls load_report()`
- c0297 ..> c0295: `run_skill() calls run_session()`
- c0297 ..> c0295: `type in __init__`
- c0297 ..> c0296: `run_skill() constructs SkillRunResult`
- c0297 ..> c0296: `type in _meta`
- c0297 ..> c0296: `type in run`
- c0297 ..> c0296: `type in run_skill`
- c0297 ..> c0296: `type in write_summary`
- c0297 ..> c0297: `run() calls run_skill()`
- c0297 ..> c0297: `run() calls write_summary()`
- c0297 ..> c0297: `run_skill() calls _meta()`
- c0297 ..> c0298: `run_skill() calls load_events()`
- c0297 ..> c0298: `run_skill() calls prepare_workspace()`
- c0297 ..> c0298: `run_skill() calls scan_for_breaches()`
- c0298 ..> c0030: `scan_for_breaches() calls get()`
- c0298 ..> c0298: `prepare_workspace() calls _build_fixture_repo()`

## Type key

- Type1: `dict[str, Any]`
- Type2: `Any | None`
- Type3: `list[str] | None`
- Type4: `int | None`
- Type5: `str | None`
- Type6: `dict[str, list[EventHandler]]`
- Type7: `dict[str, set[asyncio.Queue[dict[str, Any]]]]`
- Type8: `dict[str, int]`
- Type9: `float | None`
- Type10: `AsyncGenerator[dict[str, Any], None]`
- Type11: `OrderedDict[str, CacheEntry]`
- Type12: `User | None`
- Type13: `dict[str, dict[str, Any]] | None`
- Type14: `dict[str, Any] | None`
- Type15: `list[int] | None`
- Type16: `EntityType | None`
- Type17: `Literal[ "memory_link", "entity_memory", "entity_relationship", "entity_project",
  "memory_project", "document_project", "code_artifact_project", "memory_document", "memory_skill",
  "memory_code_artifact", "memory_file", "file_project", "entity_file", "skill_project",
  "skill_file", "skill_code_artifact", "skill_document", "plan_project", "plan_task", ]`
- Type18: `Literal["memory", "entity", "project", "document", "code_artifact", "file", "skill",
  "plan", "task"]`
- Type19: `datetime | None`
- Type20: `list[int] |None`
- Type21: `bool | None`
- Type22: `PlanStatus | None`
- Type23: `list[CriterionCreate] | None`
- Type24: `TaskPriority | None`
- Type25: `ProjectType | None`
- Type26: `ProjectStatus | None`
- Type27: `dict | None`
- Type28: `Callable[..., Awaitable[Any]]`
- Type29: `tuple[list[ActivityLogEntry], int]`
- Type30: `ActionType | None`
- Type31: `ActorType | None`
- Type32: `CodeArtifact | None`
- Type33: `Document | None`
- Type34: `Entity | None`
- Type35: `tuple[list[EntitySummary], int]`
- Type36: `list[tuple[int, int]]`
- Type37: `list[tuple[int, str]]`
- Type38: `list[tuple[int, str, str]]`
- Type39: `File | None`
- Type40: `list[tuple[Memory, MemoryScore]]`
- Type41: `Memory | None`
- Type42: `list[tuple[Memory, float]]`
- Type43: `tuple[list[Memory], int]`
- Type44: `tuple[list[dict[str, Any]], bool]`
- Type45: `list[tuple[int, list[float]]]`
- Type46: `Plan | None`
- Type47: `Project | None`
- Type48: `Skill | None`
- Type49: `Task | None`
- Type50: `TaskState | None`
- Type51: `dict[str, bool]`
- Type52: `Callable[[dict[str, bool]], T]`
- Type53: `list[tuple[int, float]]`
- Type54: `list[tuple[int,float]]`
- Type55: `RerankAdapter | None`
- Type56: `Mapped["UsersTable"]`
- Type57: `Mapped["ProjectsTable"]`
- Type58: `Mapped[list["MemoryTable"]]`
- Type59: `Mapped[list["SkillsTable"]]`
- Type60: `Mapped["TasksTable"]`
- Type61: `Mapped[list["ProjectsTable"]]`
- Type62: `Mapped[list["FilesTable"]]`
- Type63: `Mapped[list["EntityRelationshipsTable"]]`
- Type64: `Mapped["EntitiesTable"]`
- Type65: `Mapped[list["EntitiesTable"]]`
- Type66: `Mapped[list["CodeArtifactsTable"]]`
- Type67: `Mapped[list["DocumentsTable"]]`
- Type68: `Mapped[list["TasksTable"]]`
- Type69: `Mapped[list["PlansTable"]]`
- Type70: `Mapped["PlansTable"]`
- Type71: `Mapped[list["CriteriaTable"]]`
- Type72: `Mapped[list["TaskDependenciesTable"]]`
- Type73: `Path | None`
- Type74: `"LocalExecutor"`
- Type75: `tuple[Any, str]`
- Type76: `tuple[int, int]`
- Type77: `tuple[set[str], frozenset[str]]`
- Type78: `frozenset[str] | None`
- Type79: `list[int] | int | None`
- Type80: `list[dict[str, Any]] | None`
- Type81: `dict[str, ToolImplementation]`
- Type82: `ToolImplementation | None`
- Type83: `"EventBus | None"`
- Type84: `tuple[list[int], int, list[tuple[int, str]]]`
- Type85: `tuple[list[int], int, list[tuple[int, str, str]]]`
- Type86: `ProjectServiceProtocol | None`
- Type87: `DocumentServiceProtocol | None`
- Type88: `CodeArtifactServiceProtocol | None`
- Type89: `FileServiceProtocol | None`
- Type90: `SkillServiceProtocol | None`
- Type91: `PlanServiceProtocol | None`
- Type92: `TaskServiceProtocol | None`
- Type93: `tuple[str, int]`
- Type94: `list | None`
- Type95: `"EventBus"`
- Type96: `tuple[Memory, list[MemorySummary]]`
- Type97: `tuple[list[Memory], list[LinkedMemory], int, bool]`
- Type98: `tuple[list[Memory], int, bool]`
- Type99: `ValidationResult | None`
- Type100: `Callable[[int, int], None] | None`
- Type101: `dict[str, tuple]`
- Type102: `tuple[str, ...]`
- Type103: `Literal["cli"]`
- Type104: `dict[str, float]`
- Type105: `tuple[int, str]`
- Type106: `dict[str, str]`
- Type107: `dict[str, dict[str, str]]`
- Type108: `Literal["blocker", "major", "minor", "nit"]`
- Type109: `Literal["ok", "missing", "invalid_json", "schema_error"]`
- Type110: `WalkthroughReport | None`
- Type111: `Literal["ok", "issue"]`
- Type112: `Literal["pass", "issues", "blocked"]`
- Type113: `subprocess.Popen | None`
- Type114: `Literal["ran", "timeout"]`
- Type115: `list[dict[str, Any]]`
- Relation116: `_validate_rebuild_scope() calls count_memories_for_targeted_rebuild()`
- Relation117: `create_code_artifact_adapters() constructs CodeArtifactToolAdapters`

## Signature key

- Signature1: `+create_repositories(db_adapter: unknown, embeddings_adapter: unknown,
  reranker_adapter: unknown) unknown`
- Signature2: `+query_events(user_id: UUID, entity_type: EntityType | None, action: ActionType |
  None, entity_id: int | None, actor: ActorType | None, since: datetime | None, until: datetime |
  None, limit: int, offset: int) tuple[list[ActivityLogEntry], int]`
- Signature3: `+list_code_artifacts(user_id: UUID, project_id: int | None, language: str | None,
  tags: list[str] | None) list[CodeArtifactSummary]`
- Signature4: `+update_code_artifact(user_id: UUID, artifact_id: int, artifact_data:
  CodeArtifactUpdate) CodeArtifact`
- Signature5: `+list_documents(user_id: UUID, project_id: int | None, document_type: str | None,
  tags: list[str] | None) list[DocumentSummary]`
- Signature6: `+update_document(user_id: UUID, document_id: int, document_data: DocumentUpdate)
  Document`
- Signature7: `+list_entities(user_id: UUID, project_ids: list[int] | None, entity_type: EntityType
  | None, tags: list[str] | None, limit: int, offset: int) tuple[list[EntitySummary], int]`
- Signature8: `+search_entities(user_id: UUID, search_query: str, entity_type: EntityType | None,
  tags: list[str] | None, limit: int) list[EntitySummary]`
- Signature9: `+create_entity_relationship(user_id: UUID, relationship_data:
  EntityRelationshipCreate) EntityRelationship`
- Signature10: `+get_entity_relationships(user_id: UUID, entity_id: int, direction: str | None,
  relationship_type: str | None) list[EntityRelationship]`
- Signature11: `+update_entity_relationship(user_id: UUID, relationship_id: int, relationship_data:
  EntityRelationshipUpdate) EntityRelationship`
- Signature12: `+list_files(user_id: UUID, project_id: int | None, mime_type: str | None, tags:
  list[str] | None) list[FileSummary]`
- Signature13: `+search(user_id: UUID, query: str, query_context: str, k: int, importance_threshold:
  int | None, project_ids: list[int] | None, exclude_ids: list[int] | None) list[Memory]`
- Signature14: `+search_scored(user_id: UUID, query: str, query_context: str, k: int,
  importance_threshold: int | None, project_ids: list[int] | None, exclude_ids: list[int] | None)
  list[tuple[Memory, MemoryScore]]`
- Signature15: `+update_memory(user_id: UUID, memory_id: int, updated_memory: MemoryUpdate,
  existing_memory: Memory, search_fields_changed: bool) Memory | None`
- Signature16: `+get_linked_memories(user_id: UUID, memory_id: int, project_ids: list[int] | None,
  max_links: int) list[Memory]`
- Signature17: `+find_obsolete_matches(user_id: UUID, memory_id: int, limit: int, min_similarity:
  float) list[tuple[Memory, float]]`
- Signature18: `+list_memories(user_id: UUID, limit: int, offset: int, project_ids: list[int] |
  None, include_obsolete: bool, sort_by: str, sort_order: str, tags: list[str] | None,
  importance_min: int | None, created_since: datetime | None) tuple[list[Memory], int]`
- Signature19: `+get_subgraph_nodes(user_id: UUID, center_type: str, center_id: int, depth: int,
  include_memories: bool, include_entities: bool, include_projects: bool, include_documents: bool,
  include_code_artifacts: bool, max_nodes: int) tuple[list[dict[str, Any]], bool]`
- Signature20: `+count_memories_for_targeted_rebuild(user_id: UUID, memory_ids: list[int] | None,
  project_id: int | None) int`
- Signature21: `+get_memories_for_targeted_rebuild(user_id: UUID, limit: int, after_id: int | None,
  memory_ids: list[int] | None, project_id: int | None) list[Memory]`
- Signature22: `+list_projects(user_id: UUID, status: ProjectStatus | None, repo_name: str | None,
  name: str | None) list[ProjectSummary]`
- Signature23: `+list_skills(user_id: UUID, project_id: int | None, tags: list[str] | None,
  importance_threshold: int | None) list[SkillSummary]`
- Signature24: `+unlink_skill_from_code_artifact(user_id: UUID, skill_id: int, code_artifact_id:
  int) dict`
- Signature25: `+list_tasks(user_id: UUID, plan_id: int, state: TaskState | None, priority:
  TaskPriority | None, assigned_agent: str | None) list[TaskSummary]`
- Signature26: `+transition_task_state(user_id: UUID, task_id: int, new_state: TaskState,
  expected_version: int, assigned_agent: str | None) Task`
- Signature27: `+create_criterion(user_id: UUID, task_id: int, criterion_data: CriterionCreate)
  Criterion`
- Signature28: `+update_criterion(user_id: UUID, criterion_id: int, criterion_data: CriterionUpdate)
  Criterion`
- Signature29: `+load_fastembed_model(model_role: str, model_name: str, cache_dir: str, factory:
  Callable[[dict[str, bool]], T]) T`
- Signature30: `-__init__(model: str, threads: int, cache_dir: str | None, workers: int, providers:
  list[str] | None) unknown`
- Signature31: `-_create_text_cross_encoder(model: str, threads: int, cache_dir: str | None,
  providers: list[str] | None, fastembed_kwargs: dict[str, bool]) unknown`
- Signature32: `-__init__(db_adapter: PostgresDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) unknown`
- Signature33: `+semantic_search(user_id: UUID, query: str, k: int, importance_threshold: int |
  None, project_ids: list[int] | None, exclude_ids: list[int] | None) list[Memory]`
- Signature34: `+semantic_search_scored(user_id: UUID, query: str, k: int, importance_threshold: int
  | None, project_ids: list[int] | None, exclude_ids: list[int] | None) list[tuple[Memory, float]]`
- Signature35: `+update_memory(user_id: UUID, memory_id: int, updated_memory: MemoryUpdate,
  existing_memory: Memory, search_fields_changed: bool) Memory`
- Signature36: `-_link_projects(session: unknown, memory: MemoryTable, project_ids: list[int],
  user_id: UUID) None`
- Signature37: `-_link_code_artifacts(session: unknown, memory: MemoryTable, code_artifact_ids:
  list[int], user_id: UUID) None`
- Signature38: `-_link_documents(session: unknown, memory: MemoryTable, document_ids: list[int],
  user_id: UUID) None`
- Signature39: `-_link_files(session: unknown, memory: MemoryTable, file_ids: list[int], user_id:
  UUID) None`
- Signature40: `-_link_skills(session: unknown, memory: MemoryTable, skill_ids: list[int], user_id:
  UUID) None`
- Signature41: `-_build_targeted_rebuild_filter(user_id: UUID, memory_ids: list[int] | None,
  project_id: int | None) unknown`
- Signature42: `+get_subgraph_nodes(user_id: UUID, center_type: str, center_id: int, depth: int,
  include_memories: bool, include_entities: bool, include_projects: bool, include_documents: bool,
  include_code_artifacts: bool, include_files: bool, include_skills: bool, include_plans: bool,
  include_tasks: bool, max_nodes: int) tuple[list[dict[str, Any]], bool]`
- Signature43: `-__init__(db_adapter: SqliteDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) unknown`
- Signature44: `-__init__(db_adapter: SqliteDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) None`
- Signature45: `+create_code_artifact(title: str, description: str, code: str, language: str, ctx:
  Context, tags: list[str] | None, project_id: int | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) CodeArtifact`
- Signature46: `+update_code_artifact(artifact_id: int, ctx: Context, title: str | None,
  description: str | None, code: str | None, language: str | None, tags: list[str] | None,
  project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) CodeArtifact`
- Signature47: `+create_document(title: str, description: str, content: str, ctx: Context,
  document_type: str, filename: str | None, tags: list[str] | None, project_id: int | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) Document`
- Signature48: `+update_document(document_id: int, ctx: Context, title: str | None, description: str
  | None, content: str | None, document_type: str | None, filename: str | None, tags: list[str] |
  None, project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url:
  str | None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) Document`
- Signature49: `+create_entity(name: str, entity_type: str, ctx: Context, custom_type: str | None,
  notes: str | None, tags: list[str] | None, aka: list[str] | None, project_ids: list[int] | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) Entity`
- Signature50: `+search_entities(query: str, ctx: Context, entity_type: str | None, tags: list[str]
  | None, limit: int) dict`
- Signature51: `+update_entity(entity_id: int, ctx: Context, name: str | None, entity_type: str |
  None, custom_type: str | None, notes: str | None, tags: list[str] | None, aka: list[str] | None,
  project_ids: list[int] | None, source_repo: str | None, source_files: list[str] | None,
  source_url: str | None, confidence: float | None, encoding_agent: str | None, encoding_version:
  str | None, agent_id: str | None, agent_version: str | None, agent_model: str | None) Entity`
- Signature52: `+create_entity_relationship(source_entity_id: int, target_entity_id: int,
  relationship_type: str, ctx: Context, strength: float | None, confidence: float | None, metadata:
  dict[str, Any] | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) EntityRelationship`
- Signature53: `+get_entity_relationships(entity_id: int, ctx: Context, direction: str | None,
  relationship_type: str | None) dict`
- Signature54: `+update_entity_relationship(relationship_id: int, ctx: Context, relationship_type:
  str | None, strength: float | None, confidence: float | None, metadata: dict[str, Any] | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, encoding_agent:
  str | None, encoding_version: str | None, agent_id: str | None, agent_version: str | None,
  agent_model: str | None) EntityRelationship`
- Signature55: `+create_file(filename: str, description: str, data: str, mime_type: str, ctx:
  Context, tags: list[str] | None, project_id: int | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) unknown`
- Signature56: `+update_file(file_id: int, ctx: Context, filename: str | None, description: str |
  None, data: str | None, mime_type: str | None, tags: list[str] | None, project_id: int | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) unknown`
- Signature57: `+create_memory(title: str, content: str, context: str, keywords: list[str], tags:
  list[str], importance: int, ctx: Context, project_ids: list[int] | None, code_artifact_ids:
  list[int] | None, document_ids: list[int] | None, file_ids: list[int] | None, source_repo: str |
  None, source_files: list[str] | None, source_url: str | None, confidence: float | None,
  encoding_agent: str | None, encoding_version: str | None, agent_id: str | None, agent_version: str
  | None, agent_model: str | None) MemoryCreateResponse`
- Signature58: `+query_memory(query: str, query_context: str, ctx: Context, k: int, include_links:
  bool, max_links_per_primary: int, importance_threshold: int | None, project_ids: list[int] | None,
  strict_project_filter: bool) MemoryQueryResult`
- Signature59: `+update_memory(ctx: Context, memory_id: int | None, id: int | None, title: str |
  None, content: str | None, context: str | None, keywords: list[str] | None, tags: list[str] |
  None, importance: int | None, project_ids: list[int] | None, code_artifact_ids: list[int] | None,
  document_ids: list[int] | None, file_ids: list[int] | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None, kwargs: unknown) Memory`
- Signature60: `+link_memories(ctx: Context, memory_id: int | None, related_ids: list[int] | int |
  None, source_id: int | None, target_id: int | None, target_ids: list[int] | int | None,
  related_id: int | None, memory_id_1: int | None, memory_id_2: int | None, from_id: int | None,
  to_id: int | None, from_memory_id: int | None, to_memory_id: int | None, memory_ids: list[int] |
  None, ids: list[int] | None, id: int | None, linked_ids: list[int] | int | None,
  related_memory_ids: list[int] | int | None, kwargs: unknown) dict`
- Signature61: `+unlink_memories(ctx: Context, source_id: int | None, target_id: int | None,
  memory_id: int | None, related_id: int | None, related_ids: list[int] | int | None, target_ids:
  list[int] | int | None, memory_ids: list[int] | None, ids: list[int] | None, memory_id_1: int |
  None, memory_id_2: int | None, from_id: int | None, to_id: int | None, from_memory_id: int | None,
  to_memory_id: int | None, id: int | None, linked_ids: list[int] | int | None, related_memory_ids:
  list[int] | int | None, kwargs: unknown) dict`
- Signature62: `+mark_memory_obsolete(ctx: Context, memory_id: int | None, id: int | None, reason:
  str, superseded_by: int | None, kwargs: unknown) dict`
- Signature63: `+get_recent_memories(ctx: Context, limit: int, offset: int, project_ids: list[int] |
  None, include_obsolete: bool, sort_by: str, sort_order: str, tags: list[str] | None,
  importance_min: int | None, created_since: str | None) dict`
- Signature64: `+create_plan(title: str, project_id: int, ctx: Context, goal: str | None, context:
  str | None, status: str, source_repo: str | None, source_files: list[str] | None, source_url: str
  | None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature65: `+update_plan(plan_id: int, ctx: Context, title: str | None, goal: str | None,
  context: str | None, status: str | None, source_repo: str | None, source_files: list[str] | None,
  source_url: str | None, confidence: float | None, encoding_agent: str | None, encoding_version:
  str | None, agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature66: `+create_project(name: str, description: str, project_type: ProjectType, ctx:
  Context, status: ProjectStatus, repo_name: str | None, last_encoding_point: str | None, notes: str
  | None, source_repo: str | None, source_files: list[str] | None, source_url: str | None,
  confidence: float | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str
  | None, agent_version: str | None, agent_model: str | None) Project`
- Signature67: `+update_project(project_id: int, ctx: Context, name: str | None, description: str |
  None, project_type: ProjectType | None, status: ProjectStatus | None, repo_name: str | None,
  last_encoding_point: str | None, notes: str | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) Project`
- Signature68: `+create_skill(name: str, description: str, content: str, ctx: Context, license: str
  | None, compatibility: str | None, allowed_tools: list[str] | None, metadata: dict[str, Any] |
  None, tags: list[str] | None, importance: int, project_id: int | None, source_repo: str | None,
  source_files: list[str] | None, source_url: str | None, confidence: float | None, encoding_agent:
  str | None, encoding_version: str | None, agent_id: str | None, agent_version: str | None,
  agent_model: str | None) unknown`
- Signature69: `+list_skills(ctx: Context, project_id: int | None, tags: list[str] | None,
  importance_threshold: int | None) dict`
- Signature70: `+update_skill(skill_id: int, ctx: Context, name: str | None, description: str |
  None, content: str | None, license: str | None, compatibility: str | None, allowed_tools:
  list[str] | None, metadata: dict[str, Any] | None, tags: list[str] | None, importance: int | None,
  project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature71: `+import_skill(skill_md_content: str, ctx: Context, project_id: int | None,
  importance: int) unknown`
- Signature72: `+unlink_skill_from_code_artifact(skill_id: int, code_artifact_id: int, ctx: Context)
  dict`
- Signature73: `+create_task(title: str, plan_id: int, ctx: Context, description: str | None,
  priority: str, assigned_agent: str | None, criteria: list[dict[str, Any]] | None, dependency_ids:
  list[int] | None, source_repo: str | None, source_files: list[str] | None, source_url: str | None,
  confidence: float | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str
  | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature74: `+update_task(task_id: int, ctx: Context, title: str | None, description: str | None,
  priority: str | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature75: `+query_tasks(plan_id: int, ctx: Context, state: str | None, priority: str | None,
  assigned_agent: str | None) unknown`
- Signature76: `+create_project_adapters(project_service: ProjectService, user_service: UserService)
  dict[str, Any]`
- Signature77: `+create_code_artifact_adapters(code_artifact_service: CodeArtifactService,
  user_service: UserService) dict[str, Any]`
- Signature78: `+create_document_adapters(document_service: DocumentService, user_service:
  UserService) dict[str, Any]`
- Signature79: `+register_simplified_tool(registry: ToolRegistry, name: str, category: ToolCategory,
  description: str, parameters: list[dict], returns: str, implementation: Any, examples: list[str],
  tags: list[str], mutates: bool) unknown`
- Signature80: `+register_all_tools_metadata(registry: ToolRegistry, user_service: UserService,
  memory_service: MemoryService, project_service: unknown, code_artifact_service: unknown,
  document_service: unknown, entity_service: unknown, plan_service: unknown, task_service: unknown,
  file_service: unknown, skill_service: unknown) unknown`
- Signature81: `+register(name: str, category: ToolCategory, description: str, parameters:
  list[ToolParameter], returns: str, implementation: Any, examples: list[str], tags: list[str],
  mutates: bool) None`
- Signature82: `+get_activity(user_id: UUID, entity_type: EntityType | None, action: ActionType |
  None, entity_id: int | None, actor: ActorType | None, since: datetime | None, until: datetime |
  None, limit: int, offset: int) ActivityListResponse`
- Signature83: `+get_entity_history(user_id: UUID, entity_type: EntityType, entity_id: int, limit:
  int, offset: int) ActivityListResponse`
- Signature84: `-_emit_event(user_id: UUID, entity_type: EntityType, entity_id: int, action:
  ActionType, snapshot: dict, changes: dict | None, metadata: dict | None) None`
- Signature85: `-_emit_event(user_id: UUID, entity_type: ActivityEntityType, entity_id: int, action:
  ActionType, snapshot: dict, changes: dict | None, metadata: dict | None) None`
- Signature86: `-__init__(memory_repo: MemoryRepository, entity_repo: EntityRepository,
  project_service: ProjectServiceProtocol | None, document_service: DocumentServiceProtocol | None,
  code_artifact_service: CodeArtifactServiceProtocol | None, file_service: FileServiceProtocol |
  None, skill_service: SkillServiceProtocol | None, plan_service: PlanServiceProtocol | None,
  task_service: TaskServiceProtocol | None) unknown`
- Signature87: `+get_subgraph(user_id: UUID, center_node_id: str, depth: int, node_types: list[str]
  | None, max_nodes: int) SubgraphResponse`
- Signature88: `-_fetch_node_data(user_id: UUID, memory_ids: list[int], entity_ids: list[int],
  project_ids: list[int], document_ids: list[int], code_artifact_ids: list[int], file_ids:
  list[int], skill_ids: list[int], depth_lookup: dict, plan_ids: list[int] | None, task_ids:
  list[int] | None, task_summaries: list | None) list[SubgraphNode]`
- Signature89: `-_fetch_edges(user_id: UUID, memory_ids: list[int], entity_ids: list[int],
  project_ids: list[int], document_ids: list[int], code_artifact_ids: list[int], file_ids: list[int]
  | None, skill_ids: list[int] | None, plan_ids: list[int] | None, task_ids: list[int] | None,
  task_summaries: list | None) list[SubgraphEdge]`
- Signature90: `+mark_memory_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: int
  | None) bool`
- Signature91: `-_fetch_linked_memories(user_id: unknown, primary_memories: list[Memory],
  max_links_per_primary: int, project_ids: list[int] | None) list[LinkedMemory]`
- Signature92: `-_apply_token_budget(primary_memories: list[Memory], linked_memories:
  list[LinkedMemory], max_tokens: int, max_memories: int) tuple[list[Memory], list[LinkedMemory],
  int, bool]`
- Signature93: `+truncate_memories_by_budget(memories: list[Memory], max_tokens: int, max_count:
  int) tuple[list[Memory], int, bool]`
- Signature94: `-__init__(memory_repository: MemoryRepository, embedding_adapter: EmbeddingsAdapter,
  batch_size: int) unknown`
- Signature95: `+rebuild_targeted(user_id: UUID, memory_ids: list[int] | None, project_id: int |
  None, progress_callback: Callable[[int, int], None] | None) TargetedRebuildResult`
- Signature96: `-_record_unresolved_memory_ids(memory_ids: list[int] | None, project_id: int | None,
  result: TargetedRebuildResult) None`
- Signature97: `-_recompute_auto_links(user_id: UUID, memory_ids: list[int], result:
  TargetedRebuildResult) None`
- Signature98: `+import_skill(user_id: UUID, skill_md_content: str, project_id: int | None,
  importance: int) Skill`
- Signature99: `-__init__(task_repo: TaskRepository, plan_service: PlanService, event_bus: "EventBus
  | None") unknown`
- Signature100: `+transition_task(user_id: UUID, task_id: int, new_state: TaskState,
  expected_version: int) Task`
- Signature101: `-_validate_same_plan(user_id: UUID, task_id: int, dep_task_id: int,
  expected_plan_id: int) None`
- Signature102: `+run_session(skill: str, skill_dir: Path, workspace: Path, prompt: str, timeout:
  float) SessionOutcome`
- Signature103: `-__init__(config: HarnessConfig, runner: SessionRunner, server_url: str, run_dir:
  Path) unknown`

## Extraction warnings

- `Unresolved Python binding: EventBus uses asyncio.Task`
- `Unresolved or out-of-scope base: ActionType -> StrEnum`
- `Unresolved or out-of-scope base: ActivityEvent -> BaseModel`
- `Unresolved or out-of-scope base: ActivityListResponse -> BaseModel`
- `Unresolved or out-of-scope base: ActivityLogEntry -> BaseModel`
- `Unresolved or out-of-scope base: ActivityRepository -> Protocol`
- `Unresolved or out-of-scope base: ActorType -> StrEnum`
- `Unresolved or out-of-scope base: Base -> DeclarativeBase`
- `Unresolved or out-of-scope base: CliError -> Exception`
- `Unresolved or out-of-scope base: CodeArtifactCreate -> BaseModel`
- `Unresolved or out-of-scope base: CodeArtifactRepository -> Protocol`
- `Unresolved or out-of-scope base: CodeArtifactServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: CodeArtifactSummary -> BaseModel`
- `Unresolved or out-of-scope base: CodeArtifactUpdate -> BaseModel`
- `Unresolved or out-of-scope base: ConflictError -> Exception`
- `Unresolved or out-of-scope base: ConsoleFormatter -> logging.Formatter`
- `Unresolved or out-of-scope base: Criterion -> BaseModel`
- `Unresolved or out-of-scope base: CriterionCreate -> BaseModel`
- `Unresolved or out-of-scope base: CriterionUpdate -> BaseModel`
- `Unresolved or out-of-scope base: CyclicDependencyError -> Exception`
- `Unresolved or out-of-scope base: DependencyNotMetError -> Exception`
- `Unresolved or out-of-scope base: DocumentCreate -> BaseModel`
- `Unresolved or out-of-scope base: DocumentRepository -> Protocol`
- `Unresolved or out-of-scope base: DocumentServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: DocumentSummary -> BaseModel`
- `Unresolved or out-of-scope base: DocumentUpdate -> BaseModel`
- `Unresolved or out-of-scope base: EmbeddingsAdapter -> Protocol`
- `Unresolved or out-of-scope base: EntityCreate -> BaseModel`
- `Unresolved or out-of-scope base: EntityListResponse -> BaseModel`
- `Unresolved or out-of-scope base: EntityRelationshipCreate -> BaseModel`
- `Unresolved or out-of-scope base: EntityRelationshipUpdate -> BaseModel`
- `Unresolved or out-of-scope base: EntityRepository -> Protocol`
- `Unresolved or out-of-scope base: EntitySummary -> BaseModel`
- `Unresolved or out-of-scope base: EntityType -> StrEnum`
- `Unresolved or out-of-scope base: EntityUpdate -> BaseModel`
- `Unresolved or out-of-scope base: FileCreate -> BaseModel`
- `Unresolved or out-of-scope base: FileRepository -> Protocol`
- `Unresolved or out-of-scope base: FileServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: FileSummary -> BaseModel`
- `Unresolved or out-of-scope base: FileUpdate -> BaseModel`
- `Unresolved or out-of-scope base: HarnessConfig -> BaseSettings`
- `Unresolved or out-of-scope base: HarnessInfraError -> RuntimeError`
- `Unresolved or out-of-scope base: HealthStatus -> BaseModel`
- `Unresolved or out-of-scope base: InvalidStateTransitionError -> Exception`
- `Unresolved or out-of-scope base: JSONFormatter -> logging.Formatter`
- `Unresolved or out-of-scope base: LinkedMemory -> BaseModel`
- `Unresolved or out-of-scope base: MemoryCreate -> BaseModel`
- `Unresolved or out-of-scope base: MemoryCreateResponse -> BaseModel`
- `Unresolved or out-of-scope base: MemoryLinkRequest -> BaseModel`
- `Unresolved or out-of-scope base: MemoryListResponse -> BaseModel`
- `Unresolved or out-of-scope base: MemoryQueryRequest -> BaseModel`
- `Unresolved or out-of-scope base: MemoryQueryResult -> BaseModel`
- `Unresolved or out-of-scope base: MemoryRepository -> Protocol`
- `Unresolved or out-of-scope base: MemoryScore -> BaseModel`
- `Unresolved or out-of-scope base: MemorySummary -> BaseModel`
- `Unresolved or out-of-scope base: MemoryUpdate -> BaseModel`
- `Unresolved or out-of-scope base: NotFoundError -> Exception`
- `Unresolved or out-of-scope base: ObsoleteMatch -> BaseModel`
- `Unresolved or out-of-scope base: PlanCreate -> BaseModel`
- `Unresolved or out-of-scope base: PlanRepository -> Protocol`
- `Unresolved or out-of-scope base: PlanServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: PlanStatus -> StrEnum`
- `Unresolved or out-of-scope base: PlanSummary -> BaseModel`
- `Unresolved or out-of-scope base: PlanUpdate -> BaseModel`
- `Unresolved or out-of-scope base: ProjectCreate -> BaseModel`
- `Unresolved or out-of-scope base: ProjectRepository -> Protocol`
- `Unresolved or out-of-scope base: ProjectServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: ProjectStatus -> StrEnum`
- `Unresolved or out-of-scope base: ProjectSummary -> BaseModel`
- `Unresolved or out-of-scope base: ProjectType -> StrEnum`
- `Unresolved or out-of-scope base: ProjectUpdate -> BaseModel`
- `Unresolved or out-of-scope base: ReportIssue -> BaseModel`
- `Unresolved or out-of-scope base: ReportStep -> BaseModel`
- `Unresolved or out-of-scope base: RerankAdapter -> Protocol`
- `Unresolved or out-of-scope base: SensitiveDataFilter -> logging.Filter`
- `Unresolved or out-of-scope base: SessionRunner -> Protocol`
- `Unresolved or out-of-scope base: Settings -> BaseSettings`
- `Unresolved or out-of-scope base: SkillCreate -> BaseModel`
- `Unresolved or out-of-scope base: SkillLinks -> BaseModel`
- `Unresolved or out-of-scope base: SkillRepository -> Protocol`
- `Unresolved or out-of-scope base: SkillServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: SkillSummary -> BaseModel`
- `Unresolved or out-of-scope base: SkillUpdate -> BaseModel`
- `Unresolved or out-of-scope base: SubgraphEdge -> BaseModel`
- `Unresolved or out-of-scope base: SubgraphMeta -> BaseModel`
- `Unresolved or out-of-scope base: SubgraphNode -> BaseModel`
- `Unresolved or out-of-scope base: SubgraphResponse -> BaseModel`
- `Unresolved or out-of-scope base: Task -> BaseModel`
- `Unresolved or out-of-scope base: TaskCreate -> BaseModel`
- `Unresolved or out-of-scope base: TaskDependency -> BaseModel`
- `Unresolved or out-of-scope base: TaskDependencyCreate -> BaseModel`
- `Unresolved or out-of-scope base: TaskPriority -> StrEnum`
- `Unresolved or out-of-scope base: TaskRepository -> Protocol`
- `Unresolved or out-of-scope base: TaskServiceProtocol -> Protocol`
- `Unresolved or out-of-scope base: TaskState -> StrEnum`
- `Unresolved or out-of-scope base: TaskSummary -> BaseModel`
- `Unresolved or out-of-scope base: TaskUpdate -> BaseModel`
- `Unresolved or out-of-scope base: ToolCategory -> StrEnum`
- `Unresolved or out-of-scope base: ToolExecutor -> Protocol`
- `Unresolved or out-of-scope base: ToolMetadata -> BaseModel`
- `Unresolved or out-of-scope base: ToolParameter -> BaseModel`
- `Unresolved or out-of-scope base: UserCreate -> BaseModel`
- `Unresolved or out-of-scope base: UserRepository -> Protocol`
- `Unresolved or out-of-scope base: UserResponse -> BaseModel`
- `Unresolved or out-of-scope base: UserUpdate -> BaseModel`
- `Unresolved or out-of-scope base: WalkthroughReport -> BaseModel`
