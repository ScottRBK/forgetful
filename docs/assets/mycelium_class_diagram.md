# Mermaid class diagrams

Declared types and signatures; unknown types are `unknown`. Receivers are omitted.
Fields are associations, not lifetime ownership. Calls are static heuristic estimates.
Members and connections within each view are uncapped.
Parallel arrows are summarized.
Cross-diagram relationships are retained in the complete relationship list.

Included: 296 boxes. Calls without in-scope endpoints: 0.

## Test filtering

Mode: exclude.
Saved detector version: 2.
Test paths: `test_harness/runs`, `tests`.
Keep paths: none.
Calls removed by test filtering: 4561. Type relationships removed: 119.

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
- `tests/e2e/test_plan_external_ref_e2e.py`: 2 source occurrences (test-path).
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
- `tests/e2e_sqlite/test_cli_passthrough.py`: 13 source occurrences (test-path).
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
- `tests/e2e_sqlite/test_plan_external_ref_storage.py`: 2 source occurrences (test-path).
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
- `tests/plan_external_ref_cases.py`: 16 source occurrences (test-path).

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
    class c0013["alembic/versions/20261008_add_plan_external_ref.py"] {
        <<module>>
        +upgrade() None
        +downgrade() None
    }
    class c0014["Runtime"] {
        <<class>>
        +db_adapter: Any
        +repos: Type1
        +services: Services
        +registry: ToolRegistry
        +permitted_tools: set[str]
        +instance_scopes: frozenset[str]
        +event_bus: Type2
    }
    class c0015["Services"] {
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
    class c0016["app/bootstrap.py"] {
        <<module>>
        +get_embedding_adapter() unknown
        +get_reranker_adapter() unknown
        +check_first_run_models() unknown
        +create_db_adapter() unknown
        +create_repositories(Signature1)
        +build_runtime() Runtime
        +dispose_runtime(runtime: Runtime) None
    }
    class c0017["app/config/auth.py"] {
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
    class c0018["ConsoleFormatter"] {
        <<class>>
        +COLOURS: unknown
        +RESET: unknown
        +format(record: logging.LogRecord) str
    }
    class c0019["JSONFormatter"] {
        <<class>>
        +format(record: logging.LogRecord) str
    }
    class c0020["SensitiveDataFilter"] {
        <<class>>
        +SENSITIVE_PATTERNS: unknown
        +filter(record: logging.LogRecord) bool
        -_mask_value(value: unknown) unknown
    }
    class c0021["app/config/logging_config.py"] {
        <<module>>
        -_serialise_log_value(obj: unknown) unknown
        +configure_logging(log_level: str, log_format: str) logging.handlers.QueueListener
        +shutdown_logging() unknown
    }
    class c0022["Settings"] {
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
    class c0023["app/config/settings.py"] {
        <<module>>
        +parse_onnx_providers(value: Type5) Type3
    }
    class c0024["EventBus"] {
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
    class c0025["ConflictError"] {
        <<class>>
    }
    class c0026["CyclicDependencyError"] {
        <<class>>
    }
    class c0027["DependencyNotMetError"] {
        <<class>>
    }
    class c0028["InvalidStateTransitionError"] {
        <<class>>
    }
    class c0029["NotFoundError"] {
        <<class>>
    }
    class c0030["CacheEntry"] {
        <<class>>
        +user: User
        +expires_at: float
    }
    class c0031["TokenCache"] {
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
    class c0032["app/middleware/auth.py"] {
        <<module>>
        +get_user_from_auth(ctx: Context) User
        +get_user_from_request(request: Request, mcp: FastMCP) User
    }
    class c0033["app/middleware/logging_middleware.py"] {
        <<module>>
        +get_request_id() Type5
        +set_request_id(request_id: str) None
        +get_user_id() Type5
        +set_user_id(user_id: str) None
    }
    class c0034["ActionType"] {
        <<class>>
        +CREATED: unknown
        +UPDATED: unknown
        +DELETED: unknown
        +READ: unknown
        +QUERIED: unknown
    }
    class c0035["ActivityEvent"] {
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
    class c0036["ActivityListResponse"] {
        <<class>>
        +events: list[ActivityLogEntry]
        +total: int
        +limit: int
        +offset: int
        +model_config: unknown
    }
    class c0037["ActivityLogEntry"] {
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
    class c0038["ActorType"] {
        <<class>>
        +USER: unknown
        +SYSTEM: unknown
        +LLM_MAINTENANCE: unknown
    }
    class c0039["EntityType"] {
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
    class c0040["CodeArtifact"] {
        <<class>>
        +id: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0041["CodeArtifactCreate"] {
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
    class c0042["CodeArtifactSummary"] {
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
    class c0043["CodeArtifactUpdate"] {
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
    class c0044["Document"] {
        <<class>>
        +id: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0045["DocumentCreate"] {
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
    class c0046["DocumentSummary"] {
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
    class c0047["DocumentUpdate"] {
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
    class c0048["Entity"] {
        <<class>>
        +id: int
        +project_ids: Type15
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0049["EntityCreate"] {
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
    class c0050["EntityListResponse"] {
        <<class>>
        +entities: list[EntitySummary]
        +total: int
        +limit: int
        +offset: int
    }
    class c0051["EntityRelationship"] {
        <<class>>
        +id: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0052["EntityRelationshipCreate"] {
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
    class c0053["EntityRelationshipUpdate"] {
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
    class c0054["EntitySummary"] {
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
    class c0055["EntityType"] {
        <<class>>
        +ORGANIZATION: unknown
        +INDIVIDUAL: unknown
        +TEAM: unknown
        +DEVICE: unknown
        +SYSTEM: unknown
        +OTHER: unknown
        -_missing_(value: unknown) unknown
    }
    class c0056["EntityUpdate"] {
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
    class c0057["File"] {
        <<class>>
        +id: int
        +size_bytes: int
        +project_id: Type4
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0058["FileCreate"] {
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
    class c0059["FileSummary"] {
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
    class c0060["FileUpdate"] {
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
    class c0061["SubgraphEdge"] {
        <<class>>
        +id: str
        +source: str
        +target: str
        +type: Type17
        +data: Type14
    }
    class c0062["SubgraphMeta"] {
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
    class c0063["SubgraphNode"] {
        <<class>>
        +id: str
        +type: Type18
        +depth: int
        +label: str
        +data: Type1
    }
    class c0064["SubgraphResponse"] {
        <<class>>
        +nodes: list[SubgraphNode]
        +edges: list[SubgraphEdge]
        +meta: SubgraphMeta
    }
    class c0065["LinkedMemory"] {
        <<class>>
        +memory: Memory
        +link_source_id: int
        +model_config: unknown
    }
    class c0066["Memory"] {
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
    class c0067["MemoryCreate"] {
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
    class c0068["MemoryCreateResponse"] {
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
    class c0069["MemoryLinkRequest"] {
        <<class>>
        +memory_id: int
        +related_ids: list[int]
        +validate_related_ids(v: unknown, info: unknown) unknown
    }
    class c0070["MemoryListResponse"] {
        <<class>>
        +memories: list[Memory]
        +total: int
        +limit: int
        +offset: int
    }
    class c0071["MemoryQueryRequest"] {
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
    class c0072["MemoryQueryResult"] {
        <<class>>
        +query: str
        +primary_memories: list[Memory]
        +linked_memories: list[LinkedMemory]
        +scores: list[MemoryScore]
        +total_count: int
        +token_count: int
        +truncated: bool
    }
    class c0073["MemoryScore"] {
        <<class>>
        +memory_id: int
        +similarity: float
        +rerank_score: Type9
    }
    class c0074["MemorySummary"] {
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
    class c0075["MemoryUpdate"] {
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
    class c0076["ObsoleteMatch"] {
        <<class>>
        +id: int
        +title: str
        +similarity: float
        +obsolete_reason: Type5
        +superseded_by: Type4
        +obsoleted_at: Type19
        +project_ids: list[int]
    }
    class c0077["HealthStatus"] {
        <<class>>
        +status: str
        +timestamp: datetime
        +service: str
        +version: str
    }
    class c0078["Criterion"] {
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
    class c0079["CriterionCreate"] {
        <<class>>
        +description: str
        +strip_description(v: str) str
    }
    class c0080["CriterionUpdate"] {
        <<class>>
        +description: Type5
        +met: Type21
        +strip_description(v: Type5) Type5
    }
    class c0081["Plan"] {
        <<class>>
        +id: int
        +task_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0082["PlanCreate"] {
        <<class>>
        +title: str
        +project_id: int
        +goal: Type5
        +context: Type5
        +status: PlanStatus
        +external_ref: Type22
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
    class c0083["PlanStatus"] {
        <<class>>
        +DRAFT: unknown
        +ACTIVE: unknown
        +COMPLETED: unknown
        +ARCHIVED: unknown
    }
    class c0084["PlanSummary"] {
        <<class>>
        +id: int
        +title: str
        +project_id: int
        +status: PlanStatus
        +external_ref: Type5
        +task_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0085["PlanUpdate"] {
        <<class>>
        +title: Type5
        +goal: Type5
        +context: Type5
        +status: Type23
        +external_ref: Type22
        +source_repo: Type5
        +source_files: Type3
        +source_url: Type5
        +confidence: Type9
        +encoding_agent: Type5
        +encoding_version: Type5
        +agent_id: Type5
        +agent_version: Type5
        +agent_model: Type5
        +ignore_null_external_ref(data: Any) Any
        +validate_source_files(v: unknown) unknown
        +strip_title(v: Type5) Type5
        +strip_optional(v: Type5) Type5
    }
    class c0086["Task"] {
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
    class c0087["TaskCreate"] {
        <<class>>
        +title: str
        +plan_id: int
        +description: Type5
        +priority: TaskPriority
        +assigned_agent: Type5
        +criteria: Type24
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
    class c0088["TaskDependency"] {
        <<class>>
        +id: int
        +task_id: int
        +depends_on_task_id: int
        +created_at: datetime
        +model_config: unknown
    }
    class c0089["TaskDependencyCreate"] {
        <<class>>
        +task_id: int
        +depends_on_task_id: int
        +cannot_depend_on_self(v: int, info: unknown) int
    }
    class c0090["TaskPriority"] {
        <<class>>
        +P0: unknown
        +P1: unknown
        +P2: unknown
        +P3: unknown
    }
    class c0091["TaskState"] {
        <<class>>
        +TODO: unknown
        +DOING: unknown
        +WAITING: unknown
        +DONE: unknown
        +CANCELLED: unknown
    }
    class c0092["TaskSummary"] {
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
    class c0093["TaskUpdate"] {
        <<class>>
        +title: Type5
        +description: Type5
        +priority: Type25
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
    class c0094["Project"] {
        <<class>>
        +id: int
        +memory_count: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0095["ProjectCreate"] {
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
    class c0096["ProjectStatus"] {
        <<class>>
        +ACTIVE: unknown
        +ARCHIVED: unknown
        +COMPLETED: unknown
    }
    class c0097["ProjectSummary"] {
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
    class c0098["ProjectType"] {
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
    class c0099["ProjectUpdate"] {
        <<class>>
        +name: Type5
        +description: Type5
        +project_type: Type26
        +status: Type27
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
    class c0100["Skill"] {
        <<class>>
        +id: int
        +created_at: datetime
        +updated_at: datetime
        +model_config: unknown
    }
    class c0101["SkillCreate"] {
        <<class>>
        +name: str
        +description: str
        +content: str
        +license: Type5
        +compatibility: Type5
        +allowed_tools: Type3
        +metadata: Type28
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
    class c0102["SkillLinks"] {
        <<class>>
        +memory_ids: list[int]
        +file_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
    }
    class c0103["SkillSummary"] {
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
    class c0104["SkillUpdate"] {
        <<class>>
        +name: Type5
        +description: Type5
        +content: Type5
        +license: Type5
        +compatibility: Type5
        +allowed_tools: Type3
        +metadata: Type28
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
    class c0105["ToolCategory"] {
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
    class c0106["ToolDataDetailed"] {
        <<class>>
        +json_schema: Type1
        +further_examples: list[str]
    }
    class c0107["ToolImplementation"] {
        <<class>>
        +metadata: ToolMetadata
        +implementation: Type29
    }
    class c0108["ToolMetadata"] {
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
    class c0109["ToolParameter"] {
        <<class>>
        +name: str
        +type: str
        +description: str
        +required: bool
        +default: Type2
        +example: Type2
    }
    class c0110["User"] {
        <<class>>
        +id: UUID
        +updated_at: datetime
        +created_at: datetime
        +model_config: unknown
    }
    class c0111["UserCreate"] {
        <<class>>
        +external_id: str
        +name: str
        +email: str
        +idp_metadata: Type28
        +notes: Type5
    }
    class c0112["UserResponse"] {
        <<class>>
        +name: str
        +notes: Type5
        +updated_at: datetime
        +created_at: datetime
        +model_config: unknown
    }
    class c0113["UserUpdate"] {
        <<class>>
        +external_id: Type5
        +name: Type5
        +email: Type5
        +idp_metadata: Type28
        +notes: Type5
    }
    class c0114["ActivityRepository"] {
        <<class>>
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type31) int
    }
    class c0115["CodeArtifactRepository"] {
        <<class>>
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type33
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0116["DocumentRepository"] {
        <<class>>
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type34
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0117["EntityRepository"] {
        <<class>>
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type35
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
        +get_all_entity_memory_links(user_id: UUID) Type37
        +get_all_entity_project_links(user_id: UUID) Type37
        +get_all_entity_file_links(user_id: UUID) Type37
        +get_entity_memories(user_id: UUID, entity_id: int) Type38
        +get_memory_entities(user_id: UUID, memory_id: int) Type39
    }
    class c0118["ToolExecutor"] {
        <<class>>
        +execute(tool_name: str, arguments: Type1) Any
        +list_tools(category: Type5) Type1
        +tool_info(tool_name: str) Type1
        +close() None
    }
    class c0119["FileRepository"] {
        <<class>>
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type40
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
    }
    class c0120["MemoryRepository"] {
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
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type43
        +find_obsolete_matches(Signature17)
        +list_memories(Signature18)
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +get_subgraph_nodes(Signature19)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type46) list[int]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type46) None
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0121["ValidationResult"] {
        <<class>>
        +count_ok: bool
        +dimensions_ok: bool
        +search_ok: bool
        +all_passed: bool
    }
    class c0122["PlanRepository"] {
        <<class>>
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type47
        +list_plans(Signature22)
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0123["ProjectRepository"] {
        <<class>>
        +list_projects(Signature23)
        +get_project_by_id(user_id: UUID, project_id: int) Type48
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0124["SkillRepository"] {
        <<class>>
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type49
        +list_skills(Signature24)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature25)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type37
        +get_all_skill_code_artifact_links(user_id: UUID) Type37
        +get_all_skill_document_links(user_id: UUID) Type37
    }
    class c0125["TaskRepository"] {
        <<class>>
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type50
        +list_tasks(Signature26)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature27)
        +create_criterion(Signature28)
        +update_criterion(Signature29)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0126["UserRepository"] {
        <<class>>
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0127["AzureOpenAIAdapter"] {
        <<class>>
        -__init__() unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: unknown) list[float]
    }
    class c0128["EmbeddingsAdapter"] {
        <<class>>
        +generate_embedding(text: str) list[float]
    }
    class c0129["FastEmbeddingAdapter"] {
        <<class>>
        -__init__(providers: Type3) unknown
        +providers: unknown
        +model: unknown
        -_create_text_embedding(fastembed_kwargs: Type52) unknown
        +generate_embedding(text: str) list[float]
    }
    class c0130["GoogleEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +model: unknown
        +client: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0131["OllamaEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0132["OpenAIEmbeddingsAdapter"] {
        <<class>>
        -__init__() unknown
        +supports_dimensions: unknown
        +client: unknown
        +model: unknown
        +generate_embedding(text: str) list[float]
    }
    class c0133["app/repositories/embeddings/fastembed_offline.py"] {
        <<module>>
        +get_fastembed_kwargs() Type52
        +load_fastembed_model(Signature30)
    }
    class c0134["FastEmbedCrossEncoderAdapter"] {
        <<class>>
        -__init__(Signature31)
        +model_name: unknown
        +threads: unknown
        +cache_dir: unknown
        +providers: unknown
        -_model: unknown
        -_executor: unknown
        -_create_text_cross_encoder(Signature32)
        +rerank(query: str, documents: list[str]) Type54
        -_rerank_sync(query: str, documents: list[str]) Type55
        -__del__() unknown
    }
    class c0135["HttpRerankAdapter"] {
        <<class>>
        -__init__(model: Type5, url: Type5, api_key: Type5) unknown
        +model: unknown
        +url: unknown
        +api_key: unknown
        +rerank(query: str, documents: list[str]) Type54
    }
    class c0136["RerankAdapter"] {
        <<class>>
        +rerank(query: str, documents: list[str]) Type54
    }
    class c0137["app/repositories/helpers.py"] {
        <<module>>
        +build_embedding_text(memory_data: MemoryCreate) str
        +build_memory_text(memory: Memory) str
        +build_skill_embedding_text(skill_data: unknown) str
        +build_contextual_query(query: str, context: str) str
    }
    class c0138["PostgresActivityRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type31) int
    }
    class c0139["PostgresCodeArtifactRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type33
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0140["PostgresDocumentRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type34
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0141["PostgresEntityRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type35
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
        +get_all_entity_memory_links(user_id: UUID) Type37
        +get_all_entity_project_links(user_id: UUID) Type37
        +get_all_entity_file_links(user_id: UUID) Type37
        +get_memory_entities(user_id: UUID, memory_id: int) Type39
        +get_entity_memories(user_id: UUID, entity_id: int) Type38
    }
    class c0142["PostgresFileRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type40
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
        -_to_file_model(file_table: FilesTable) File
    }
    class c0143["PostgresMemoryRepository"] {
        <<class>>
        -__init__(Signature33)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +search(Signature13)
        +search_scored(Signature14)
        +semantic_search(Signature34)
        +semantic_search_scored(Signature35)
        +create_memory(user_id: UUID, memory: MemoryCreate) Memory
        +update_memory(Signature36)
        +get_memory_by_id(user_id: UUID, memory_id: int) Memory
        +get_memory_table_by_id(user_id: UUID, memory_id: int) MemoryTable
        +mark_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: Type4) bool
        +find_similar_memories(user_id: UUID, memory_id: int, max_links: int) list[Memory]
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type43
        +find_obsolete_matches(Signature17)
        +get_linked_memories(Signature16)
        +create_link(user_id: UUID, source_id: int, target_id: int) MemoryLinkTable
        +create_links_batch(user_id: UUID, source_id: int, target_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +list_memories(Signature18)
        -_link_projects(Signature37)
        -_link_code_artifacts(Signature38)
        -_link_documents(Signature39)
        -_link_files(Signature40)
        -_link_skills(Signature41)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type46) None
        -_build_targeted_rebuild_filter(Signature42)
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type46) list[int]
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        -_generate_embeddings(text: str) list[float]
        +get_subgraph_nodes(Signature43)
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0144["PostgresPlanRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type47
        +list_plans(Signature22)
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0145["PostgresDatabaseAdapter"] {
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
    class c0146["ActivityLogTable"] {
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
    class c0147["Base"] {
        <<class>>
    }
    class c0148["CodeArtifactsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +skills: Type60
        -__table_args__: unknown
    }
    class c0149["CriteriaTable"] {
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
        +task: Type61
        -__table_args__: unknown
    }
    class c0150["DocumentsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +skills: Type60
        -__table_args__: unknown
    }
    class c0151["EntitiesTable"] {
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
        +user: Type57
        +projects: Type62
        +memories: Type59
        +files: Type63
        +outgoing_relationships: Type64
        +incoming_relationships: Type64
        +project_ids: list[int]
        -__table_args__: unknown
    }
    class c0152["EntityRelationshipsTable"] {
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
        +source_entity: Type65
        +target_entity: Type65
        -__table_args__: unknown
    }
    class c0153["FilesTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +entities: Type66
        +skills: Type60
        -__table_args__: unknown
    }
    class c0154["MemoryLinkTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +source_id: Mapped[int]
        +target_id: Mapped[int]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0155["MemoryTable"] {
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
        +user: Type57
        +projects: Type62
        +code_artifacts: Type67
        +documents: Type68
        +files: Type63
        +skills: Type60
        +entities: Type66
        +linked_memories: Type59
        +linking_memories: Type59
        +linked_memory_ids: list[int]
        +project_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +entity_ids: list[int]
        -__table_args__: unknown
    }
    class c0156["PlansTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +goal: Mapped[str]
        +context: Mapped[str]
        +status: Mapped[str]
        +external_ref: Type69
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
        +user: Type57
        +project: Type58
        +tasks: Type70
        +task_count() int
        -__table_args__: unknown
    }
    class c0157["ProjectsTable"] {
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
        +user: Type57
        +memories: Type59
        +code_artifacts: Type67
        +documents: Type68
        +entities: Type66
        +files: Type63
        +skills: Type60
        +plans: Type71
        +memory_count() int
        -__table_args__: unknown
    }
    class c0158["SkillsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +files: Type63
        +code_artifacts: Type67
        +documents: Type68
        -__table_args__: unknown
    }
    class c0159["TaskDependenciesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[UUID]
        +task_id: Mapped[int]
        +depends_on_task_id: Mapped[int]
        +created_at: Mapped[datetime]
        +task: Type61
        -__table_args__: unknown
    }
    class c0160["TasksTable"] {
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
        +plan: Type72
        +criteria: Type73
        +dependency_ids: list[int]
        +depends_on: Type74
        -__table_args__: unknown
    }
    class c0161["UsersTable"] {
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
        +memories: Type59
        +projects: Type62
        +code_artifacts: Type67
        +documents: Type68
        +entities: Type66
        +files: Type63
        +skills: Type60
        +plans: Type71
    }
    class c0162["PostgresProjectRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +list_projects(Signature23)
        +get_project_by_id(user_id: UUID, project_id: int) Type48
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0163["PostgresSkillRepository"] {
        <<class>>
        -__init__(Signature33)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type49
        +list_skills(Signature24)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature25)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type37
        +get_all_skill_code_artifact_links(user_id: UUID) Type37
        +get_all_skill_document_links(user_id: UUID) Type37
        -_to_skill(row: SkillsTable) Skill
    }
    class c0164["PostgresTaskRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type50
        +list_tasks(Signature26)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature27)
        +create_criterion(Signature28)
        +update_criterion(Signature29)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0165["PostgresUserRepository"] {
        <<class>>
        -__init__(db_adapter: PostgresDatabaseAdapter) unknown
        +db_adapter: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0166["SqliteActivityRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +save_event(user_id: UUID, event: ActivityEvent) ActivityLogEntry
        +query_events(Signature2)
        +cleanup_expired(user_id: UUID, retention_days: int) int
        +count_events(user_id: UUID, entity_type: Type16, action: Type31) int
    }
    class c0167["SqliteCodeArtifactRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact_by_id(user_id: UUID, artifact_id: int) Type33
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0168["SqliteDocumentRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document_by_id(user_id: UUID, document_id: int) Type34
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0169["SqliteEntityRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_entity(user_id: UUID, entity_data: EntityCreate) Entity
        +get_entity_by_id(user_id: UUID, entity_id: int) Type35
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
        +get_all_entity_memory_links(user_id: UUID) Type37
        +get_all_entity_project_links(user_id: UUID) Type37
        +get_all_entity_file_links(user_id: UUID) Type37
        +get_memory_entities(user_id: UUID, memory_id: int) Type39
        +get_entity_memories(user_id: UUID, entity_id: int) Type38
    }
    class c0170["SqliteFileRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file_by_id(user_id: UUID, file_id: int) Type40
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
        -_to_file_model(file_table: FilesTable) File
    }
    class c0171["SqliteMemoryRepository"] {
        <<class>>
        -__init__(Signature44)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +search(Signature13)
        +search_scored(Signature14)
        +semantic_search(Signature34)
        +semantic_search_scored(Signature35)
        +create_memory(user_id: UUID, memory: MemoryCreate) Memory
        +update_memory(Signature36)
        +get_memory_by_id(user_id: UUID, memory_id: int) Memory
        +get_memory_table_by_id(user_id: UUID, memory_id: int) MemoryTable
        +mark_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: Type4) bool
        +find_similar_memories(user_id: UUID, memory_id: int, max_links: int) list[Memory]
        +find_similar_memories_scored(user_id: UUID, memory_id: int, max_links: int) Type43
        +find_obsolete_matches(Signature17)
        +get_linked_memories(Signature16)
        +create_link(user_id: UUID, source_id: int, target_id: int) MemoryLinkTable
        +create_links_batch(user_id: UUID, source_id: int, target_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, source_id: int, target_id: int) bool
        +list_memories(Signature18)
        -_link_projects(Signature37)
        -_link_code_artifacts(Signature38)
        -_link_documents(Signature39)
        -_link_files(Signature40)
        -_link_skills(Signature41)
        +count_all_memories() int
        +get_memories_for_reembedding(limit: int, offset: int) list[Memory]
        +reset_embedding_storage() None
        +bulk_update_embeddings(updates: Type46) None
        -_build_targeted_rebuild_filter(Signature42)
        +count_memories_for_targeted_rebuild(Signature20)
        +get_memories_for_targeted_rebuild(Signature21)
        +upsert_targeted_embeddings(user_id: UUID, updates: Type46) list[int]
        +validate_embedding_count() bool
        +validate_embedding_dimensions() bool
        +validate_search_works() bool
        -_generate_embeddings(text: str) list[float]
        +get_subgraph_nodes(Signature43)
        +record_memory_access(user_id: UUID, memory_ids: list[int], accessed_at: Type19) int
    }
    class c0172["SqlitePlanRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan_by_id(user_id: UUID, plan_id: int) Type47
        +list_plans(Signature22)
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Plan
        +delete_plan(user_id: UUID, plan_id: int) bool
    }
    class c0173["SqliteProjectRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +list_projects(Signature23)
        +get_project_by_id(user_id: UUID, project_id: int) Type48
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Project
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0174["SqliteSkillRepository"] {
        <<class>>
        -__init__(Signature45)
        +db_adapter: unknown
        +embedding_adapter: unknown
        +rerank_adapter: unknown
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +skill_name_exists(user_id: UUID, name: str) bool
        +get_skill_by_id(user_id: UUID, skill_id: int) Type49
        +list_skills(Signature24)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature25)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type37
        +get_all_skill_code_artifact_links(user_id: UUID) Type37
        +get_all_skill_document_links(user_id: UUID) Type37
        -_to_skill(skill_table: SkillsTable) Skill
    }
    class c0175["SqliteDatabaseAdapter"] {
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
    class c0176["app/repositories/sqlite/sqlite_adapter.py"] {
        <<module>>
        -_sqlite_connection_creator() unknown
    }
    class c0177["ActivityLogTable"] {
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
    class c0178["Base"] {
        <<class>>
    }
    class c0179["CodeArtifactsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +skills: Type60
        -__table_args__: unknown
    }
    class c0180["CriteriaTable"] {
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
        +task: Type61
        -__table_args__: unknown
    }
    class c0181["DocumentsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +skills: Type60
        -__table_args__: unknown
    }
    class c0182["EntitiesTable"] {
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
        +user: Type57
        +projects: Type62
        +memories: Type59
        +files: Type63
        +outgoing_relationships: Type64
        +incoming_relationships: Type64
        +project_ids: list[int]
        -__table_args__: unknown
    }
    class c0183["EntityRelationshipsTable"] {
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
        +source_entity: Type65
        +target_entity: Type65
        -__table_args__: unknown
    }
    class c0184["FilesTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +entities: Type66
        +skills: Type60
        -__table_args__: unknown
    }
    class c0185["MemoryLinkTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +source_id: Mapped[int]
        +target_id: Mapped[int]
        +created_at: Mapped[datetime]
        -__table_args__: unknown
    }
    class c0186["MemoryTable"] {
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
        +user: Type57
        +projects: Type62
        +code_artifacts: Type67
        +documents: Type68
        +files: Type63
        +skills: Type60
        +entities: Type66
        +linked_memories: Type59
        +linking_memories: Type59
        +linked_memory_ids: list[int]
        +project_ids: list[int]
        +code_artifact_ids: list[int]
        +document_ids: list[int]
        +file_ids: list[int]
        +skill_ids: list[int]
        +entity_ids: list[int]
        -__table_args__: unknown
    }
    class c0187["PlansTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +project_id: Mapped[int]
        +title: Mapped[str]
        +goal: Mapped[str]
        +context: Mapped[str]
        +status: Mapped[str]
        +external_ref: Type69
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
        +user: Type57
        +project: Type58
        +tasks: Type70
        +task_count() int
        -__table_args__: unknown
    }
    class c0188["ProjectsTable"] {
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
        +user: Type57
        +memories: Type59
        +code_artifacts: Type67
        +documents: Type68
        +entities: Type66
        +files: Type63
        +skills: Type60
        +plans: Type71
        +memory_count() int
        -__table_args__: unknown
    }
    class c0189["SkillsTable"] {
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
        +user: Type57
        +project: Type58
        +memories: Type59
        +files: Type63
        +code_artifacts: Type67
        +documents: Type68
        -__table_args__: unknown
    }
    class c0190["TaskDependenciesTable"] {
        <<class>>
        -__tablename__: unknown
        +id: Mapped[int]
        +user_id: Mapped[str]
        +task_id: Mapped[int]
        +depends_on_task_id: Mapped[int]
        +created_at: Mapped[datetime]
        +task: Type61
        -__table_args__: unknown
    }
    class c0191["TasksTable"] {
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
        +plan: Type72
        +criteria: Type73
        +dependency_ids: list[int]
        +depends_on: Type74
        -__table_args__: unknown
    }
    class c0192["UsersTable"] {
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
        +memories: Type59
        +projects: Type62
        +code_artifacts: Type67
        +documents: Type68
        +entities: Type66
        +files: Type63
        +skills: Type60
        +plans: Type71
    }
    class c0193["SqliteTaskRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task_by_id(user_id: UUID, task_id: int) Type50
        +list_tasks(Signature26)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Task
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task_state(Signature27)
        +create_criterion(Signature28)
        +update_criterion(Signature29)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +get_criteria_for_task(user_id: UUID, task_id: int) list[Criterion]
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) TaskDependency
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        +get_dependencies(user_id: UUID, task_id: int) list[int]
        +get_dependents(user_id: UUID, task_id: int) list[int]
    }
    class c0194["SqliteUserRepository"] {
        <<class>>
        -__init__(db_adapter: SqliteDatabaseAdapter) unknown
        +db_adapter: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_user_by_external_id(external_id: str) Type12
        +create_user(user: UserCreate) User
        +update_user(user_id: UUID, updated_user: UserUpdate) User
    }
    class c0195["app/routes/api/activity.py"] {
        <<module>>
        +parse_int_param(params: unknown, key: str, default: int) int
        +parse_datetime_param(params: unknown, key: str) Type19
        +register(mcp: FastMCP) unknown
    }
    class c0196["app/routes/api/auth.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0197["app/routes/api/code_artifacts.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0198["app/routes/api/documents.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0199["app/routes/api/entities.py"] {
        <<module>>
        +parse_int_param(params: Any, name: str, default: Type4) Type4
        +register(mcp: FastMCP) unknown
    }
    class c0200["app/routes/api/files.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0201["app/routes/api/graph.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0202["app/routes/api/health.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0203["app/routes/api/memories.py"] {
        <<module>>
        +parse_int_param(params: Any, name: str, default: Type4) Type4
        +register(mcp: FastMCP) unknown
    }
    class c0204["app/routes/api/plans.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0205["app/routes/api/projects.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0206["app/routes/api/skills.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0207["app/routes/api/tasks.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0208["app/routes/cli/auth_commands.py"] {
        <<module>>
        +upsert_env_var(env_file: Path, key: str, value: str) None
        -_oauth_client_factory(url: str, token_dir: Path) unknown
        -_plain_client_factory(url: str, _token: Type5) unknown
        -_has_cached_credentials(url: str, token_dir: Path) bool
        +login(server: str, env_file: Type75, token_dir: Type75, client_factory: unknown) int
        +status(server: Type5) int
        +logout(token_dir: Type75) int
    }
    class c0209["CliContext"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        +fastmcp: unknown
    }
    class c0210["_CliRuntime"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        +user_service: unknown
        +auth: unknown
    }
    class c0211["LocalExecutor"] {
        <<class>>
        -__init__(runtime: Runtime) unknown
        -_runtime: unknown
        -_ctx: unknown
        +create() Type76
        +execute(tool_name: str, arguments: Type1) Any
        +list_tools(category: Type5) Type1
        +tool_info(tool_name: str) Type1
        +close() None
    }
    class c0212["app/routes/cli/parser.py"] {
        <<module>>
        -_json_object(value: str) dict
        +build_parser() argparse.ArgumentParser
        -_build_executor(args: unknown) unknown
        -_run_tool_command(args: unknown) int
        +dispatch(argv: unknown, serve_runner: unknown, reembed_runner: unknown) unknown
        -_run_auth_command(args: unknown) int
    }
    class c0213["app/routes/cli/paths.py"] {
        <<module>>
        +config_dir() Path
        +user_env_file() Path
        +token_cache_dir() Path
    }
    class c0214["RemoteExecutor"] {
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
    class c0215["app/routes/cli/remote_executor.py"] {
        <<module>>
        +normalize_server_url(url: str) str
        -_default_client_factory(url: str, token: Type5) unknown
    }
    class c0216["app/routes/cli/render.py"] {
        <<module>>
        +to_jsonable(value: Any) Any
        +render_result(value: Any, as_json: bool) str
        +emit_error(message: str, as_json: bool) None
        +render_memory_lines(memories: list[dict]) str
        +render_memory_detail(memory: dict) str
        +render_project_lines(projects: list[dict]) str
    }
    class c0217["CliError"] {
        <<class>>
    }
    class c0218["app/routes/cli/verbs.py"] {
        <<module>>
        +resolve_project(executor: unknown, value: str) int
        +run(executor: unknown, args: unknown) Type77
        -_memory_search(executor: unknown, args: unknown) Type77
        -_memory_save(executor: unknown, args: unknown) Type77
        -_memory_get(executor: unknown, args: unknown) Type77
        -_memory_recent(executor: unknown, args: unknown) Type77
        -_project_list(executor: unknown) Type77
    }
    class c0219["app/routes/mcp/code_artifact_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0220["app/routes/mcp/document_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0221["app/routes/mcp/entity_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0222["app/routes/mcp/memory_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0223["app/routes/mcp/meta_tools.py"] {
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
    class c0224["app/routes/mcp/pagination.py"] {
        <<module>>
        +clamp_list_pagination(limit: int, offset: int) Type78
    }
    class c0225["app/routes/mcp/project_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0226["app/routes/mcp/scope_resolver.py"] {
        <<module>>
        +parse_scopes(scope_string: str) frozenset[str]
        +resolve_permitted_tools(scopes: frozenset[str], registry: ToolRegistry) set[str]
        +get_required_scope(tool_name: str, registry: ToolRegistry) str
        +get_effective_scopes(ctx: Context) Type79
        -_extract_token_scopes(ctx: Context) Type80
    }
    class c0227["app/routes/mcp/skill_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0228["CodeArtifactToolAdapters"] {
        <<class>>
        -__init__(code_artifact_service: CodeArtifactService, user_service: UserService) unknown
        +code_artifact_service: unknown
        +user_service: unknown
        +create_code_artifact(Signature46)
        +get_code_artifact(artifact_id: int, ctx: Context) CodeArtifact
        +list_code_artifacts(ctx: Context, project_id: Type4, language: Type5, tags: Type3) dict
        +update_code_artifact(Signature47)
        +delete_code_artifact(artifact_id: int, ctx: Context) dict
    }
    class c0229["DocumentToolAdapters"] {
        <<class>>
        -__init__(document_service: DocumentService, user_service: UserService) unknown
        +document_service: unknown
        +user_service: unknown
        +create_document(Signature48)
        +get_document(document_id: int, ctx: Context) Document
        +list_documents(ctx: Context, project_id: Type4, document_type: Type5, tags: Type3) dict
        +update_document(Signature49)
        +delete_document(document_id: int, ctx: Context) dict
    }
    class c0230["EntityToolAdapters"] {
        <<class>>
        -__init__(entity_service: EntityService, user_service: UserService) unknown
        +entity_service: unknown
        +user_service: unknown
        +create_entity(Signature50)
        +get_entity(entity_id: int, ctx: Context) Entity
        +list_entities(ctx: Context, project_ids: Type15, entity_type: Type5, tags: Type3) dict
        +search_entities(Signature51)
        +update_entity(Signature52)
        +delete_entity(entity_id: int, ctx: Context) dict
        +link_entity_to_memory(entity_id: int, memory_id: int, ctx: Context) dict
        +unlink_entity_from_memory(entity_id: int, memory_id: int, ctx: Context) dict
        +link_entity_to_project(entity_id: int, project_id: int, ctx: Context) dict
        +unlink_entity_from_project(entity_id: int, project_id: int, ctx: Context) dict
        +create_entity_relationship(Signature53)
        +get_entity_relationships(Signature54)
        +update_entity_relationship(Signature55)
        +delete_entity_relationship(relationship_id: int, ctx: Context) dict
        +get_entity_memories(entity_id: int, ctx: Context) dict
        +get_memory_entities(memory_id: int, ctx: Context) dict
    }
    class c0231["FileToolAdapters"] {
        <<class>>
        -__init__(file_service: unknown, user_service: UserService) unknown
        +file_service: unknown
        +user_service: unknown
        +create_file(Signature56)
        +get_file(file_id: int, ctx: Context) unknown
        +list_files(ctx: Context, project_id: Type4, mime_type: Type5, tags: Type3) dict
        +update_file(Signature57)
        +delete_file(file_id: int, ctx: Context) dict
    }
    class c0232["MemoryToolAdapters"] {
        <<class>>
        -__init__(memory_service: MemoryService, user_service: UserService) unknown
        +memory_service: unknown
        +user_service: unknown
        -_build_re_embedding_service() ReEmbeddingService
        -_validate_rebuild_scope(user_id: unknown, memory_ids: Type15, project_id: Type4) None
        +create_memory(Signature58)
        +query_memory(Signature59)
        +update_memory(Signature60)
        +link_memories(Signature61)
        +unlink_memories(Signature62)
        +get_memory(ctx: Context, memory_id: Type4, id: Type4, kwargs: unknown) Memory
        +mark_memory_obsolete(Signature63)
        +get_recent_memories(Signature64)
        +rebuild_embeddings(ctx: Context, memory_ids: Type15, project_id: Type4) Type1
    }
    class c0233["PlanToolAdapters"] {
        <<class>>
        -__init__(plan_service: unknown, user_service: unknown) unknown
        +plan_service: unknown
        +user_service: unknown
        +create_plan(Signature65)
        +update_plan(Signature66)
        +get_plan(plan_id: int, ctx: Context) unknown
        +list_plans(ctx: Context, project_id: Type4, status: Type5, external_ref: Type5) unknown
    }
    class c0234["ProjectToolAdapters"] {
        <<class>>
        -__init__(project_service: ProjectService, user_service: UserService) unknown
        +project_service: unknown
        +user_service: unknown
        +create_project(Signature67)
        +update_project(Signature68)
        +delete_project(project_id: int, ctx: Context) dict
        +list_projects(ctx: Context, status: Type5, repo_name: Type5, name: Type5) dict
        +get_project(project_id: int, ctx: Context) Project
    }
    class c0235["SkillToolAdapters"] {
        <<class>>
        -__init__(skill_service: unknown, user_service: UserService) unknown
        +skill_service: unknown
        +user_service: unknown
        +create_skill(Signature69)
        +get_skill(skill_id: int, ctx: Context) unknown
        +list_skills(Signature70)
        +update_skill(Signature71)
        +delete_skill(skill_id: int, ctx: Context) dict
        +search_skills(query: str, ctx: Context, k: int, project_id: Type4) dict
        +import_skill(Signature72)
        +export_skill(skill_id: int, ctx: Context) str
        +link_skill_to_memory(skill_id: int, memory_id: int, ctx: Context) dict
        +unlink_skill_from_memory(skill_id: int, memory_id: int, ctx: Context) dict
        +link_skill_to_file(skill_id: int, file_id: int, ctx: Context) dict
        +unlink_skill_from_file(skill_id: int, file_id: int, ctx: Context) dict
        +link_skill_to_code_artifact(skill_id: int, code_artifact_id: int, ctx: Context) dict
        +unlink_skill_from_code_artifact(Signature73)
        +link_skill_to_document(skill_id: int, document_id: int, ctx: Context) dict
        +unlink_skill_from_document(skill_id: int, document_id: int, ctx: Context) dict
        +get_skill_links(skill_id: int, ctx: Context) dict
    }
    class c0236["TaskToolAdapters"] {
        <<class>>
        -__init__(task_service: unknown, user_service: unknown) unknown
        +task_service: unknown
        +user_service: unknown
        +create_task(Signature74)
        +update_task(Signature75)
        +get_task(task_id: int, ctx: Context) unknown
        +query_tasks(Signature76)
        +claim_task(task_id: int, agent_id: str, version: int, ctx: Context) unknown
        +transition_task(task_id: int, state: str, version: int, ctx: Context) unknown
        +add_criterion(task_id: int, description: str, ctx: Context) unknown
        +verify_criterion(criterion_id: int, met: bool, ctx: Context) unknown
        +delete_criterion(criterion_id: int, ctx: Context) unknown
        +add_dependency(task_id: int, depends_on_task_id: int, ctx: Context) unknown
        +remove_dependency(task_id: int, depends_on_task_id: int, ctx: Context) unknown
    }
    class c0237["UserToolAdapters"] {
        <<class>>
        -__init__(user_service: UserService) unknown
        +user_service: unknown
        +get_current_user(ctx: Context) UserResponse
        +update_user_notes(user_notes: str, ctx: Context) UserResponse
    }
    class c0238["app/routes/mcp/tool_adapters.py"] {
        <<module>>
        -_coerce_int_id(val: Any, param_name: str) int
        -_coerce_int_ids(vals: Any, param_name: str) list[int]
        +create_user_adapters(user_service: UserService) Type1
        +create_memory_adapters(memory_service: MemoryService, user_service: UserService) Type1
        +create_project_adapters(Signature77)
        +create_code_artifact_adapters(Signature78)
        +create_document_adapters(Signature79)
        +create_entity_adapters(entity_service: EntityService, user_service: UserService) Type1
        +create_plan_adapters(plan_service: unknown, user_service: unknown) Type1
        +create_task_adapters(task_service: unknown, user_service: unknown) Type1
        +create_file_adapters(file_service: unknown, user_service: UserService) Type1
        +create_skill_adapters(skill_service: unknown, user_service: UserService) Type1
    }
    class c0239["app/routes/mcp/tool_metadata_registry.py"] {
        <<module>>
        +register_simplified_tool(Signature80)
        +register_user_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_memory_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_all_tools_metadata(Signature81)
        +register_project_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_code_artifact_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_document_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_entity_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_plan_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_task_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_file_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
        +register_skill_tools_metadata(registry: ToolRegistry, adapters: Type1) unknown
    }
    class c0240["ToolRegistry"] {
        <<class>>
        -__init__() unknown
        -_tools: Type83
        +register(Signature82)
        -_tools#91;name#93;: unknown
        +get_tool(name: str) Type84
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
    class c0241["app/routes/mcp/user_tools.py"] {
        <<module>>
        +register(mcp: FastMCP) unknown
    }
    class c0242["ActivityService"] {
        <<class>>
        -__init__(activity_repo: ActivityRepository) unknown
        +activity_repo: unknown
        +handle_event(event: ActivityEvent) None
        +get_activity(Signature83)
        +get_entity_history(Signature84)
        +count_activity(user_id: UUID, entity_type: Type16, action: Type31) int
        -_cleanup_if_configured(user_id: UUID) None
    }
    class c0243["BackupService"] {
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
    class c0244["CodeArtifactService"] {
        <<class>>
        -__init__(artifact_repo: CodeArtifactRepository, event_bus: Type85) unknown
        +artifact_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_code_artifact(user_id: UUID, artifact_data: CodeArtifactCreate) CodeArtifact
        +get_code_artifact(user_id: UUID, artifact_id: int) CodeArtifact
        +list_code_artifacts(Signature3)
        +update_code_artifact(Signature4)
        +delete_code_artifact(user_id: UUID, artifact_id: int) bool
    }
    class c0245["DocumentService"] {
        <<class>>
        -__init__(document_repo: DocumentRepository, event_bus: Type85) unknown
        +document_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_document(user_id: UUID, document_data: DocumentCreate) Document
        +get_document(user_id: UUID, document_id: int) Document
        +list_documents(Signature5)
        +update_document(Signature6)
        +delete_document(user_id: UUID, document_id: int) bool
    }
    class c0246["EntityService"] {
        <<class>>
        -__init__(entity_repo: EntityRepository, event_bus: Type85) unknown
        +entity_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature86)
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
        +get_all_entity_memory_links(user_id: UUID) Type37
        +get_all_entity_project_links(user_id: UUID) Type37
        +get_all_entity_file_links(user_id: UUID) Type37
        +get_entity_memories(user_id: UUID, entity_id: int) Type86
        +get_memory_entities(user_id: UUID, memory_id: int) Type87
    }
    class c0247["FileService"] {
        <<class>>
        -__init__(file_repo: FileRepository, event_bus: Type85) unknown
        +file_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        -_snapshot_without_data(file: File) dict
        +create_file(user_id: UUID, file_data: FileCreate) File
        +get_file(user_id: UUID, file_id: int) File
        +list_files(Signature12)
        +update_file(user_id: UUID, file_id: int, file_data: FileUpdate) File
        +delete_file(user_id: UUID, file_id: int) bool
    }
    class c0248["CodeArtifactServiceProtocol"] {
        <<class>>
        +get_code_artifact(user_id: UUID, artifact_id: int) Any
    }
    class c0249["DocumentServiceProtocol"] {
        <<class>>
        +get_document(user_id: UUID, document_id: int) Any
    }
    class c0250["FileServiceProtocol"] {
        <<class>>
        +get_file(user_id: UUID, file_id: int) Any
        +list_files(user_id: UUID, kwargs: unknown) Any
    }
    class c0251["GraphService"] {
        <<class>>
        -__init__(Signature87)
        +memory_repo: unknown
        +entity_repo: unknown
        +project_service: unknown
        +document_service: unknown
        +code_artifact_service: unknown
        +file_service: unknown
        +skill_service: unknown
        +plan_service: unknown
        +task_service: unknown
        +parse_node_id(node_id: str) Type95
        +get_subgraph(Signature88)
        -_validate_center_node(user_id: UUID, center_type: str, center_id: int) None
        -_fetch_node_data(Signature89)
        -_fetch_edges(Signature90)
    }
    class c0252["PlanServiceProtocol"] {
        <<class>>
        +get_plan(user_id: UUID, plan_id: int) Any
        +list_plans(user_id: UUID, kwargs: unknown) Any
    }
    class c0253["ProjectServiceProtocol"] {
        <<class>>
        +get_project(user_id: UUID, project_id: int) Any
    }
    class c0254["SkillServiceProtocol"] {
        <<class>>
        +get_skill(user_id: UUID, skill_id: int) Any
        +get_all_skill_file_links(user_id: UUID) Type37
        +get_all_skill_code_artifact_links(user_id: UUID) Type37
        +get_all_skill_document_links(user_id: UUID) Type37
    }
    class c0255["TaskServiceProtocol"] {
        <<class>>
        +get_task(user_id: UUID, task_id: int) Any
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) Any
    }
    class c0256["MemoryService"] {
        <<class>>
        -__init__(memory_repo: MemoryRepository, event_bus: Type85) unknown
        +memory_repo: unknown
        -_event_bus: unknown
        +register_access_tracking_handlers(event_bus: Type97) None
        +query_memory(user_id: UUID, memory_query: MemoryQueryRequest) MemoryQueryResult
        +create_memory(user_id: UUID, memory_data: MemoryCreate) Type98
        +update_memory(user_id: UUID, memory_id: int, updated_memory: MemoryUpdate) Type42
        +mark_memory_obsolete(Signature91)
        +get_memory(user_id: UUID, memory_id: int) Type42
        +find_obsolete_matches(user_id: UUID, memory_id: int) list[ObsoleteMatch]
        +list_memories(Signature18)
        +link_memories(user_id: UUID, memory_id: int, related_ids: list[int]) list[int]
        +unlink_memories(user_id: UUID, memory_id: int, target_id: int) bool
        -_fetch_linked_memories(Signature92)
        -_apply_token_budget(Signature93)
        -_count_memory_tokens(memory: Memory) int
        +truncate_memories_by_budget(Signature94)
        +handle_memory_access_event(event: ActivityEvent) None
        -_emit_event(Signature85)
    }
    class c0257["PlanService"] {
        <<class>>
        -__init__(plan_repo: PlanRepository, event_bus: Type85) unknown
        +plan_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_plan(user_id: UUID, plan_data: PlanCreate) Plan
        +get_plan(user_id: UUID, plan_id: int) Plan
        +list_plans(Signature22)
        +update_plan(user_id: UUID, plan_id: int, plan_data: PlanUpdate) Type47
        +delete_plan(user_id: UUID, plan_id: int) bool
        +check_plan_completion(user_id: UUID, plan_id: int) bool
    }
    class c0258["ProjectService"] {
        <<class>>
        -__init__(project_repo: ProjectRepository, event_bus: Type85) unknown
        +project_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +list_projects(Signature23)
        +get_project(user_id: UUID, project_id: int) Project
        +create_project(user_id: UUID, project_data: ProjectCreate) Project
        +update_project(user_id: UUID, project_id: int, project_data: ProjectUpdate) Type48
        +delete_project(user_id: UUID, project_id: int) bool
    }
    class c0259["ReEmbedResult"] {
        <<class>>
        +total_processed: int
        +total_memories: int
        +validation: Type101
    }
    class c0260["ReEmbeddingService"] {
        <<class>>
        -__init__(Signature95)
        +memory_repository: unknown
        +embedding_adapter: unknown
        +batch_size: unknown
        +re_embed_all(progress_callback: Type102) ReEmbedResult
        +rebuild_targeted(Signature96)
        -_record_unresolved_memory_ids(Signature97)
        -_recompute_auto_links(Signature98)
        +validate() ValidationResult
    }
    class c0261["TargetedRebuildResult"] {
        <<class>>
        +rebuilt_ids: list[int]
        +skipped_ids: list[int]
        +failed: list[dict]
    }
    class c0262["SkillService"] {
        <<class>>
        -__init__(skill_repo: SkillRepository, event_bus: Type85) unknown
        +skill_repo: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_skill(user_id: UUID, skill_data: SkillCreate) Skill
        +get_skill(user_id: UUID, skill_id: int) Skill
        +list_skills(Signature24)
        +update_skill(user_id: UUID, skill_id: int, skill_data: SkillUpdate) Skill
        +delete_skill(user_id: UUID, skill_id: int) bool
        +search_skills(user_id: UUID, query: str, k: int, project_id: Type4) list[SkillSummary]
        +import_skill(Signature99)
        +export_skill(user_id: UUID, skill_id: int) str
        +link_skill_to_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +unlink_skill_from_memory(user_id: UUID, skill_id: int, memory_id: int) dict
        +link_skill_to_file(user_id: UUID, skill_id: int, file_id: int) dict
        +unlink_skill_from_file(user_id: UUID, skill_id: int, file_id: int) dict
        +link_skill_to_code_artifact(user_id: UUID, skill_id: int, code_artifact_id: int) dict
        +unlink_skill_from_code_artifact(Signature25)
        +link_skill_to_document(user_id: UUID, skill_id: int, document_id: int) dict
        +unlink_skill_from_document(user_id: UUID, skill_id: int, document_id: int) dict
        +get_skill_links(user_id: UUID, skill_id: int) SkillLinks
        +get_all_skill_file_links(user_id: UUID) Type37
        +get_all_skill_code_artifact_links(user_id: UUID) Type37
        +get_all_skill_document_links(user_id: UUID) Type37
    }
    class c0263["app/services/skill_service.py"] {
        <<module>>
        -_quote_unquoted_frontmatter_scalars(raw: str) str
    }
    class c0264["TaskService"] {
        <<class>>
        -__init__(Signature100)
        +task_repo: unknown
        +plan_service: unknown
        -_event_bus: unknown
        -_emit_event(Signature85)
        +create_task(user_id: UUID, task_data: TaskCreate) Task
        +get_task(user_id: UUID, task_id: int) Task
        +list_tasks(Signature26)
        +list_tasks_for_user(user_id: UUID, plan_ids: Type15) list[TaskSummary]
        +update_task(user_id: UUID, task_id: int, task_data: TaskUpdate) Type50
        +delete_task(user_id: UUID, task_id: int) bool
        +transition_task(Signature101)
        +claim_task(user_id: UUID, task_id: int, agent_id: str, expected_version: int) Task
        +add_criterion(user_id: UUID, task_id: int, criterion_data: CriterionCreate) Criterion
        +update_criterion(Signature29)
        +delete_criterion(user_id: UUID, criterion_id: int) bool
        +add_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) unknown
        +remove_dependency(user_id: UUID, task_id: int, depends_on_task_id: int) bool
        -_validate_dependencies_met(user_id: UUID, task: Task) None
        -_validate_all_criteria_met(user_id: UUID, task: Task) None
        -_validate_no_cycle(user_id: UUID, task_id: int, new_dep_id: int) None
        -_validate_same_plan(Signature102)
        -_check_plan_auto_completion(user_id: UUID, plan_id: int) None
    }
    class c0265["UserService"] {
        <<class>>
        -__init__(user_repo: UserRepository) unknown
        +user_repo: unknown
        +get_user_by_id(user_id: UUID) Type12
        +get_or_create_user(user: UserCreate) Type12
        +update_user(user_update: UserUpdate) Type12
    }
    class c0266["app/utils/provenance.py"] {
        <<module>>
        +apply_provenance_defaults(data: unknown) unknown
        +apply_provenance_defaults_for_update(data: unknown) unknown
    }
    class c0267["app/utils/pydantic_helper.py"] {
        <<module>>
        +get_changed_fields(input_model: BaseModel, existing_model: BaseModel) Type103
        +filter_none_values(kwargs: unknown) unknown
    }
    class c0268["app/utils/repository_identity.py"] {
        <<module>>
        +repository_identity(value: str) Type104
    }
    class c0269["TokenCounter"] {
        <<class>>
        -__init__(model: str) unknown
        +encoding: unknown
        +count_tokens(text: str) int
    }
    class c0270["app/version.py"] {
        <<module>>
        +get_version() str
    }
    class c0271["debug/reranker-test.py"] {
        <<module>>
        +main() unknown
        +jina() unknown
        +fast_embed_rank() unknown
        +http_rank() unknown
    }
    class c0272["debug/sqlite_vec_poc.py"] {
        <<module>>
        +test_sqlite_vec_sync() unknown
        +test_sqlite_vec_async() unknown
    }
    class c0273["debug/test_google_embeddings.py"] {
        <<module>>
        +test_embeddings() unknown
    }
    class c0274["debug/test_mcp_connection.py"] {
        <<module>>
        +main() unknown
    }
    class c0275["debug/test_sqlite_init.py"] {
        <<module>>
        +test_sqlite_init() unknown
    }
    class c0276["main.py"] {
        <<module>>
        +lifespan(app: unknown) unknown
        +root(request: Request) JSONResponse
        -_run_reembed(args: unknown) unknown
        -_serve(transport: unknown, host: unknown, port: unknown) unknown
        -_legacy_launcher(argv: unknown) unknown
        +cli() unknown
    }
    class c0277["test_harness/__main__.py"] {
        <<module>>
        +config_from_argv(argv: list[str]) HarnessConfig
        -_print_summary(results: list[SkillRunResult], run_dir: Path) None
        -_run(config: HarnessConfig) int
        +main(argv: Type3) int
    }
    class c0278["HarnessConfig"] {
        <<class>>
        +model_config: unknown
        +agent_type: str
        +model: str
        +effort: Type5
        +surface: Type105
        +skills: list[str]
        +skill_timeout: float
        +skill_timeouts: Type106
        +skills_dir: Path
        +output_dir: Path
        +rebuild_image: bool
        -_only_cli_is_implemented(value: str) str
        -_subset_of_walkthrough_order(value: list[str]) list[str]
        +timeout_for(skill: str) float
    }
    class c0279["AgentContainer"] {
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
        +run_session(Signature103)
        -_exec(cmd: list[str], log_path: Type75) Type107
        +stop() None
    }
    class c0280["test_harness/container.py"] {
        <<module>>
        +build_container_env(server_url: str) Type108
        +exec_command(timeout: float, skill: str) list[str]
        +staged_mount(files: list[Path], container_dir: str, staged: list[Path]) Type109
        +provision_agent(agent_type: str, staged: list[Path], auth_path: Path) Type109
        +export_requirements() str
        +requirements_hash(requirements: str) str
        -_docker_client() unknown
        +ensure_image(rebuild: bool, log: unknown) None
        -_prepare_harness_mount(run_dir: Path) Path
    }
    class c0281["test_harness/docker/runner.py"] {
        <<module>>
        -_shell() unknown
        +health() None
        -_attach_debug_log(path: Path) None
        +run_session(skill_dir: Path) None
        +main() int
    }
    class c0282["test_harness/prompts.py"] {
        <<module>>
        +build_prompt(skill: str) str
    }
    class c0283["ReportIssue"] {
        <<class>>
        +model_config: unknown
        +severity: Type110
        +where: str
        +what: str
        +evidence: str
        -_normalize_severity: unknown
    }
    class c0284["ReportLoad"] {
        <<class>>
        +status: Type111
        +report: Type112
        +detail: str
    }
    class c0285["ReportStep"] {
        <<class>>
        +model_config: unknown
        +step: str
        +commands: list[str]
        +observed: str
        +verdict: Type113
        -_normalize_verdict: unknown
    }
    class c0286["WalkthroughReport"] {
        <<class>>
        +model_config: unknown
        +skill: str
        +verdict: Type114
        +steps: list[ReportStep]
        +issues: list[ReportIssue]
        -_normalize_verdict: unknown
    }
    class c0287["test_harness/report.py"] {
        <<module>>
        -_lowercase(value: Any) Any
        -_normalize_step_verdict(value: Any) Any
        -_normalize_report_verdict(value: Any) Any
        -_normalize_severity(value: Any) Any
        +report_contract_example() str
        +load_report(path: Path) ReportLoad
    }
    class c0292["HarnessInfraError"] {
        <<class>>
    }
    class c0293["ThrowawayForgetful"] {
        <<class>>
        -__init__(run_dir: Path, boot_timeout: float) unknown
        +run_dir: unknown
        +boot_timeout: unknown
        +port: Type4
        +process: Type115
        -_log_file: unknown
        +url: str
        +mcp_url: str
        -_child_env() Type108
        +start() None
        -_wait_until_healthy() None
        +stop() None
        +execute(tool_name: str, arguments: Type1) Any
        +seed_skills(skills_dir: Path, names: Iterable[str]) list[dict]
    }
    class c0294["test_harness/server.py"] {
        <<module>>
        -_plain_client_factory(url: str, token: Type5) unknown
        -_ephemeral_port() int
    }
    class c0295["SessionOutcome"] {
        <<class>>
        +kind: Type116
        +detail: str
    }
    class c0296["SessionRunner"] {
        <<class>>
        +run_session(Signature103)
    }
    class c0297["SkillRunResult"] {
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
    class c0298["Walkthrough"] {
        <<class>>
        -__init__(Signature104)
        +config: unknown
        +runner: unknown
        +server_url: unknown
        +run_dir: unknown
        +run() list[SkillRunResult]
        +run_skill(skill: str) SkillRunResult
        -_meta(result: SkillRunResult, started: float) Type1
        +write_summary(results: list[SkillRunResult]) None
    }
    class c0299["test_harness/walkthrough.py"] {
        <<module>>
        +prepare_workspace(skill_dir: Path, skill: str, skills_dir: Path) Path
        -_build_fixture_repo(root: Path) None
        +load_events(path: Path) Type117
        +scan_for_breaches(events: Type117) list[str]
    }
    c0002 ..> c0002 : 2 relationships (see list)
    c0002 ..> c0031 : run_migrations_online() calls get()
    c0002 ..> c0145 : run_async_migrations() calls dispose()
    c0002 ..> c0218 : run_migrations_online() calls run()
    c0003 ..> c0000 : 2 relationships (see list)
    c0003 ..> c0001 : 2 relationships (see list)
    c0003 ..> c0003 : 2 relationships (see list)
    c0005 ..> c0005 : upgrade() calls _get_user_id_type()
    c0007 ..> c0007 : upgrade() calls _get_user_id_type()
    c0008 ..> c0008 : 2 relationships (see list)
    c0009 ..> c0009 : 4 relationships (see list)
    c0010 ..> c0010 : 4 relationships (see list)
    c0014 --> c0015 : field services
    c0014 --> c0240 : field registry
    c0016 ..> c0014 : 3 relationships (see list)
    c0016 ..> c0015 : build_runtime() constructs Services
    c0016 ..> c0016 : 5 relationships (see list)
    c0016 ..> c0024 : 3 relationships (see list)
    c0016 ..> c0127 : get_embedding_adapter() constructs AzureOpenAIAdapter
    c0016 ..> c0129 : get_embedding_adapter() constructs FastEmbeddingAdapter
    c0016 ..> c0130 : get_embedding_adapter() constructs GoogleEmbeddingsAdapter
    c0016 ..> c0131 : get_embedding_adapter() constructs OllamaEmbeddingsAdapter
    c0016 ..> c0132 : get_embedding_adapter() constructs OpenAIEmbeddingsAdapter
    c0016 ..> c0134 : get_reranker_adapter() constructs FastEmbedCrossEncoderAdapter
    c0016 ..> c0135 : get_reranker_adapter() constructs HttpRerankAdapter
    c0016 ..> c0138 : create_repositories() constructs PostgresActivityRepository
    c0016 ..> c0139 : create_repositories() constructs PostgresCodeArtifactRepository
    c0016 ..> c0140 : create_repositories() constructs PostgresDocumentRepository
    c0016 ..> c0141 : create_repositories() constructs PostgresEntityRepository
    c0016 ..> c0142 : create_repositories() constructs PostgresFileRepository
    c0016 ..> c0143 : create_repositories() constructs PostgresMemoryRepository
    c0016 ..> c0144 : create_repositories() constructs PostgresPlanRepository
    c0016 ..> c0145 : 3 relationships (see list)
    c0016 ..> c0162 : create_repositories() constructs PostgresProjectRepository
    c0016 ..> c0163 : create_repositories() constructs PostgresSkillRepository
    c0016 ..> c0164 : create_repositories() constructs PostgresTaskRepository
    c0016 ..> c0165 : create_repositories() constructs PostgresUserRepository
    c0016 ..> c0166 : create_repositories() constructs SqliteActivityRepository
    c0016 ..> c0167 : create_repositories() constructs SqliteCodeArtifactRepository
    c0016 ..> c0168 : create_repositories() constructs SqliteDocumentRepository
    c0016 ..> c0169 : create_repositories() constructs SqliteEntityRepository
    c0016 ..> c0170 : create_repositories() constructs SqliteFileRepository
    c0016 ..> c0171 : create_repositories() constructs SqliteMemoryRepository
    c0016 ..> c0172 : create_repositories() constructs SqlitePlanRepository
    c0016 ..> c0173 : create_repositories() constructs SqliteProjectRepository
    c0016 ..> c0174 : create_repositories() constructs SqliteSkillRepository
    c0016 ..> c0175 : create_db_adapter() constructs SqliteDatabaseAdapter
    c0016 ..> c0193 : create_repositories() constructs SqliteTaskRepository
    c0016 ..> c0194 : create_repositories() constructs SqliteUserRepository
    c0016 ..> c0226 : 2 relationships (see list)
    c0016 ..> c0239 : build_runtime() calls register_all_tools_metadata()
    c0016 ..> c0240 : 2 relationships (see list)
    c0016 ..> c0242 : build_runtime() constructs ActivityService
    c0016 ..> c0244 : build_runtime() constructs CodeArtifactService
    c0016 ..> c0245 : build_runtime() constructs DocumentService
    c0016 ..> c0246 : build_runtime() constructs EntityService
    c0016 ..> c0247 : build_runtime() constructs FileService
    c0016 ..> c0251 : build_runtime() constructs GraphService
    c0016 ..> c0256 : 2 relationships (see list)
    c0016 ..> c0257 : build_runtime() constructs PlanService
    c0016 ..> c0258 : build_runtime() constructs ProjectService
    c0016 ..> c0262 : build_runtime() constructs SkillService
    c0016 ..> c0264 : build_runtime() constructs TaskService
    c0016 ..> c0265 : build_runtime() constructs UserService
    c0017 ..> c0017 : 7 relationships (see list)
    c0017 ..> c0031 : build_auth_provider() calls get()
    c0019 ..> c0031 : format() calls get()
    c0019 ..> c0033 : 2 relationships (see list)
    c0020 ..> c0020 : filter() calls _mask_value()
    c0021 ..> c0018 : configure_logging() constructs ConsoleFormatter
    c0021 ..> c0019 : configure_logging() constructs JSONFormatter
    c0021 ..> c0020 : configure_logging() constructs SensitiveDataFilter
    c0021 ..> c0024 : configure_logging() calls clear()
    c0021 ..> c0279 : 2 relationships (see list)
    c0022 ..> c0023 : 3 relationships (see list)
    c0024 ..> c0024 : 3 relationships (see list)
    c0024 ..> c0031 : 6 relationships (see list)
    c0024 ..> c0035 : 3 relationships (see list)
    c0024 ..> c0125 : emit() calls create_task()
    c0030 --> c0110 : field user
    c0031 ..> c0024 : clear() calls clear()
    c0031 --> c0030 : field _cache
    c0031 ..> c0030 : set() constructs CacheEntry
    c0031 ..> c0031 : 3 relationships (see list)
    c0031 ..> c0110 : 2 relationships (see list)
    c0032 ..> c0031 : 2 relationships (see list)
    c0032 ..> c0110 : 2 relationships (see list)
    c0032 ..> c0111 : 2 relationships (see list)
    c0032 ..> c0265 : 2 relationships (see list)
    c0033 ..> c0031 : 2 relationships (see list)
    c0035 --> c0034 : field action
    c0035 --> c0038 : field actor
    c0035 --> c0039 : field entity_type
    c0036 --> c0037 : field events
    c0037 --> c0034 : field action
    c0037 --> c0038 : field actor
    c0037 --> c0039 : field entity_type
    c0040 --|> c0041 : inherits
    c0044 --|> c0045 : inherits
    c0045 ..> c0031 : calculate_size_bytes() calls get()
    c0048 --|> c0049 : inherits
    c0049 --> c0055 : field entity_type
    c0050 --> c0054 : field entities
    c0051 --|> c0052 : inherits
    c0054 --> c0055 : field entity_type
    c0056 --> c0055 : field entity_type
    c0057 --|> c0058 : inherits
    c0064 --> c0061 : field edges
    c0064 --> c0062 : field meta
    c0064 --> c0063 : field nodes
    c0065 --> c0066 : field memory
    c0066 --|> c0067 : inherits
    c0068 --> c0074 : field similar_memories
    c0068 --> c0076 : field obsolete_matches
    c0070 --> c0066 : field memories
    c0072 --> c0065 : field linked_memories
    c0072 --> c0066 : field primary_memories
    c0072 --> c0073 : field scores
    c0081 --|> c0082 : inherits
    c0082 --> c0083 : field status
    c0084 --> c0083 : field status
    c0085 ..> c0031 : ignore_null_external_ref() calls get()
    c0085 --> c0083 : field status
    c0086 --> c0078 : field criteria
    c0086 --> c0090 : field priority
    c0086 --> c0091 : field state
    c0087 --> c0079 : field criteria
    c0087 --> c0090 : field priority
    c0089 ..> c0031 : cannot_depend_on_self() calls get()
    c0092 --> c0090 : field priority
    c0092 --> c0091 : field state
    c0093 --> c0090 : field priority
    c0094 --|> c0095 : inherits
    c0095 --> c0096 : field status
    c0095 --> c0098 : field project_type
    c0097 --> c0096 : field status
    c0097 --> c0098 : field project_type
    c0099 --> c0096 : field status
    c0099 --> c0098 : field project_type
    c0100 --|> c0101 : inherits
    c0106 --|> c0108 : inherits
    c0107 --> c0108 : field metadata
    c0108 ..> c0031 : _map_python_type_to_json_type() calls get()
    c0108 --> c0105 : field category
    c0108 ..> c0108 : 2 relationships (see list)
    c0108 --> c0109 : field parameters
    c0110 --|> c0111 : inherits
    c0114 ..> c0034 : 2 relationships (see list)
    c0114 ..> c0035 : type in save_event
    c0114 ..> c0037 : 2 relationships (see list)
    c0114 ..> c0038 : type in query_events
    c0114 ..> c0039 : 2 relationships (see list)
    c0115 ..> c0040 : 3 relationships (see list)
    c0115 ..> c0041 : type in create_code_artifact
    c0115 ..> c0042 : type in list_code_artifacts
    c0115 ..> c0043 : type in update_code_artifact
    c0116 ..> c0044 : 3 relationships (see list)
    c0116 ..> c0045 : type in create_document
    c0116 ..> c0046 : type in list_documents
    c0116 ..> c0047 : type in update_document
    c0117 ..> c0048 : 3 relationships (see list)
    c0117 ..> c0049 : type in create_entity
    c0117 ..> c0051 : 4 relationships (see list)
    c0117 ..> c0052 : type in create_entity_relationship
    c0117 ..> c0053 : type in update_entity_relationship
    c0117 ..> c0054 : 2 relationships (see list)
    c0117 ..> c0055 : 2 relationships (see list)
    c0117 ..> c0056 : type in update_entity
    c0119 ..> c0057 : 3 relationships (see list)
    c0119 ..> c0058 : type in create_file
    c0119 ..> c0059 : type in list_files
    c0119 ..> c0060 : type in update_file
    c0120 ..> c0066 : 12 relationships (see list)
    c0120 ..> c0067 : type in create_memory
    c0120 ..> c0073 : type in search_scored
    c0120 ..> c0075 : type in update_memory
    c0122 ..> c0081 : 3 relationships (see list)
    c0122 ..> c0082 : type in create_plan
    c0122 ..> c0083 : type in list_plans
    c0122 ..> c0084 : type in list_plans
    c0122 ..> c0085 : type in update_plan
    c0123 ..> c0094 : 3 relationships (see list)
    c0123 ..> c0095 : type in create_project
    c0123 ..> c0096 : type in list_projects
    c0123 ..> c0097 : type in list_projects
    c0123 ..> c0099 : type in update_project
    c0124 ..> c0100 : 3 relationships (see list)
    c0124 ..> c0101 : type in create_skill
    c0124 ..> c0102 : type in get_skill_links
    c0124 ..> c0103 : 2 relationships (see list)
    c0124 ..> c0104 : type in update_skill
    c0125 ..> c0078 : 3 relationships (see list)
    c0125 ..> c0079 : type in create_criterion
    c0125 ..> c0080 : type in update_criterion
    c0125 ..> c0086 : 4 relationships (see list)
    c0125 ..> c0087 : type in create_task
    c0125 ..> c0088 : type in add_dependency
    c0125 ..> c0090 : type in list_tasks
    c0125 ..> c0091 : 2 relationships (see list)
    c0125 ..> c0092 : 2 relationships (see list)
    c0125 ..> c0093 : type in update_task
    c0126 ..> c0110 : 4 relationships (see list)
    c0126 ..> c0111 : type in create_user
    c0126 ..> c0113 : type in update_user
    c0127 --|> c0128 : inherits
    c0129 --|> c0128 : inherits
    c0130 --|> c0128 : inherits
    c0131 --|> c0128 : inherits
    c0131 ..> c0129 : __init__() calls _create_text_embedding()
    c0131 ..> c0133 : __init__() calls load_fastembed_model()
    c0131 ..> c0211 : generate_embedding() calls create()
    c0132 --|> c0128 : inherits
    c0133 ..> c0133 : load_fastembed_model() calls get_fastembed_kwargs()
    c0134 ..> c0135 : _rerank_sync() calls rerank()
    c0135 ..> c0133 : __init__() calls load_fastembed_model()
    c0135 ..> c0134 : __init__() calls _create_text_cross_encoder()
    c0137 ..> c0066 : type in build_memory_text
    c0137 ..> c0067 : type in build_embedding_text
    c0138 ..> c0034 : 2 relationships (see list)
    c0138 ..> c0035 : type in save_event
    c0138 ..> c0037 : 4 relationships (see list)
    c0138 ..> c0038 : type in query_events
    c0138 ..> c0039 : 2 relationships (see list)
    c0138 ..> c0118 : 3 relationships (see list)
    c0138 ..> c0145 : 5 relationships (see list)
    c0138 ..> c0146 : save_event() constructs ActivityLogTable
    c0139 ..> c0029 : update_code_artifact() constructs NotFoundError
    c0139 ..> c0031 : update_code_artifact() calls get()
    c0139 ..> c0040 : 3 relationships (see list)
    c0139 ..> c0041 : type in create_code_artifact
    c0139 ..> c0042 : type in list_code_artifacts
    c0139 ..> c0043 : type in update_code_artifact
    c0139 ..> c0118 : 4 relationships (see list)
    c0139 ..> c0145 : 6 relationships (see list)
    c0139 ..> c0148 : create_code_artifact() constructs CodeArtifactsTable
    c0140 ..> c0029 : update_document() constructs NotFoundError
    c0140 ..> c0031 : update_document() calls get()
    c0140 ..> c0044 : 3 relationships (see list)
    c0140 ..> c0045 : type in create_document
    c0140 ..> c0046 : type in list_documents
    c0140 ..> c0047 : type in update_document
    c0140 ..> c0118 : 4 relationships (see list)
    c0140 ..> c0145 : 6 relationships (see list)
    c0140 ..> c0150 : create_document() constructs DocumentsTable
    c0141 ..> c0029 : 8 relationships (see list)
    c0141 ..> c0031 : update_entity() calls get()
    c0141 ..> c0048 : 3 relationships (see list)
    c0141 ..> c0049 : type in create_entity
    c0141 ..> c0051 : 8 relationships (see list)
    c0141 ..> c0052 : type in create_entity_relationship
    c0141 ..> c0053 : type in update_entity_relationship
    c0141 ..> c0054 : 2 relationships (see list)
    c0141 ..> c0055 : 2 relationships (see list)
    c0141 ..> c0056 : type in update_entity
    c0141 ..> c0118 : 20 relationships (see list)
    c0141 ..> c0145 : 21 relationships (see list)
    c0141 ..> c0151 : create_entity() constructs EntitiesTable
    c0141 ..> c0152 : create_entity_relationship() constructs EntityRelationshipsTable
    c0142 ..> c0029 : update_file() constructs NotFoundError
    c0142 ..> c0057 : 5 relationships (see list)
    c0142 ..> c0058 : type in create_file
    c0142 ..> c0059 : type in list_files
    c0142 ..> c0060 : type in update_file
    c0142 ..> c0118 : 4 relationships (see list)
    c0142 ..> c0142 : 3 relationships (see list)
    c0142 ..> c0145 : 6 relationships (see list)
    c0142 ..> c0153 : 2 relationships (see list)
    c0143 ..> c0024 : update_memory() calls clear()
    c0143 ..> c0029 : 11 relationships (see list)
    c0143 ..> c0031 : 2 relationships (see list)
    c0143 ..> c0066 : 14 relationships (see list)
    c0143 ..> c0067 : type in create_memory
    c0143 ..> c0073 : 2 relationships (see list)
    c0143 ..> c0075 : type in update_memory
    c0143 ..> c0118 : 25 relationships (see list)
    c0143 ..> c0128 : type in __init__
    c0143 ..> c0131 : _generate_embeddings() calls generate_embedding()
    c0143 ..> c0135 : search_scored() calls rerank()
    c0143 ..> c0136 : type in __init__
    c0143 ..> c0137 : 4 relationships (see list)
    c0143 ..> c0143 : 23 relationships (see list)
    c0143 ..> c0145 : 24 relationships (see list)
    c0143 ..> c0154 : 2 relationships (see list)
    c0143 ..> c0155 : 7 relationships (see list)
    c0144 ..> c0025 : 2 relationships (see list)
    c0144 ..> c0029 : update_plan() constructs NotFoundError
    c0144 ..> c0081 : 3 relationships (see list)
    c0144 ..> c0082 : type in create_plan
    c0144 ..> c0083 : type in list_plans
    c0144 ..> c0084 : type in list_plans
    c0144 ..> c0085 : type in update_plan
    c0144 ..> c0118 : 4 relationships (see list)
    c0144 ..> c0145 : 6 relationships (see list)
    c0144 ..> c0156 : create_plan() constructs PlansTable
    c0145 ..> c0003 : _run_migrations() calls upgrade()
    c0145 ..> c0118 : 4 relationships (see list)
    c0145 ..> c0145 : 2 relationships (see list)
    c0145 ..> c0175 : dispose() calls dispose()
    c0146 --|> c0147 : inherits
    c0148 --|> c0147 : inherits
    c0148 --> c0155 : field memories
    c0148 --> c0157 : field project
    c0148 --> c0158 : field skills
    c0148 --> c0161 : field user
    c0149 --|> c0147 : inherits
    c0149 --> c0160 : field task
    c0150 --|> c0147 : inherits
    c0150 --> c0155 : field memories
    c0150 --> c0157 : field project
    c0150 --> c0158 : field skills
    c0150 --> c0161 : field user
    c0151 --|> c0147 : inherits
    c0151 --> c0152 : 2 relationships (see list)
    c0151 --> c0153 : field files
    c0151 --> c0155 : field memories
    c0151 --> c0157 : field projects
    c0151 --> c0161 : field user
    c0152 --|> c0147 : inherits
    c0152 --> c0151 : 2 relationships (see list)
    c0153 --|> c0147 : inherits
    c0153 --> c0151 : field entities
    c0153 --> c0155 : field memories
    c0153 --> c0157 : field project
    c0153 --> c0158 : field skills
    c0153 --> c0161 : field user
    c0154 --|> c0147 : inherits
    c0155 --|> c0147 : inherits
    c0155 --> c0148 : field code_artifacts
    c0155 --> c0150 : field documents
    c0155 --> c0151 : field entities
    c0155 --> c0153 : field files
    c0155 --> c0157 : field projects
    c0155 --> c0158 : field skills
    c0155 --> c0161 : field user
    c0156 --|> c0147 : inherits
    c0156 --> c0157 : field project
    c0156 --> c0160 : field tasks
    c0156 --> c0161 : field user
    c0157 --|> c0147 : inherits
    c0157 --> c0148 : field code_artifacts
    c0157 --> c0150 : field documents
    c0157 --> c0151 : field entities
    c0157 --> c0153 : field files
    c0157 --> c0155 : field memories
    c0157 --> c0156 : field plans
    c0157 --> c0158 : field skills
    c0157 --> c0161 : field user
    c0158 --|> c0147 : inherits
    c0158 --> c0148 : field code_artifacts
    c0158 --> c0150 : field documents
    c0158 --> c0153 : field files
    c0158 --> c0155 : field memories
    c0158 --> c0157 : field project
    c0158 --> c0161 : field user
    c0159 --|> c0147 : inherits
    c0159 --> c0160 : field task
    c0160 --|> c0147 : inherits
    c0160 --> c0149 : field criteria
    c0160 --> c0156 : field plan
    c0160 --> c0159 : field depends_on
    c0161 --|> c0147 : inherits
    c0161 --> c0148 : field code_artifacts
    c0161 --> c0150 : field documents
    c0161 --> c0151 : field entities
    c0161 --> c0153 : field files
    c0161 --> c0155 : field memories
    c0161 --> c0156 : field plans
    c0161 --> c0157 : field projects
    c0161 --> c0158 : field skills
    c0162 ..> c0029 : update_project() constructs NotFoundError
    c0162 ..> c0094 : 3 relationships (see list)
    c0162 ..> c0095 : type in create_project
    c0162 ..> c0096 : type in list_projects
    c0162 ..> c0097 : type in list_projects
    c0162 ..> c0099 : type in update_project
    c0162 ..> c0118 : 4 relationships (see list)
    c0162 ..> c0145 : 6 relationships (see list)
    c0162 ..> c0157 : create_project() constructs ProjectsTable
    c0162 ..> c0268 : list_projects() calls repository_identity()
    c0163 ..> c0029 : 6 relationships (see list)
    c0163 ..> c0100 : 5 relationships (see list)
    c0163 ..> c0101 : type in create_skill
    c0163 ..> c0102 : 2 relationships (see list)
    c0163 ..> c0103 : 2 relationships (see list)
    c0163 ..> c0104 : type in update_skill
    c0163 ..> c0118 : 18 relationships (see list)
    c0163 ..> c0128 : type in __init__
    c0163 ..> c0131 : 3 relationships (see list)
    c0163 ..> c0135 : search_skills() calls rerank()
    c0163 ..> c0136 : type in __init__
    c0163 ..> c0137 : 2 relationships (see list)
    c0163 ..> c0145 : 20 relationships (see list)
    c0163 ..> c0158 : 2 relationships (see list)
    c0163 ..> c0163 : 3 relationships (see list)
    c0164 ..> c0025 : transition_task_state() constructs ConflictError
    c0164 ..> c0029 : 3 relationships (see list)
    c0164 ..> c0031 : update_criterion() calls get()
    c0164 ..> c0078 : 3 relationships (see list)
    c0164 ..> c0079 : type in create_criterion
    c0164 ..> c0080 : type in update_criterion
    c0164 ..> c0086 : 4 relationships (see list)
    c0164 ..> c0087 : type in create_task
    c0164 ..> c0088 : type in add_dependency
    c0164 ..> c0090 : 3 relationships (see list)
    c0164 ..> c0091 : 4 relationships (see list)
    c0164 ..> c0092 : 4 relationships (see list)
    c0164 ..> c0093 : type in update_task
    c0164 ..> c0118 : 12 relationships (see list)
    c0164 ..> c0145 : 16 relationships (see list)
    c0164 ..> c0149 : create_criterion() constructs CriteriaTable
    c0164 ..> c0159 : add_dependency() constructs TaskDependenciesTable
    c0164 ..> c0160 : create_task() constructs TasksTable
    c0164 ..> c0164 : update_task() calls get_task_by_id()
    c0165 ..> c0029 : update_user() constructs NotFoundError
    c0165 ..> c0110 : 4 relationships (see list)
    c0165 ..> c0111 : type in create_user
    c0165 ..> c0113 : type in update_user
    c0165 ..> c0118 : 3 relationships (see list)
    c0165 ..> c0145 : 5 relationships (see list)
    c0165 ..> c0161 : create_user() constructs UsersTable
    c0166 ..> c0034 : 2 relationships (see list)
    c0166 ..> c0035 : type in save_event
    c0166 ..> c0037 : 4 relationships (see list)
    c0166 ..> c0038 : type in query_events
    c0166 ..> c0039 : 2 relationships (see list)
    c0166 ..> c0118 : 3 relationships (see list)
    c0166 ..> c0175 : 5 relationships (see list)
    c0166 ..> c0177 : save_event() constructs ActivityLogTable
    c0167 ..> c0029 : update_code_artifact() constructs NotFoundError
    c0167 ..> c0031 : update_code_artifact() calls get()
    c0167 ..> c0040 : 3 relationships (see list)
    c0167 ..> c0041 : type in create_code_artifact
    c0167 ..> c0042 : type in list_code_artifacts
    c0167 ..> c0043 : type in update_code_artifact
    c0167 ..> c0118 : 4 relationships (see list)
    c0167 ..> c0175 : 6 relationships (see list)
    c0167 ..> c0179 : create_code_artifact() constructs CodeArtifactsTable
    c0168 ..> c0029 : update_document() constructs NotFoundError
    c0168 ..> c0031 : update_document() calls get()
    c0168 ..> c0044 : 3 relationships (see list)
    c0168 ..> c0045 : type in create_document
    c0168 ..> c0046 : type in list_documents
    c0168 ..> c0047 : type in update_document
    c0168 ..> c0118 : 4 relationships (see list)
    c0168 ..> c0175 : 6 relationships (see list)
    c0168 ..> c0181 : create_document() constructs DocumentsTable
    c0169 ..> c0029 : 8 relationships (see list)
    c0169 ..> c0031 : update_entity() calls get()
    c0169 ..> c0048 : 3 relationships (see list)
    c0169 ..> c0049 : type in create_entity
    c0169 ..> c0051 : 8 relationships (see list)
    c0169 ..> c0052 : type in create_entity_relationship
    c0169 ..> c0053 : type in update_entity_relationship
    c0169 ..> c0054 : 2 relationships (see list)
    c0169 ..> c0055 : 2 relationships (see list)
    c0169 ..> c0056 : type in update_entity
    c0169 ..> c0118 : 20 relationships (see list)
    c0169 ..> c0175 : 21 relationships (see list)
    c0169 ..> c0182 : create_entity() constructs EntitiesTable
    c0169 ..> c0183 : create_entity_relationship() constructs EntityRelationshipsTable
    c0170 ..> c0029 : update_file() constructs NotFoundError
    c0170 ..> c0057 : 5 relationships (see list)
    c0170 ..> c0058 : type in create_file
    c0170 ..> c0059 : type in list_files
    c0170 ..> c0060 : type in update_file
    c0170 ..> c0118 : 4 relationships (see list)
    c0170 ..> c0170 : 3 relationships (see list)
    c0170 ..> c0175 : 6 relationships (see list)
    c0170 ..> c0184 : 2 relationships (see list)
    c0171 ..> c0024 : update_memory() calls clear()
    c0171 ..> c0029 : 12 relationships (see list)
    c0171 ..> c0031 : 2 relationships (see list)
    c0171 ..> c0066 : 14 relationships (see list)
    c0171 ..> c0067 : type in create_memory
    c0171 ..> c0073 : 2 relationships (see list)
    c0171 ..> c0075 : type in update_memory
    c0171 ..> c0118 : 27 relationships (see list)
    c0171 ..> c0128 : type in __init__
    c0171 ..> c0131 : _generate_embeddings() calls generate_embedding()
    c0171 ..> c0135 : search_scored() calls rerank()
    c0171 ..> c0136 : type in __init__
    c0171 ..> c0137 : 4 relationships (see list)
    c0171 ..> c0171 : 21 relationships (see list)
    c0171 ..> c0175 : 24 relationships (see list)
    c0171 ..> c0185 : 2 relationships (see list)
    c0171 ..> c0186 : 7 relationships (see list)
    c0172 ..> c0025 : 2 relationships (see list)
    c0172 ..> c0029 : update_plan() constructs NotFoundError
    c0172 ..> c0081 : 3 relationships (see list)
    c0172 ..> c0082 : type in create_plan
    c0172 ..> c0083 : type in list_plans
    c0172 ..> c0084 : type in list_plans
    c0172 ..> c0085 : type in update_plan
    c0172 ..> c0118 : 4 relationships (see list)
    c0172 ..> c0175 : 6 relationships (see list)
    c0172 ..> c0187 : create_plan() constructs PlansTable
    c0173 ..> c0029 : update_project() constructs NotFoundError
    c0173 ..> c0094 : 3 relationships (see list)
    c0173 ..> c0095 : type in create_project
    c0173 ..> c0096 : type in list_projects
    c0173 ..> c0097 : type in list_projects
    c0173 ..> c0099 : type in update_project
    c0173 ..> c0118 : 4 relationships (see list)
    c0173 ..> c0175 : 6 relationships (see list)
    c0173 ..> c0188 : create_project() constructs ProjectsTable
    c0173 ..> c0268 : list_projects() calls repository_identity()
    c0174 ..> c0029 : 6 relationships (see list)
    c0174 ..> c0100 : 5 relationships (see list)
    c0174 ..> c0101 : type in create_skill
    c0174 ..> c0102 : 2 relationships (see list)
    c0174 ..> c0103 : 2 relationships (see list)
    c0174 ..> c0104 : type in update_skill
    c0174 ..> c0118 : 19 relationships (see list)
    c0174 ..> c0128 : type in __init__
    c0174 ..> c0131 : 3 relationships (see list)
    c0174 ..> c0135 : search_skills() calls rerank()
    c0174 ..> c0136 : type in __init__
    c0174 ..> c0137 : 2 relationships (see list)
    c0174 ..> c0174 : 3 relationships (see list)
    c0174 ..> c0175 : 20 relationships (see list)
    c0174 ..> c0189 : 2 relationships (see list)
    c0175 ..> c0003 : _run_migrations() calls upgrade()
    c0175 ..> c0118 : 3 relationships (see list)
    c0175 ..> c0145 : dispose() calls dispose()
    c0175 ..> c0175 : 2 relationships (see list)
    c0176 ..> c0118 : _sqlite_connection_creator() calls execute()
    c0177 --|> c0178 : inherits
    c0179 --|> c0178 : inherits
    c0179 --> c0186 : field memories
    c0179 --> c0188 : field project
    c0179 --> c0189 : field skills
    c0179 --> c0192 : field user
    c0180 --|> c0178 : inherits
    c0180 --> c0191 : field task
    c0181 --|> c0178 : inherits
    c0181 --> c0186 : field memories
    c0181 --> c0188 : field project
    c0181 --> c0189 : field skills
    c0181 --> c0192 : field user
    c0182 --|> c0178 : inherits
    c0182 --> c0183 : 2 relationships (see list)
    c0182 --> c0184 : field files
    c0182 --> c0186 : field memories
    c0182 --> c0188 : field projects
    c0182 --> c0192 : field user
    c0183 --|> c0178 : inherits
    c0183 --> c0182 : 2 relationships (see list)
    c0184 --|> c0178 : inherits
    c0184 --> c0182 : field entities
    c0184 --> c0186 : field memories
    c0184 --> c0188 : field project
    c0184 --> c0189 : field skills
    c0184 --> c0192 : field user
    c0185 --|> c0178 : inherits
    c0186 --|> c0178 : inherits
    c0186 --> c0179 : field code_artifacts
    c0186 --> c0181 : field documents
    c0186 --> c0182 : field entities
    c0186 --> c0184 : field files
    c0186 --> c0188 : field projects
    c0186 --> c0189 : field skills
    c0186 --> c0192 : field user
    c0187 --|> c0178 : inherits
    c0187 --> c0188 : field project
    c0187 --> c0191 : field tasks
    c0187 --> c0192 : field user
    c0188 --|> c0178 : inherits
    c0188 --> c0179 : field code_artifacts
    c0188 --> c0181 : field documents
    c0188 --> c0182 : field entities
    c0188 --> c0184 : field files
    c0188 --> c0186 : field memories
    c0188 --> c0187 : field plans
    c0188 --> c0189 : field skills
    c0188 --> c0192 : field user
    c0189 --|> c0178 : inherits
    c0189 --> c0179 : field code_artifacts
    c0189 --> c0181 : field documents
    c0189 --> c0184 : field files
    c0189 --> c0186 : field memories
    c0189 --> c0188 : field project
    c0189 --> c0192 : field user
    c0190 --|> c0178 : inherits
    c0190 --> c0191 : field task
    c0191 --|> c0178 : inherits
    c0191 --> c0180 : field criteria
    c0191 --> c0187 : field plan
    c0191 --> c0190 : field depends_on
    c0192 --|> c0178 : inherits
    c0192 --> c0179 : field code_artifacts
    c0192 --> c0181 : field documents
    c0192 --> c0182 : field entities
    c0192 --> c0184 : field files
    c0192 --> c0186 : field memories
    c0192 --> c0187 : field plans
    c0192 --> c0188 : field projects
    c0192 --> c0189 : field skills
    c0193 ..> c0025 : transition_task_state() constructs ConflictError
    c0193 ..> c0029 : 3 relationships (see list)
    c0193 ..> c0031 : update_criterion() calls get()
    c0193 ..> c0078 : 3 relationships (see list)
    c0193 ..> c0079 : type in create_criterion
    c0193 ..> c0080 : type in update_criterion
    c0193 ..> c0086 : 4 relationships (see list)
    c0193 ..> c0087 : type in create_task
    c0193 ..> c0088 : type in add_dependency
    c0193 ..> c0090 : 3 relationships (see list)
    c0193 ..> c0091 : 4 relationships (see list)
    c0193 ..> c0092 : 4 relationships (see list)
    c0193 ..> c0093 : type in update_task
    c0193 ..> c0118 : 12 relationships (see list)
    c0193 ..> c0175 : 16 relationships (see list)
    c0193 ..> c0180 : create_criterion() constructs CriteriaTable
    c0193 ..> c0190 : add_dependency() constructs TaskDependenciesTable
    c0193 ..> c0191 : create_task() constructs TasksTable
    c0193 ..> c0193 : update_task() calls get_task_by_id()
    c0194 ..> c0029 : update_user() constructs NotFoundError
    c0194 ..> c0110 : 4 relationships (see list)
    c0194 ..> c0111 : type in create_user
    c0194 ..> c0113 : type in update_user
    c0194 ..> c0118 : 3 relationships (see list)
    c0194 ..> c0175 : 5 relationships (see list)
    c0194 ..> c0192 : create_user() constructs UsersTable
    c0195 ..> c0031 : 2 relationships (see list)
    c0199 ..> c0031 : parse_int_param() calls get()
    c0203 ..> c0031 : parse_int_param() calls get()
    c0208 ..> c0031 : status() calls get()
    c0208 ..> c0208 : 2 relationships (see list)
    c0208 ..> c0213 : 4 relationships (see list)
    c0208 ..> c0214 : 3 relationships (see list)
    c0208 ..> c0215 : 2 relationships (see list)
    c0209 ..> c0014 : type in __init__
    c0209 ..> c0210 : __init__() constructs _CliRuntime
    c0210 ..> c0014 : type in __init__
    c0211 ..> c0014 : type in __init__
    c0211 ..> c0016 : 2 relationships (see list)
    c0211 ..> c0118 : execute() calls execute()
    c0211 ..> c0209 : __init__() constructs CliContext
    c0211 ..> c0223 : 3 relationships (see list)
    c0212 ..> c0031 : _build_executor() calls get()
    c0212 ..> c0118 : 4 relationships (see list)
    c0212 ..> c0208 : 3 relationships (see list)
    c0212 ..> c0211 : _build_executor() calls create()
    c0212 ..> c0212 : 4 relationships (see list)
    c0212 ..> c0214 : _build_executor() constructs RemoteExecutor
    c0212 ..> c0216 : 3 relationships (see list)
    c0212 ..> c0218 : 2 relationships (see list)
    c0212 ..> c0270 : build_parser() calls get_version()
    c0213 ..> c0213 : 2 relationships (see list)
    c0214 ..> c0118 : close() calls close()
    c0214 ..> c0214 : 3 relationships (see list)
    c0214 ..> c0215 : __init__() calls normalize_server_url()
    c0215 ..> c0213 : _default_client_factory() calls token_cache_dir()
    c0216 ..> c0031 : 3 relationships (see list)
    c0216 ..> c0216 : render_result() calls to_jsonable()
    c0218 ..> c0031 : 4 relationships (see list)
    c0218 ..> c0118 : 6 relationships (see list)
    c0218 ..> c0216 : 10 relationships (see list)
    c0218 ..> c0217 : resolve_project() constructs CliError
    c0218 ..> c0218 : 4 relationships (see list)
    c0223 ..> c0105 : build_discovery_payload() constructs ToolCategory
    c0223 ..> c0108 : 2 relationships (see list)
    c0223 ..> c0223 : 8 relationships (see list)
    c0223 ..> c0226 : 2 relationships (see list)
    c0223 ..> c0240 : 8 relationships (see list)
    c0226 ..> c0031 : 3 relationships (see list)
    c0226 ..> c0226 : 3 relationships (see list)
    c0226 ..> c0240 : 5 relationships (see list)
    c0228 ..> c0032 : 5 relationships (see list)
    c0228 ..> c0040 : 3 relationships (see list)
    c0228 ..> c0041 : create_code_artifact() constructs CodeArtifactCreate
    c0228 ..> c0043 : update_code_artifact() constructs CodeArtifactUpdate
    c0228 ..> c0244 : 6 relationships (see list)
    c0228 ..> c0265 : type in __init__
    c0228 ..> c0267 : update_code_artifact() calls filter_none_values()
    c0229 ..> c0032 : 5 relationships (see list)
    c0229 ..> c0044 : 3 relationships (see list)
    c0229 ..> c0045 : create_document() constructs DocumentCreate
    c0229 ..> c0047 : update_document() constructs DocumentUpdate
    c0229 ..> c0245 : 6 relationships (see list)
    c0229 ..> c0265 : type in __init__
    c0229 ..> c0267 : update_document() calls filter_none_values()
    c0230 ..> c0032 : 16 relationships (see list)
    c0230 ..> c0048 : 3 relationships (see list)
    c0230 ..> c0049 : create_entity() constructs EntityCreate
    c0230 ..> c0051 : 2 relationships (see list)
    c0230 ..> c0052 : create_entity_relationship() constructs EntityRelationshipCreate
    c0230 ..> c0053 : update_entity_relationship() constructs EntityRelationshipUpdate
    c0230 ..> c0055 : 2 relationships (see list)
    c0230 ..> c0056 : update_entity() constructs EntityUpdate
    c0230 ..> c0246 : 17 relationships (see list)
    c0230 ..> c0265 : type in __init__
    c0230 ..> c0267 : 3 relationships (see list)
    c0231 ..> c0032 : 5 relationships (see list)
    c0231 ..> c0058 : create_file() constructs FileCreate
    c0231 ..> c0060 : update_file() constructs FileUpdate
    c0231 ..> c0119 : 4 relationships (see list)
    c0231 ..> c0247 : get_file() calls get_file()
    c0231 ..> c0265 : type in __init__
    c0231 ..> c0267 : update_file() calls filter_none_values()
    c0232 ..> c0032 : 9 relationships (see list)
    c0232 ..> c0066 : 2 relationships (see list)
    c0232 ..> c0067 : create_memory() constructs MemoryCreate
    c0232 ..> c0068 : 2 relationships (see list)
    c0232 ..> c0071 : query_memory() constructs MemoryQueryRequest
    c0232 ..> c0072 : type in query_memory
    c0232 ..> c0075 : update_memory() constructs MemoryUpdate
    c0232 ..> c0120 : Relation118
    c0232 ..> c0224 : get_recent_memories() calls clamp_list_pagination()
    c0232 ..> c0232 : 2 relationships (see list)
    c0232 ..> c0238 : 13 relationships (see list)
    c0232 ..> c0256 : 10 relationships (see list)
    c0232 ..> c0260 : 3 relationships (see list)
    c0232 ..> c0265 : type in __init__
    c0232 ..> c0267 : update_memory() calls filter_none_values()
    c0233 ..> c0032 : 4 relationships (see list)
    c0233 ..> c0082 : create_plan() constructs PlanCreate
    c0233 ..> c0083 : 3 relationships (see list)
    c0233 ..> c0085 : update_plan() constructs PlanUpdate
    c0233 ..> c0122 : 3 relationships (see list)
    c0233 ..> c0252 : get_plan() calls get_plan()
    c0233 ..> c0267 : update_plan() calls filter_none_values()
    c0234 ..> c0032 : 5 relationships (see list)
    c0234 ..> c0094 : 3 relationships (see list)
    c0234 ..> c0095 : create_project() constructs ProjectCreate
    c0234 ..> c0096 : 3 relationships (see list)
    c0234 ..> c0098 : 2 relationships (see list)
    c0234 ..> c0099 : update_project() constructs ProjectUpdate
    c0234 ..> c0258 : 6 relationships (see list)
    c0234 ..> c0265 : type in __init__
    c0234 ..> c0267 : update_project() calls filter_none_values()
    c0235 ..> c0032 : 17 relationships (see list)
    c0235 ..> c0101 : create_skill() constructs SkillCreate
    c0235 ..> c0104 : update_skill() constructs SkillUpdate
    c0235 ..> c0124 : 14 relationships (see list)
    c0235 ..> c0254 : get_skill() calls get_skill()
    c0235 ..> c0262 : 2 relationships (see list)
    c0235 ..> c0265 : type in __init__
    c0235 ..> c0267 : update_skill() calls filter_none_values()
    c0236 ..> c0032 : 11 relationships (see list)
    c0236 ..> c0079 : 2 relationships (see list)
    c0236 ..> c0080 : verify_criterion() constructs CriterionUpdate
    c0236 ..> c0087 : create_task() constructs TaskCreate
    c0236 ..> c0090 : 3 relationships (see list)
    c0236 ..> c0091 : 2 relationships (see list)
    c0236 ..> c0093 : update_task() constructs TaskUpdate
    c0236 ..> c0125 : 7 relationships (see list)
    c0236 ..> c0255 : get_task() calls get_task()
    c0236 ..> c0264 : 3 relationships (see list)
    c0236 ..> c0267 : update_task() calls filter_none_values()
    c0237 ..> c0032 : 2 relationships (see list)
    c0237 ..> c0112 : 4 relationships (see list)
    c0237 ..> c0113 : update_user_notes() constructs UserUpdate
    c0237 ..> c0265 : 2 relationships (see list)
    c0238 ..> c0228 : Relation119
    c0238 ..> c0229 : create_document_adapters() constructs DocumentToolAdapters
    c0238 ..> c0230 : create_entity_adapters() constructs EntityToolAdapters
    c0238 ..> c0231 : create_file_adapters() constructs FileToolAdapters
    c0238 ..> c0232 : create_memory_adapters() constructs MemoryToolAdapters
    c0238 ..> c0233 : create_plan_adapters() constructs PlanToolAdapters
    c0238 ..> c0234 : create_project_adapters() constructs ProjectToolAdapters
    c0238 ..> c0235 : create_skill_adapters() constructs SkillToolAdapters
    c0238 ..> c0236 : create_task_adapters() constructs TaskToolAdapters
    c0238 ..> c0237 : create_user_adapters() constructs UserToolAdapters
    c0238 ..> c0238 : _coerce_int_ids() calls _coerce_int_id()
    c0238 ..> c0244 : type in create_code_artifact_adapters
    c0238 ..> c0245 : type in create_document_adapters
    c0238 ..> c0246 : type in create_entity_adapters
    c0238 ..> c0256 : type in create_memory_adapters
    c0238 ..> c0258 : type in create_project_adapters
    c0238 ..> c0265 : 8 relationships (see list)
    c0239 ..> c0031 : 11 relationships (see list)
    c0239 ..> c0105 : type in register_simplified_tool
    c0239 ..> c0109 : register_simplified_tool() constructs ToolParameter
    c0239 ..> c0238 : 10 relationships (see list)
    c0239 ..> c0239 : 20 relationships (see list)
    c0239 ..> c0240 : 14 relationships (see list)
    c0239 ..> c0256 : type in register_all_tools_metadata
    c0239 ..> c0265 : type in register_all_tools_metadata
    c0240 ..> c0031 : 3 relationships (see list)
    c0240 ..> c0105 : 3 relationships (see list)
    c0240 --> c0107 : field _tools
    c0240 ..> c0107 : 2 relationships (see list)
    c0240 ..> c0108 : 5 relationships (see list)
    c0240 ..> c0109 : type in register
    c0240 ..> c0240 : execute() calls get_tool()
    c0242 ..> c0034 : 2 relationships (see list)
    c0242 ..> c0035 : type in handle_event
    c0242 ..> c0036 : 3 relationships (see list)
    c0242 ..> c0038 : type in get_activity
    c0242 ..> c0039 : 3 relationships (see list)
    c0242 ..> c0114 : 5 relationships (see list)
    c0242 ..> c0242 : 2 relationships (see list)
    c0243 ..> c0218 : 2 relationships (see list)
    c0243 ..> c0243 : 4 relationships (see list)
    c0244 ..> c0024 : 2 relationships (see list)
    c0244 ..> c0029 : 2 relationships (see list)
    c0244 ..> c0034 : type in _emit_event
    c0244 ..> c0035 : _emit_event() constructs ActivityEvent
    c0244 ..> c0039 : type in _emit_event
    c0244 ..> c0040 : 3 relationships (see list)
    c0244 ..> c0041 : type in create_code_artifact
    c0244 ..> c0042 : type in list_code_artifacts
    c0244 ..> c0043 : type in update_code_artifact
    c0244 ..> c0115 : 8 relationships (see list)
    c0244 ..> c0244 : 5 relationships (see list)
    c0244 ..> c0266 : 2 relationships (see list)
    c0244 ..> c0267 : update_code_artifact() calls get_changed_fields()
    c0245 ..> c0024 : 2 relationships (see list)
    c0245 ..> c0029 : 2 relationships (see list)
    c0245 ..> c0034 : type in _emit_event
    c0245 ..> c0035 : _emit_event() constructs ActivityEvent
    c0245 ..> c0039 : type in _emit_event
    c0245 ..> c0044 : 3 relationships (see list)
    c0245 ..> c0045 : type in create_document
    c0245 ..> c0046 : type in list_documents
    c0245 ..> c0047 : type in update_document
    c0245 ..> c0116 : 8 relationships (see list)
    c0245 ..> c0245 : 5 relationships (see list)
    c0245 ..> c0266 : 2 relationships (see list)
    c0245 ..> c0267 : update_document() calls get_changed_fields()
    c0246 ..> c0024 : 2 relationships (see list)
    c0246 ..> c0029 : 2 relationships (see list)
    c0246 ..> c0034 : type in _emit_event
    c0246 ..> c0035 : _emit_event() constructs ActivityEvent
    c0246 ..> c0039 : type in _emit_event
    c0246 ..> c0048 : 3 relationships (see list)
    c0246 ..> c0049 : type in create_entity
    c0246 ..> c0051 : 4 relationships (see list)
    c0246 ..> c0052 : type in create_entity_relationship
    c0246 ..> c0053 : type in update_entity_relationship
    c0246 ..> c0054 : 2 relationships (see list)
    c0246 ..> c0055 : 2 relationships (see list)
    c0246 ..> c0056 : type in update_entity
    c0246 ..> c0117 : 23 relationships (see list)
    c0246 ..> c0246 : 13 relationships (see list)
    c0246 ..> c0266 : 4 relationships (see list)
    c0246 ..> c0267 : update_entity() calls get_changed_fields()
    c0247 ..> c0024 : 2 relationships (see list)
    c0247 ..> c0029 : 2 relationships (see list)
    c0247 ..> c0034 : type in _emit_event
    c0247 ..> c0035 : _emit_event() constructs ActivityEvent
    c0247 ..> c0039 : type in _emit_event
    c0247 ..> c0057 : 4 relationships (see list)
    c0247 ..> c0058 : type in create_file
    c0247 ..> c0059 : type in list_files
    c0247 ..> c0060 : type in update_file
    c0247 ..> c0119 : 8 relationships (see list)
    c0247 ..> c0247 : 9 relationships (see list)
    c0247 ..> c0266 : 2 relationships (see list)
    c0247 ..> c0267 : update_file() calls get_changed_fields()
    c0251 ..> c0029 : _validate_center_node() constructs NotFoundError
    c0251 ..> c0031 : _fetch_node_data() calls get()
    c0251 ..> c0061 : 2 relationships (see list)
    c0251 ..> c0062 : get_subgraph() constructs SubgraphMeta
    c0251 ..> c0063 : 2 relationships (see list)
    c0251 ..> c0064 : 2 relationships (see list)
    c0251 ..> c0117 : 7 relationships (see list)
    c0251 ..> c0120 : 5 relationships (see list)
    c0251 ..> c0248 : 4 relationships (see list)
    c0251 ..> c0249 : 4 relationships (see list)
    c0251 ..> c0250 : 4 relationships (see list)
    c0251 ..> c0251 : 4 relationships (see list)
    c0251 ..> c0252 : 4 relationships (see list)
    c0251 ..> c0253 : 3 relationships (see list)
    c0251 ..> c0254 : 7 relationships (see list)
    c0251 ..> c0255 : 3 relationships (see list)
    c0256 ..> c0024 : 4 relationships (see list)
    c0256 ..> c0031 : handle_memory_access_event() calls get()
    c0256 ..> c0034 : type in _emit_event
    c0256 ..> c0035 : 2 relationships (see list)
    c0256 ..> c0039 : type in _emit_event
    c0256 ..> c0065 : 3 relationships (see list)
    c0256 ..> c0066 : 8 relationships (see list)
    c0256 ..> c0067 : type in create_memory
    c0256 ..> c0071 : type in query_memory
    c0256 ..> c0072 : 2 relationships (see list)
    c0256 ..> c0074 : 2 relationships (see list)
    c0256 ..> c0075 : type in update_memory
    c0256 ..> c0076 : 2 relationships (see list)
    c0256 ..> c0120 : 17 relationships (see list)
    c0256 ..> c0256 : 12 relationships (see list)
    c0256 ..> c0266 : 2 relationships (see list)
    c0256 ..> c0267 : update_memory() calls get_changed_fields()
    c0256 ..> c0269 : 2 relationships (see list)
    c0257 ..> c0024 : 2 relationships (see list)
    c0257 ..> c0028 : update_plan() constructs InvalidStateTransitionError
    c0257 ..> c0029 : get_plan() constructs NotFoundError
    c0257 ..> c0031 : update_plan() calls get()
    c0257 ..> c0034 : type in _emit_event
    c0257 ..> c0035 : _emit_event() constructs ActivityEvent
    c0257 ..> c0039 : type in _emit_event
    c0257 ..> c0081 : 3 relationships (see list)
    c0257 ..> c0082 : type in create_plan
    c0257 ..> c0083 : 3 relationships (see list)
    c0257 ..> c0084 : type in list_plans
    c0257 ..> c0085 : type in update_plan
    c0257 ..> c0122 : 9 relationships (see list)
    c0257 ..> c0257 : 4 relationships (see list)
    c0257 ..> c0266 : 2 relationships (see list)
    c0257 ..> c0267 : update_plan() calls get_changed_fields()
    c0258 ..> c0024 : 2 relationships (see list)
    c0258 ..> c0029 : get_project() constructs NotFoundError
    c0258 ..> c0034 : type in _emit_event
    c0258 ..> c0035 : _emit_event() constructs ActivityEvent
    c0258 ..> c0039 : type in _emit_event
    c0258 ..> c0094 : 3 relationships (see list)
    c0258 ..> c0095 : type in create_project
    c0258 ..> c0096 : type in list_projects
    c0258 ..> c0097 : type in list_projects
    c0258 ..> c0099 : type in update_project
    c0258 ..> c0123 : 8 relationships (see list)
    c0258 ..> c0258 : 5 relationships (see list)
    c0258 ..> c0266 : 2 relationships (see list)
    c0258 ..> c0267 : update_project() calls get_changed_fields()
    c0259 --> c0121 : field validation
    c0260 ..> c0120 : 13 relationships (see list)
    c0260 ..> c0121 : 3 relationships (see list)
    c0260 ..> c0128 : type in __init__
    c0260 ..> c0131 : 2 relationships (see list)
    c0260 ..> c0137 : 2 relationships (see list)
    c0260 ..> c0259 : 2 relationships (see list)
    c0260 ..> c0260 : 3 relationships (see list)
    c0260 ..> c0261 : 4 relationships (see list)
    c0262 ..> c0024 : 2 relationships (see list)
    c0262 ..> c0029 : 2 relationships (see list)
    c0262 ..> c0031 : import_skill() calls get()
    c0262 ..> c0034 : type in _emit_event
    c0262 ..> c0035 : _emit_event() constructs ActivityEvent
    c0262 ..> c0039 : type in _emit_event
    c0262 ..> c0100 : 4 relationships (see list)
    c0262 ..> c0101 : 2 relationships (see list)
    c0262 ..> c0102 : type in get_skill_links
    c0262 ..> c0103 : 2 relationships (see list)
    c0262 ..> c0104 : type in update_skill
    c0262 ..> c0124 : 23 relationships (see list)
    c0262 ..> c0262 : 14 relationships (see list)
    c0262 ..> c0263 : import_skill() calls _quote_unquoted_frontmatter_scalars()
    c0262 ..> c0266 : 2 relationships (see list)
    c0262 ..> c0267 : update_skill() calls get_changed_fields()
    c0264 ..> c0024 : 2 relationships (see list)
    c0264 ..> c0025 : 2 relationships (see list)
    c0264 ..> c0026 : _validate_no_cycle() constructs CyclicDependencyError
    c0264 ..> c0027 : _validate_dependencies_met() constructs DependencyNotMetError
    c0264 ..> c0028 : 5 relationships (see list)
    c0264 ..> c0029 : 6 relationships (see list)
    c0264 ..> c0031 : transition_task() calls get()
    c0264 ..> c0034 : type in _emit_event
    c0264 ..> c0035 : _emit_event() constructs ActivityEvent
    c0264 ..> c0039 : type in _emit_event
    c0264 ..> c0078 : 2 relationships (see list)
    c0264 ..> c0079 : type in add_criterion
    c0264 ..> c0080 : type in update_criterion
    c0264 ..> c0083 : 2 relationships (see list)
    c0264 ..> c0085 : _check_plan_auto_completion() constructs PlanUpdate
    c0264 ..> c0086 : 7 relationships (see list)
    c0264 ..> c0087 : type in create_task
    c0264 ..> c0090 : type in list_tasks
    c0264 ..> c0091 : 7 relationships (see list)
    c0264 ..> c0092 : 2 relationships (see list)
    c0264 ..> c0093 : type in update_task
    c0264 ..> c0125 : 28 relationships (see list)
    c0264 ..> c0257 : 9 relationships (see list)
    c0264 ..> c0264 : 9 relationships (see list)
    c0264 ..> c0266 : 2 relationships (see list)
    c0264 ..> c0267 : update_task() calls get_changed_fields()
    c0265 ..> c0110 : 3 relationships (see list)
    c0265 ..> c0111 : 2 relationships (see list)
    c0265 ..> c0113 : 2 relationships (see list)
    c0265 ..> c0126 : 8 relationships (see list)
    c0265 ..> c0267 : 2 relationships (see list)
    c0271 ..> c0134 : fast_embed_rank() constructs FastEmbedCrossEncoderAdapter
    c0271 ..> c0135 : 3 relationships (see list)
    c0272 ..> c0118 : 4 relationships (see list)
    c0273 ..> c0130 : test_embeddings() constructs GoogleEmbeddingsAdapter
    c0273 ..> c0131 : test_embeddings() calls generate_embedding()
    c0274 ..> c0118 : main() calls list_tools()
    c0275 ..> c0118 : test_sqlite_init() calls execute()
    c0275 ..> c0175 : 5 relationships (see list)
    c0276 ..> c0016 : 5 relationships (see list)
    c0276 ..> c0021 : 2 relationships (see list)
    c0276 ..> c0031 : lifespan() constructs TokenCache
    c0276 ..> c0120 : 2 relationships (see list)
    c0276 ..> c0145 : 2 relationships (see list)
    c0276 ..> c0195 : 2 relationships (see list)
    c0276 ..> c0212 : cli() calls dispatch()
    c0276 ..> c0218 : 2 relationships (see list)
    c0276 ..> c0243 : 3 relationships (see list)
    c0276 ..> c0260 : 2 relationships (see list)
    c0276 ..> c0270 : _legacy_launcher() calls get_version()
    c0276 ..> c0276 : 3 relationships (see list)
    c0277 ..> c0277 : 3 relationships (see list)
    c0277 ..> c0278 : 3 relationships (see list)
    c0277 ..> c0279 : 3 relationships (see list)
    c0277 ..> c0280 : _run() calls ensure_image()
    c0277 ..> c0293 : 2 relationships (see list)
    c0277 ..> c0297 : type in _print_summary
    c0277 ..> c0298 : 4 relationships (see list)
    c0278 ..> c0031 : timeout_for() calls get()
    c0279 ..> c0024 : stop() calls clear()
    c0279 ..> c0031 : start() calls get()
    c0279 ..> c0118 : _exec() calls close()
    c0279 ..> c0278 : type in __init__
    c0279 ..> c0279 : 2 relationships (see list)
    c0279 ..> c0280 : 5 relationships (see list)
    c0279 ..> c0292 : 3 relationships (see list)
    c0279 ..> c0293 : stop() calls stop()
    c0279 ..> c0295 : 2 relationships (see list)
    c0279 ..> c0298 : start() calls run()
    c0280 ..> c0031 : ensure_image() calls get()
    c0280 ..> c0280 : 4 relationships (see list)
    c0280 ..> c0292 : 4 relationships (see list)
    c0280 ..> c0298 : 3 relationships (see list)
    c0281 ..> c0031 : 2 relationships (see list)
    c0281 ..> c0218 : main() calls run()
    c0281 ..> c0279 : health() calls health_check()
    c0281 ..> c0281 : 5 relationships (see list)
    c0282 ..> c0031 : build_prompt() calls get()
    c0282 ..> c0287 : build_prompt() calls report_contract_example()
    c0284 --> c0286 : field report
    c0286 --> c0283 : field issues
    c0286 --> c0285 : field steps
    c0287 ..> c0031 : _normalize_severity() calls get()
    c0287 ..> c0284 : 2 relationships (see list)
    c0287 ..> c0287 : 3 relationships (see list)
    c0293 ..> c0031 : _wait_until_healthy() calls get()
    c0293 ..> c0214 : 5 relationships (see list)
    c0293 ..> c0292 : 3 relationships (see list)
    c0293 ..> c0293 : 3 relationships (see list)
    c0293 ..> c0294 : start() calls _ephemeral_port()
    c0296 ..> c0295 : type in run_session
    c0297 --> c0284 : field report_load
    c0298 ..> c0031 : run_skill() calls get()
    c0298 ..> c0278 : 2 relationships (see list)
    c0298 ..> c0282 : run_skill() calls build_prompt()
    c0298 ..> c0287 : run_skill() calls load_report()
    c0298 ..> c0296 : 2 relationships (see list)
    c0298 ..> c0297 : 5 relationships (see list)
    c0298 ..> c0298 : 3 relationships (see list)
    c0298 ..> c0299 : 3 relationships (see list)
    c0299 ..> c0031 : scan_for_breaches() calls get()
    c0299 ..> c0299 : prepare_workspace() calls _build_fixture_repo()
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
- c0013: `alembic/versions/20261008_add_plan_external_ref.py` —
  `alembic/versions/20261008_add_plan_external_ref.py`:1
- c0014: `Runtime` — `app/bootstrap.py`:203
- c0015: `Services` — `app/bootstrap.py`:185
- c0016: `app/bootstrap.py` — `app/bootstrap.py`:1
- c0017: `app/config/auth.py` — `app/config/auth.py`:1
- c0018: `ConsoleFormatter` — `app/config/logging_config.py`:21
- c0019: `JSONFormatter` — `app/config/logging_config.py`:104
- c0020: `SensitiveDataFilter` — `app/config/logging_config.py`:56
- c0021: `app/config/logging_config.py` — `app/config/logging_config.py`:1
- c0022: `Settings` — `app/config/settings.py`:33
- c0023: `app/config/settings.py` — `app/config/settings.py`:1
- c0024: `EventBus` — `app/events/event_bus.py`:28
- c0025: `ConflictError` — `app/exceptions.py`:7
- c0026: `CyclicDependencyError` — `app/exceptions.py`:19
- c0027: `DependencyNotMetError` — `app/exceptions.py`:15
- c0028: `InvalidStateTransitionError` — `app/exceptions.py`:11
- c0029: `NotFoundError` — `app/exceptions.py`:4
- c0030: `CacheEntry` — `app/middleware/auth.py`:23
- c0031: `TokenCache` — `app/middleware/auth.py`:29
- c0032: `app/middleware/auth.py` — `app/middleware/auth.py`:1
- c0033: `app/middleware/logging_middleware.py` — `app/middleware/logging_middleware.py`:1
- c0034: `ActionType` — `app/models/activity_models.py`:33
- c0035: `ActivityEvent` — `app/models/activity_models.py`:49
- c0036: `ActivityListResponse` — `app/models/activity_models.py`:126
- c0037: `ActivityLogEntry` — `app/models/activity_models.py`:102
- c0038: `ActorType` — `app/models/activity_models.py`:42
- c0039: `EntityType` — `app/models/activity_models.py`:14
- c0040: `CodeArtifact` — `app/models/code_artifact_models.py`:222
- c0041: `CodeArtifactCreate` — `app/models/code_artifact_models.py`:13
- c0042: `CodeArtifactSummary` — `app/models/code_artifact_models.py`:253
- c0043: `CodeArtifactUpdate` — `app/models/code_artifact_models.py`:116
- c0044: `Document` — `app/models/document_models.py`:238
- c0045: `DocumentCreate` — `app/models/document_models.py`:13
- c0046: `DocumentSummary` — `app/models/document_models.py`:269
- c0047: `DocumentUpdate` — `app/models/document_models.py`:130
- c0048: `Entity` — `app/models/entity_models.py`:285
- c0049: `EntityCreate` — `app/models/entity_models.py`:34
- c0050: `EntityListResponse` — `app/models/entity_models.py`:365
- c0051: `EntityRelationship` — `app/models/entity_models.py`:537
- c0052: `EntityRelationshipCreate` — `app/models/entity_models.py`:391
- c0053: `EntityRelationshipUpdate` — `app/models/entity_models.py`:473
- c0054: `EntitySummary` — `app/models/entity_models.py`:316
- c0055: `EntityType` — `app/models/entity_models.py`:15
- c0056: `EntityUpdate` — `app/models/entity_models.py`:158
- c0057: `File` — `app/models/file_models.py`:233
- c0058: `FileCreate` — `app/models/file_models.py`:14
- c0059: `FileSummary` — `app/models/file_models.py`:263
- c0060: `FileUpdate` — `app/models/file_models.py`:124
- c0061: `SubgraphEdge` — `app/models/graph_models.py`:36
- c0062: `SubgraphMeta` — `app/models/graph_models.py`:81
- c0063: `SubgraphNode` — `app/models/graph_models.py`:10
- c0064: `SubgraphResponse` — `app/models/graph_models.py`:253
- c0065: `LinkedMemory` — `app/models/memory_models.py`:421
- c0066: `Memory` — `app/models/memory_models.py`:272
- c0067: `MemoryCreate` — `app/models/memory_models.py`:8
- c0068: `MemoryCreateResponse` — `app/models/memory_models.py`:340
- c0069: `MemoryLinkRequest` — `app/models/memory_models.py`:441
- c0070: `MemoryListResponse` — `app/models/memory_models.py`:363
- c0071: `MemoryQueryRequest` — `app/models/memory_models.py`:370
- c0072: `MemoryQueryResult` — `app/models/memory_models.py`:428
- c0073: `MemoryScore` — `app/models/memory_models.py`:317
- c0074: `MemorySummary` — `app/models/memory_models.py`:300
- c0075: `MemoryUpdate` — `app/models/memory_models.py`:143
- c0076: `ObsoleteMatch` — `app/models/memory_models.py`:328
- c0077: `HealthStatus` — `app/models/models.py`:8
- c0078: `Criterion` — `app/models/plan_models.py`:100
- c0079: `CriterionCreate` — `app/models/plan_models.py`:79
- c0080: `CriterionUpdate` — `app/models/plan_models.py`:89
- c0081: `Plan` — `app/models/plan_models.py`:240
- c0082: `PlanCreate` — `app/models/plan_models.py`:151
- c0083: `PlanStatus` — `app/models/plan_models.py`:28
- c0084: `PlanSummary` — `app/models/plan_models.py`:250
- c0085: `PlanUpdate` — `app/models/plan_models.py`:192
- c0086: `Task` — `app/models/plan_models.py`:343
- c0087: `TaskCreate` — `app/models/plan_models.py`:269
- c0088: `TaskDependency` — `app/models/plan_models.py`:131
- c0089: `TaskDependencyCreate` — `app/models/plan_models.py`:118
- c0090: `TaskPriority` — `app/models/plan_models.py`:45
- c0091: `TaskState` — `app/models/plan_models.py`:36
- c0092: `TaskSummary` — `app/models/plan_models.py`:373
- c0093: `TaskUpdate` — `app/models/plan_models.py`:308
- c0094: `Project` — `app/models/project_models.py`:223
- c0095: `ProjectCreate` — `app/models/project_models.py`:33
- c0096: `ProjectStatus` — `app/models/project_models.py`:26
- c0097: `ProjectSummary` — `app/models/project_models.py`:254
- c0098: `ProjectType` — `app/models/project_models.py`:9
- c0099: `ProjectUpdate` — `app/models/project_models.py`:129
- c0100: `Skill` — `app/models/skill_models.py`:202
- c0101: `SkillCreate` — `app/models/skill_models.py`:16
- c0102: `SkillLinks` — `app/models/skill_models.py`:234
- c0103: `SkillSummary` — `app/models/skill_models.py`:215
- c0104: `SkillUpdate` — `app/models/skill_models.py`:132
- c0105: `ToolCategory` — `app/models/tool_registry_models.py`:11
- c0106: `ToolDataDetailed` — `app/models/tool_registry_models.py`:147
- c0107: `ToolImplementation` — `app/models/tool_registry_models.py`:154
- c0108: `ToolMetadata` — `app/models/tool_registry_models.py`:34
- c0109: `ToolParameter` — `app/models/tool_registry_models.py`:25
- c0110: `User` — `app/models/user_models.py`:21
- c0111: `UserCreate` — `app/models/user_models.py`:7
- c0112: `UserResponse` — `app/models/user_models.py`:28
- c0113: `UserUpdate` — `app/models/user_models.py`:14
- c0114: `ActivityRepository` — `app/protocols/activity_protocol.py`:20
- c0115: `CodeArtifactRepository` — `app/protocols/code_artifact_protocol.py`:17
- c0116: `DocumentRepository` — `app/protocols/document_protocol.py`:17
- c0117: `EntityRepository` — `app/protocols/entity_protocol.py`:21
- c0118: `ToolExecutor` — `app/protocols/executor.py`:10
- c0119: `FileRepository` — `app/protocols/file_protocol.py`:17
- c0120: `MemoryRepository` — `app/protocols/memory_protocol.py`:21
- c0121: `ValidationResult` — `app/protocols/memory_protocol.py`:10
- c0122: `PlanRepository` — `app/protocols/plan_protocol.py`:13
- c0123: `ProjectRepository` — `app/protocols/project_protocol.py`:13
- c0124: `SkillRepository` — `app/protocols/skill_protocol.py`:18
- c0125: `TaskRepository` — `app/protocols/task_protocol.py`:18
- c0126: `UserRepository` — `app/protocols/user_protocol.py`:7
- c0127: `AzureOpenAIAdapter` — `app/repositories/embeddings/embedding_adapter.py`:71
- c0128: `EmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:16
- c0129: `FastEmbeddingAdapter` — `app/repositories/embeddings/embedding_adapter.py`:21
- c0130: `GoogleEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:106
- c0131: `OllamaEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:201
- c0132: `OpenAIEmbeddingsAdapter` — `app/repositories/embeddings/embedding_adapter.py`:143
- c0133: `app/repositories/embeddings/fastembed_offline.py` —
  `app/repositories/embeddings/fastembed_offline.py`:1
- c0134: `FastEmbedCrossEncoderAdapter` — `app/repositories/embeddings/reranker_adapter.py`:21
- c0135: `HttpRerankAdapter` — `app/repositories/embeddings/reranker_adapter.py`:111
- c0136: `RerankAdapter` — `app/repositories/embeddings/reranker_adapter.py`:13
- c0137: `app/repositories/helpers.py` — `app/repositories/helpers.py`:1
- c0138: `PostgresActivityRepository` — `app/repositories/postgres/activity_repository.py`:26
- c0139: `PostgresCodeArtifactRepository` —
  `app/repositories/postgres/code_artifact_repository.py`:22
- c0140: `PostgresDocumentRepository` — `app/repositories/postgres/document_repository.py`:22
- c0141: `PostgresEntityRepository` — `app/repositories/postgres/entity_repository.py`:34
- c0142: `PostgresFileRepository` — `app/repositories/postgres/file_repository.py`:18
- c0143: `PostgresMemoryRepository` — `app/repositories/postgres/memory_repository.py`:36
- c0144: `PostgresPlanRepository` — `app/repositories/postgres/plan_repository.py`:25
- c0145: `PostgresDatabaseAdapter` — `app/repositories/postgres/postgres_adapter.py`:18
- c0146: `ActivityLogTable` — `app/repositories/postgres/postgres_tables.py`:1177
- c0147: `Base` — `app/repositories/postgres/postgres_tables.py`:26
- c0148: `CodeArtifactsTable` — `app/repositories/postgres/postgres_tables.py`:519
- c0149: `CriteriaTable` — `app/repositories/postgres/postgres_tables.py`:1115
- c0150: `DocumentsTable` — `app/repositories/postgres/postgres_tables.py`:584
- c0151: `EntitiesTable` — `app/repositories/postgres/postgres_tables.py`:813
- c0152: `EntityRelationshipsTable` — `app/repositories/postgres/postgres_tables.py`:916
- c0153: `FilesTable` — `app/repositories/postgres/postgres_tables.py`:651
- c0154: `MemoryLinkTable` — `app/repositories/postgres/postgres_tables.py`:412
- c0155: `MemoryTable` — `app/repositories/postgres/postgres_tables.py`:178
- c0156: `PlansTable` — `app/repositories/postgres/postgres_tables.py`:982
- c0157: `ProjectsTable` — `app/repositories/postgres/postgres_tables.py`:433
- c0158: `SkillsTable` — `app/repositories/postgres/postgres_tables.py`:724
- c0159: `TaskDependenciesTable` — `app/repositories/postgres/postgres_tables.py`:1149
- c0160: `TasksTable` — `app/repositories/postgres/postgres_tables.py`:1042
- c0161: `UsersTable` — `app/repositories/postgres/postgres_tables.py`:112
- c0162: `PostgresProjectRepository` — `app/repositories/postgres/project_repository.py`:27
- c0163: `PostgresSkillRepository` — `app/repositories/postgres/skill_repository.py`:36
- c0164: `PostgresTaskRepository` — `app/repositories/postgres/task_repository.py`:33
- c0165: `PostgresUserRepository` — `app/repositories/postgres/user_repository.py`:15
- c0166: `SqliteActivityRepository` — `app/repositories/sqlite/activity_repository.py`:26
- c0167: `SqliteCodeArtifactRepository` — `app/repositories/sqlite/code_artifact_repository.py`:22
- c0168: `SqliteDocumentRepository` — `app/repositories/sqlite/document_repository.py`:22
- c0169: `SqliteEntityRepository` — `app/repositories/sqlite/entity_repository.py`:36
- c0170: `SqliteFileRepository` — `app/repositories/sqlite/file_repository.py`:18
- c0171: `SqliteMemoryRepository` — `app/repositories/sqlite/memory_repository.py`:37
- c0172: `SqlitePlanRepository` — `app/repositories/sqlite/plan_repository.py`:25
- c0173: `SqliteProjectRepository` — `app/repositories/sqlite/project_repository.py`:27
- c0174: `SqliteSkillRepository` — `app/repositories/sqlite/skill_repository.py`:37
- c0175: `SqliteDatabaseAdapter` — `app/repositories/sqlite/sqlite_adapter.py`:46
- c0176: `app/repositories/sqlite/sqlite_adapter.py` — `app/repositories/sqlite/sqlite_adapter.py`:1
- c0177: `ActivityLogTable` — `app/repositories/sqlite/sqlite_tables.py`:1184
- c0178: `Base` — `app/repositories/sqlite/sqlite_tables.py`:31
- c0179: `CodeArtifactsTable` — `app/repositories/sqlite/sqlite_tables.py`:524
- c0180: `CriteriaTable` — `app/repositories/sqlite/sqlite_tables.py`:1124
- c0181: `DocumentsTable` — `app/repositories/sqlite/sqlite_tables.py`:591
- c0182: `EntitiesTable` — `app/repositories/sqlite/sqlite_tables.py`:822
- c0183: `EntityRelationshipsTable` — `app/repositories/sqlite/sqlite_tables.py`:925
- c0184: `FilesTable` — `app/repositories/sqlite/sqlite_tables.py`:659
- c0185: `MemoryLinkTable` — `app/repositories/sqlite/sqlite_tables.py`:414
- c0186: `MemoryTable` — `app/repositories/sqlite/sqlite_tables.py`:177
- c0187: `PlansTable` — `app/repositories/sqlite/sqlite_tables.py`:994
- c0188: `ProjectsTable` — `app/repositories/sqlite/sqlite_tables.py`:437
- c0189: `SkillsTable` — `app/repositories/sqlite/sqlite_tables.py`:733
- c0190: `TaskDependenciesTable` — `app/repositories/sqlite/sqlite_tables.py`:1157
- c0191: `TasksTable` — `app/repositories/sqlite/sqlite_tables.py`:1052
- c0192: `UsersTable` — `app/repositories/sqlite/sqlite_tables.py`:124
- c0193: `SqliteTaskRepository` — `app/repositories/sqlite/task_repository.py`:33
- c0194: `SqliteUserRepository` — `app/repositories/sqlite/user_repository.py`:15
- c0195: `app/routes/api/activity.py` — `app/routes/api/activity.py`:1
- c0196: `app/routes/api/auth.py` — `app/routes/api/auth.py`:1
- c0197: `app/routes/api/code_artifacts.py` — `app/routes/api/code_artifacts.py`:1
- c0198: `app/routes/api/documents.py` — `app/routes/api/documents.py`:1
- c0199: `app/routes/api/entities.py` — `app/routes/api/entities.py`:1
- c0200: `app/routes/api/files.py` — `app/routes/api/files.py`:1
- c0201: `app/routes/api/graph.py` — `app/routes/api/graph.py`:1
- c0202: `app/routes/api/health.py` — `app/routes/api/health.py`:1
- c0203: `app/routes/api/memories.py` — `app/routes/api/memories.py`:1
- c0204: `app/routes/api/plans.py` — `app/routes/api/plans.py`:1
- c0205: `app/routes/api/projects.py` — `app/routes/api/projects.py`:1
- c0206: `app/routes/api/skills.py` — `app/routes/api/skills.py`:1
- c0207: `app/routes/api/tasks.py` — `app/routes/api/tasks.py`:1
- c0208: `app/routes/cli/auth_commands.py` — `app/routes/cli/auth_commands.py`:1
- c0209: `CliContext` — `app/routes/cli/context.py`:19
- c0210: `_CliRuntime` — `app/routes/cli/context.py`:11
- c0211: `LocalExecutor` — `app/routes/cli/local_executor.py`:18
- c0212: `app/routes/cli/parser.py` — `app/routes/cli/parser.py`:1
- c0213: `app/routes/cli/paths.py` — `app/routes/cli/paths.py`:1
- c0214: `RemoteExecutor` — `app/routes/cli/remote_executor.py`:67
- c0215: `app/routes/cli/remote_executor.py` — `app/routes/cli/remote_executor.py`:1
- c0216: `app/routes/cli/render.py` — `app/routes/cli/render.py`:1
- c0217: `CliError` — `app/routes/cli/verbs.py`:20
- c0218: `app/routes/cli/verbs.py` — `app/routes/cli/verbs.py`:1
- c0219: `app/routes/mcp/code_artifact_tools.py` — `app/routes/mcp/code_artifact_tools.py`:1
- c0220: `app/routes/mcp/document_tools.py` — `app/routes/mcp/document_tools.py`:1
- c0221: `app/routes/mcp/entity_tools.py` — `app/routes/mcp/entity_tools.py`:1
- c0222: `app/routes/mcp/memory_tools.py` — `app/routes/mcp/memory_tools.py`:1
- c0223: `app/routes/mcp/meta_tools.py` — `app/routes/mcp/meta_tools.py`:1
- c0224: `app/routes/mcp/pagination.py` — `app/routes/mcp/pagination.py`:1
- c0225: `app/routes/mcp/project_tools.py` — `app/routes/mcp/project_tools.py`:1
- c0226: `app/routes/mcp/scope_resolver.py` — `app/routes/mcp/scope_resolver.py`:1
- c0227: `app/routes/mcp/skill_tools.py` — `app/routes/mcp/skill_tools.py`:1
- c0228: `CodeArtifactToolAdapters` — `app/routes/mcp/tool_adapters.py`:1039
- c0229: `DocumentToolAdapters` — `app/routes/mcp/tool_adapters.py`:1206
- c0230: `EntityToolAdapters` — `app/routes/mcp/tool_adapters.py`:1375
- c0231: `FileToolAdapters` — `app/routes/mcp/tool_adapters.py`:2142
- c0232: `MemoryToolAdapters` — `app/routes/mcp/tool_adapters.py`:145
- c0233: `PlanToolAdapters` — `app/routes/mcp/tool_adapters.py`:1792
- c0234: `ProjectToolAdapters` — `app/routes/mcp/tool_adapters.py`:861
- c0235: `SkillToolAdapters` — `app/routes/mcp/tool_adapters.py`:2309
- c0236: `TaskToolAdapters` — `app/routes/mcp/tool_adapters.py`:1919
- c0237: `UserToolAdapters` — `app/routes/mcp/tool_adapters.py`:102
- c0238: `app/routes/mcp/tool_adapters.py` — `app/routes/mcp/tool_adapters.py`:1
- c0239: `app/routes/mcp/tool_metadata_registry.py` — `app/routes/mcp/tool_metadata_registry.py`:1
- c0240: `ToolRegistry` — `app/routes/mcp/tool_registry.py`:19
- c0241: `app/routes/mcp/user_tools.py` — `app/routes/mcp/user_tools.py`:1
- c0242: `ActivityService` — `app/services/activity_service.py`:24
- c0243: `BackupService` — `app/services/backup_service.py`:16
- c0244: `CodeArtifactService` — `app/services/code_artifact_service.py`:40
- c0245: `DocumentService` — `app/services/document_service.py`:40
- c0246: `EntityService` — `app/services/entity_service.py`:47
- c0247: `FileService` — `app/services/file_service.py`:40
- c0248: `CodeArtifactServiceProtocol` — `app/services/graph_service.py`:41
- c0249: `DocumentServiceProtocol` — `app/services/graph_service.py`:36
- c0250: `FileServiceProtocol` — `app/services/graph_service.py`:46
- c0251: `GraphService` — `app/services/graph_service.py`:73
- c0252: `PlanServiceProtocol` — `app/services/graph_service.py`:60
- c0253: `ProjectServiceProtocol` — `app/services/graph_service.py`:31
- c0254: `SkillServiceProtocol` — `app/services/graph_service.py`:52
- c0255: `TaskServiceProtocol` — `app/services/graph_service.py`:66
- c0256: `MemoryService` — `app/services/memory_service.py`:42
- c0257: `PlanService` — `app/services/plan_service.py`:37
- c0258: `ProjectService` — `app/services/project_service.py`:33
- c0259: `ReEmbedResult` — `app/services/re_embedding_service.py`:20
- c0260: `ReEmbeddingService` — `app/services/re_embedding_service.py`:40
- c0261: `TargetedRebuildResult` — `app/services/re_embedding_service.py`:28
- c0262: `SkillService` — `app/services/skill_service.py`:72
- c0263: `app/services/skill_service.py` — `app/services/skill_service.py`:1
- c0264: `TaskService` — `app/services/task_service.py`:46
- c0265: `UserService` — `app/services/user_service.py`:14
- c0266: `app/utils/provenance.py` — `app/utils/provenance.py`:1
- c0267: `app/utils/pydantic_helper.py` — `app/utils/pydantic_helper.py`:1
- c0268: `app/utils/repository_identity.py` — `app/utils/repository_identity.py`:1
- c0269: `TokenCounter` — `app/utils/token_counter.py`:10
- c0270: `app/version.py` — `app/version.py`:1
- c0271: `debug/reranker-test.py` — `debug/reranker-test.py`:1
- c0272: `debug/sqlite_vec_poc.py` — `debug/sqlite_vec_poc.py`:1
- c0273: `debug/test_google_embeddings.py` — `debug/test_google_embeddings.py`:1
- c0274: `debug/test_mcp_connection.py` — `debug/test_mcp_connection.py`:1
- c0275: `debug/test_sqlite_init.py` — `debug/test_sqlite_init.py`:1
- c0276: `main.py` — `main.py`:1
- c0277: `test_harness/__main__.py` — `test_harness/__main__.py`:1
- c0278: `HarnessConfig` — `test_harness/config.py`:29
- c0279: `AgentContainer` — `test_harness/container.py`:174
- c0280: `test_harness/container.py` — `test_harness/container.py`:1
- c0281: `test_harness/docker/runner.py` — `test_harness/docker/runner.py`:1
- c0282: `test_harness/prompts.py` — `test_harness/prompts.py`:1
- c0283: `ReportIssue` — `test_harness/report.py`:71
- c0284: `ReportLoad` — `test_harness/report.py`:94
- c0285: `ReportStep` — `test_harness/report.py`:60
- c0286: `WalkthroughReport` — `test_harness/report.py`:82
- c0287: `test_harness/report.py` — `test_harness/report.py`:1
- c0292: `HarnessInfraError` — `test_harness/server.py`:27
- c0293: `ThrowawayForgetful` — `test_harness/server.py`:43
- c0294: `test_harness/server.py` — `test_harness/server.py`:1
- c0295: `SessionOutcome` — `test_harness/walkthrough.py`:43
- c0296: `SessionRunner` — `test_harness/walkthrough.py`:51
- c0297: `SkillRunResult` — `test_harness/walkthrough.py`:58
- c0298: `Walkthrough` — `test_harness/walkthrough.py`:128
- c0299: `test_harness/walkthrough.py` — `test_harness/walkthrough.py`:1

## Relationships

- c0002 ..> c0002: `run_migrations_online() calls do_run_migrations()`
- c0002 ..> c0002: `run_migrations_online() calls run_async_migrations()`
- c0002 ..> c0031: `run_migrations_online() calls get()`
- c0002 ..> c0145: `run_async_migrations() calls dispose()`
- c0002 ..> c0218: `run_migrations_online() calls run()`
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
- c0014 --> c0015: `field services`
- c0014 --> c0240: `field registry`
- c0016 ..> c0014: `build_runtime() constructs Runtime`
- c0016 ..> c0014: `type in build_runtime`
- c0016 ..> c0014: `type in dispose_runtime`
- c0016 ..> c0015: `build_runtime() constructs Services`
- c0016 ..> c0016: `build_runtime() calls check_first_run_models()`
- c0016 ..> c0016: `build_runtime() calls create_db_adapter()`
- c0016 ..> c0016: `build_runtime() calls create_repositories()`
- c0016 ..> c0016: `build_runtime() calls get_embedding_adapter()`
- c0016 ..> c0016: `build_runtime() calls get_reranker_adapter()`
- c0016 ..> c0024: `build_runtime() calls subscribe()`
- c0016 ..> c0024: `build_runtime() constructs EventBus`
- c0016 ..> c0024: `dispose_runtime() calls wait_for_pending()`
- c0016 ..> c0127: `get_embedding_adapter() constructs AzureOpenAIAdapter`
- c0016 ..> c0129: `get_embedding_adapter() constructs FastEmbeddingAdapter`
- c0016 ..> c0130: `get_embedding_adapter() constructs GoogleEmbeddingsAdapter`
- c0016 ..> c0131: `get_embedding_adapter() constructs OllamaEmbeddingsAdapter`
- c0016 ..> c0132: `get_embedding_adapter() constructs OpenAIEmbeddingsAdapter`
- c0016 ..> c0134: `get_reranker_adapter() constructs FastEmbedCrossEncoderAdapter`
- c0016 ..> c0135: `get_reranker_adapter() constructs HttpRerankAdapter`
- c0016 ..> c0138: `create_repositories() constructs PostgresActivityRepository`
- c0016 ..> c0139: `create_repositories() constructs PostgresCodeArtifactRepository`
- c0016 ..> c0140: `create_repositories() constructs PostgresDocumentRepository`
- c0016 ..> c0141: `create_repositories() constructs PostgresEntityRepository`
- c0016 ..> c0142: `create_repositories() constructs PostgresFileRepository`
- c0016 ..> c0143: `create_repositories() constructs PostgresMemoryRepository`
- c0016 ..> c0144: `create_repositories() constructs PostgresPlanRepository`
- c0016 ..> c0145: `build_runtime() calls init_db()`
- c0016 ..> c0145: `create_db_adapter() constructs PostgresDatabaseAdapter`
- c0016 ..> c0145: `dispose_runtime() calls dispose()`
- c0016 ..> c0162: `create_repositories() constructs PostgresProjectRepository`
- c0016 ..> c0163: `create_repositories() constructs PostgresSkillRepository`
- c0016 ..> c0164: `create_repositories() constructs PostgresTaskRepository`
- c0016 ..> c0165: `create_repositories() constructs PostgresUserRepository`
- c0016 ..> c0166: `create_repositories() constructs SqliteActivityRepository`
- c0016 ..> c0167: `create_repositories() constructs SqliteCodeArtifactRepository`
- c0016 ..> c0168: `create_repositories() constructs SqliteDocumentRepository`
- c0016 ..> c0169: `create_repositories() constructs SqliteEntityRepository`
- c0016 ..> c0170: `create_repositories() constructs SqliteFileRepository`
- c0016 ..> c0171: `create_repositories() constructs SqliteMemoryRepository`
- c0016 ..> c0172: `create_repositories() constructs SqlitePlanRepository`
- c0016 ..> c0173: `create_repositories() constructs SqliteProjectRepository`
- c0016 ..> c0174: `create_repositories() constructs SqliteSkillRepository`
- c0016 ..> c0175: `create_db_adapter() constructs SqliteDatabaseAdapter`
- c0016 ..> c0193: `create_repositories() constructs SqliteTaskRepository`
- c0016 ..> c0194: `create_repositories() constructs SqliteUserRepository`
- c0016 ..> c0226: `build_runtime() calls parse_scopes()`
- c0016 ..> c0226: `build_runtime() calls resolve_permitted_tools()`
- c0016 ..> c0239: `build_runtime() calls register_all_tools_metadata()`
- c0016 ..> c0240: `build_runtime() calls list_categories()`
- c0016 ..> c0240: `build_runtime() constructs ToolRegistry`
- c0016 ..> c0242: `build_runtime() constructs ActivityService`
- c0016 ..> c0244: `build_runtime() constructs CodeArtifactService`
- c0016 ..> c0245: `build_runtime() constructs DocumentService`
- c0016 ..> c0246: `build_runtime() constructs EntityService`
- c0016 ..> c0247: `build_runtime() constructs FileService`
- c0016 ..> c0251: `build_runtime() constructs GraphService`
- c0016 ..> c0256: `build_runtime() calls register_access_tracking_handlers()`
- c0016 ..> c0256: `build_runtime() constructs MemoryService`
- c0016 ..> c0257: `build_runtime() constructs PlanService`
- c0016 ..> c0258: `build_runtime() constructs ProjectService`
- c0016 ..> c0262: `build_runtime() constructs SkillService`
- c0016 ..> c0264: `build_runtime() constructs TaskService`
- c0016 ..> c0265: `build_runtime() constructs UserService`
- c0017 ..> c0017: `_build_github() calls _required()`
- c0017 ..> c0017: `_build_github() calls _scopes()`
- c0017 ..> c0017: `_build_google() calls _required()`
- c0017 ..> c0017: `_build_google() calls _scopes()`
- c0017 ..> c0017: `_build_introspection() calls _required()`
- c0017 ..> c0017: `_build_introspection() calls _scopes()`
- c0017 ..> c0017: `_build_jwt() calls _scopes()`
- c0017 ..> c0031: `build_auth_provider() calls get()`
- c0019 ..> c0031: `format() calls get()`
- c0019 ..> c0033: `format() calls get_request_id()`
- c0019 ..> c0033: `format() calls get_user_id()`
- c0020 ..> c0020: `filter() calls _mask_value()`
- c0021 ..> c0018: `configure_logging() constructs ConsoleFormatter`
- c0021 ..> c0019: `configure_logging() constructs JSONFormatter`
- c0021 ..> c0020: `configure_logging() constructs SensitiveDataFilter`
- c0021 ..> c0024: `configure_logging() calls clear()`
- c0021 ..> c0279: `configure_logging() calls start()`
- c0021 ..> c0279: `shutdown_logging() calls stop()`
- c0022 ..> c0023: `_validate_onnx_providers() calls parse_onnx_providers()`
- c0022 ..> c0023: `embedding_onnx_providers() calls parse_onnx_providers()`
- c0022 ..> c0023: `reranking_onnx_providers() calls parse_onnx_providers()`
- c0024 ..> c0024: `_emit_to_streams() calls _next_seq()`
- c0024 ..> c0024: `emit() calls _emit_to_streams()`
- c0024 ..> c0024: `emit() calls _safe_dispatch()`
- c0024 ..> c0031: `_emit_to_streams() calls get()`
- c0024 ..> c0031: `clear() calls clear()`
- c0024 ..> c0031: `get_current_seq() calls get()`
- c0024 ..> c0031: `stream_subscriber_count() calls get()`
- c0024 ..> c0031: `subscribe_stream() calls get()`
- c0024 ..> c0031: `subscriber_count() calls get()`
- c0024 ..> c0035: `type in _emit_to_streams`
- c0024 ..> c0035: `type in _safe_dispatch`
- c0024 ..> c0035: `type in emit`
- c0024 ..> c0125: `emit() calls create_task()`
- c0030 --> c0110: `field user`
- c0031 ..> c0024: `clear() calls clear()`
- c0031 --> c0030: `field _cache`
- c0031 ..> c0030: `set() constructs CacheEntry`
- c0031 ..> c0031: `get() calls _hash_token()`
- c0031 ..> c0031: `invalidate() calls _hash_token()`
- c0031 ..> c0031: `set() calls _hash_token()`
- c0031 ..> c0110: `type in get`
- c0031 ..> c0110: `type in set`
- c0032 ..> c0031: `get_user_from_auth() calls get()`
- c0032 ..> c0031: `get_user_from_request() calls get()`
- c0032 ..> c0110: `type in get_user_from_auth`
- c0032 ..> c0110: `type in get_user_from_request`
- c0032 ..> c0111: `get_user_from_auth() constructs UserCreate`
- c0032 ..> c0111: `get_user_from_request() constructs UserCreate`
- c0032 ..> c0265: `get_user_from_auth() calls get_or_create_user()`
- c0032 ..> c0265: `get_user_from_request() calls get_or_create_user()`
- c0033 ..> c0031: `get_request_id() calls get()`
- c0033 ..> c0031: `get_user_id() calls get()`
- c0035 --> c0034: `field action`
- c0035 --> c0038: `field actor`
- c0035 --> c0039: `field entity_type`
- c0036 --> c0037: `field events`
- c0037 --> c0034: `field action`
- c0037 --> c0038: `field actor`
- c0037 --> c0039: `field entity_type`
- c0040 --|> c0041: `inherits`
- c0044 --|> c0045: `inherits`
- c0045 ..> c0031: `calculate_size_bytes() calls get()`
- c0048 --|> c0049: `inherits`
- c0049 --> c0055: `field entity_type`
- c0050 --> c0054: `field entities`
- c0051 --|> c0052: `inherits`
- c0054 --> c0055: `field entity_type`
- c0056 --> c0055: `field entity_type`
- c0057 --|> c0058: `inherits`
- c0064 --> c0061: `field edges`
- c0064 --> c0062: `field meta`
- c0064 --> c0063: `field nodes`
- c0065 --> c0066: `field memory`
- c0066 --|> c0067: `inherits`
- c0068 --> c0074: `field similar_memories`
- c0068 --> c0076: `field obsolete_matches`
- c0070 --> c0066: `field memories`
- c0072 --> c0065: `field linked_memories`
- c0072 --> c0066: `field primary_memories`
- c0072 --> c0073: `field scores`
- c0081 --|> c0082: `inherits`
- c0082 --> c0083: `field status`
- c0084 --> c0083: `field status`
- c0085 ..> c0031: `ignore_null_external_ref() calls get()`
- c0085 --> c0083: `field status`
- c0086 --> c0078: `field criteria`
- c0086 --> c0090: `field priority`
- c0086 --> c0091: `field state`
- c0087 --> c0079: `field criteria`
- c0087 --> c0090: `field priority`
- c0089 ..> c0031: `cannot_depend_on_self() calls get()`
- c0092 --> c0090: `field priority`
- c0092 --> c0091: `field state`
- c0093 --> c0090: `field priority`
- c0094 --|> c0095: `inherits`
- c0095 --> c0096: `field status`
- c0095 --> c0098: `field project_type`
- c0097 --> c0096: `field status`
- c0097 --> c0098: `field project_type`
- c0099 --> c0096: `field status`
- c0099 --> c0098: `field project_type`
- c0100 --|> c0101: `inherits`
- c0106 --|> c0108: `inherits`
- c0107 --> c0108: `field metadata`
- c0108 ..> c0031: `_map_python_type_to_json_type() calls get()`
- c0108 --> c0105: `field category`
- c0108 ..> c0108: `_generate_json_schema() calls _map_python_type_to_json_type()`
- c0108 ..> c0108: `to_detailed_dict() calls _generate_json_schema()`
- c0108 --> c0109: `field parameters`
- c0110 --|> c0111: `inherits`
- c0114 ..> c0034: `type in count_events`
- c0114 ..> c0034: `type in query_events`
- c0114 ..> c0035: `type in save_event`
- c0114 ..> c0037: `type in query_events`
- c0114 ..> c0037: `type in save_event`
- c0114 ..> c0038: `type in query_events`
- c0114 ..> c0039: `type in count_events`
- c0114 ..> c0039: `type in query_events`
- c0115 ..> c0040: `type in create_code_artifact`
- c0115 ..> c0040: `type in get_code_artifact_by_id`
- c0115 ..> c0040: `type in update_code_artifact`
- c0115 ..> c0041: `type in create_code_artifact`
- c0115 ..> c0042: `type in list_code_artifacts`
- c0115 ..> c0043: `type in update_code_artifact`
- c0116 ..> c0044: `type in create_document`
- c0116 ..> c0044: `type in get_document_by_id`
- c0116 ..> c0044: `type in update_document`
- c0116 ..> c0045: `type in create_document`
- c0116 ..> c0046: `type in list_documents`
- c0116 ..> c0047: `type in update_document`
- c0117 ..> c0048: `type in create_entity`
- c0117 ..> c0048: `type in get_entity_by_id`
- c0117 ..> c0048: `type in update_entity`
- c0117 ..> c0049: `type in create_entity`
- c0117 ..> c0051: `type in create_entity_relationship`
- c0117 ..> c0051: `type in get_all_entity_relationships`
- c0117 ..> c0051: `type in get_entity_relationships`
- c0117 ..> c0051: `type in update_entity_relationship`
- c0117 ..> c0052: `type in create_entity_relationship`
- c0117 ..> c0053: `type in update_entity_relationship`
- c0117 ..> c0054: `type in list_entities`
- c0117 ..> c0054: `type in search_entities`
- c0117 ..> c0055: `type in list_entities`
- c0117 ..> c0055: `type in search_entities`
- c0117 ..> c0056: `type in update_entity`
- c0119 ..> c0057: `type in create_file`
- c0119 ..> c0057: `type in get_file_by_id`
- c0119 ..> c0057: `type in update_file`
- c0119 ..> c0058: `type in create_file`
- c0119 ..> c0059: `type in list_files`
- c0119 ..> c0060: `type in update_file`
- c0120 ..> c0066: `type in create_memory`
- c0120 ..> c0066: `type in find_obsolete_matches`
- c0120 ..> c0066: `type in find_similar_memories`
- c0120 ..> c0066: `type in find_similar_memories_scored`
- c0120 ..> c0066: `type in get_linked_memories`
- c0120 ..> c0066: `type in get_memories_for_reembedding`
- c0120 ..> c0066: `type in get_memories_for_targeted_rebuild`
- c0120 ..> c0066: `type in get_memory_by_id`
- c0120 ..> c0066: `type in list_memories`
- c0120 ..> c0066: `type in search`
- c0120 ..> c0066: `type in search_scored`
- c0120 ..> c0066: `type in update_memory`
- c0120 ..> c0067: `type in create_memory`
- c0120 ..> c0073: `type in search_scored`
- c0120 ..> c0075: `type in update_memory`
- c0122 ..> c0081: `type in create_plan`
- c0122 ..> c0081: `type in get_plan_by_id`
- c0122 ..> c0081: `type in update_plan`
- c0122 ..> c0082: `type in create_plan`
- c0122 ..> c0083: `type in list_plans`
- c0122 ..> c0084: `type in list_plans`
- c0122 ..> c0085: `type in update_plan`
- c0123 ..> c0094: `type in create_project`
- c0123 ..> c0094: `type in get_project_by_id`
- c0123 ..> c0094: `type in update_project`
- c0123 ..> c0095: `type in create_project`
- c0123 ..> c0096: `type in list_projects`
- c0123 ..> c0097: `type in list_projects`
- c0123 ..> c0099: `type in update_project`
- c0124 ..> c0100: `type in create_skill`
- c0124 ..> c0100: `type in get_skill_by_id`
- c0124 ..> c0100: `type in update_skill`
- c0124 ..> c0101: `type in create_skill`
- c0124 ..> c0102: `type in get_skill_links`
- c0124 ..> c0103: `type in list_skills`
- c0124 ..> c0103: `type in search_skills`
- c0124 ..> c0104: `type in update_skill`
- c0125 ..> c0078: `type in create_criterion`
- c0125 ..> c0078: `type in get_criteria_for_task`
- c0125 ..> c0078: `type in update_criterion`
- c0125 ..> c0079: `type in create_criterion`
- c0125 ..> c0080: `type in update_criterion`
- c0125 ..> c0086: `type in create_task`
- c0125 ..> c0086: `type in get_task_by_id`
- c0125 ..> c0086: `type in transition_task_state`
- c0125 ..> c0086: `type in update_task`
- c0125 ..> c0087: `type in create_task`
- c0125 ..> c0088: `type in add_dependency`
- c0125 ..> c0090: `type in list_tasks`
- c0125 ..> c0091: `type in list_tasks`
- c0125 ..> c0091: `type in transition_task_state`
- c0125 ..> c0092: `type in list_tasks`
- c0125 ..> c0092: `type in list_tasks_for_user`
- c0125 ..> c0093: `type in update_task`
- c0126 ..> c0110: `type in create_user`
- c0126 ..> c0110: `type in get_user_by_external_id`
- c0126 ..> c0110: `type in get_user_by_id`
- c0126 ..> c0110: `type in update_user`
- c0126 ..> c0111: `type in create_user`
- c0126 ..> c0113: `type in update_user`
- c0127 --|> c0128: `inherits`
- c0129 --|> c0128: `inherits`
- c0130 --|> c0128: `inherits`
- c0131 --|> c0128: `inherits`
- c0131 ..> c0129: `__init__() calls _create_text_embedding()`
- c0131 ..> c0133: `__init__() calls load_fastembed_model()`
- c0131 ..> c0211: `generate_embedding() calls create()`
- c0132 --|> c0128: `inherits`
- c0133 ..> c0133: `load_fastembed_model() calls get_fastembed_kwargs()`
- c0134 ..> c0135: `_rerank_sync() calls rerank()`
- c0135 ..> c0133: `__init__() calls load_fastembed_model()`
- c0135 ..> c0134: `__init__() calls _create_text_cross_encoder()`
- c0137 ..> c0066: `type in build_memory_text`
- c0137 ..> c0067: `type in build_embedding_text`
- c0138 ..> c0034: `type in count_events`
- c0138 ..> c0034: `type in query_events`
- c0138 ..> c0035: `type in save_event`
- c0138 ..> c0037: `query_events() constructs ActivityLogEntry`
- c0138 ..> c0037: `save_event() constructs ActivityLogEntry`
- c0138 ..> c0037: `type in query_events`
- c0138 ..> c0037: `type in save_event`
- c0138 ..> c0038: `type in query_events`
- c0138 ..> c0039: `type in count_events`
- c0138 ..> c0039: `type in query_events`
- c0138 ..> c0118: `cleanup_expired() calls execute()`
- c0138 ..> c0118: `count_events() calls execute()`
- c0138 ..> c0118: `query_events() calls execute()`
- c0138 ..> c0145: `cleanup_expired() calls session()`
- c0138 ..> c0145: `count_events() calls session()`
- c0138 ..> c0145: `query_events() calls session()`
- c0138 ..> c0145: `save_event() calls session()`
- c0138 ..> c0145: `type in __init__`
- c0138 ..> c0146: `save_event() constructs ActivityLogTable`
- c0139 ..> c0029: `update_code_artifact() constructs NotFoundError`
- c0139 ..> c0031: `update_code_artifact() calls get()`
- c0139 ..> c0040: `type in create_code_artifact`
- c0139 ..> c0040: `type in get_code_artifact_by_id`
- c0139 ..> c0040: `type in update_code_artifact`
- c0139 ..> c0041: `type in create_code_artifact`
- c0139 ..> c0042: `type in list_code_artifacts`
- c0139 ..> c0043: `type in update_code_artifact`
- c0139 ..> c0118: `delete_code_artifact() calls execute()`
- c0139 ..> c0118: `get_code_artifact_by_id() calls execute()`
- c0139 ..> c0118: `list_code_artifacts() calls execute()`
- c0139 ..> c0118: `update_code_artifact() calls execute()`
- c0139 ..> c0145: `create_code_artifact() calls session()`
- c0139 ..> c0145: `delete_code_artifact() calls session()`
- c0139 ..> c0145: `get_code_artifact_by_id() calls session()`
- c0139 ..> c0145: `list_code_artifacts() calls session()`
- c0139 ..> c0145: `type in __init__`
- c0139 ..> c0145: `update_code_artifact() calls session()`
- c0139 ..> c0148: `create_code_artifact() constructs CodeArtifactsTable`
- c0140 ..> c0029: `update_document() constructs NotFoundError`
- c0140 ..> c0031: `update_document() calls get()`
- c0140 ..> c0044: `type in create_document`
- c0140 ..> c0044: `type in get_document_by_id`
- c0140 ..> c0044: `type in update_document`
- c0140 ..> c0045: `type in create_document`
- c0140 ..> c0046: `type in list_documents`
- c0140 ..> c0047: `type in update_document`
- c0140 ..> c0118: `delete_document() calls execute()`
- c0140 ..> c0118: `get_document_by_id() calls execute()`
- c0140 ..> c0118: `list_documents() calls execute()`
- c0140 ..> c0118: `update_document() calls execute()`
- c0140 ..> c0145: `create_document() calls session()`
- c0140 ..> c0145: `delete_document() calls session()`
- c0140 ..> c0145: `get_document_by_id() calls session()`
- c0140 ..> c0145: `list_documents() calls session()`
- c0140 ..> c0145: `type in __init__`
- c0140 ..> c0145: `update_document() calls session()`
- c0140 ..> c0150: `create_document() constructs DocumentsTable`
- c0141 ..> c0029: `create_entity_relationship() constructs NotFoundError`
- c0141 ..> c0029: `get_entity_memories() constructs NotFoundError`
- c0141 ..> c0029: `get_entity_relationships() constructs NotFoundError`
- c0141 ..> c0029: `get_memory_entities() constructs NotFoundError`
- c0141 ..> c0029: `link_entity_to_memory() constructs NotFoundError`
- c0141 ..> c0029: `link_entity_to_project() constructs NotFoundError`
- c0141 ..> c0029: `update_entity() constructs NotFoundError`
- c0141 ..> c0029: `update_entity_relationship() constructs NotFoundError`
- c0141 ..> c0031: `update_entity() calls get()`
- c0141 ..> c0048: `type in create_entity`
- c0141 ..> c0048: `type in get_entity_by_id`
- c0141 ..> c0048: `type in update_entity`
- c0141 ..> c0049: `type in create_entity`
- c0141 ..> c0051: `create_entity_relationship() constructs EntityRelationship`
- c0141 ..> c0051: `get_all_entity_relationships() constructs EntityRelationship`
- c0141 ..> c0051: `get_entity_relationships() constructs EntityRelationship`
- c0141 ..> c0051: `type in create_entity_relationship`
- c0141 ..> c0051: `type in get_all_entity_relationships`
- c0141 ..> c0051: `type in get_entity_relationships`
- c0141 ..> c0051: `type in update_entity_relationship`
- c0141 ..> c0051: `update_entity_relationship() constructs EntityRelationship`
- c0141 ..> c0052: `type in create_entity_relationship`
- c0141 ..> c0053: `type in update_entity_relationship`
- c0141 ..> c0054: `type in list_entities`
- c0141 ..> c0054: `type in search_entities`
- c0141 ..> c0055: `type in list_entities`
- c0141 ..> c0055: `type in search_entities`
- c0141 ..> c0056: `type in update_entity`
- c0141 ..> c0118: `create_entity() calls execute()`
- c0141 ..> c0118: `create_entity_relationship() calls execute()`
- c0141 ..> c0118: `delete_entity() calls execute()`
- c0141 ..> c0118: `delete_entity_relationship() calls execute()`
- c0141 ..> c0118: `get_all_entity_file_links() calls execute()`
- c0141 ..> c0118: `get_all_entity_memory_links() calls execute()`
- c0141 ..> c0118: `get_all_entity_project_links() calls execute()`
- c0141 ..> c0118: `get_all_entity_relationships() calls execute()`
- c0141 ..> c0118: `get_entity_by_id() calls execute()`
- c0141 ..> c0118: `get_entity_memories() calls execute()`
- c0141 ..> c0118: `get_entity_relationships() calls execute()`
- c0141 ..> c0118: `get_memory_entities() calls execute()`
- c0141 ..> c0118: `link_entity_to_memory() calls execute()`
- c0141 ..> c0118: `link_entity_to_project() calls execute()`
- c0141 ..> c0118: `list_entities() calls execute()`
- c0141 ..> c0118: `search_entities() calls execute()`
- c0141 ..> c0118: `unlink_entity_from_memory() calls execute()`
- c0141 ..> c0118: `unlink_entity_from_project() calls execute()`
- c0141 ..> c0118: `update_entity() calls execute()`
- c0141 ..> c0118: `update_entity_relationship() calls execute()`
- c0141 ..> c0145: `create_entity() calls session()`
- c0141 ..> c0145: `create_entity_relationship() calls session()`
- c0141 ..> c0145: `delete_entity() calls session()`
- c0141 ..> c0145: `delete_entity_relationship() calls session()`
- c0141 ..> c0145: `get_all_entity_file_links() calls session()`
- c0141 ..> c0145: `get_all_entity_memory_links() calls session()`
- c0141 ..> c0145: `get_all_entity_project_links() calls session()`
- c0141 ..> c0145: `get_all_entity_relationships() calls session()`
- c0141 ..> c0145: `get_entity_by_id() calls session()`
- c0141 ..> c0145: `get_entity_memories() calls session()`
- c0141 ..> c0145: `get_entity_relationships() calls session()`
- c0141 ..> c0145: `get_memory_entities() calls session()`
- c0141 ..> c0145: `link_entity_to_memory() calls session()`
- c0141 ..> c0145: `link_entity_to_project() calls session()`
- c0141 ..> c0145: `list_entities() calls session()`
- c0141 ..> c0145: `search_entities() calls session()`
- c0141 ..> c0145: `type in __init__`
- c0141 ..> c0145: `unlink_entity_from_memory() calls session()`
- c0141 ..> c0145: `unlink_entity_from_project() calls session()`
- c0141 ..> c0145: `update_entity() calls session()`
- c0141 ..> c0145: `update_entity_relationship() calls session()`
- c0141 ..> c0151: `create_entity() constructs EntitiesTable`
- c0141 ..> c0152: `create_entity_relationship() constructs EntityRelationshipsTable`
- c0142 ..> c0029: `update_file() constructs NotFoundError`
- c0142 ..> c0057: `_to_file_model() constructs File`
- c0142 ..> c0057: `type in _to_file_model`
- c0142 ..> c0057: `type in create_file`
- c0142 ..> c0057: `type in get_file_by_id`
- c0142 ..> c0057: `type in update_file`
- c0142 ..> c0058: `type in create_file`
- c0142 ..> c0059: `type in list_files`
- c0142 ..> c0060: `type in update_file`
- c0142 ..> c0118: `delete_file() calls execute()`
- c0142 ..> c0118: `get_file_by_id() calls execute()`
- c0142 ..> c0118: `list_files() calls execute()`
- c0142 ..> c0118: `update_file() calls execute()`
- c0142 ..> c0142: `create_file() calls _to_file_model()`
- c0142 ..> c0142: `get_file_by_id() calls _to_file_model()`
- c0142 ..> c0142: `update_file() calls _to_file_model()`
- c0142 ..> c0145: `create_file() calls session()`
- c0142 ..> c0145: `delete_file() calls session()`
- c0142 ..> c0145: `get_file_by_id() calls session()`
- c0142 ..> c0145: `list_files() calls session()`
- c0142 ..> c0145: `type in __init__`
- c0142 ..> c0145: `update_file() calls session()`
- c0142 ..> c0153: `create_file() constructs FilesTable`
- c0142 ..> c0153: `type in _to_file_model`
- c0143 ..> c0024: `update_memory() calls clear()`
- c0143 ..> c0029: `_link_code_artifacts() constructs NotFoundError`
- c0143 ..> c0029: `_link_documents() constructs NotFoundError`
- c0143 ..> c0029: `_link_files() constructs NotFoundError`
- c0143 ..> c0029: `_link_projects() constructs NotFoundError`
- c0143 ..> c0029: `_link_skills() constructs NotFoundError`
- c0143 ..> c0029: `create_link() constructs NotFoundError`
- c0143 ..> c0029: `get_linked_memories() constructs NotFoundError`
- c0143 ..> c0029: `get_memory_by_id() constructs NotFoundError`
- c0143 ..> c0029: `get_memory_table_by_id() constructs NotFoundError`
- c0143 ..> c0029: `mark_obsolete() constructs NotFoundError`
- c0143 ..> c0029: `update_memory() constructs NotFoundError`
- c0143 ..> c0031: `create_link() calls get()`
- c0143 ..> c0031: `list_memories() calls get()`
- c0143 ..> c0066: `type in create_memory`
- c0143 ..> c0066: `type in find_obsolete_matches`
- c0143 ..> c0066: `type in find_similar_memories`
- c0143 ..> c0066: `type in find_similar_memories_scored`
- c0143 ..> c0066: `type in get_linked_memories`
- c0143 ..> c0066: `type in get_memories_for_reembedding`
- c0143 ..> c0066: `type in get_memories_for_targeted_rebuild`
- c0143 ..> c0066: `type in get_memory_by_id`
- c0143 ..> c0066: `type in list_memories`
- c0143 ..> c0066: `type in search`
- c0143 ..> c0066: `type in search_scored`
- c0143 ..> c0066: `type in semantic_search`
- c0143 ..> c0066: `type in semantic_search_scored`
- c0143 ..> c0066: `type in update_memory`
- c0143 ..> c0067: `type in create_memory`
- c0143 ..> c0073: `search_scored() constructs MemoryScore`
- c0143 ..> c0073: `type in search_scored`
- c0143 ..> c0075: `type in update_memory`
- c0143 ..> c0118: `_link_code_artifacts() calls execute()`
- c0143 ..> c0118: `_link_documents() calls execute()`
- c0143 ..> c0118: `_link_files() calls execute()`
- c0143 ..> c0118: `_link_projects() calls execute()`
- c0143 ..> c0118: `_link_skills() calls execute()`
- c0143 ..> c0118: `bulk_update_embeddings() calls execute()`
- c0143 ..> c0118: `count_memories_for_targeted_rebuild() calls execute()`
- c0143 ..> c0118: `create_memory() calls execute()`
- c0143 ..> c0118: `find_obsolete_matches() calls execute()`
- c0143 ..> c0118: `find_similar_memories_scored() calls execute()`
- c0143 ..> c0118: `get_linked_memories() calls execute()`
- c0143 ..> c0118: `get_memories_for_reembedding() calls execute()`
- c0143 ..> c0118: `get_memories_for_targeted_rebuild() calls execute()`
- c0143 ..> c0118: `get_memory_table_by_id() calls execute()`
- c0143 ..> c0118: `get_subgraph_nodes() calls execute()`
- c0143 ..> c0118: `list_memories() calls execute()`
- c0143 ..> c0118: `mark_obsolete() calls execute()`
- c0143 ..> c0118: `record_memory_access() calls execute()`
- c0143 ..> c0118: `reset_embedding_storage() calls execute()`
- c0143 ..> c0118: `semantic_search_scored() calls execute()`
- c0143 ..> c0118: `unlink_memories() calls execute()`
- c0143 ..> c0118: `update_memory() calls execute()`
- c0143 ..> c0118: `upsert_targeted_embeddings() calls execute()`
- c0143 ..> c0118: `validate_embedding_dimensions() calls execute()`
- c0143 ..> c0118: `validate_search_works() calls execute()`
- c0143 ..> c0128: `type in __init__`
- c0143 ..> c0131: `_generate_embeddings() calls generate_embedding()`
- c0143 ..> c0135: `search_scored() calls rerank()`
- c0143 ..> c0136: `type in __init__`
- c0143 ..> c0137: `create_memory() calls build_embedding_text()`
- c0143 ..> c0137: `search_scored() calls build_contextual_query()`
- c0143 ..> c0137: `search_scored() calls build_memory_text()`
- c0143 ..> c0137: `update_memory() calls build_embedding_text()`
- c0143 ..> c0143: `count_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0143 ..> c0143: `create_links_batch() calls create_link()`
- c0143 ..> c0143: `create_memory() calls _generate_embeddings()`
- c0143 ..> c0143: `create_memory() calls _link_code_artifacts()`
- c0143 ..> c0143: `create_memory() calls _link_documents()`
- c0143 ..> c0143: `create_memory() calls _link_files()`
- c0143 ..> c0143: `create_memory() calls _link_projects()`
- c0143 ..> c0143: `create_memory() calls _link_skills()`
- c0143 ..> c0143: `find_obsolete_matches() calls get_memory_table_by_id()`
- c0143 ..> c0143: `find_similar_memories() calls find_similar_memories_scored()`
- c0143 ..> c0143: `find_similar_memories_scored() calls get_memory_table_by_id()`
- c0143 ..> c0143: `get_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0143 ..> c0143: `get_memory_by_id() calls get_memory_table_by_id()`
- c0143 ..> c0143: `search() calls search_scored()`
- c0143 ..> c0143: `search_scored() calls semantic_search_scored()`
- c0143 ..> c0143: `semantic_search() calls semantic_search_scored()`
- c0143 ..> c0143: `semantic_search_scored() calls _generate_embeddings()`
- c0143 ..> c0143: `update_memory() calls _generate_embeddings()`
- c0143 ..> c0143: `update_memory() calls _link_code_artifacts()`
- c0143 ..> c0143: `update_memory() calls _link_documents()`
- c0143 ..> c0143: `update_memory() calls _link_files()`
- c0143 ..> c0143: `update_memory() calls _link_projects()`
- c0143 ..> c0143: `validate_search_works() calls _generate_embeddings()`
- c0143 ..> c0145: `bulk_update_embeddings() calls system_session()`
- c0143 ..> c0145: `count_all_memories() calls system_session()`
- c0143 ..> c0145: `count_memories_for_targeted_rebuild() calls system_session()`
- c0143 ..> c0145: `create_link() calls session()`
- c0143 ..> c0145: `create_memory() calls session()`
- c0143 ..> c0145: `find_obsolete_matches() calls session()`
- c0143 ..> c0145: `find_similar_memories_scored() calls session()`
- c0143 ..> c0145: `get_linked_memories() calls session()`
- c0143 ..> c0145: `get_memories_for_reembedding() calls system_session()`
- c0143 ..> c0145: `get_memories_for_targeted_rebuild() calls system_session()`
- c0143 ..> c0145: `get_memory_table_by_id() calls session()`
- c0143 ..> c0145: `get_subgraph_nodes() calls session()`
- c0143 ..> c0145: `list_memories() calls session()`
- c0143 ..> c0145: `mark_obsolete() calls session()`
- c0143 ..> c0145: `record_memory_access() calls system_session()`
- c0143 ..> c0145: `reset_embedding_storage() calls system_session()`
- c0143 ..> c0145: `semantic_search_scored() calls session()`
- c0143 ..> c0145: `type in __init__`
- c0143 ..> c0145: `unlink_memories() calls session()`
- c0143 ..> c0145: `update_memory() calls session()`
- c0143 ..> c0145: `upsert_targeted_embeddings() calls system_session()`
- c0143 ..> c0145: `validate_embedding_count() calls system_session()`
- c0143 ..> c0145: `validate_embedding_dimensions() calls system_session()`
- c0143 ..> c0145: `validate_search_works() calls system_session()`
- c0143 ..> c0154: `create_link() constructs MemoryLinkTable`
- c0143 ..> c0154: `type in create_link`
- c0143 ..> c0155: `create_memory() constructs MemoryTable`
- c0143 ..> c0155: `type in _link_code_artifacts`
- c0143 ..> c0155: `type in _link_documents`
- c0143 ..> c0155: `type in _link_files`
- c0143 ..> c0155: `type in _link_projects`
- c0143 ..> c0155: `type in _link_skills`
- c0143 ..> c0155: `type in get_memory_table_by_id`
- c0144 ..> c0025: `create_plan() constructs ConflictError`
- c0144 ..> c0025: `update_plan() constructs ConflictError`
- c0144 ..> c0029: `update_plan() constructs NotFoundError`
- c0144 ..> c0081: `type in create_plan`
- c0144 ..> c0081: `type in get_plan_by_id`
- c0144 ..> c0081: `type in update_plan`
- c0144 ..> c0082: `type in create_plan`
- c0144 ..> c0083: `type in list_plans`
- c0144 ..> c0084: `type in list_plans`
- c0144 ..> c0085: `type in update_plan`
- c0144 ..> c0118: `delete_plan() calls execute()`
- c0144 ..> c0118: `get_plan_by_id() calls execute()`
- c0144 ..> c0118: `list_plans() calls execute()`
- c0144 ..> c0118: `update_plan() calls execute()`
- c0144 ..> c0145: `create_plan() calls session()`
- c0144 ..> c0145: `delete_plan() calls session()`
- c0144 ..> c0145: `get_plan_by_id() calls session()`
- c0144 ..> c0145: `list_plans() calls session()`
- c0144 ..> c0145: `type in __init__`
- c0144 ..> c0145: `update_plan() calls session()`
- c0144 ..> c0156: `create_plan() constructs PlansTable`
- c0145 ..> c0003: `_run_migrations() calls upgrade()`
- c0145 ..> c0118: `init_db() calls execute()`
- c0145 ..> c0118: `session() calls close()`
- c0145 ..> c0118: `session() calls execute()`
- c0145 ..> c0118: `system_session() calls close()`
- c0145 ..> c0145: `__init__() calls construct_postgres_connection_string()`
- c0145 ..> c0145: `_run_migrations() calls construct_postgres_connection_string()`
- c0145 ..> c0175: `dispose() calls dispose()`
- c0146 --|> c0147: `inherits`
- c0148 --|> c0147: `inherits`
- c0148 --> c0155: `field memories`
- c0148 --> c0157: `field project`
- c0148 --> c0158: `field skills`
- c0148 --> c0161: `field user`
- c0149 --|> c0147: `inherits`
- c0149 --> c0160: `field task`
- c0150 --|> c0147: `inherits`
- c0150 --> c0155: `field memories`
- c0150 --> c0157: `field project`
- c0150 --> c0158: `field skills`
- c0150 --> c0161: `field user`
- c0151 --|> c0147: `inherits`
- c0151 --> c0152: `field incoming_relationships`
- c0151 --> c0152: `field outgoing_relationships`
- c0151 --> c0153: `field files`
- c0151 --> c0155: `field memories`
- c0151 --> c0157: `field projects`
- c0151 --> c0161: `field user`
- c0152 --|> c0147: `inherits`
- c0152 --> c0151: `field source_entity`
- c0152 --> c0151: `field target_entity`
- c0153 --|> c0147: `inherits`
- c0153 --> c0151: `field entities`
- c0153 --> c0155: `field memories`
- c0153 --> c0157: `field project`
- c0153 --> c0158: `field skills`
- c0153 --> c0161: `field user`
- c0154 --|> c0147: `inherits`
- c0155 --|> c0147: `inherits`
- c0155 --> c0148: `field code_artifacts`
- c0155 --> c0150: `field documents`
- c0155 --> c0151: `field entities`
- c0155 --> c0153: `field files`
- c0155 --> c0157: `field projects`
- c0155 --> c0158: `field skills`
- c0155 --> c0161: `field user`
- c0156 --|> c0147: `inherits`
- c0156 --> c0157: `field project`
- c0156 --> c0160: `field tasks`
- c0156 --> c0161: `field user`
- c0157 --|> c0147: `inherits`
- c0157 --> c0148: `field code_artifacts`
- c0157 --> c0150: `field documents`
- c0157 --> c0151: `field entities`
- c0157 --> c0153: `field files`
- c0157 --> c0155: `field memories`
- c0157 --> c0156: `field plans`
- c0157 --> c0158: `field skills`
- c0157 --> c0161: `field user`
- c0158 --|> c0147: `inherits`
- c0158 --> c0148: `field code_artifacts`
- c0158 --> c0150: `field documents`
- c0158 --> c0153: `field files`
- c0158 --> c0155: `field memories`
- c0158 --> c0157: `field project`
- c0158 --> c0161: `field user`
- c0159 --|> c0147: `inherits`
- c0159 --> c0160: `field task`
- c0160 --|> c0147: `inherits`
- c0160 --> c0149: `field criteria`
- c0160 --> c0156: `field plan`
- c0160 --> c0159: `field depends_on`
- c0161 --|> c0147: `inherits`
- c0161 --> c0148: `field code_artifacts`
- c0161 --> c0150: `field documents`
- c0161 --> c0151: `field entities`
- c0161 --> c0153: `field files`
- c0161 --> c0155: `field memories`
- c0161 --> c0156: `field plans`
- c0161 --> c0157: `field projects`
- c0161 --> c0158: `field skills`
- c0162 ..> c0029: `update_project() constructs NotFoundError`
- c0162 ..> c0094: `type in create_project`
- c0162 ..> c0094: `type in get_project_by_id`
- c0162 ..> c0094: `type in update_project`
- c0162 ..> c0095: `type in create_project`
- c0162 ..> c0096: `type in list_projects`
- c0162 ..> c0097: `type in list_projects`
- c0162 ..> c0099: `type in update_project`
- c0162 ..> c0118: `delete_project() calls execute()`
- c0162 ..> c0118: `get_project_by_id() calls execute()`
- c0162 ..> c0118: `list_projects() calls execute()`
- c0162 ..> c0118: `update_project() calls execute()`
- c0162 ..> c0145: `create_project() calls session()`
- c0162 ..> c0145: `delete_project() calls session()`
- c0162 ..> c0145: `get_project_by_id() calls session()`
- c0162 ..> c0145: `list_projects() calls session()`
- c0162 ..> c0145: `type in __init__`
- c0162 ..> c0145: `update_project() calls session()`
- c0162 ..> c0157: `create_project() constructs ProjectsTable`
- c0162 ..> c0268: `list_projects() calls repository_identity()`
- c0163 ..> c0029: `get_skill_links() constructs NotFoundError`
- c0163 ..> c0029: `link_skill_to_code_artifact() constructs NotFoundError`
- c0163 ..> c0029: `link_skill_to_document() constructs NotFoundError`
- c0163 ..> c0029: `link_skill_to_file() constructs NotFoundError`
- c0163 ..> c0029: `link_skill_to_memory() constructs NotFoundError`
- c0163 ..> c0029: `update_skill() constructs NotFoundError`
- c0163 ..> c0100: `_to_skill() constructs Skill`
- c0163 ..> c0100: `type in _to_skill`
- c0163 ..> c0100: `type in create_skill`
- c0163 ..> c0100: `type in get_skill_by_id`
- c0163 ..> c0100: `type in update_skill`
- c0163 ..> c0101: `type in create_skill`
- c0163 ..> c0102: `get_skill_links() constructs SkillLinks`
- c0163 ..> c0102: `type in get_skill_links`
- c0163 ..> c0103: `type in list_skills`
- c0163 ..> c0103: `type in search_skills`
- c0163 ..> c0104: `type in update_skill`
- c0163 ..> c0118: `delete_skill() calls execute()`
- c0163 ..> c0118: `get_all_skill_code_artifact_links() calls execute()`
- c0163 ..> c0118: `get_all_skill_document_links() calls execute()`
- c0163 ..> c0118: `get_all_skill_file_links() calls execute()`
- c0163 ..> c0118: `get_skill_by_id() calls execute()`
- c0163 ..> c0118: `get_skill_links() calls execute()`
- c0163 ..> c0118: `link_skill_to_code_artifact() calls execute()`
- c0163 ..> c0118: `link_skill_to_document() calls execute()`
- c0163 ..> c0118: `link_skill_to_file() calls execute()`
- c0163 ..> c0118: `link_skill_to_memory() calls execute()`
- c0163 ..> c0118: `list_skills() calls execute()`
- c0163 ..> c0118: `search_skills() calls execute()`
- c0163 ..> c0118: `skill_name_exists() calls execute()`
- c0163 ..> c0118: `unlink_skill_from_code_artifact() calls execute()`
- c0163 ..> c0118: `unlink_skill_from_document() calls execute()`
- c0163 ..> c0118: `unlink_skill_from_file() calls execute()`
- c0163 ..> c0118: `unlink_skill_from_memory() calls execute()`
- c0163 ..> c0118: `update_skill() calls execute()`
- c0163 ..> c0128: `type in __init__`
- c0163 ..> c0131: `create_skill() calls generate_embedding()`
- c0163 ..> c0131: `search_skills() calls generate_embedding()`
- c0163 ..> c0131: `update_skill() calls generate_embedding()`
- c0163 ..> c0135: `search_skills() calls rerank()`
- c0163 ..> c0136: `type in __init__`
- c0163 ..> c0137: `create_skill() calls build_skill_embedding_text()`
- c0163 ..> c0137: `update_skill() calls build_skill_embedding_text()`
- c0163 ..> c0145: `create_skill() calls session()`
- c0163 ..> c0145: `delete_skill() calls session()`
- c0163 ..> c0145: `get_all_skill_code_artifact_links() calls session()`
- c0163 ..> c0145: `get_all_skill_document_links() calls session()`
- c0163 ..> c0145: `get_all_skill_file_links() calls session()`
- c0163 ..> c0145: `get_skill_by_id() calls session()`
- c0163 ..> c0145: `get_skill_links() calls session()`
- c0163 ..> c0145: `link_skill_to_code_artifact() calls session()`
- c0163 ..> c0145: `link_skill_to_document() calls session()`
- c0163 ..> c0145: `link_skill_to_file() calls session()`
- c0163 ..> c0145: `link_skill_to_memory() calls session()`
- c0163 ..> c0145: `list_skills() calls session()`
- c0163 ..> c0145: `search_skills() calls session()`
- c0163 ..> c0145: `skill_name_exists() calls session()`
- c0163 ..> c0145: `type in __init__`
- c0163 ..> c0145: `unlink_skill_from_code_artifact() calls session()`
- c0163 ..> c0145: `unlink_skill_from_document() calls session()`
- c0163 ..> c0145: `unlink_skill_from_file() calls session()`
- c0163 ..> c0145: `unlink_skill_from_memory() calls session()`
- c0163 ..> c0145: `update_skill() calls session()`
- c0163 ..> c0158: `create_skill() constructs SkillsTable`
- c0163 ..> c0158: `type in _to_skill`
- c0163 ..> c0163: `create_skill() calls _to_skill()`
- c0163 ..> c0163: `get_skill_by_id() calls _to_skill()`
- c0163 ..> c0163: `update_skill() calls _to_skill()`
- c0164 ..> c0025: `transition_task_state() constructs ConflictError`
- c0164 ..> c0029: `transition_task_state() constructs NotFoundError`
- c0164 ..> c0029: `update_criterion() constructs NotFoundError`
- c0164 ..> c0029: `update_task() constructs NotFoundError`
- c0164 ..> c0031: `update_criterion() calls get()`
- c0164 ..> c0078: `type in create_criterion`
- c0164 ..> c0078: `type in get_criteria_for_task`
- c0164 ..> c0078: `type in update_criterion`
- c0164 ..> c0079: `type in create_criterion`
- c0164 ..> c0080: `type in update_criterion`
- c0164 ..> c0086: `type in create_task`
- c0164 ..> c0086: `type in get_task_by_id`
- c0164 ..> c0086: `type in transition_task_state`
- c0164 ..> c0086: `type in update_task`
- c0164 ..> c0087: `type in create_task`
- c0164 ..> c0088: `type in add_dependency`
- c0164 ..> c0090: `list_tasks() constructs TaskPriority`
- c0164 ..> c0090: `list_tasks_for_user() constructs TaskPriority`
- c0164 ..> c0090: `type in list_tasks`
- c0164 ..> c0091: `list_tasks() constructs TaskState`
- c0164 ..> c0091: `list_tasks_for_user() constructs TaskState`
- c0164 ..> c0091: `type in list_tasks`
- c0164 ..> c0091: `type in transition_task_state`
- c0164 ..> c0092: `list_tasks() constructs TaskSummary`
- c0164 ..> c0092: `list_tasks_for_user() constructs TaskSummary`
- c0164 ..> c0092: `type in list_tasks`
- c0164 ..> c0092: `type in list_tasks_for_user`
- c0164 ..> c0093: `type in update_task`
- c0164 ..> c0118: `delete_criterion() calls execute()`
- c0164 ..> c0118: `delete_task() calls execute()`
- c0164 ..> c0118: `get_criteria_for_task() calls execute()`
- c0164 ..> c0118: `get_dependencies() calls execute()`
- c0164 ..> c0118: `get_dependents() calls execute()`
- c0164 ..> c0118: `get_task_by_id() calls execute()`
- c0164 ..> c0118: `list_tasks() calls execute()`
- c0164 ..> c0118: `list_tasks_for_user() calls execute()`
- c0164 ..> c0118: `remove_dependency() calls execute()`
- c0164 ..> c0118: `transition_task_state() calls execute()`
- c0164 ..> c0118: `update_criterion() calls execute()`
- c0164 ..> c0118: `update_task() calls execute()`
- c0164 ..> c0145: `add_dependency() calls session()`
- c0164 ..> c0145: `create_criterion() calls session()`
- c0164 ..> c0145: `create_task() calls session()`
- c0164 ..> c0145: `delete_criterion() calls session()`
- c0164 ..> c0145: `delete_task() calls session()`
- c0164 ..> c0145: `get_criteria_for_task() calls session()`
- c0164 ..> c0145: `get_dependencies() calls session()`
- c0164 ..> c0145: `get_dependents() calls session()`
- c0164 ..> c0145: `get_task_by_id() calls session()`
- c0164 ..> c0145: `list_tasks() calls session()`
- c0164 ..> c0145: `list_tasks_for_user() calls session()`
- c0164 ..> c0145: `remove_dependency() calls session()`
- c0164 ..> c0145: `transition_task_state() calls session()`
- c0164 ..> c0145: `type in __init__`
- c0164 ..> c0145: `update_criterion() calls session()`
- c0164 ..> c0145: `update_task() calls session()`
- c0164 ..> c0149: `create_criterion() constructs CriteriaTable`
- c0164 ..> c0159: `add_dependency() constructs TaskDependenciesTable`
- c0164 ..> c0160: `create_task() constructs TasksTable`
- c0164 ..> c0164: `update_task() calls get_task_by_id()`
- c0165 ..> c0029: `update_user() constructs NotFoundError`
- c0165 ..> c0110: `type in create_user`
- c0165 ..> c0110: `type in get_user_by_external_id`
- c0165 ..> c0110: `type in get_user_by_id`
- c0165 ..> c0110: `type in update_user`
- c0165 ..> c0111: `type in create_user`
- c0165 ..> c0113: `type in update_user`
- c0165 ..> c0118: `get_user_by_external_id() calls execute()`
- c0165 ..> c0118: `get_user_by_id() calls execute()`
- c0165 ..> c0118: `update_user() calls execute()`
- c0165 ..> c0145: `create_user() calls system_session()`
- c0165 ..> c0145: `get_user_by_external_id() calls system_session()`
- c0165 ..> c0145: `get_user_by_id() calls system_session()`
- c0165 ..> c0145: `type in __init__`
- c0165 ..> c0145: `update_user() calls system_session()`
- c0165 ..> c0161: `create_user() constructs UsersTable`
- c0166 ..> c0034: `type in count_events`
- c0166 ..> c0034: `type in query_events`
- c0166 ..> c0035: `type in save_event`
- c0166 ..> c0037: `query_events() constructs ActivityLogEntry`
- c0166 ..> c0037: `save_event() constructs ActivityLogEntry`
- c0166 ..> c0037: `type in query_events`
- c0166 ..> c0037: `type in save_event`
- c0166 ..> c0038: `type in query_events`
- c0166 ..> c0039: `type in count_events`
- c0166 ..> c0039: `type in query_events`
- c0166 ..> c0118: `cleanup_expired() calls execute()`
- c0166 ..> c0118: `count_events() calls execute()`
- c0166 ..> c0118: `query_events() calls execute()`
- c0166 ..> c0175: `cleanup_expired() calls session()`
- c0166 ..> c0175: `count_events() calls session()`
- c0166 ..> c0175: `query_events() calls session()`
- c0166 ..> c0175: `save_event() calls session()`
- c0166 ..> c0175: `type in __init__`
- c0166 ..> c0177: `save_event() constructs ActivityLogTable`
- c0167 ..> c0029: `update_code_artifact() constructs NotFoundError`
- c0167 ..> c0031: `update_code_artifact() calls get()`
- c0167 ..> c0040: `type in create_code_artifact`
- c0167 ..> c0040: `type in get_code_artifact_by_id`
- c0167 ..> c0040: `type in update_code_artifact`
- c0167 ..> c0041: `type in create_code_artifact`
- c0167 ..> c0042: `type in list_code_artifacts`
- c0167 ..> c0043: `type in update_code_artifact`
- c0167 ..> c0118: `delete_code_artifact() calls execute()`
- c0167 ..> c0118: `get_code_artifact_by_id() calls execute()`
- c0167 ..> c0118: `list_code_artifacts() calls execute()`
- c0167 ..> c0118: `update_code_artifact() calls execute()`
- c0167 ..> c0175: `create_code_artifact() calls session()`
- c0167 ..> c0175: `delete_code_artifact() calls session()`
- c0167 ..> c0175: `get_code_artifact_by_id() calls session()`
- c0167 ..> c0175: `list_code_artifacts() calls session()`
- c0167 ..> c0175: `type in __init__`
- c0167 ..> c0175: `update_code_artifact() calls session()`
- c0167 ..> c0179: `create_code_artifact() constructs CodeArtifactsTable`
- c0168 ..> c0029: `update_document() constructs NotFoundError`
- c0168 ..> c0031: `update_document() calls get()`
- c0168 ..> c0044: `type in create_document`
- c0168 ..> c0044: `type in get_document_by_id`
- c0168 ..> c0044: `type in update_document`
- c0168 ..> c0045: `type in create_document`
- c0168 ..> c0046: `type in list_documents`
- c0168 ..> c0047: `type in update_document`
- c0168 ..> c0118: `delete_document() calls execute()`
- c0168 ..> c0118: `get_document_by_id() calls execute()`
- c0168 ..> c0118: `list_documents() calls execute()`
- c0168 ..> c0118: `update_document() calls execute()`
- c0168 ..> c0175: `create_document() calls session()`
- c0168 ..> c0175: `delete_document() calls session()`
- c0168 ..> c0175: `get_document_by_id() calls session()`
- c0168 ..> c0175: `list_documents() calls session()`
- c0168 ..> c0175: `type in __init__`
- c0168 ..> c0175: `update_document() calls session()`
- c0168 ..> c0181: `create_document() constructs DocumentsTable`
- c0169 ..> c0029: `create_entity_relationship() constructs NotFoundError`
- c0169 ..> c0029: `get_entity_memories() constructs NotFoundError`
- c0169 ..> c0029: `get_entity_relationships() constructs NotFoundError`
- c0169 ..> c0029: `get_memory_entities() constructs NotFoundError`
- c0169 ..> c0029: `link_entity_to_memory() constructs NotFoundError`
- c0169 ..> c0029: `link_entity_to_project() constructs NotFoundError`
- c0169 ..> c0029: `update_entity() constructs NotFoundError`
- c0169 ..> c0029: `update_entity_relationship() constructs NotFoundError`
- c0169 ..> c0031: `update_entity() calls get()`
- c0169 ..> c0048: `type in create_entity`
- c0169 ..> c0048: `type in get_entity_by_id`
- c0169 ..> c0048: `type in update_entity`
- c0169 ..> c0049: `type in create_entity`
- c0169 ..> c0051: `create_entity_relationship() constructs EntityRelationship`
- c0169 ..> c0051: `get_all_entity_relationships() constructs EntityRelationship`
- c0169 ..> c0051: `get_entity_relationships() constructs EntityRelationship`
- c0169 ..> c0051: `type in create_entity_relationship`
- c0169 ..> c0051: `type in get_all_entity_relationships`
- c0169 ..> c0051: `type in get_entity_relationships`
- c0169 ..> c0051: `type in update_entity_relationship`
- c0169 ..> c0051: `update_entity_relationship() constructs EntityRelationship`
- c0169 ..> c0052: `type in create_entity_relationship`
- c0169 ..> c0053: `type in update_entity_relationship`
- c0169 ..> c0054: `type in list_entities`
- c0169 ..> c0054: `type in search_entities`
- c0169 ..> c0055: `type in list_entities`
- c0169 ..> c0055: `type in search_entities`
- c0169 ..> c0056: `type in update_entity`
- c0169 ..> c0118: `create_entity() calls execute()`
- c0169 ..> c0118: `create_entity_relationship() calls execute()`
- c0169 ..> c0118: `delete_entity() calls execute()`
- c0169 ..> c0118: `delete_entity_relationship() calls execute()`
- c0169 ..> c0118: `get_all_entity_file_links() calls execute()`
- c0169 ..> c0118: `get_all_entity_memory_links() calls execute()`
- c0169 ..> c0118: `get_all_entity_project_links() calls execute()`
- c0169 ..> c0118: `get_all_entity_relationships() calls execute()`
- c0169 ..> c0118: `get_entity_by_id() calls execute()`
- c0169 ..> c0118: `get_entity_memories() calls execute()`
- c0169 ..> c0118: `get_entity_relationships() calls execute()`
- c0169 ..> c0118: `get_memory_entities() calls execute()`
- c0169 ..> c0118: `link_entity_to_memory() calls execute()`
- c0169 ..> c0118: `link_entity_to_project() calls execute()`
- c0169 ..> c0118: `list_entities() calls execute()`
- c0169 ..> c0118: `search_entities() calls execute()`
- c0169 ..> c0118: `unlink_entity_from_memory() calls execute()`
- c0169 ..> c0118: `unlink_entity_from_project() calls execute()`
- c0169 ..> c0118: `update_entity() calls execute()`
- c0169 ..> c0118: `update_entity_relationship() calls execute()`
- c0169 ..> c0175: `create_entity() calls session()`
- c0169 ..> c0175: `create_entity_relationship() calls session()`
- c0169 ..> c0175: `delete_entity() calls session()`
- c0169 ..> c0175: `delete_entity_relationship() calls session()`
- c0169 ..> c0175: `get_all_entity_file_links() calls session()`
- c0169 ..> c0175: `get_all_entity_memory_links() calls session()`
- c0169 ..> c0175: `get_all_entity_project_links() calls session()`
- c0169 ..> c0175: `get_all_entity_relationships() calls session()`
- c0169 ..> c0175: `get_entity_by_id() calls session()`
- c0169 ..> c0175: `get_entity_memories() calls session()`
- c0169 ..> c0175: `get_entity_relationships() calls session()`
- c0169 ..> c0175: `get_memory_entities() calls session()`
- c0169 ..> c0175: `link_entity_to_memory() calls session()`
- c0169 ..> c0175: `link_entity_to_project() calls session()`
- c0169 ..> c0175: `list_entities() calls session()`
- c0169 ..> c0175: `search_entities() calls session()`
- c0169 ..> c0175: `type in __init__`
- c0169 ..> c0175: `unlink_entity_from_memory() calls session()`
- c0169 ..> c0175: `unlink_entity_from_project() calls session()`
- c0169 ..> c0175: `update_entity() calls session()`
- c0169 ..> c0175: `update_entity_relationship() calls session()`
- c0169 ..> c0182: `create_entity() constructs EntitiesTable`
- c0169 ..> c0183: `create_entity_relationship() constructs EntityRelationshipsTable`
- c0170 ..> c0029: `update_file() constructs NotFoundError`
- c0170 ..> c0057: `_to_file_model() constructs File`
- c0170 ..> c0057: `type in _to_file_model`
- c0170 ..> c0057: `type in create_file`
- c0170 ..> c0057: `type in get_file_by_id`
- c0170 ..> c0057: `type in update_file`
- c0170 ..> c0058: `type in create_file`
- c0170 ..> c0059: `type in list_files`
- c0170 ..> c0060: `type in update_file`
- c0170 ..> c0118: `delete_file() calls execute()`
- c0170 ..> c0118: `get_file_by_id() calls execute()`
- c0170 ..> c0118: `list_files() calls execute()`
- c0170 ..> c0118: `update_file() calls execute()`
- c0170 ..> c0170: `create_file() calls _to_file_model()`
- c0170 ..> c0170: `get_file_by_id() calls _to_file_model()`
- c0170 ..> c0170: `update_file() calls _to_file_model()`
- c0170 ..> c0175: `create_file() calls session()`
- c0170 ..> c0175: `delete_file() calls session()`
- c0170 ..> c0175: `get_file_by_id() calls session()`
- c0170 ..> c0175: `list_files() calls session()`
- c0170 ..> c0175: `type in __init__`
- c0170 ..> c0175: `update_file() calls session()`
- c0170 ..> c0184: `create_file() constructs FilesTable`
- c0170 ..> c0184: `type in _to_file_model`
- c0171 ..> c0024: `update_memory() calls clear()`
- c0171 ..> c0029: `_link_code_artifacts() constructs NotFoundError`
- c0171 ..> c0029: `_link_documents() constructs NotFoundError`
- c0171 ..> c0029: `_link_files() constructs NotFoundError`
- c0171 ..> c0029: `_link_projects() constructs NotFoundError`
- c0171 ..> c0029: `_link_skills() constructs NotFoundError`
- c0171 ..> c0029: `create_link() constructs NotFoundError`
- c0171 ..> c0029: `find_similar_memories_scored() constructs NotFoundError`
- c0171 ..> c0029: `get_linked_memories() constructs NotFoundError`
- c0171 ..> c0029: `get_memory_by_id() constructs NotFoundError`
- c0171 ..> c0029: `get_memory_table_by_id() constructs NotFoundError`
- c0171 ..> c0029: `mark_obsolete() constructs NotFoundError`
- c0171 ..> c0029: `update_memory() constructs NotFoundError`
- c0171 ..> c0031: `create_link() calls get()`
- c0171 ..> c0031: `list_memories() calls get()`
- c0171 ..> c0066: `type in create_memory`
- c0171 ..> c0066: `type in find_obsolete_matches`
- c0171 ..> c0066: `type in find_similar_memories`
- c0171 ..> c0066: `type in find_similar_memories_scored`
- c0171 ..> c0066: `type in get_linked_memories`
- c0171 ..> c0066: `type in get_memories_for_reembedding`
- c0171 ..> c0066: `type in get_memories_for_targeted_rebuild`
- c0171 ..> c0066: `type in get_memory_by_id`
- c0171 ..> c0066: `type in list_memories`
- c0171 ..> c0066: `type in search`
- c0171 ..> c0066: `type in search_scored`
- c0171 ..> c0066: `type in semantic_search`
- c0171 ..> c0066: `type in semantic_search_scored`
- c0171 ..> c0066: `type in update_memory`
- c0171 ..> c0067: `type in create_memory`
- c0171 ..> c0073: `search_scored() constructs MemoryScore`
- c0171 ..> c0073: `type in search_scored`
- c0171 ..> c0075: `type in update_memory`
- c0171 ..> c0118: `_link_code_artifacts() calls execute()`
- c0171 ..> c0118: `_link_documents() calls execute()`
- c0171 ..> c0118: `_link_files() calls execute()`
- c0171 ..> c0118: `_link_projects() calls execute()`
- c0171 ..> c0118: `_link_skills() calls execute()`
- c0171 ..> c0118: `bulk_update_embeddings() calls execute()`
- c0171 ..> c0118: `count_all_memories() calls execute()`
- c0171 ..> c0118: `count_memories_for_targeted_rebuild() calls execute()`
- c0171 ..> c0118: `create_memory() calls execute()`
- c0171 ..> c0118: `find_obsolete_matches() calls execute()`
- c0171 ..> c0118: `find_similar_memories_scored() calls execute()`
- c0171 ..> c0118: `get_linked_memories() calls execute()`
- c0171 ..> c0118: `get_memories_for_reembedding() calls execute()`
- c0171 ..> c0118: `get_memories_for_targeted_rebuild() calls execute()`
- c0171 ..> c0118: `get_memory_table_by_id() calls execute()`
- c0171 ..> c0118: `get_subgraph_nodes() calls execute()`
- c0171 ..> c0118: `list_memories() calls execute()`
- c0171 ..> c0118: `mark_obsolete() calls execute()`
- c0171 ..> c0118: `record_memory_access() calls execute()`
- c0171 ..> c0118: `reset_embedding_storage() calls execute()`
- c0171 ..> c0118: `semantic_search_scored() calls execute()`
- c0171 ..> c0118: `unlink_memories() calls execute()`
- c0171 ..> c0118: `update_memory() calls execute()`
- c0171 ..> c0118: `upsert_targeted_embeddings() calls execute()`
- c0171 ..> c0118: `validate_embedding_count() calls execute()`
- c0171 ..> c0118: `validate_embedding_dimensions() calls execute()`
- c0171 ..> c0118: `validate_search_works() calls execute()`
- c0171 ..> c0128: `type in __init__`
- c0171 ..> c0131: `_generate_embeddings() calls generate_embedding()`
- c0171 ..> c0135: `search_scored() calls rerank()`
- c0171 ..> c0136: `type in __init__`
- c0171 ..> c0137: `create_memory() calls build_embedding_text()`
- c0171 ..> c0137: `search_scored() calls build_contextual_query()`
- c0171 ..> c0137: `search_scored() calls build_memory_text()`
- c0171 ..> c0137: `update_memory() calls build_embedding_text()`
- c0171 ..> c0171: `count_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0171 ..> c0171: `create_links_batch() calls create_link()`
- c0171 ..> c0171: `create_memory() calls _generate_embeddings()`
- c0171 ..> c0171: `create_memory() calls _link_code_artifacts()`
- c0171 ..> c0171: `create_memory() calls _link_documents()`
- c0171 ..> c0171: `create_memory() calls _link_files()`
- c0171 ..> c0171: `create_memory() calls _link_projects()`
- c0171 ..> c0171: `create_memory() calls _link_skills()`
- c0171 ..> c0171: `find_similar_memories() calls find_similar_memories_scored()`
- c0171 ..> c0171: `get_memories_for_targeted_rebuild() calls _build_targeted_rebuild_filter()`
- c0171 ..> c0171: `get_memory_by_id() calls get_memory_table_by_id()`
- c0171 ..> c0171: `search() calls search_scored()`
- c0171 ..> c0171: `search_scored() calls semantic_search_scored()`
- c0171 ..> c0171: `semantic_search() calls semantic_search_scored()`
- c0171 ..> c0171: `semantic_search_scored() calls _generate_embeddings()`
- c0171 ..> c0171: `update_memory() calls _generate_embeddings()`
- c0171 ..> c0171: `update_memory() calls _link_code_artifacts()`
- c0171 ..> c0171: `update_memory() calls _link_documents()`
- c0171 ..> c0171: `update_memory() calls _link_files()`
- c0171 ..> c0171: `update_memory() calls _link_projects()`
- c0171 ..> c0171: `validate_search_works() calls _generate_embeddings()`
- c0171 ..> c0175: `bulk_update_embeddings() calls system_session()`
- c0171 ..> c0175: `count_all_memories() calls system_session()`
- c0171 ..> c0175: `count_memories_for_targeted_rebuild() calls system_session()`
- c0171 ..> c0175: `create_link() calls session()`
- c0171 ..> c0175: `create_memory() calls session()`
- c0171 ..> c0175: `find_obsolete_matches() calls session()`
- c0171 ..> c0175: `find_similar_memories_scored() calls session()`
- c0171 ..> c0175: `get_linked_memories() calls session()`
- c0171 ..> c0175: `get_memories_for_reembedding() calls system_session()`
- c0171 ..> c0175: `get_memories_for_targeted_rebuild() calls system_session()`
- c0171 ..> c0175: `get_memory_table_by_id() calls session()`
- c0171 ..> c0175: `get_subgraph_nodes() calls session()`
- c0171 ..> c0175: `list_memories() calls session()`
- c0171 ..> c0175: `mark_obsolete() calls session()`
- c0171 ..> c0175: `record_memory_access() calls system_session()`
- c0171 ..> c0175: `reset_embedding_storage() calls system_session()`
- c0171 ..> c0175: `semantic_search_scored() calls session()`
- c0171 ..> c0175: `type in __init__`
- c0171 ..> c0175: `unlink_memories() calls session()`
- c0171 ..> c0175: `update_memory() calls session()`
- c0171 ..> c0175: `upsert_targeted_embeddings() calls system_session()`
- c0171 ..> c0175: `validate_embedding_count() calls system_session()`
- c0171 ..> c0175: `validate_embedding_dimensions() calls system_session()`
- c0171 ..> c0175: `validate_search_works() calls system_session()`
- c0171 ..> c0185: `create_link() constructs MemoryLinkTable`
- c0171 ..> c0185: `type in create_link`
- c0171 ..> c0186: `create_memory() constructs MemoryTable`
- c0171 ..> c0186: `type in _link_code_artifacts`
- c0171 ..> c0186: `type in _link_documents`
- c0171 ..> c0186: `type in _link_files`
- c0171 ..> c0186: `type in _link_projects`
- c0171 ..> c0186: `type in _link_skills`
- c0171 ..> c0186: `type in get_memory_table_by_id`
- c0172 ..> c0025: `create_plan() constructs ConflictError`
- c0172 ..> c0025: `update_plan() constructs ConflictError`
- c0172 ..> c0029: `update_plan() constructs NotFoundError`
- c0172 ..> c0081: `type in create_plan`
- c0172 ..> c0081: `type in get_plan_by_id`
- c0172 ..> c0081: `type in update_plan`
- c0172 ..> c0082: `type in create_plan`
- c0172 ..> c0083: `type in list_plans`
- c0172 ..> c0084: `type in list_plans`
- c0172 ..> c0085: `type in update_plan`
- c0172 ..> c0118: `delete_plan() calls execute()`
- c0172 ..> c0118: `get_plan_by_id() calls execute()`
- c0172 ..> c0118: `list_plans() calls execute()`
- c0172 ..> c0118: `update_plan() calls execute()`
- c0172 ..> c0175: `create_plan() calls session()`
- c0172 ..> c0175: `delete_plan() calls session()`
- c0172 ..> c0175: `get_plan_by_id() calls session()`
- c0172 ..> c0175: `list_plans() calls session()`
- c0172 ..> c0175: `type in __init__`
- c0172 ..> c0175: `update_plan() calls session()`
- c0172 ..> c0187: `create_plan() constructs PlansTable`
- c0173 ..> c0029: `update_project() constructs NotFoundError`
- c0173 ..> c0094: `type in create_project`
- c0173 ..> c0094: `type in get_project_by_id`
- c0173 ..> c0094: `type in update_project`
- c0173 ..> c0095: `type in create_project`
- c0173 ..> c0096: `type in list_projects`
- c0173 ..> c0097: `type in list_projects`
- c0173 ..> c0099: `type in update_project`
- c0173 ..> c0118: `delete_project() calls execute()`
- c0173 ..> c0118: `get_project_by_id() calls execute()`
- c0173 ..> c0118: `list_projects() calls execute()`
- c0173 ..> c0118: `update_project() calls execute()`
- c0173 ..> c0175: `create_project() calls session()`
- c0173 ..> c0175: `delete_project() calls session()`
- c0173 ..> c0175: `get_project_by_id() calls session()`
- c0173 ..> c0175: `list_projects() calls session()`
- c0173 ..> c0175: `type in __init__`
- c0173 ..> c0175: `update_project() calls session()`
- c0173 ..> c0188: `create_project() constructs ProjectsTable`
- c0173 ..> c0268: `list_projects() calls repository_identity()`
- c0174 ..> c0029: `get_skill_links() constructs NotFoundError`
- c0174 ..> c0029: `link_skill_to_code_artifact() constructs NotFoundError`
- c0174 ..> c0029: `link_skill_to_document() constructs NotFoundError`
- c0174 ..> c0029: `link_skill_to_file() constructs NotFoundError`
- c0174 ..> c0029: `link_skill_to_memory() constructs NotFoundError`
- c0174 ..> c0029: `update_skill() constructs NotFoundError`
- c0174 ..> c0100: `_to_skill() constructs Skill`
- c0174 ..> c0100: `type in _to_skill`
- c0174 ..> c0100: `type in create_skill`
- c0174 ..> c0100: `type in get_skill_by_id`
- c0174 ..> c0100: `type in update_skill`
- c0174 ..> c0101: `type in create_skill`
- c0174 ..> c0102: `get_skill_links() constructs SkillLinks`
- c0174 ..> c0102: `type in get_skill_links`
- c0174 ..> c0103: `type in list_skills`
- c0174 ..> c0103: `type in search_skills`
- c0174 ..> c0104: `type in update_skill`
- c0174 ..> c0118: `create_skill() calls execute()`
- c0174 ..> c0118: `delete_skill() calls execute()`
- c0174 ..> c0118: `get_all_skill_code_artifact_links() calls execute()`
- c0174 ..> c0118: `get_all_skill_document_links() calls execute()`
- c0174 ..> c0118: `get_all_skill_file_links() calls execute()`
- c0174 ..> c0118: `get_skill_by_id() calls execute()`
- c0174 ..> c0118: `get_skill_links() calls execute()`
- c0174 ..> c0118: `link_skill_to_code_artifact() calls execute()`
- c0174 ..> c0118: `link_skill_to_document() calls execute()`
- c0174 ..> c0118: `link_skill_to_file() calls execute()`
- c0174 ..> c0118: `link_skill_to_memory() calls execute()`
- c0174 ..> c0118: `list_skills() calls execute()`
- c0174 ..> c0118: `search_skills() calls execute()`
- c0174 ..> c0118: `skill_name_exists() calls execute()`
- c0174 ..> c0118: `unlink_skill_from_code_artifact() calls execute()`
- c0174 ..> c0118: `unlink_skill_from_document() calls execute()`
- c0174 ..> c0118: `unlink_skill_from_file() calls execute()`
- c0174 ..> c0118: `unlink_skill_from_memory() calls execute()`
- c0174 ..> c0118: `update_skill() calls execute()`
- c0174 ..> c0128: `type in __init__`
- c0174 ..> c0131: `create_skill() calls generate_embedding()`
- c0174 ..> c0131: `search_skills() calls generate_embedding()`
- c0174 ..> c0131: `update_skill() calls generate_embedding()`
- c0174 ..> c0135: `search_skills() calls rerank()`
- c0174 ..> c0136: `type in __init__`
- c0174 ..> c0137: `create_skill() calls build_skill_embedding_text()`
- c0174 ..> c0137: `update_skill() calls build_skill_embedding_text()`
- c0174 ..> c0174: `create_skill() calls _to_skill()`
- c0174 ..> c0174: `get_skill_by_id() calls _to_skill()`
- c0174 ..> c0174: `update_skill() calls _to_skill()`
- c0174 ..> c0175: `create_skill() calls session()`
- c0174 ..> c0175: `delete_skill() calls session()`
- c0174 ..> c0175: `get_all_skill_code_artifact_links() calls session()`
- c0174 ..> c0175: `get_all_skill_document_links() calls session()`
- c0174 ..> c0175: `get_all_skill_file_links() calls session()`
- c0174 ..> c0175: `get_skill_by_id() calls session()`
- c0174 ..> c0175: `get_skill_links() calls session()`
- c0174 ..> c0175: `link_skill_to_code_artifact() calls session()`
- c0174 ..> c0175: `link_skill_to_document() calls session()`
- c0174 ..> c0175: `link_skill_to_file() calls session()`
- c0174 ..> c0175: `link_skill_to_memory() calls session()`
- c0174 ..> c0175: `list_skills() calls session()`
- c0174 ..> c0175: `search_skills() calls session()`
- c0174 ..> c0175: `skill_name_exists() calls session()`
- c0174 ..> c0175: `type in __init__`
- c0174 ..> c0175: `unlink_skill_from_code_artifact() calls session()`
- c0174 ..> c0175: `unlink_skill_from_document() calls session()`
- c0174 ..> c0175: `unlink_skill_from_file() calls session()`
- c0174 ..> c0175: `unlink_skill_from_memory() calls session()`
- c0174 ..> c0175: `update_skill() calls session()`
- c0174 ..> c0189: `create_skill() constructs SkillsTable`
- c0174 ..> c0189: `type in _to_skill`
- c0175 ..> c0003: `_run_migrations() calls upgrade()`
- c0175 ..> c0118: `init_db() calls execute()`
- c0175 ..> c0118: `session() calls close()`
- c0175 ..> c0118: `system_session() calls close()`
- c0175 ..> c0145: `dispose() calls dispose()`
- c0175 ..> c0175: `__init__() calls _construct_connection_string()`
- c0175 ..> c0175: `_run_migrations() calls _construct_connection_string()`
- c0176 ..> c0118: `_sqlite_connection_creator() calls execute()`
- c0177 --|> c0178: `inherits`
- c0179 --|> c0178: `inherits`
- c0179 --> c0186: `field memories`
- c0179 --> c0188: `field project`
- c0179 --> c0189: `field skills`
- c0179 --> c0192: `field user`
- c0180 --|> c0178: `inherits`
- c0180 --> c0191: `field task`
- c0181 --|> c0178: `inherits`
- c0181 --> c0186: `field memories`
- c0181 --> c0188: `field project`
- c0181 --> c0189: `field skills`
- c0181 --> c0192: `field user`
- c0182 --|> c0178: `inherits`
- c0182 --> c0183: `field incoming_relationships`
- c0182 --> c0183: `field outgoing_relationships`
- c0182 --> c0184: `field files`
- c0182 --> c0186: `field memories`
- c0182 --> c0188: `field projects`
- c0182 --> c0192: `field user`
- c0183 --|> c0178: `inherits`
- c0183 --> c0182: `field source_entity`
- c0183 --> c0182: `field target_entity`
- c0184 --|> c0178: `inherits`
- c0184 --> c0182: `field entities`
- c0184 --> c0186: `field memories`
- c0184 --> c0188: `field project`
- c0184 --> c0189: `field skills`
- c0184 --> c0192: `field user`
- c0185 --|> c0178: `inherits`
- c0186 --|> c0178: `inherits`
- c0186 --> c0179: `field code_artifacts`
- c0186 --> c0181: `field documents`
- c0186 --> c0182: `field entities`
- c0186 --> c0184: `field files`
- c0186 --> c0188: `field projects`
- c0186 --> c0189: `field skills`
- c0186 --> c0192: `field user`
- c0187 --|> c0178: `inherits`
- c0187 --> c0188: `field project`
- c0187 --> c0191: `field tasks`
- c0187 --> c0192: `field user`
- c0188 --|> c0178: `inherits`
- c0188 --> c0179: `field code_artifacts`
- c0188 --> c0181: `field documents`
- c0188 --> c0182: `field entities`
- c0188 --> c0184: `field files`
- c0188 --> c0186: `field memories`
- c0188 --> c0187: `field plans`
- c0188 --> c0189: `field skills`
- c0188 --> c0192: `field user`
- c0189 --|> c0178: `inherits`
- c0189 --> c0179: `field code_artifacts`
- c0189 --> c0181: `field documents`
- c0189 --> c0184: `field files`
- c0189 --> c0186: `field memories`
- c0189 --> c0188: `field project`
- c0189 --> c0192: `field user`
- c0190 --|> c0178: `inherits`
- c0190 --> c0191: `field task`
- c0191 --|> c0178: `inherits`
- c0191 --> c0180: `field criteria`
- c0191 --> c0187: `field plan`
- c0191 --> c0190: `field depends_on`
- c0192 --|> c0178: `inherits`
- c0192 --> c0179: `field code_artifacts`
- c0192 --> c0181: `field documents`
- c0192 --> c0182: `field entities`
- c0192 --> c0184: `field files`
- c0192 --> c0186: `field memories`
- c0192 --> c0187: `field plans`
- c0192 --> c0188: `field projects`
- c0192 --> c0189: `field skills`
- c0193 ..> c0025: `transition_task_state() constructs ConflictError`
- c0193 ..> c0029: `transition_task_state() constructs NotFoundError`
- c0193 ..> c0029: `update_criterion() constructs NotFoundError`
- c0193 ..> c0029: `update_task() constructs NotFoundError`
- c0193 ..> c0031: `update_criterion() calls get()`
- c0193 ..> c0078: `type in create_criterion`
- c0193 ..> c0078: `type in get_criteria_for_task`
- c0193 ..> c0078: `type in update_criterion`
- c0193 ..> c0079: `type in create_criterion`
- c0193 ..> c0080: `type in update_criterion`
- c0193 ..> c0086: `type in create_task`
- c0193 ..> c0086: `type in get_task_by_id`
- c0193 ..> c0086: `type in transition_task_state`
- c0193 ..> c0086: `type in update_task`
- c0193 ..> c0087: `type in create_task`
- c0193 ..> c0088: `type in add_dependency`
- c0193 ..> c0090: `list_tasks() constructs TaskPriority`
- c0193 ..> c0090: `list_tasks_for_user() constructs TaskPriority`
- c0193 ..> c0090: `type in list_tasks`
- c0193 ..> c0091: `list_tasks() constructs TaskState`
- c0193 ..> c0091: `list_tasks_for_user() constructs TaskState`
- c0193 ..> c0091: `type in list_tasks`
- c0193 ..> c0091: `type in transition_task_state`
- c0193 ..> c0092: `list_tasks() constructs TaskSummary`
- c0193 ..> c0092: `list_tasks_for_user() constructs TaskSummary`
- c0193 ..> c0092: `type in list_tasks`
- c0193 ..> c0092: `type in list_tasks_for_user`
- c0193 ..> c0093: `type in update_task`
- c0193 ..> c0118: `delete_criterion() calls execute()`
- c0193 ..> c0118: `delete_task() calls execute()`
- c0193 ..> c0118: `get_criteria_for_task() calls execute()`
- c0193 ..> c0118: `get_dependencies() calls execute()`
- c0193 ..> c0118: `get_dependents() calls execute()`
- c0193 ..> c0118: `get_task_by_id() calls execute()`
- c0193 ..> c0118: `list_tasks() calls execute()`
- c0193 ..> c0118: `list_tasks_for_user() calls execute()`
- c0193 ..> c0118: `remove_dependency() calls execute()`
- c0193 ..> c0118: `transition_task_state() calls execute()`
- c0193 ..> c0118: `update_criterion() calls execute()`
- c0193 ..> c0118: `update_task() calls execute()`
- c0193 ..> c0175: `add_dependency() calls session()`
- c0193 ..> c0175: `create_criterion() calls session()`
- c0193 ..> c0175: `create_task() calls session()`
- c0193 ..> c0175: `delete_criterion() calls session()`
- c0193 ..> c0175: `delete_task() calls session()`
- c0193 ..> c0175: `get_criteria_for_task() calls session()`
- c0193 ..> c0175: `get_dependencies() calls session()`
- c0193 ..> c0175: `get_dependents() calls session()`
- c0193 ..> c0175: `get_task_by_id() calls session()`
- c0193 ..> c0175: `list_tasks() calls session()`
- c0193 ..> c0175: `list_tasks_for_user() calls session()`
- c0193 ..> c0175: `remove_dependency() calls session()`
- c0193 ..> c0175: `transition_task_state() calls session()`
- c0193 ..> c0175: `type in __init__`
- c0193 ..> c0175: `update_criterion() calls session()`
- c0193 ..> c0175: `update_task() calls session()`
- c0193 ..> c0180: `create_criterion() constructs CriteriaTable`
- c0193 ..> c0190: `add_dependency() constructs TaskDependenciesTable`
- c0193 ..> c0191: `create_task() constructs TasksTable`
- c0193 ..> c0193: `update_task() calls get_task_by_id()`
- c0194 ..> c0029: `update_user() constructs NotFoundError`
- c0194 ..> c0110: `type in create_user`
- c0194 ..> c0110: `type in get_user_by_external_id`
- c0194 ..> c0110: `type in get_user_by_id`
- c0194 ..> c0110: `type in update_user`
- c0194 ..> c0111: `type in create_user`
- c0194 ..> c0113: `type in update_user`
- c0194 ..> c0118: `get_user_by_external_id() calls execute()`
- c0194 ..> c0118: `get_user_by_id() calls execute()`
- c0194 ..> c0118: `update_user() calls execute()`
- c0194 ..> c0175: `create_user() calls system_session()`
- c0194 ..> c0175: `get_user_by_external_id() calls system_session()`
- c0194 ..> c0175: `get_user_by_id() calls system_session()`
- c0194 ..> c0175: `type in __init__`
- c0194 ..> c0175: `update_user() calls system_session()`
- c0194 ..> c0192: `create_user() constructs UsersTable`
- c0195 ..> c0031: `parse_datetime_param() calls get()`
- c0195 ..> c0031: `parse_int_param() calls get()`
- c0199 ..> c0031: `parse_int_param() calls get()`
- c0203 ..> c0031: `parse_int_param() calls get()`
- c0208 ..> c0031: `status() calls get()`
- c0208 ..> c0208: `login() calls upsert_env_var()`
- c0208 ..> c0208: `status() calls _has_cached_credentials()`
- c0208 ..> c0213: `login() calls token_cache_dir()`
- c0208 ..> c0213: `login() calls user_env_file()`
- c0208 ..> c0213: `logout() calls token_cache_dir()`
- c0208 ..> c0213: `status() calls token_cache_dir()`
- c0208 ..> c0214: `status() calls close()`
- c0208 ..> c0214: `status() calls execute()`
- c0208 ..> c0214: `status() constructs RemoteExecutor`
- c0208 ..> c0215: `login() calls normalize_server_url()`
- c0208 ..> c0215: `status() calls normalize_server_url()`
- c0209 ..> c0014: `type in __init__`
- c0209 ..> c0210: `__init__() constructs _CliRuntime`
- c0210 ..> c0014: `type in __init__`
- c0211 ..> c0014: `type in __init__`
- c0211 ..> c0016: `close() calls dispose_runtime()`
- c0211 ..> c0016: `create() calls build_runtime()`
- c0211 ..> c0118: `execute() calls execute()`
- c0211 ..> c0209: `__init__() constructs CliContext`
- c0211 ..> c0223: `execute() calls ensure_tool_executable()`
- c0211 ..> c0223: `list_tools() calls build_discovery_payload()`
- c0211 ..> c0223: `tool_info() calls build_tool_documentation()`
- c0212 ..> c0031: `_build_executor() calls get()`
- c0212 ..> c0118: `_run_tool_command() calls close()`
- c0212 ..> c0118: `_run_tool_command() calls execute()`
- c0212 ..> c0118: `_run_tool_command() calls list_tools()`
- c0212 ..> c0118: `_run_tool_command() calls tool_info()`
- c0212 ..> c0208: `_run_auth_command() calls login()`
- c0212 ..> c0208: `_run_auth_command() calls logout()`
- c0212 ..> c0208: `_run_auth_command() calls status()`
- c0212 ..> c0211: `_build_executor() calls create()`
- c0212 ..> c0212: `_run_tool_command() calls _build_executor()`
- c0212 ..> c0212: `dispatch() calls _run_auth_command()`
- c0212 ..> c0212: `dispatch() calls _run_tool_command()`
- c0212 ..> c0212: `dispatch() calls build_parser()`
- c0212 ..> c0214: `_build_executor() constructs RemoteExecutor`
- c0212 ..> c0216: `_run_auth_command() calls emit_error()`
- c0212 ..> c0216: `_run_tool_command() calls emit_error()`
- c0212 ..> c0216: `_run_tool_command() calls render_result()`
- c0212 ..> c0218: `_run_tool_command() calls run()`
- c0212 ..> c0218: `dispatch() calls run()`
- c0212 ..> c0270: `build_parser() calls get_version()`
- c0213 ..> c0213: `token_cache_dir() calls config_dir()`
- c0213 ..> c0213: `user_env_file() calls config_dir()`
- c0214 ..> c0118: `close() calls close()`
- c0214 ..> c0214: `execute() calls _call()`
- c0214 ..> c0214: `list_tools() calls _call()`
- c0214 ..> c0214: `tool_info() calls _call()`
- c0214 ..> c0215: `__init__() calls normalize_server_url()`
- c0215 ..> c0213: `_default_client_factory() calls token_cache_dir()`
- c0216 ..> c0031: `render_memory_detail() calls get()`
- c0216 ..> c0031: `render_memory_lines() calls get()`
- c0216 ..> c0031: `render_project_lines() calls get()`
- c0216 ..> c0216: `render_result() calls to_jsonable()`
- c0218 ..> c0031: `_memory_recent() calls get()`
- c0218 ..> c0031: `_memory_search() calls get()`
- c0218 ..> c0031: `_project_list() calls get()`
- c0218 ..> c0031: `resolve_project() calls get()`
- c0218 ..> c0118: `_memory_get() calls execute()`
- c0218 ..> c0118: `_memory_recent() calls execute()`
- c0218 ..> c0118: `_memory_save() calls execute()`
- c0218 ..> c0118: `_memory_search() calls execute()`
- c0218 ..> c0118: `_project_list() calls execute()`
- c0218 ..> c0118: `resolve_project() calls execute()`
- c0218 ..> c0216: `_memory_get() calls render_memory_detail()`
- c0218 ..> c0216: `_memory_get() calls to_jsonable()`
- c0218 ..> c0216: `_memory_recent() calls render_memory_lines()`
- c0218 ..> c0216: `_memory_recent() calls to_jsonable()`
- c0218 ..> c0216: `_memory_save() calls to_jsonable()`
- c0218 ..> c0216: `_memory_search() calls render_memory_lines()`
- c0218 ..> c0216: `_memory_search() calls to_jsonable()`
- c0218 ..> c0216: `_project_list() calls render_project_lines()`
- c0218 ..> c0216: `_project_list() calls to_jsonable()`
- c0218 ..> c0216: `resolve_project() calls to_jsonable()`
- c0218 ..> c0217: `resolve_project() constructs CliError`
- c0218 ..> c0218: `_memory_recent() calls resolve_project()`
- c0218 ..> c0218: `_memory_save() calls resolve_project()`
- c0218 ..> c0218: `_memory_search() calls resolve_project()`
- c0218 ..> c0218: `run() calls _project_list()`
- c0223 ..> c0105: `build_discovery_payload() constructs ToolCategory`
- c0223 ..> c0108: `build_discovery_payload() calls to_discovery_dict()`
- c0223 ..> c0108: `build_tool_documentation() calls to_detailed_dict()`
- c0223 ..> c0223: `_build_discover_docstring() calls _build_category_list()`
- c0223 ..> c0223: `_build_discover_docstring() calls _build_compact_discover_docstring()`
- c0223 ..> c0223: `_build_discover_docstring() calls _get_mcp_descriptor_mode()`
- c0223 ..> c0223: `_build_execute_docstring() calls _build_compact_execute_docstring()`
- c0223 ..> c0223: `_build_execute_docstring() calls _build_tool_categories_line()`
- c0223 ..> c0223: `_build_execute_docstring() calls _get_mcp_descriptor_mode()`
- c0223 ..> c0223: `register() calls _build_discover_docstring()`
- c0223 ..> c0223: `register() calls _build_execute_docstring()`
- c0223 ..> c0226: `build_tool_documentation() calls get_required_scope()`
- c0223 ..> c0226: `ensure_tool_executable() calls get_required_scope()`
- c0223 ..> c0240: `build_discovery_payload() calls get_permitted_by_category()`
- c0223 ..> c0240: `build_discovery_payload() calls get_permitted_categories()`
- c0223 ..> c0240: `build_discovery_payload() calls get_permitted_tools()`
- c0223 ..> c0240: `build_tool_documentation() calls get_permitted_tools()`
- c0223 ..> c0240: `build_tool_documentation() calls get_tool()`
- c0223 ..> c0240: `build_tool_documentation() calls is_permitted()`
- c0223 ..> c0240: `ensure_tool_executable() calls get_permitted_tools()`
- c0223 ..> c0240: `ensure_tool_executable() calls tool_exists()`
- c0226 ..> c0031: `_extract_token_scopes() calls get()`
- c0226 ..> c0031: `get_required_scope() calls get()`
- c0226 ..> c0031: `resolve_permitted_tools() calls get()`
- c0226 ..> c0226: `_extract_token_scopes() calls parse_scopes()`
- c0226 ..> c0226: `get_effective_scopes() calls _extract_token_scopes()`
- c0226 ..> c0226: `get_effective_scopes() calls resolve_permitted_tools()`
- c0226 ..> c0240: `get_effective_scopes() calls list_all_tools()`
- c0226 ..> c0240: `get_required_scope() calls get_tool()`
- c0226 ..> c0240: `resolve_permitted_tools() calls list_all_tools()`
- c0226 ..> c0240: `type in get_required_scope`
- c0226 ..> c0240: `type in resolve_permitted_tools`
- c0228 ..> c0032: `create_code_artifact() calls get_user_from_auth()`
- c0228 ..> c0032: `delete_code_artifact() calls get_user_from_auth()`
- c0228 ..> c0032: `get_code_artifact() calls get_user_from_auth()`
- c0228 ..> c0032: `list_code_artifacts() calls get_user_from_auth()`
- c0228 ..> c0032: `update_code_artifact() calls get_user_from_auth()`
- c0228 ..> c0040: `type in create_code_artifact`
- c0228 ..> c0040: `type in get_code_artifact`
- c0228 ..> c0040: `type in update_code_artifact`
- c0228 ..> c0041: `create_code_artifact() constructs CodeArtifactCreate`
- c0228 ..> c0043: `update_code_artifact() constructs CodeArtifactUpdate`
- c0228 ..> c0244: `create_code_artifact() calls create_code_artifact()`
- c0228 ..> c0244: `delete_code_artifact() calls delete_code_artifact()`
- c0228 ..> c0244: `get_code_artifact() calls get_code_artifact()`
- c0228 ..> c0244: `list_code_artifacts() calls list_code_artifacts()`
- c0228 ..> c0244: `type in __init__`
- c0228 ..> c0244: `update_code_artifact() calls update_code_artifact()`
- c0228 ..> c0265: `type in __init__`
- c0228 ..> c0267: `update_code_artifact() calls filter_none_values()`
- c0229 ..> c0032: `create_document() calls get_user_from_auth()`
- c0229 ..> c0032: `delete_document() calls get_user_from_auth()`
- c0229 ..> c0032: `get_document() calls get_user_from_auth()`
- c0229 ..> c0032: `list_documents() calls get_user_from_auth()`
- c0229 ..> c0032: `update_document() calls get_user_from_auth()`
- c0229 ..> c0044: `type in create_document`
- c0229 ..> c0044: `type in get_document`
- c0229 ..> c0044: `type in update_document`
- c0229 ..> c0045: `create_document() constructs DocumentCreate`
- c0229 ..> c0047: `update_document() constructs DocumentUpdate`
- c0229 ..> c0245: `create_document() calls create_document()`
- c0229 ..> c0245: `delete_document() calls delete_document()`
- c0229 ..> c0245: `get_document() calls get_document()`
- c0229 ..> c0245: `list_documents() calls list_documents()`
- c0229 ..> c0245: `type in __init__`
- c0229 ..> c0245: `update_document() calls update_document()`
- c0229 ..> c0265: `type in __init__`
- c0229 ..> c0267: `update_document() calls filter_none_values()`
- c0230 ..> c0032: `create_entity() calls get_user_from_auth()`
- c0230 ..> c0032: `create_entity_relationship() calls get_user_from_auth()`
- c0230 ..> c0032: `delete_entity() calls get_user_from_auth()`
- c0230 ..> c0032: `delete_entity_relationship() calls get_user_from_auth()`
- c0230 ..> c0032: `get_entity() calls get_user_from_auth()`
- c0230 ..> c0032: `get_entity_memories() calls get_user_from_auth()`
- c0230 ..> c0032: `get_entity_relationships() calls get_user_from_auth()`
- c0230 ..> c0032: `get_memory_entities() calls get_user_from_auth()`
- c0230 ..> c0032: `link_entity_to_memory() calls get_user_from_auth()`
- c0230 ..> c0032: `link_entity_to_project() calls get_user_from_auth()`
- c0230 ..> c0032: `list_entities() calls get_user_from_auth()`
- c0230 ..> c0032: `search_entities() calls get_user_from_auth()`
- c0230 ..> c0032: `unlink_entity_from_memory() calls get_user_from_auth()`
- c0230 ..> c0032: `unlink_entity_from_project() calls get_user_from_auth()`
- c0230 ..> c0032: `update_entity() calls get_user_from_auth()`
- c0230 ..> c0032: `update_entity_relationship() calls get_user_from_auth()`
- c0230 ..> c0048: `type in create_entity`
- c0230 ..> c0048: `type in get_entity`
- c0230 ..> c0048: `type in update_entity`
- c0230 ..> c0049: `create_entity() constructs EntityCreate`
- c0230 ..> c0051: `type in create_entity_relationship`
- c0230 ..> c0051: `type in update_entity_relationship`
- c0230 ..> c0052: `create_entity_relationship() constructs EntityRelationshipCreate`
- c0230 ..> c0053: `update_entity_relationship() constructs EntityRelationshipUpdate`
- c0230 ..> c0055: `list_entities() constructs EntityType`
- c0230 ..> c0055: `search_entities() constructs EntityType`
- c0230 ..> c0056: `update_entity() constructs EntityUpdate`
- c0230 ..> c0246: `create_entity() calls create_entity()`
- c0230 ..> c0246: `create_entity_relationship() calls create_entity_relationship()`
- c0230 ..> c0246: `delete_entity() calls delete_entity()`
- c0230 ..> c0246: `delete_entity_relationship() calls delete_entity_relationship()`
- c0230 ..> c0246: `get_entity() calls get_entity()`
- c0230 ..> c0246: `get_entity_memories() calls get_entity_memories()`
- c0230 ..> c0246: `get_entity_relationships() calls get_entity_relationships()`
- c0230 ..> c0246: `get_memory_entities() calls get_memory_entities()`
- c0230 ..> c0246: `link_entity_to_memory() calls link_entity_to_memory()`
- c0230 ..> c0246: `link_entity_to_project() calls link_entity_to_project()`
- c0230 ..> c0246: `list_entities() calls list_entities()`
- c0230 ..> c0246: `search_entities() calls search_entities()`
- c0230 ..> c0246: `type in __init__`
- c0230 ..> c0246: `unlink_entity_from_memory() calls unlink_entity_from_memory()`
- c0230 ..> c0246: `unlink_entity_from_project() calls unlink_entity_from_project()`
- c0230 ..> c0246: `update_entity() calls update_entity()`
- c0230 ..> c0246: `update_entity_relationship() calls update_entity_relationship()`
- c0230 ..> c0265: `type in __init__`
- c0230 ..> c0267: `create_entity() calls filter_none_values()`
- c0230 ..> c0267: `update_entity() calls filter_none_values()`
- c0230 ..> c0267: `update_entity_relationship() calls filter_none_values()`
- c0231 ..> c0032: `create_file() calls get_user_from_auth()`
- c0231 ..> c0032: `delete_file() calls get_user_from_auth()`
- c0231 ..> c0032: `get_file() calls get_user_from_auth()`
- c0231 ..> c0032: `list_files() calls get_user_from_auth()`
- c0231 ..> c0032: `update_file() calls get_user_from_auth()`
- c0231 ..> c0058: `create_file() constructs FileCreate`
- c0231 ..> c0060: `update_file() constructs FileUpdate`
- c0231 ..> c0119: `create_file() calls create_file()`
- c0231 ..> c0119: `delete_file() calls delete_file()`
- c0231 ..> c0119: `list_files() calls list_files()`
- c0231 ..> c0119: `update_file() calls update_file()`
- c0231 ..> c0247: `get_file() calls get_file()`
- c0231 ..> c0265: `type in __init__`
- c0231 ..> c0267: `update_file() calls filter_none_values()`
- c0232 ..> c0032: `create_memory() calls get_user_from_auth()`
- c0232 ..> c0032: `get_memory() calls get_user_from_auth()`
- c0232 ..> c0032: `get_recent_memories() calls get_user_from_auth()`
- c0232 ..> c0032: `link_memories() calls get_user_from_auth()`
- c0232 ..> c0032: `mark_memory_obsolete() calls get_user_from_auth()`
- c0232 ..> c0032: `query_memory() calls get_user_from_auth()`
- c0232 ..> c0032: `rebuild_embeddings() calls get_user_from_auth()`
- c0232 ..> c0032: `unlink_memories() calls get_user_from_auth()`
- c0232 ..> c0032: `update_memory() calls get_user_from_auth()`
- c0232 ..> c0066: `type in get_memory`
- c0232 ..> c0066: `type in update_memory`
- c0232 ..> c0067: `create_memory() constructs MemoryCreate`
- c0232 ..> c0068: `create_memory() constructs MemoryCreateResponse`
- c0232 ..> c0068: `type in create_memory`
- c0232 ..> c0071: `query_memory() constructs MemoryQueryRequest`
- c0232 ..> c0072: `type in query_memory`
- c0232 ..> c0075: `update_memory() constructs MemoryUpdate`
- c0232 ..> c0120: `_validate_rebuild_scope() calls count_memories_for_targeted_rebuild()`
- c0232 ..> c0224: `get_recent_memories() calls clamp_list_pagination()`
- c0232 ..> c0232: `rebuild_embeddings() calls _build_re_embedding_service()`
- c0232 ..> c0232: `rebuild_embeddings() calls _validate_rebuild_scope()`
- c0232 ..> c0238: `create_memory() calls _coerce_int_id()`
- c0232 ..> c0238: `create_memory() calls _coerce_int_ids()`
- c0232 ..> c0238: `get_memory() calls _coerce_int_id()`
- c0232 ..> c0238: `get_recent_memories() calls _coerce_int_id()`
- c0232 ..> c0238: `link_memories() calls _coerce_int_id()`
- c0232 ..> c0238: `link_memories() calls _coerce_int_ids()`
- c0232 ..> c0238: `mark_memory_obsolete() calls _coerce_int_id()`
- c0232 ..> c0238: `query_memory() calls _coerce_int_id()`
- c0232 ..> c0238: `rebuild_embeddings() calls _coerce_int_id()`
- c0232 ..> c0238: `unlink_memories() calls _coerce_int_id()`
- c0232 ..> c0238: `unlink_memories() calls _coerce_int_ids()`
- c0232 ..> c0238: `update_memory() calls _coerce_int_id()`
- c0232 ..> c0238: `update_memory() calls _coerce_int_ids()`
- c0232 ..> c0256: `create_memory() calls create_memory()`
- c0232 ..> c0256: `create_memory() calls find_obsolete_matches()`
- c0232 ..> c0256: `get_memory() calls get_memory()`
- c0232 ..> c0256: `get_recent_memories() calls list_memories()`
- c0232 ..> c0256: `link_memories() calls link_memories()`
- c0232 ..> c0256: `mark_memory_obsolete() calls mark_memory_obsolete()`
- c0232 ..> c0256: `query_memory() calls query_memory()`
- c0232 ..> c0256: `type in __init__`
- c0232 ..> c0256: `unlink_memories() calls unlink_memories()`
- c0232 ..> c0256: `update_memory() calls update_memory()`
- c0232 ..> c0260: `_build_re_embedding_service() constructs ReEmbeddingService`
- c0232 ..> c0260: `rebuild_embeddings() calls rebuild_targeted()`
- c0232 ..> c0260: `type in _build_re_embedding_service`
- c0232 ..> c0265: `type in __init__`
- c0232 ..> c0267: `update_memory() calls filter_none_values()`
- c0233 ..> c0032: `create_plan() calls get_user_from_auth()`
- c0233 ..> c0032: `get_plan() calls get_user_from_auth()`
- c0233 ..> c0032: `list_plans() calls get_user_from_auth()`
- c0233 ..> c0032: `update_plan() calls get_user_from_auth()`
- c0233 ..> c0082: `create_plan() constructs PlanCreate`
- c0233 ..> c0083: `create_plan() constructs PlanStatus`
- c0233 ..> c0083: `list_plans() constructs PlanStatus`
- c0233 ..> c0083: `update_plan() constructs PlanStatus`
- c0233 ..> c0085: `update_plan() constructs PlanUpdate`
- c0233 ..> c0122: `create_plan() calls create_plan()`
- c0233 ..> c0122: `list_plans() calls list_plans()`
- c0233 ..> c0122: `update_plan() calls update_plan()`
- c0233 ..> c0252: `get_plan() calls get_plan()`
- c0233 ..> c0267: `update_plan() calls filter_none_values()`
- c0234 ..> c0032: `create_project() calls get_user_from_auth()`
- c0234 ..> c0032: `delete_project() calls get_user_from_auth()`
- c0234 ..> c0032: `get_project() calls get_user_from_auth()`
- c0234 ..> c0032: `list_projects() calls get_user_from_auth()`
- c0234 ..> c0032: `update_project() calls get_user_from_auth()`
- c0234 ..> c0094: `type in create_project`
- c0234 ..> c0094: `type in get_project`
- c0234 ..> c0094: `type in update_project`
- c0234 ..> c0095: `create_project() constructs ProjectCreate`
- c0234 ..> c0096: `list_projects() constructs ProjectStatus`
- c0234 ..> c0096: `type in create_project`
- c0234 ..> c0096: `type in update_project`
- c0234 ..> c0098: `type in create_project`
- c0234 ..> c0098: `type in update_project`
- c0234 ..> c0099: `update_project() constructs ProjectUpdate`
- c0234 ..> c0258: `create_project() calls create_project()`
- c0234 ..> c0258: `delete_project() calls delete_project()`
- c0234 ..> c0258: `get_project() calls get_project()`
- c0234 ..> c0258: `list_projects() calls list_projects()`
- c0234 ..> c0258: `type in __init__`
- c0234 ..> c0258: `update_project() calls update_project()`
- c0234 ..> c0265: `type in __init__`
- c0234 ..> c0267: `update_project() calls filter_none_values()`
- c0235 ..> c0032: `create_skill() calls get_user_from_auth()`
- c0235 ..> c0032: `delete_skill() calls get_user_from_auth()`
- c0235 ..> c0032: `export_skill() calls get_user_from_auth()`
- c0235 ..> c0032: `get_skill() calls get_user_from_auth()`
- c0235 ..> c0032: `get_skill_links() calls get_user_from_auth()`
- c0235 ..> c0032: `import_skill() calls get_user_from_auth()`
- c0235 ..> c0032: `link_skill_to_code_artifact() calls get_user_from_auth()`
- c0235 ..> c0032: `link_skill_to_document() calls get_user_from_auth()`
- c0235 ..> c0032: `link_skill_to_file() calls get_user_from_auth()`
- c0235 ..> c0032: `link_skill_to_memory() calls get_user_from_auth()`
- c0235 ..> c0032: `list_skills() calls get_user_from_auth()`
- c0235 ..> c0032: `search_skills() calls get_user_from_auth()`
- c0235 ..> c0032: `unlink_skill_from_code_artifact() calls get_user_from_auth()`
- c0235 ..> c0032: `unlink_skill_from_document() calls get_user_from_auth()`
- c0235 ..> c0032: `unlink_skill_from_file() calls get_user_from_auth()`
- c0235 ..> c0032: `unlink_skill_from_memory() calls get_user_from_auth()`
- c0235 ..> c0032: `update_skill() calls get_user_from_auth()`
- c0235 ..> c0101: `create_skill() constructs SkillCreate`
- c0235 ..> c0104: `update_skill() constructs SkillUpdate`
- c0235 ..> c0124: `create_skill() calls create_skill()`
- c0235 ..> c0124: `delete_skill() calls delete_skill()`
- c0235 ..> c0124: `get_skill_links() calls get_skill_links()`
- c0235 ..> c0124: `link_skill_to_code_artifact() calls link_skill_to_code_artifact()`
- c0235 ..> c0124: `link_skill_to_document() calls link_skill_to_document()`
- c0235 ..> c0124: `link_skill_to_file() calls link_skill_to_file()`
- c0235 ..> c0124: `link_skill_to_memory() calls link_skill_to_memory()`
- c0235 ..> c0124: `list_skills() calls list_skills()`
- c0235 ..> c0124: `search_skills() calls search_skills()`
- c0235 ..> c0124: `unlink_skill_from_code_artifact() calls unlink_skill_from_code_artifact()`
- c0235 ..> c0124: `unlink_skill_from_document() calls unlink_skill_from_document()`
- c0235 ..> c0124: `unlink_skill_from_file() calls unlink_skill_from_file()`
- c0235 ..> c0124: `unlink_skill_from_memory() calls unlink_skill_from_memory()`
- c0235 ..> c0124: `update_skill() calls update_skill()`
- c0235 ..> c0254: `get_skill() calls get_skill()`
- c0235 ..> c0262: `export_skill() calls export_skill()`
- c0235 ..> c0262: `import_skill() calls import_skill()`
- c0235 ..> c0265: `type in __init__`
- c0235 ..> c0267: `update_skill() calls filter_none_values()`
- c0236 ..> c0032: `add_criterion() calls get_user_from_auth()`
- c0236 ..> c0032: `add_dependency() calls get_user_from_auth()`
- c0236 ..> c0032: `claim_task() calls get_user_from_auth()`
- c0236 ..> c0032: `create_task() calls get_user_from_auth()`
- c0236 ..> c0032: `delete_criterion() calls get_user_from_auth()`
- c0236 ..> c0032: `get_task() calls get_user_from_auth()`
- c0236 ..> c0032: `query_tasks() calls get_user_from_auth()`
- c0236 ..> c0032: `remove_dependency() calls get_user_from_auth()`
- c0236 ..> c0032: `transition_task() calls get_user_from_auth()`
- c0236 ..> c0032: `update_task() calls get_user_from_auth()`
- c0236 ..> c0032: `verify_criterion() calls get_user_from_auth()`
- c0236 ..> c0079: `add_criterion() constructs CriterionCreate`
- c0236 ..> c0079: `create_task() constructs CriterionCreate`
- c0236 ..> c0080: `verify_criterion() constructs CriterionUpdate`
- c0236 ..> c0087: `create_task() constructs TaskCreate`
- c0236 ..> c0090: `create_task() constructs TaskPriority`
- c0236 ..> c0090: `query_tasks() constructs TaskPriority`
- c0236 ..> c0090: `update_task() constructs TaskPriority`
- c0236 ..> c0091: `query_tasks() constructs TaskState`
- c0236 ..> c0091: `transition_task() constructs TaskState`
- c0236 ..> c0093: `update_task() constructs TaskUpdate`
- c0236 ..> c0125: `add_dependency() calls add_dependency()`
- c0236 ..> c0125: `create_task() calls create_task()`
- c0236 ..> c0125: `delete_criterion() calls delete_criterion()`
- c0236 ..> c0125: `query_tasks() calls list_tasks()`
- c0236 ..> c0125: `remove_dependency() calls remove_dependency()`
- c0236 ..> c0125: `update_task() calls update_task()`
- c0236 ..> c0125: `verify_criterion() calls update_criterion()`
- c0236 ..> c0255: `get_task() calls get_task()`
- c0236 ..> c0264: `add_criterion() calls add_criterion()`
- c0236 ..> c0264: `claim_task() calls claim_task()`
- c0236 ..> c0264: `transition_task() calls transition_task()`
- c0236 ..> c0267: `update_task() calls filter_none_values()`
- c0237 ..> c0032: `get_current_user() calls get_user_from_auth()`
- c0237 ..> c0032: `update_user_notes() calls get_user_from_auth()`
- c0237 ..> c0112: `get_current_user() constructs UserResponse`
- c0237 ..> c0112: `type in get_current_user`
- c0237 ..> c0112: `type in update_user_notes`
- c0237 ..> c0112: `update_user_notes() constructs UserResponse`
- c0237 ..> c0113: `update_user_notes() constructs UserUpdate`
- c0237 ..> c0265: `type in __init__`
- c0237 ..> c0265: `update_user_notes() calls update_user()`
- c0238 ..> c0228: `create_code_artifact_adapters() constructs CodeArtifactToolAdapters`
- c0238 ..> c0229: `create_document_adapters() constructs DocumentToolAdapters`
- c0238 ..> c0230: `create_entity_adapters() constructs EntityToolAdapters`
- c0238 ..> c0231: `create_file_adapters() constructs FileToolAdapters`
- c0238 ..> c0232: `create_memory_adapters() constructs MemoryToolAdapters`
- c0238 ..> c0233: `create_plan_adapters() constructs PlanToolAdapters`
- c0238 ..> c0234: `create_project_adapters() constructs ProjectToolAdapters`
- c0238 ..> c0235: `create_skill_adapters() constructs SkillToolAdapters`
- c0238 ..> c0236: `create_task_adapters() constructs TaskToolAdapters`
- c0238 ..> c0237: `create_user_adapters() constructs UserToolAdapters`
- c0238 ..> c0238: `_coerce_int_ids() calls _coerce_int_id()`
- c0238 ..> c0244: `type in create_code_artifact_adapters`
- c0238 ..> c0245: `type in create_document_adapters`
- c0238 ..> c0246: `type in create_entity_adapters`
- c0238 ..> c0256: `type in create_memory_adapters`
- c0238 ..> c0258: `type in create_project_adapters`
- c0238 ..> c0265: `type in create_code_artifact_adapters`
- c0238 ..> c0265: `type in create_document_adapters`
- c0238 ..> c0265: `type in create_entity_adapters`
- c0238 ..> c0265: `type in create_file_adapters`
- c0238 ..> c0265: `type in create_memory_adapters`
- c0238 ..> c0265: `type in create_project_adapters`
- c0238 ..> c0265: `type in create_skill_adapters`
- c0238 ..> c0265: `type in create_user_adapters`
- c0239 ..> c0031: `register_code_artifact_tools_metadata() calls get()`
- c0239 ..> c0031: `register_document_tools_metadata() calls get()`
- c0239 ..> c0031: `register_entity_tools_metadata() calls get()`
- c0239 ..> c0031: `register_file_tools_metadata() calls get()`
- c0239 ..> c0031: `register_memory_tools_metadata() calls get()`
- c0239 ..> c0031: `register_plan_tools_metadata() calls get()`
- c0239 ..> c0031: `register_project_tools_metadata() calls get()`
- c0239 ..> c0031: `register_simplified_tool() calls get()`
- c0239 ..> c0031: `register_skill_tools_metadata() calls get()`
- c0239 ..> c0031: `register_task_tools_metadata() calls get()`
- c0239 ..> c0031: `register_user_tools_metadata() calls get()`
- c0239 ..> c0105: `type in register_simplified_tool`
- c0239 ..> c0109: `register_simplified_tool() constructs ToolParameter`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_code_artifact_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_document_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_entity_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_file_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_memory_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_plan_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_project_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_skill_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_task_adapters()`
- c0239 ..> c0238: `register_all_tools_metadata() calls create_user_adapters()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_code_artifact_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_document_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_entity_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_file_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_memory_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_plan_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_project_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_skill_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_task_tools_metadata()`
- c0239 ..> c0239: `register_all_tools_metadata() calls register_user_tools_metadata()`
- c0239 ..> c0239: `register_code_artifact_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_document_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_entity_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_file_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_memory_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_plan_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_project_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_skill_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_task_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0239: `register_user_tools_metadata() calls register_simplified_tool()`
- c0239 ..> c0240: `register_all_tools_metadata() calls list_categories()`
- c0239 ..> c0240: `register_simplified_tool() calls register()`
- c0239 ..> c0240: `type in register_all_tools_metadata`
- c0239 ..> c0240: `type in register_code_artifact_tools_metadata`
- c0239 ..> c0240: `type in register_document_tools_metadata`
- c0239 ..> c0240: `type in register_entity_tools_metadata`
- c0239 ..> c0240: `type in register_file_tools_metadata`
- c0239 ..> c0240: `type in register_memory_tools_metadata`
- c0239 ..> c0240: `type in register_plan_tools_metadata`
- c0239 ..> c0240: `type in register_project_tools_metadata`
- c0239 ..> c0240: `type in register_simplified_tool`
- c0239 ..> c0240: `type in register_skill_tools_metadata`
- c0239 ..> c0240: `type in register_task_tools_metadata`
- c0239 ..> c0240: `type in register_user_tools_metadata`
- c0239 ..> c0256: `type in register_all_tools_metadata`
- c0239 ..> c0265: `type in register_all_tools_metadata`
- c0240 ..> c0031: `get_permitted_categories() calls get()`
- c0240 ..> c0031: `get_tool() calls get()`
- c0240 ..> c0031: `list_categories() calls get()`
- c0240 ..> c0105: `type in get_permitted_by_category`
- c0240 ..> c0105: `type in list_by_category`
- c0240 ..> c0105: `type in register`
- c0240 --> c0107: `field _tools`
- c0240 ..> c0107: `register() constructs ToolImplementation`
- c0240 ..> c0107: `type in get_tool`
- c0240 ..> c0108: `register() constructs ToolMetadata`
- c0240 ..> c0108: `type in get_permitted_by_category`
- c0240 ..> c0108: `type in get_permitted_tools`
- c0240 ..> c0108: `type in list_all_tools`
- c0240 ..> c0108: `type in list_by_category`
- c0240 ..> c0109: `type in register`
- c0240 ..> c0240: `execute() calls get_tool()`
- c0242 ..> c0034: `type in count_activity`
- c0242 ..> c0034: `type in get_activity`
- c0242 ..> c0035: `type in handle_event`
- c0242 ..> c0036: `get_activity() constructs ActivityListResponse`
- c0242 ..> c0036: `type in get_activity`
- c0242 ..> c0036: `type in get_entity_history`
- c0242 ..> c0038: `type in get_activity`
- c0242 ..> c0039: `type in count_activity`
- c0242 ..> c0039: `type in get_activity`
- c0242 ..> c0039: `type in get_entity_history`
- c0242 ..> c0114: `_cleanup_if_configured() calls cleanup_expired()`
- c0242 ..> c0114: `count_activity() calls count_events()`
- c0242 ..> c0114: `get_activity() calls query_events()`
- c0242 ..> c0114: `handle_event() calls save_event()`
- c0242 ..> c0114: `type in __init__`
- c0242 ..> c0242: `get_activity() calls _cleanup_if_configured()`
- c0242 ..> c0242: `get_entity_history() calls get_activity()`
- c0243 ..> c0218: `_backup_postgres() calls run()`
- c0243 ..> c0218: `_restore_postgres() calls run()`
- c0243 ..> c0243: `create_backup() calls _backup_postgres()`
- c0243 ..> c0243: `create_backup() calls _backup_sqlite()`
- c0243 ..> c0243: `restore_backup() calls _restore_postgres()`
- c0243 ..> c0243: `restore_backup() calls _restore_sqlite()`
- c0244 ..> c0024: `_emit_event() calls emit()`
- c0244 ..> c0024: `type in __init__`
- c0244 ..> c0029: `get_code_artifact() constructs NotFoundError`
- c0244 ..> c0029: `update_code_artifact() constructs NotFoundError`
- c0244 ..> c0034: `type in _emit_event`
- c0244 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0244 ..> c0039: `type in _emit_event`
- c0244 ..> c0040: `type in create_code_artifact`
- c0244 ..> c0040: `type in get_code_artifact`
- c0244 ..> c0040: `type in update_code_artifact`
- c0244 ..> c0041: `type in create_code_artifact`
- c0244 ..> c0042: `type in list_code_artifacts`
- c0244 ..> c0043: `type in update_code_artifact`
- c0244 ..> c0115: `create_code_artifact() calls create_code_artifact()`
- c0244 ..> c0115: `delete_code_artifact() calls delete_code_artifact()`
- c0244 ..> c0115: `delete_code_artifact() calls get_code_artifact_by_id()`
- c0244 ..> c0115: `get_code_artifact() calls get_code_artifact_by_id()`
- c0244 ..> c0115: `list_code_artifacts() calls list_code_artifacts()`
- c0244 ..> c0115: `type in __init__`
- c0244 ..> c0115: `update_code_artifact() calls get_code_artifact_by_id()`
- c0244 ..> c0115: `update_code_artifact() calls update_code_artifact()`
- c0244 ..> c0244: `create_code_artifact() calls _emit_event()`
- c0244 ..> c0244: `delete_code_artifact() calls _emit_event()`
- c0244 ..> c0244: `get_code_artifact() calls _emit_event()`
- c0244 ..> c0244: `list_code_artifacts() calls _emit_event()`
- c0244 ..> c0244: `update_code_artifact() calls _emit_event()`
- c0244 ..> c0266: `create_code_artifact() calls apply_provenance_defaults()`
- c0244 ..> c0266: `update_code_artifact() calls apply_provenance_defaults_for_update()`
- c0244 ..> c0267: `update_code_artifact() calls get_changed_fields()`
- c0245 ..> c0024: `_emit_event() calls emit()`
- c0245 ..> c0024: `type in __init__`
- c0245 ..> c0029: `get_document() constructs NotFoundError`
- c0245 ..> c0029: `update_document() constructs NotFoundError`
- c0245 ..> c0034: `type in _emit_event`
- c0245 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0245 ..> c0039: `type in _emit_event`
- c0245 ..> c0044: `type in create_document`
- c0245 ..> c0044: `type in get_document`
- c0245 ..> c0044: `type in update_document`
- c0245 ..> c0045: `type in create_document`
- c0245 ..> c0046: `type in list_documents`
- c0245 ..> c0047: `type in update_document`
- c0245 ..> c0116: `create_document() calls create_document()`
- c0245 ..> c0116: `delete_document() calls delete_document()`
- c0245 ..> c0116: `delete_document() calls get_document_by_id()`
- c0245 ..> c0116: `get_document() calls get_document_by_id()`
- c0245 ..> c0116: `list_documents() calls list_documents()`
- c0245 ..> c0116: `type in __init__`
- c0245 ..> c0116: `update_document() calls get_document_by_id()`
- c0245 ..> c0116: `update_document() calls update_document()`
- c0245 ..> c0245: `create_document() calls _emit_event()`
- c0245 ..> c0245: `delete_document() calls _emit_event()`
- c0245 ..> c0245: `get_document() calls _emit_event()`
- c0245 ..> c0245: `list_documents() calls _emit_event()`
- c0245 ..> c0245: `update_document() calls _emit_event()`
- c0245 ..> c0266: `create_document() calls apply_provenance_defaults()`
- c0245 ..> c0266: `update_document() calls apply_provenance_defaults_for_update()`
- c0245 ..> c0267: `update_document() calls get_changed_fields()`
- c0246 ..> c0024: `_emit_event() calls emit()`
- c0246 ..> c0024: `type in __init__`
- c0246 ..> c0029: `get_entity() constructs NotFoundError`
- c0246 ..> c0029: `update_entity() constructs NotFoundError`
- c0246 ..> c0034: `type in _emit_event`
- c0246 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0246 ..> c0039: `type in _emit_event`
- c0246 ..> c0048: `type in create_entity`
- c0246 ..> c0048: `type in get_entity`
- c0246 ..> c0048: `type in update_entity`
- c0246 ..> c0049: `type in create_entity`
- c0246 ..> c0051: `type in create_entity_relationship`
- c0246 ..> c0051: `type in get_all_entity_relationships`
- c0246 ..> c0051: `type in get_entity_relationships`
- c0246 ..> c0051: `type in update_entity_relationship`
- c0246 ..> c0052: `type in create_entity_relationship`
- c0246 ..> c0053: `type in update_entity_relationship`
- c0246 ..> c0054: `type in list_entities`
- c0246 ..> c0054: `type in search_entities`
- c0246 ..> c0055: `type in list_entities`
- c0246 ..> c0055: `type in search_entities`
- c0246 ..> c0056: `type in update_entity`
- c0246 ..> c0117: `create_entity() calls create_entity()`
- c0246 ..> c0117: `create_entity_relationship() calls create_entity_relationship()`
- c0246 ..> c0117: `delete_entity() calls delete_entity()`
- c0246 ..> c0117: `delete_entity() calls get_entity_by_id()`
- c0246 ..> c0117: `delete_entity_relationship() calls delete_entity_relationship()`
- c0246 ..> c0117: `get_all_entity_file_links() calls get_all_entity_file_links()`
- c0246 ..> c0117: `get_all_entity_memory_links() calls get_all_entity_memory_links()`
- c0246 ..> c0117: `get_all_entity_project_links() calls get_all_entity_project_links()`
- c0246 ..> c0117: `get_all_entity_relationships() calls get_all_entity_relationships()`
- c0246 ..> c0117: `get_entity() calls get_entity_by_id()`
- c0246 ..> c0117: `get_entity_memories() calls get_entity_memories()`
- c0246 ..> c0117: `get_entity_relationships() calls get_entity_relationships()`
- c0246 ..> c0117: `get_memory_entities() calls get_memory_entities()`
- c0246 ..> c0117: `link_entity_to_memory() calls link_entity_to_memory()`
- c0246 ..> c0117: `link_entity_to_project() calls link_entity_to_project()`
- c0246 ..> c0117: `list_entities() calls list_entities()`
- c0246 ..> c0117: `search_entities() calls search_entities()`
- c0246 ..> c0117: `type in __init__`
- c0246 ..> c0117: `unlink_entity_from_memory() calls unlink_entity_from_memory()`
- c0246 ..> c0117: `unlink_entity_from_project() calls unlink_entity_from_project()`
- c0246 ..> c0117: `update_entity() calls get_entity_by_id()`
- c0246 ..> c0117: `update_entity() calls update_entity()`
- c0246 ..> c0117: `update_entity_relationship() calls update_entity_relationship()`
- c0246 ..> c0246: `create_entity() calls _emit_event()`
- c0246 ..> c0246: `create_entity_relationship() calls _emit_event()`
- c0246 ..> c0246: `delete_entity() calls _emit_event()`
- c0246 ..> c0246: `delete_entity_relationship() calls _emit_event()`
- c0246 ..> c0246: `get_entity() calls _emit_event()`
- c0246 ..> c0246: `link_entity_to_memory() calls _emit_event()`
- c0246 ..> c0246: `link_entity_to_project() calls _emit_event()`
- c0246 ..> c0246: `list_entities() calls _emit_event()`
- c0246 ..> c0246: `search_entities() calls _emit_event()`
- c0246 ..> c0246: `unlink_entity_from_memory() calls _emit_event()`
- c0246 ..> c0246: `unlink_entity_from_project() calls _emit_event()`
- c0246 ..> c0246: `update_entity() calls _emit_event()`
- c0246 ..> c0246: `update_entity_relationship() calls _emit_event()`
- c0246 ..> c0266: `create_entity() calls apply_provenance_defaults()`
- c0246 ..> c0266: `create_entity_relationship() calls apply_provenance_defaults()`
- c0246 ..> c0266: `update_entity() calls apply_provenance_defaults_for_update()`
- c0246 ..> c0266: `update_entity_relationship() calls apply_provenance_defaults_for_update()`
- c0246 ..> c0267: `update_entity() calls get_changed_fields()`
- c0247 ..> c0024: `_emit_event() calls emit()`
- c0247 ..> c0024: `type in __init__`
- c0247 ..> c0029: `get_file() constructs NotFoundError`
- c0247 ..> c0029: `update_file() constructs NotFoundError`
- c0247 ..> c0034: `type in _emit_event`
- c0247 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0247 ..> c0039: `type in _emit_event`
- c0247 ..> c0057: `type in _snapshot_without_data`
- c0247 ..> c0057: `type in create_file`
- c0247 ..> c0057: `type in get_file`
- c0247 ..> c0057: `type in update_file`
- c0247 ..> c0058: `type in create_file`
- c0247 ..> c0059: `type in list_files`
- c0247 ..> c0060: `type in update_file`
- c0247 ..> c0119: `create_file() calls create_file()`
- c0247 ..> c0119: `delete_file() calls delete_file()`
- c0247 ..> c0119: `delete_file() calls get_file_by_id()`
- c0247 ..> c0119: `get_file() calls get_file_by_id()`
- c0247 ..> c0119: `list_files() calls list_files()`
- c0247 ..> c0119: `type in __init__`
- c0247 ..> c0119: `update_file() calls get_file_by_id()`
- c0247 ..> c0119: `update_file() calls update_file()`
- c0247 ..> c0247: `create_file() calls _emit_event()`
- c0247 ..> c0247: `create_file() calls _snapshot_without_data()`
- c0247 ..> c0247: `delete_file() calls _emit_event()`
- c0247 ..> c0247: `delete_file() calls _snapshot_without_data()`
- c0247 ..> c0247: `get_file() calls _emit_event()`
- c0247 ..> c0247: `get_file() calls _snapshot_without_data()`
- c0247 ..> c0247: `list_files() calls _emit_event()`
- c0247 ..> c0247: `update_file() calls _emit_event()`
- c0247 ..> c0247: `update_file() calls _snapshot_without_data()`
- c0247 ..> c0266: `create_file() calls apply_provenance_defaults()`
- c0247 ..> c0266: `update_file() calls apply_provenance_defaults_for_update()`
- c0247 ..> c0267: `update_file() calls get_changed_fields()`
- c0251 ..> c0029: `_validate_center_node() constructs NotFoundError`
- c0251 ..> c0031: `_fetch_node_data() calls get()`
- c0251 ..> c0061: `_fetch_edges() constructs SubgraphEdge`
- c0251 ..> c0061: `type in _fetch_edges`
- c0251 ..> c0062: `get_subgraph() constructs SubgraphMeta`
- c0251 ..> c0063: `_fetch_node_data() constructs SubgraphNode`
- c0251 ..> c0063: `type in _fetch_node_data`
- c0251 ..> c0064: `get_subgraph() constructs SubgraphResponse`
- c0251 ..> c0064: `type in get_subgraph`
- c0251 ..> c0117: `_fetch_edges() calls get_all_entity_file_links()`
- c0251 ..> c0117: `_fetch_edges() calls get_all_entity_memory_links()`
- c0251 ..> c0117: `_fetch_edges() calls get_all_entity_project_links()`
- c0251 ..> c0117: `_fetch_edges() calls get_all_entity_relationships()`
- c0251 ..> c0117: `_fetch_node_data() calls get_entity_by_id()`
- c0251 ..> c0117: `_validate_center_node() calls get_entity_by_id()`
- c0251 ..> c0117: `type in __init__`
- c0251 ..> c0120: `_fetch_edges() calls get_memory_by_id()`
- c0251 ..> c0120: `_fetch_node_data() calls get_memory_by_id()`
- c0251 ..> c0120: `_validate_center_node() calls get_memory_by_id()`
- c0251 ..> c0120: `get_subgraph() calls get_subgraph_nodes()`
- c0251 ..> c0120: `type in __init__`
- c0251 ..> c0248: `_fetch_edges() calls get_code_artifact()`
- c0251 ..> c0248: `_fetch_node_data() calls get_code_artifact()`
- c0251 ..> c0248: `_validate_center_node() calls get_code_artifact()`
- c0251 ..> c0248: `type in __init__`
- c0251 ..> c0249: `_fetch_edges() calls get_document()`
- c0251 ..> c0249: `_fetch_node_data() calls get_document()`
- c0251 ..> c0249: `_validate_center_node() calls get_document()`
- c0251 ..> c0249: `type in __init__`
- c0251 ..> c0250: `_fetch_edges() calls list_files()`
- c0251 ..> c0250: `_fetch_node_data() calls list_files()`
- c0251 ..> c0250: `_validate_center_node() calls get_file()`
- c0251 ..> c0250: `type in __init__`
- c0251 ..> c0251: `get_subgraph() calls _fetch_edges()`
- c0251 ..> c0251: `get_subgraph() calls _fetch_node_data()`
- c0251 ..> c0251: `get_subgraph() calls _validate_center_node()`
- c0251 ..> c0251: `get_subgraph() calls parse_node_id()`
- c0251 ..> c0252: `_fetch_edges() calls get_plan()`
- c0251 ..> c0252: `_fetch_node_data() calls get_plan()`
- c0251 ..> c0252: `_validate_center_node() calls get_plan()`
- c0251 ..> c0252: `type in __init__`
- c0251 ..> c0253: `_fetch_node_data() calls get_project()`
- c0251 ..> c0253: `_validate_center_node() calls get_project()`
- c0251 ..> c0253: `type in __init__`
- c0251 ..> c0254: `_fetch_edges() calls get_all_skill_code_artifact_links()`
- c0251 ..> c0254: `_fetch_edges() calls get_all_skill_document_links()`
- c0251 ..> c0254: `_fetch_edges() calls get_all_skill_file_links()`
- c0251 ..> c0254: `_fetch_edges() calls get_skill()`
- c0251 ..> c0254: `_fetch_node_data() calls get_skill()`
- c0251 ..> c0254: `_validate_center_node() calls get_skill()`
- c0251 ..> c0254: `type in __init__`
- c0251 ..> c0255: `_validate_center_node() calls get_task()`
- c0251 ..> c0255: `get_subgraph() calls list_tasks_for_user()`
- c0251 ..> c0255: `type in __init__`
- c0256 ..> c0024: `_emit_event() calls emit()`
- c0256 ..> c0024: `register_access_tracking_handlers() calls subscribe()`
- c0256 ..> c0024: `type in __init__`
- c0256 ..> c0024: `type in register_access_tracking_handlers`
- c0256 ..> c0031: `handle_memory_access_event() calls get()`
- c0256 ..> c0034: `type in _emit_event`
- c0256 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0256 ..> c0035: `type in handle_memory_access_event`
- c0256 ..> c0039: `type in _emit_event`
- c0256 ..> c0065: `_fetch_linked_memories() constructs LinkedMemory`
- c0256 ..> c0065: `type in _apply_token_budget`
- c0256 ..> c0065: `type in _fetch_linked_memories`
- c0256 ..> c0066: `type in _apply_token_budget`
- c0256 ..> c0066: `type in _count_memory_tokens`
- c0256 ..> c0066: `type in _fetch_linked_memories`
- c0256 ..> c0066: `type in create_memory`
- c0256 ..> c0066: `type in get_memory`
- c0256 ..> c0066: `type in list_memories`
- c0256 ..> c0066: `type in truncate_memories_by_budget`
- c0256 ..> c0066: `type in update_memory`
- c0256 ..> c0067: `type in create_memory`
- c0256 ..> c0071: `type in query_memory`
- c0256 ..> c0072: `query_memory() constructs MemoryQueryResult`
- c0256 ..> c0072: `type in query_memory`
- c0256 ..> c0074: `create_memory() constructs MemorySummary`
- c0256 ..> c0074: `type in create_memory`
- c0256 ..> c0075: `type in update_memory`
- c0256 ..> c0076: `find_obsolete_matches() constructs ObsoleteMatch`
- c0256 ..> c0076: `type in find_obsolete_matches`
- c0256 ..> c0120: `_fetch_linked_memories() calls get_linked_memories()`
- c0256 ..> c0120: `create_memory() calls create_links_batch()`
- c0256 ..> c0120: `create_memory() calls create_memory()`
- c0256 ..> c0120: `create_memory() calls find_similar_memories_scored()`
- c0256 ..> c0120: `find_obsolete_matches() calls find_obsolete_matches()`
- c0256 ..> c0120: `get_memory() calls get_memory_by_id()`
- c0256 ..> c0120: `handle_memory_access_event() calls record_memory_access()`
- c0256 ..> c0120: `link_memories() calls create_links_batch()`
- c0256 ..> c0120: `link_memories() calls get_memory_by_id()`
- c0256 ..> c0120: `list_memories() calls list_memories()`
- c0256 ..> c0120: `mark_memory_obsolete() calls get_memory_by_id()`
- c0256 ..> c0120: `mark_memory_obsolete() calls mark_obsolete()`
- c0256 ..> c0120: `query_memory() calls search_scored()`
- c0256 ..> c0120: `type in __init__`
- c0256 ..> c0120: `unlink_memories() calls unlink_memories()`
- c0256 ..> c0120: `update_memory() calls get_memory_by_id()`
- c0256 ..> c0120: `update_memory() calls update_memory()`
- c0256 ..> c0256: `_apply_token_budget() calls truncate_memories_by_budget()`
- c0256 ..> c0256: `create_memory() calls _emit_event()`
- c0256 ..> c0256: `get_memory() calls _emit_event()`
- c0256 ..> c0256: `link_memories() calls _emit_event()`
- c0256 ..> c0256: `mark_memory_obsolete() calls _emit_event()`
- c0256 ..> c0256: `query_memory() calls _apply_token_budget()`
- c0256 ..> c0256: `query_memory() calls _emit_event()`
- c0256 ..> c0256: `query_memory() calls _fetch_linked_memories()`
- c0256 ..> c0256: `truncate_memories_by_budget() calls _count_memory_tokens()`
- c0256 ..> c0256: `unlink_memories() calls _emit_event()`
- c0256 ..> c0256: `unlink_memories() calls get_memory()`
- c0256 ..> c0256: `update_memory() calls _emit_event()`
- c0256 ..> c0266: `create_memory() calls apply_provenance_defaults()`
- c0256 ..> c0266: `update_memory() calls apply_provenance_defaults_for_update()`
- c0256 ..> c0267: `update_memory() calls get_changed_fields()`
- c0256 ..> c0269: `_count_memory_tokens() calls count_tokens()`
- c0256 ..> c0269: `_count_memory_tokens() constructs TokenCounter`
- c0257 ..> c0024: `_emit_event() calls emit()`
- c0257 ..> c0024: `type in __init__`
- c0257 ..> c0028: `update_plan() constructs InvalidStateTransitionError`
- c0257 ..> c0029: `get_plan() constructs NotFoundError`
- c0257 ..> c0031: `update_plan() calls get()`
- c0257 ..> c0034: `type in _emit_event`
- c0257 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0257 ..> c0039: `type in _emit_event`
- c0257 ..> c0081: `type in create_plan`
- c0257 ..> c0081: `type in get_plan`
- c0257 ..> c0081: `type in update_plan`
- c0257 ..> c0082: `type in create_plan`
- c0257 ..> c0083: `check_plan_completion() constructs PlanStatus`
- c0257 ..> c0083: `type in list_plans`
- c0257 ..> c0083: `update_plan() constructs PlanStatus`
- c0257 ..> c0084: `type in list_plans`
- c0257 ..> c0085: `type in update_plan`
- c0257 ..> c0122: `check_plan_completion() calls get_plan_by_id()`
- c0257 ..> c0122: `create_plan() calls create_plan()`
- c0257 ..> c0122: `delete_plan() calls delete_plan()`
- c0257 ..> c0122: `delete_plan() calls get_plan_by_id()`
- c0257 ..> c0122: `get_plan() calls get_plan_by_id()`
- c0257 ..> c0122: `list_plans() calls list_plans()`
- c0257 ..> c0122: `type in __init__`
- c0257 ..> c0122: `update_plan() calls get_plan_by_id()`
- c0257 ..> c0122: `update_plan() calls update_plan()`
- c0257 ..> c0257: `create_plan() calls _emit_event()`
- c0257 ..> c0257: `delete_plan() calls _emit_event()`
- c0257 ..> c0257: `get_plan() calls _emit_event()`
- c0257 ..> c0257: `update_plan() calls _emit_event()`
- c0257 ..> c0266: `create_plan() calls apply_provenance_defaults()`
- c0257 ..> c0266: `update_plan() calls apply_provenance_defaults_for_update()`
- c0257 ..> c0267: `update_plan() calls get_changed_fields()`
- c0258 ..> c0024: `_emit_event() calls emit()`
- c0258 ..> c0024: `type in __init__`
- c0258 ..> c0029: `get_project() constructs NotFoundError`
- c0258 ..> c0034: `type in _emit_event`
- c0258 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0258 ..> c0039: `type in _emit_event`
- c0258 ..> c0094: `type in create_project`
- c0258 ..> c0094: `type in get_project`
- c0258 ..> c0094: `type in update_project`
- c0258 ..> c0095: `type in create_project`
- c0258 ..> c0096: `type in list_projects`
- c0258 ..> c0097: `type in list_projects`
- c0258 ..> c0099: `type in update_project`
- c0258 ..> c0123: `create_project() calls create_project()`
- c0258 ..> c0123: `delete_project() calls delete_project()`
- c0258 ..> c0123: `delete_project() calls get_project_by_id()`
- c0258 ..> c0123: `get_project() calls get_project_by_id()`
- c0258 ..> c0123: `list_projects() calls list_projects()`
- c0258 ..> c0123: `type in __init__`
- c0258 ..> c0123: `update_project() calls get_project_by_id()`
- c0258 ..> c0123: `update_project() calls update_project()`
- c0258 ..> c0258: `create_project() calls _emit_event()`
- c0258 ..> c0258: `delete_project() calls _emit_event()`
- c0258 ..> c0258: `get_project() calls _emit_event()`
- c0258 ..> c0258: `list_projects() calls _emit_event()`
- c0258 ..> c0258: `update_project() calls _emit_event()`
- c0258 ..> c0266: `create_project() calls apply_provenance_defaults()`
- c0258 ..> c0266: `update_project() calls apply_provenance_defaults_for_update()`
- c0258 ..> c0267: `update_project() calls get_changed_fields()`
- c0259 --> c0121: `field validation`
- c0260 ..> c0120: `_recompute_auto_links() calls create_links_batch()`
- c0260 ..> c0120: `_recompute_auto_links() calls find_similar_memories()`
- c0260 ..> c0120: `re_embed_all() calls bulk_update_embeddings()`
- c0260 ..> c0120: `re_embed_all() calls count_all_memories()`
- c0260 ..> c0120: `re_embed_all() calls get_memories_for_reembedding()`
- c0260 ..> c0120: `re_embed_all() calls reset_embedding_storage()`
- c0260 ..> c0120: `rebuild_targeted() calls count_memories_for_targeted_rebuild()`
- c0260 ..> c0120: `rebuild_targeted() calls get_memories_for_targeted_rebuild()`
- c0260 ..> c0120: `rebuild_targeted() calls upsert_targeted_embeddings()`
- c0260 ..> c0120: `type in __init__`
- c0260 ..> c0120: `validate() calls validate_embedding_count()`
- c0260 ..> c0120: `validate() calls validate_embedding_dimensions()`
- c0260 ..> c0120: `validate() calls validate_search_works()`
- c0260 ..> c0121: `re_embed_all() constructs ValidationResult`
- c0260 ..> c0121: `type in validate`
- c0260 ..> c0121: `validate() constructs ValidationResult`
- c0260 ..> c0128: `type in __init__`
- c0260 ..> c0131: `re_embed_all() calls generate_embedding()`
- c0260 ..> c0131: `rebuild_targeted() calls generate_embedding()`
- c0260 ..> c0137: `re_embed_all() calls build_embedding_text()`
- c0260 ..> c0137: `rebuild_targeted() calls build_embedding_text()`
- c0260 ..> c0259: `re_embed_all() constructs ReEmbedResult`
- c0260 ..> c0259: `type in re_embed_all`
- c0260 ..> c0260: `re_embed_all() calls validate()`
- c0260 ..> c0260: `rebuild_targeted() calls _recompute_auto_links()`
- c0260 ..> c0260: `rebuild_targeted() calls _record_unresolved_memory_ids()`
- c0260 ..> c0261: `rebuild_targeted() constructs TargetedRebuildResult`
- c0260 ..> c0261: `type in _recompute_auto_links`
- c0260 ..> c0261: `type in _record_unresolved_memory_ids`
- c0260 ..> c0261: `type in rebuild_targeted`
- c0262 ..> c0024: `_emit_event() calls emit()`
- c0262 ..> c0024: `type in __init__`
- c0262 ..> c0029: `get_skill() constructs NotFoundError`
- c0262 ..> c0029: `update_skill() constructs NotFoundError`
- c0262 ..> c0031: `import_skill() calls get()`
- c0262 ..> c0034: `type in _emit_event`
- c0262 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0262 ..> c0039: `type in _emit_event`
- c0262 ..> c0100: `type in create_skill`
- c0262 ..> c0100: `type in get_skill`
- c0262 ..> c0100: `type in import_skill`
- c0262 ..> c0100: `type in update_skill`
- c0262 ..> c0101: `import_skill() constructs SkillCreate`
- c0262 ..> c0101: `type in create_skill`
- c0262 ..> c0102: `type in get_skill_links`
- c0262 ..> c0103: `type in list_skills`
- c0262 ..> c0103: `type in search_skills`
- c0262 ..> c0104: `type in update_skill`
- c0262 ..> c0124: `create_skill() calls create_skill()`
- c0262 ..> c0124: `create_skill() calls skill_name_exists()`
- c0262 ..> c0124: `delete_skill() calls delete_skill()`
- c0262 ..> c0124: `delete_skill() calls get_skill_by_id()`
- c0262 ..> c0124: `get_all_skill_code_artifact_links() calls get_all_skill_code_artifact_links()`
- c0262 ..> c0124: `get_all_skill_document_links() calls get_all_skill_document_links()`
- c0262 ..> c0124: `get_all_skill_file_links() calls get_all_skill_file_links()`
- c0262 ..> c0124: `get_skill() calls get_skill_by_id()`
- c0262 ..> c0124: `get_skill_links() calls get_skill_links()`
- c0262 ..> c0124: `import_skill() calls create_skill()`
- c0262 ..> c0124: `link_skill_to_code_artifact() calls link_skill_to_code_artifact()`
- c0262 ..> c0124: `link_skill_to_document() calls link_skill_to_document()`
- c0262 ..> c0124: `link_skill_to_file() calls link_skill_to_file()`
- c0262 ..> c0124: `link_skill_to_memory() calls link_skill_to_memory()`
- c0262 ..> c0124: `list_skills() calls list_skills()`
- c0262 ..> c0124: `search_skills() calls search_skills()`
- c0262 ..> c0124: `type in __init__`
- c0262 ..> c0124: `unlink_skill_from_code_artifact() calls unlink_skill_from_code_artifact()`
- c0262 ..> c0124: `unlink_skill_from_document() calls unlink_skill_from_document()`
- c0262 ..> c0124: `unlink_skill_from_file() calls unlink_skill_from_file()`
- c0262 ..> c0124: `unlink_skill_from_memory() calls unlink_skill_from_memory()`
- c0262 ..> c0124: `update_skill() calls get_skill_by_id()`
- c0262 ..> c0124: `update_skill() calls update_skill()`
- c0262 ..> c0262: `create_skill() calls _emit_event()`
- c0262 ..> c0262: `delete_skill() calls _emit_event()`
- c0262 ..> c0262: `export_skill() calls get_skill()`
- c0262 ..> c0262: `get_skill() calls _emit_event()`
- c0262 ..> c0262: `link_skill_to_code_artifact() calls get_skill()`
- c0262 ..> c0262: `link_skill_to_document() calls get_skill()`
- c0262 ..> c0262: `link_skill_to_file() calls get_skill()`
- c0262 ..> c0262: `link_skill_to_memory() calls get_skill()`
- c0262 ..> c0262: `list_skills() calls _emit_event()`
- c0262 ..> c0262: `unlink_skill_from_code_artifact() calls get_skill()`
- c0262 ..> c0262: `unlink_skill_from_document() calls get_skill()`
- c0262 ..> c0262: `unlink_skill_from_file() calls get_skill()`
- c0262 ..> c0262: `unlink_skill_from_memory() calls get_skill()`
- c0262 ..> c0262: `update_skill() calls _emit_event()`
- c0262 ..> c0263: `import_skill() calls _quote_unquoted_frontmatter_scalars()`
- c0262 ..> c0266: `create_skill() calls apply_provenance_defaults()`
- c0262 ..> c0266: `update_skill() calls apply_provenance_defaults_for_update()`
- c0262 ..> c0267: `update_skill() calls get_changed_fields()`
- c0264 ..> c0024: `_emit_event() calls emit()`
- c0264 ..> c0024: `type in __init__`
- c0264 ..> c0025: `claim_task() constructs ConflictError`
- c0264 ..> c0025: `transition_task() constructs ConflictError`
- c0264 ..> c0026: `_validate_no_cycle() constructs CyclicDependencyError`
- c0264 ..> c0027: `_validate_dependencies_met() constructs DependencyNotMetError`
- c0264 ..> c0028: `_validate_all_criteria_met() constructs InvalidStateTransitionError`
- c0264 ..> c0028: `add_criterion() constructs InvalidStateTransitionError`
- c0264 ..> c0028: `claim_task() constructs InvalidStateTransitionError`
- c0264 ..> c0028: `create_task() constructs InvalidStateTransitionError`
- c0264 ..> c0028: `transition_task() constructs InvalidStateTransitionError`
- c0264 ..> c0029: `_validate_same_plan() constructs NotFoundError`
- c0264 ..> c0029: `add_criterion() constructs NotFoundError`
- c0264 ..> c0029: `add_dependency() constructs NotFoundError`
- c0264 ..> c0029: `claim_task() constructs NotFoundError`
- c0264 ..> c0029: `get_task() constructs NotFoundError`
- c0264 ..> c0029: `transition_task() constructs NotFoundError`
- c0264 ..> c0031: `transition_task() calls get()`
- c0264 ..> c0034: `type in _emit_event`
- c0264 ..> c0035: `_emit_event() constructs ActivityEvent`
- c0264 ..> c0039: `type in _emit_event`
- c0264 ..> c0078: `type in add_criterion`
- c0264 ..> c0078: `type in update_criterion`
- c0264 ..> c0079: `type in add_criterion`
- c0264 ..> c0080: `type in update_criterion`
- c0264 ..> c0083: `_check_plan_auto_completion() constructs PlanStatus`
- c0264 ..> c0083: `create_task() constructs PlanStatus`
- c0264 ..> c0085: `_check_plan_auto_completion() constructs PlanUpdate`
- c0264 ..> c0086: `type in _validate_all_criteria_met`
- c0264 ..> c0086: `type in _validate_dependencies_met`
- c0264 ..> c0086: `type in claim_task`
- c0264 ..> c0086: `type in create_task`
- c0264 ..> c0086: `type in get_task`
- c0264 ..> c0086: `type in transition_task`
- c0264 ..> c0086: `type in update_task`
- c0264 ..> c0087: `type in create_task`
- c0264 ..> c0090: `type in list_tasks`
- c0264 ..> c0091: `_check_plan_auto_completion() constructs TaskState`
- c0264 ..> c0091: `_validate_dependencies_met() constructs TaskState`
- c0264 ..> c0091: `add_criterion() constructs TaskState`
- c0264 ..> c0091: `claim_task() constructs TaskState`
- c0264 ..> c0091: `transition_task() constructs TaskState`
- c0264 ..> c0091: `type in list_tasks`
- c0264 ..> c0091: `type in transition_task`
- c0264 ..> c0092: `type in list_tasks`
- c0264 ..> c0092: `type in list_tasks_for_user`
- c0264 ..> c0093: `type in update_task`
- c0264 ..> c0125: `_check_plan_auto_completion() calls list_tasks()`
- c0264 ..> c0125: `_validate_all_criteria_met() calls get_criteria_for_task()`
- c0264 ..> c0125: `_validate_dependencies_met() calls get_task_by_id()`
- c0264 ..> c0125: `_validate_no_cycle() calls get_dependencies()`
- c0264 ..> c0125: `_validate_same_plan() calls get_task_by_id()`
- c0264 ..> c0125: `add_criterion() calls create_criterion()`
- c0264 ..> c0125: `add_criterion() calls get_task_by_id()`
- c0264 ..> c0125: `add_dependency() calls add_dependency()`
- c0264 ..> c0125: `add_dependency() calls get_task_by_id()`
- c0264 ..> c0125: `claim_task() calls get_task_by_id()`
- c0264 ..> c0125: `claim_task() calls transition_task_state()`
- c0264 ..> c0125: `create_task() calls add_dependency()`
- c0264 ..> c0125: `create_task() calls create_criterion()`
- c0264 ..> c0125: `create_task() calls create_task()`
- c0264 ..> c0125: `create_task() calls get_task_by_id()`
- c0264 ..> c0125: `delete_criterion() calls delete_criterion()`
- c0264 ..> c0125: `delete_task() calls delete_task()`
- c0264 ..> c0125: `delete_task() calls get_task_by_id()`
- c0264 ..> c0125: `get_task() calls get_task_by_id()`
- c0264 ..> c0125: `list_tasks() calls list_tasks()`
- c0264 ..> c0125: `list_tasks_for_user() calls list_tasks_for_user()`
- c0264 ..> c0125: `remove_dependency() calls remove_dependency()`
- c0264 ..> c0125: `transition_task() calls get_task_by_id()`
- c0264 ..> c0125: `transition_task() calls transition_task_state()`
- c0264 ..> c0125: `type in __init__`
- c0264 ..> c0125: `update_criterion() calls update_criterion()`
- c0264 ..> c0125: `update_task() calls get_task_by_id()`
- c0264 ..> c0125: `update_task() calls update_task()`
- c0264 ..> c0257: `_check_plan_auto_completion() calls get_plan()`
- c0264 ..> c0257: `_check_plan_auto_completion() calls update_plan()`
- c0264 ..> c0257: `claim_task() calls _emit_event()`
- c0264 ..> c0257: `create_task() calls _emit_event()`
- c0264 ..> c0257: `create_task() calls get_plan()`
- c0264 ..> c0257: `delete_task() calls _emit_event()`
- c0264 ..> c0257: `transition_task() calls _emit_event()`
- c0264 ..> c0257: `type in __init__`
- c0264 ..> c0257: `update_task() calls _emit_event()`
- c0264 ..> c0264: `add_dependency() calls _validate_no_cycle()`
- c0264 ..> c0264: `add_dependency() calls _validate_same_plan()`
- c0264 ..> c0264: `claim_task() calls _validate_dependencies_met()`
- c0264 ..> c0264: `create_task() calls _validate_no_cycle()`
- c0264 ..> c0264: `create_task() calls _validate_same_plan()`
- c0264 ..> c0264: `delete_task() calls _check_plan_auto_completion()`
- c0264 ..> c0264: `transition_task() calls _check_plan_auto_completion()`
- c0264 ..> c0264: `transition_task() calls _validate_all_criteria_met()`
- c0264 ..> c0264: `transition_task() calls _validate_dependencies_met()`
- c0264 ..> c0266: `create_task() calls apply_provenance_defaults()`
- c0264 ..> c0266: `update_task() calls apply_provenance_defaults_for_update()`
- c0264 ..> c0267: `update_task() calls get_changed_fields()`
- c0265 ..> c0110: `type in get_or_create_user`
- c0265 ..> c0110: `type in get_user_by_id`
- c0265 ..> c0110: `type in update_user`
- c0265 ..> c0111: `type in get_or_create_user`
- c0265 ..> c0111: `update_user() constructs UserCreate`
- c0265 ..> c0113: `get_or_create_user() constructs UserUpdate`
- c0265 ..> c0113: `type in update_user`
- c0265 ..> c0126: `get_or_create_user() calls create_user()`
- c0265 ..> c0126: `get_or_create_user() calls get_user_by_external_id()`
- c0265 ..> c0126: `get_or_create_user() calls update_user()`
- c0265 ..> c0126: `get_user_by_id() calls get_user_by_id()`
- c0265 ..> c0126: `type in __init__`
- c0265 ..> c0126: `update_user() calls create_user()`
- c0265 ..> c0126: `update_user() calls get_user_by_external_id()`
- c0265 ..> c0126: `update_user() calls update_user()`
- c0265 ..> c0267: `get_or_create_user() calls get_changed_fields()`
- c0265 ..> c0267: `update_user() calls get_changed_fields()`
- c0271 ..> c0134: `fast_embed_rank() constructs FastEmbedCrossEncoderAdapter`
- c0271 ..> c0135: `fast_embed_rank() calls rerank()`
- c0271 ..> c0135: `http_rank() calls rerank()`
- c0271 ..> c0135: `http_rank() constructs HttpRerankAdapter`
- c0272 ..> c0118: `test_sqlite_vec_async() calls close()`
- c0272 ..> c0118: `test_sqlite_vec_async() calls execute()`
- c0272 ..> c0118: `test_sqlite_vec_sync() calls close()`
- c0272 ..> c0118: `test_sqlite_vec_sync() calls execute()`
- c0273 ..> c0130: `test_embeddings() constructs GoogleEmbeddingsAdapter`
- c0273 ..> c0131: `test_embeddings() calls generate_embedding()`
- c0274 ..> c0118: `main() calls list_tools()`
- c0275 ..> c0118: `test_sqlite_init() calls execute()`
- c0275 ..> c0175: `test_sqlite_init() calls dispose()`
- c0275 ..> c0175: `test_sqlite_init() calls init_db()`
- c0275 ..> c0175: `test_sqlite_init() calls session()`
- c0275 ..> c0175: `test_sqlite_init() calls system_session()`
- c0275 ..> c0175: `test_sqlite_init() constructs SqliteDatabaseAdapter`
- c0276 ..> c0016: `_run_reembed() calls create_db_adapter()`
- c0276 ..> c0016: `_run_reembed() calls create_repositories()`
- c0276 ..> c0016: `_run_reembed() calls get_embedding_adapter()`
- c0276 ..> c0016: `lifespan() calls build_runtime()`
- c0276 ..> c0016: `lifespan() calls dispose_runtime()`
- c0276 ..> c0021: `_run_reembed() calls configure_logging()`
- c0276 ..> c0021: `lifespan() calls configure_logging()`
- c0276 ..> c0031: `lifespan() constructs TokenCache`
- c0276 ..> c0120: `_run_reembed() calls count_all_memories()`
- c0276 ..> c0120: `_run_reembed() calls reset_embedding_storage()`
- c0276 ..> c0145: `_run_reembed() calls dispose()`
- c0276 ..> c0145: `_run_reembed() calls init_db()`
- c0276 ..> c0195: `_run_reembed() calls register()`
- c0276 ..> c0195: `lifespan() calls register()`
- c0276 ..> c0212: `cli() calls dispatch()`
- c0276 ..> c0218: `_legacy_launcher() calls run()`
- c0276 ..> c0218: `_serve() calls run()`
- c0276 ..> c0243: `_run_reembed() calls create_backup()`
- c0276 ..> c0243: `_run_reembed() calls restore_backup()`
- c0276 ..> c0243: `_run_reembed() constructs BackupService`
- c0276 ..> c0260: `_run_reembed() calls re_embed_all()`
- c0276 ..> c0260: `_run_reembed() constructs ReEmbeddingService`
- c0276 ..> c0270: `_legacy_launcher() calls get_version()`
- c0276 ..> c0276: `_legacy_launcher() calls _run_reembed()`
- c0276 ..> c0276: `_legacy_launcher() calls _serve()`
- c0276 ..> c0276: `cli() calls _legacy_launcher()`
- c0277 ..> c0277: `_run() calls _print_summary()`
- c0277 ..> c0277: `main() calls _run()`
- c0277 ..> c0277: `main() calls config_from_argv()`
- c0277 ..> c0278: `config_from_argv() constructs HarnessConfig`
- c0277 ..> c0278: `type in _run`
- c0277 ..> c0278: `type in config_from_argv`
- c0277 ..> c0279: `_run() calls start()`
- c0277 ..> c0279: `_run() calls stop()`
- c0277 ..> c0279: `_run() constructs AgentContainer`
- c0277 ..> c0280: `_run() calls ensure_image()`
- c0277 ..> c0293: `_run() calls seed_skills()`
- c0277 ..> c0293: `_run() constructs ThrowawayForgetful`
- c0277 ..> c0297: `type in _print_summary`
- c0277 ..> c0298: `_run() calls run_skill()`
- c0277 ..> c0298: `_run() calls write_summary()`
- c0277 ..> c0298: `_run() constructs Walkthrough`
- c0277 ..> c0298: `main() calls run()`
- c0278 ..> c0031: `timeout_for() calls get()`
- c0279 ..> c0024: `stop() calls clear()`
- c0279 ..> c0031: `start() calls get()`
- c0279 ..> c0118: `_exec() calls close()`
- c0279 ..> c0278: `type in __init__`
- c0279 ..> c0279: `health_check() calls _exec()`
- c0279 ..> c0279: `start() calls _exec()`
- c0279 ..> c0280: `run_session() calls exec_command()`
- c0279 ..> c0280: `start() calls _docker_client()`
- c0279 ..> c0280: `start() calls _prepare_harness_mount()`
- c0279 ..> c0280: `start() calls build_container_env()`
- c0279 ..> c0280: `start() calls provision_agent()`
- c0279 ..> c0292: `health_check() constructs HarnessInfraError`
- c0279 ..> c0292: `run_session() constructs HarnessInfraError`
- c0279 ..> c0292: `start() constructs HarnessInfraError`
- c0279 ..> c0293: `stop() calls stop()`
- c0279 ..> c0295: `run_session() constructs SessionOutcome`
- c0279 ..> c0295: `type in run_session`
- c0279 ..> c0298: `start() calls run()`
- c0280 ..> c0031: `ensure_image() calls get()`
- c0280 ..> c0280: `ensure_image() calls _docker_client()`
- c0280 ..> c0280: `ensure_image() calls export_requirements()`
- c0280 ..> c0280: `ensure_image() calls requirements_hash()`
- c0280 ..> c0280: `provision_agent() calls staged_mount()`
- c0280 ..> c0292: `_docker_client() constructs HarnessInfraError`
- c0280 ..> c0292: `_prepare_harness_mount() constructs HarnessInfraError`
- c0280 ..> c0292: `ensure_image() constructs HarnessInfraError`
- c0280 ..> c0292: `provision_agent() constructs HarnessInfraError`
- c0280 ..> c0298: `_prepare_harness_mount() calls run()`
- c0280 ..> c0298: `ensure_image() calls run()`
- c0280 ..> c0298: `export_requirements() calls run()`
- c0281 ..> c0031: `health() calls get()`
- c0281 ..> c0031: `run_session() calls get()`
- c0281 ..> c0218: `main() calls run()`
- c0281 ..> c0279: `health() calls health_check()`
- c0281 ..> c0281: `health() calls _shell()`
- c0281 ..> c0281: `main() calls health()`
- c0281 ..> c0281: `main() calls run_session()`
- c0281 ..> c0281: `run_session() calls _attach_debug_log()`
- c0281 ..> c0281: `run_session() calls _shell()`
- c0282 ..> c0031: `build_prompt() calls get()`
- c0282 ..> c0287: `build_prompt() calls report_contract_example()`
- c0284 --> c0286: `field report`
- c0286 --> c0283: `field issues`
- c0286 --> c0285: `field steps`
- c0287 ..> c0031: `_normalize_severity() calls get()`
- c0287 ..> c0284: `load_report() constructs ReportLoad`
- c0287 ..> c0284: `type in load_report`
- c0287 ..> c0287: `_normalize_report_verdict() calls _lowercase()`
- c0287 ..> c0287: `_normalize_severity() calls _lowercase()`
- c0287 ..> c0287: `_normalize_step_verdict() calls _lowercase()`
- c0293 ..> c0031: `_wait_until_healthy() calls get()`
- c0293 ..> c0214: `execute() calls close()`
- c0293 ..> c0214: `execute() calls execute()`
- c0293 ..> c0214: `execute() constructs RemoteExecutor`
- c0293 ..> c0214: `seed_skills() calls execute()`
- c0293 ..> c0214: `stop() calls close()`
- c0293 ..> c0292: `_wait_until_healthy() constructs HarnessInfraError`
- c0293 ..> c0292: `seed_skills() constructs HarnessInfraError`
- c0293 ..> c0292: `start() constructs HarnessInfraError`
- c0293 ..> c0293: `_wait_until_healthy() calls stop()`
- c0293 ..> c0293: `start() calls _child_env()`
- c0293 ..> c0293: `start() calls _wait_until_healthy()`
- c0293 ..> c0294: `start() calls _ephemeral_port()`
- c0296 ..> c0295: `type in run_session`
- c0297 --> c0284: `field report_load`
- c0298 ..> c0031: `run_skill() calls get()`
- c0298 ..> c0278: `run_skill() calls timeout_for()`
- c0298 ..> c0278: `type in __init__`
- c0298 ..> c0282: `run_skill() calls build_prompt()`
- c0298 ..> c0287: `run_skill() calls load_report()`
- c0298 ..> c0296: `run_skill() calls run_session()`
- c0298 ..> c0296: `type in __init__`
- c0298 ..> c0297: `run_skill() constructs SkillRunResult`
- c0298 ..> c0297: `type in _meta`
- c0298 ..> c0297: `type in run`
- c0298 ..> c0297: `type in run_skill`
- c0298 ..> c0297: `type in write_summary`
- c0298 ..> c0298: `run() calls run_skill()`
- c0298 ..> c0298: `run() calls write_summary()`
- c0298 ..> c0298: `run_skill() calls _meta()`
- c0298 ..> c0299: `run_skill() calls load_events()`
- c0298 ..> c0299: `run_skill() calls prepare_workspace()`
- c0298 ..> c0299: `run_skill() calls scan_for_breaches()`
- c0299 ..> c0031: `scan_for_breaches() calls get()`
- c0299 ..> c0299: `prepare_workspace() calls _build_fixture_repo()`

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
- Type22: `ExternalRef | None`
- Type23: `PlanStatus | None`
- Type24: `list[CriterionCreate] | None`
- Type25: `TaskPriority | None`
- Type26: `ProjectType | None`
- Type27: `ProjectStatus | None`
- Type28: `dict | None`
- Type29: `Callable[..., Awaitable[Any]]`
- Type30: `tuple[list[ActivityLogEntry], int]`
- Type31: `ActionType | None`
- Type32: `ActorType | None`
- Type33: `CodeArtifact | None`
- Type34: `Document | None`
- Type35: `Entity | None`
- Type36: `tuple[list[EntitySummary], int]`
- Type37: `list[tuple[int, int]]`
- Type38: `list[tuple[int, str]]`
- Type39: `list[tuple[int, str, str]]`
- Type40: `File | None`
- Type41: `list[tuple[Memory, MemoryScore]]`
- Type42: `Memory | None`
- Type43: `list[tuple[Memory, float]]`
- Type44: `tuple[list[Memory], int]`
- Type45: `tuple[list[dict[str, Any]], bool]`
- Type46: `list[tuple[int, list[float]]]`
- Type47: `Plan | None`
- Type48: `Project | None`
- Type49: `Skill | None`
- Type50: `Task | None`
- Type51: `TaskState | None`
- Type52: `dict[str, bool]`
- Type53: `Callable[[dict[str, bool]], T]`
- Type54: `list[tuple[int, float]]`
- Type55: `list[tuple[int,float]]`
- Type56: `RerankAdapter | None`
- Type57: `Mapped["UsersTable"]`
- Type58: `Mapped["ProjectsTable"]`
- Type59: `Mapped[list["MemoryTable"]]`
- Type60: `Mapped[list["SkillsTable"]]`
- Type61: `Mapped["TasksTable"]`
- Type62: `Mapped[list["ProjectsTable"]]`
- Type63: `Mapped[list["FilesTable"]]`
- Type64: `Mapped[list["EntityRelationshipsTable"]]`
- Type65: `Mapped["EntitiesTable"]`
- Type66: `Mapped[list["EntitiesTable"]]`
- Type67: `Mapped[list["CodeArtifactsTable"]]`
- Type68: `Mapped[list["DocumentsTable"]]`
- Type69: `Mapped[str | None]`
- Type70: `Mapped[list["TasksTable"]]`
- Type71: `Mapped[list["PlansTable"]]`
- Type72: `Mapped["PlansTable"]`
- Type73: `Mapped[list["CriteriaTable"]]`
- Type74: `Mapped[list["TaskDependenciesTable"]]`
- Type75: `Path | None`
- Type76: `"LocalExecutor"`
- Type77: `tuple[Any, str]`
- Type78: `tuple[int, int]`
- Type79: `tuple[set[str], frozenset[str]]`
- Type80: `frozenset[str] | None`
- Type81: `list[int] | int | None`
- Type82: `list[dict[str, Any]] | None`
- Type83: `dict[str, ToolImplementation]`
- Type84: `ToolImplementation | None`
- Type85: `"EventBus | None"`
- Type86: `tuple[list[int], int, list[tuple[int, str]]]`
- Type87: `tuple[list[int], int, list[tuple[int, str, str]]]`
- Type88: `ProjectServiceProtocol | None`
- Type89: `DocumentServiceProtocol | None`
- Type90: `CodeArtifactServiceProtocol | None`
- Type91: `FileServiceProtocol | None`
- Type92: `SkillServiceProtocol | None`
- Type93: `PlanServiceProtocol | None`
- Type94: `TaskServiceProtocol | None`
- Type95: `tuple[str, int]`
- Type96: `list | None`
- Type97: `"EventBus"`
- Type98: `tuple[Memory, list[MemorySummary]]`
- Type99: `tuple[list[Memory], list[LinkedMemory], int, bool]`
- Type100: `tuple[list[Memory], int, bool]`
- Type101: `ValidationResult | None`
- Type102: `Callable[[int, int], None] | None`
- Type103: `dict[str, tuple]`
- Type104: `tuple[str, ...]`
- Type105: `Literal["cli"]`
- Type106: `dict[str, float]`
- Type107: `tuple[int, str]`
- Type108: `dict[str, str]`
- Type109: `dict[str, dict[str, str]]`
- Type110: `Literal["blocker", "major", "minor", "nit"]`
- Type111: `Literal["ok", "missing", "invalid_json", "schema_error"]`
- Type112: `WalkthroughReport | None`
- Type113: `Literal["ok", "issue"]`
- Type114: `Literal["pass", "issues", "blocked"]`
- Type115: `subprocess.Popen | None`
- Type116: `Literal["ran", "timeout"]`
- Type117: `list[dict[str, Any]]`
- Relation118: `_validate_rebuild_scope() calls count_memories_for_targeted_rebuild()`
- Relation119: `create_code_artifact_adapters() constructs CodeArtifactToolAdapters`

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
- Signature22: `+list_plans(user_id: UUID, project_id: int | None, status: PlanStatus | None,
  external_ref: str | None) list[PlanSummary]`
- Signature23: `+list_projects(user_id: UUID, status: ProjectStatus | None, repo_name: str | None,
  name: str | None) list[ProjectSummary]`
- Signature24: `+list_skills(user_id: UUID, project_id: int | None, tags: list[str] | None,
  importance_threshold: int | None) list[SkillSummary]`
- Signature25: `+unlink_skill_from_code_artifact(user_id: UUID, skill_id: int, code_artifact_id:
  int) dict`
- Signature26: `+list_tasks(user_id: UUID, plan_id: int, state: TaskState | None, priority:
  TaskPriority | None, assigned_agent: str | None) list[TaskSummary]`
- Signature27: `+transition_task_state(user_id: UUID, task_id: int, new_state: TaskState,
  expected_version: int, assigned_agent: str | None) Task`
- Signature28: `+create_criterion(user_id: UUID, task_id: int, criterion_data: CriterionCreate)
  Criterion`
- Signature29: `+update_criterion(user_id: UUID, criterion_id: int, criterion_data: CriterionUpdate)
  Criterion`
- Signature30: `+load_fastembed_model(model_role: str, model_name: str, cache_dir: str, factory:
  Callable[[dict[str, bool]], T]) T`
- Signature31: `-__init__(model: str, threads: int, cache_dir: str | None, workers: int, providers:
  list[str] | None) unknown`
- Signature32: `-_create_text_cross_encoder(model: str, threads: int, cache_dir: str | None,
  providers: list[str] | None, fastembed_kwargs: dict[str, bool]) unknown`
- Signature33: `-__init__(db_adapter: PostgresDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) unknown`
- Signature34: `+semantic_search(user_id: UUID, query: str, k: int, importance_threshold: int |
  None, project_ids: list[int] | None, exclude_ids: list[int] | None) list[Memory]`
- Signature35: `+semantic_search_scored(user_id: UUID, query: str, k: int, importance_threshold: int
  | None, project_ids: list[int] | None, exclude_ids: list[int] | None) list[tuple[Memory, float]]`
- Signature36: `+update_memory(user_id: UUID, memory_id: int, updated_memory: MemoryUpdate,
  existing_memory: Memory, search_fields_changed: bool) Memory`
- Signature37: `-_link_projects(session: unknown, memory: MemoryTable, project_ids: list[int],
  user_id: UUID) None`
- Signature38: `-_link_code_artifacts(session: unknown, memory: MemoryTable, code_artifact_ids:
  list[int], user_id: UUID) None`
- Signature39: `-_link_documents(session: unknown, memory: MemoryTable, document_ids: list[int],
  user_id: UUID) None`
- Signature40: `-_link_files(session: unknown, memory: MemoryTable, file_ids: list[int], user_id:
  UUID) None`
- Signature41: `-_link_skills(session: unknown, memory: MemoryTable, skill_ids: list[int], user_id:
  UUID) None`
- Signature42: `-_build_targeted_rebuild_filter(user_id: UUID, memory_ids: list[int] | None,
  project_id: int | None) unknown`
- Signature43: `+get_subgraph_nodes(user_id: UUID, center_type: str, center_id: int, depth: int,
  include_memories: bool, include_entities: bool, include_projects: bool, include_documents: bool,
  include_code_artifacts: bool, include_files: bool, include_skills: bool, include_plans: bool,
  include_tasks: bool, max_nodes: int) tuple[list[dict[str, Any]], bool]`
- Signature44: `-__init__(db_adapter: SqliteDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) unknown`
- Signature45: `-__init__(db_adapter: SqliteDatabaseAdapter, embedding_adapter: EmbeddingsAdapter,
  rerank_adapter: RerankAdapter | None) None`
- Signature46: `+create_code_artifact(title: str, description: str, code: str, language: str, ctx:
  Context, tags: list[str] | None, project_id: int | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) CodeArtifact`
- Signature47: `+update_code_artifact(artifact_id: int, ctx: Context, title: str | None,
  description: str | None, code: str | None, language: str | None, tags: list[str] | None,
  project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) CodeArtifact`
- Signature48: `+create_document(title: str, description: str, content: str, ctx: Context,
  document_type: str, filename: str | None, tags: list[str] | None, project_id: int | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) Document`
- Signature49: `+update_document(document_id: int, ctx: Context, title: str | None, description: str
  | None, content: str | None, document_type: str | None, filename: str | None, tags: list[str] |
  None, project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url:
  str | None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) Document`
- Signature50: `+create_entity(name: str, entity_type: str, ctx: Context, custom_type: str | None,
  notes: str | None, tags: list[str] | None, aka: list[str] | None, project_ids: list[int] | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) Entity`
- Signature51: `+search_entities(query: str, ctx: Context, entity_type: str | None, tags: list[str]
  | None, limit: int) dict`
- Signature52: `+update_entity(entity_id: int, ctx: Context, name: str | None, entity_type: str |
  None, custom_type: str | None, notes: str | None, tags: list[str] | None, aka: list[str] | None,
  project_ids: list[int] | None, source_repo: str | None, source_files: list[str] | None,
  source_url: str | None, confidence: float | None, encoding_agent: str | None, encoding_version:
  str | None, agent_id: str | None, agent_version: str | None, agent_model: str | None) Entity`
- Signature53: `+create_entity_relationship(source_entity_id: int, target_entity_id: int,
  relationship_type: str, ctx: Context, strength: float | None, confidence: float | None, metadata:
  dict[str, Any] | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) EntityRelationship`
- Signature54: `+get_entity_relationships(entity_id: int, ctx: Context, direction: str | None,
  relationship_type: str | None) dict`
- Signature55: `+update_entity_relationship(relationship_id: int, ctx: Context, relationship_type:
  str | None, strength: float | None, confidence: float | None, metadata: dict[str, Any] | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, encoding_agent:
  str | None, encoding_version: str | None, agent_id: str | None, agent_version: str | None,
  agent_model: str | None) EntityRelationship`
- Signature56: `+create_file(filename: str, description: str, data: str, mime_type: str, ctx:
  Context, tags: list[str] | None, project_id: int | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) unknown`
- Signature57: `+update_file(file_id: int, ctx: Context, filename: str | None, description: str |
  None, data: str | None, mime_type: str | None, tags: list[str] | None, project_id: int | None,
  source_repo: str | None, source_files: list[str] | None, source_url: str | None, confidence: float
  | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str | None,
  agent_version: str | None, agent_model: str | None) unknown`
- Signature58: `+create_memory(title: str, content: str, context: str, keywords: list[str], tags:
  list[str], importance: int, ctx: Context, project_ids: list[int] | None, code_artifact_ids:
  list[int] | None, document_ids: list[int] | None, file_ids: list[int] | None, source_repo: str |
  None, source_files: list[str] | None, source_url: str | None, confidence: float | None,
  encoding_agent: str | None, encoding_version: str | None, agent_id: str | None, agent_version: str
  | None, agent_model: str | None) MemoryCreateResponse`
- Signature59: `+query_memory(query: str, query_context: str, ctx: Context, k: int, include_links:
  bool, max_links_per_primary: int, importance_threshold: int | None, project_ids: list[int] | None,
  strict_project_filter: bool) MemoryQueryResult`
- Signature60: `+update_memory(ctx: Context, memory_id: int | None, id: int | None, title: str |
  None, content: str | None, context: str | None, keywords: list[str] | None, tags: list[str] |
  None, importance: int | None, project_ids: list[int] | None, code_artifact_ids: list[int] | None,
  document_ids: list[int] | None, file_ids: list[int] | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None, kwargs: unknown) Memory`
- Signature61: `+link_memories(ctx: Context, memory_id: int | None, related_ids: list[int] | int |
  None, source_id: int | None, target_id: int | None, target_ids: list[int] | int | None,
  related_id: int | None, memory_id_1: int | None, memory_id_2: int | None, from_id: int | None,
  to_id: int | None, from_memory_id: int | None, to_memory_id: int | None, memory_ids: list[int] |
  None, ids: list[int] | None, id: int | None, linked_ids: list[int] | int | None,
  related_memory_ids: list[int] | int | None, kwargs: unknown) dict`
- Signature62: `+unlink_memories(ctx: Context, source_id: int | None, target_id: int | None,
  memory_id: int | None, related_id: int | None, related_ids: list[int] | int | None, target_ids:
  list[int] | int | None, memory_ids: list[int] | None, ids: list[int] | None, memory_id_1: int |
  None, memory_id_2: int | None, from_id: int | None, to_id: int | None, from_memory_id: int | None,
  to_memory_id: int | None, id: int | None, linked_ids: list[int] | int | None, related_memory_ids:
  list[int] | int | None, kwargs: unknown) dict`
- Signature63: `+mark_memory_obsolete(ctx: Context, memory_id: int | None, id: int | None, reason:
  str, superseded_by: int | None, kwargs: unknown) dict`
- Signature64: `+get_recent_memories(ctx: Context, limit: int, offset: int, project_ids: list[int] |
  None, include_obsolete: bool, sort_by: str, sort_order: str, tags: list[str] | None,
  importance_min: int | None, created_since: str | None) dict`
- Signature65: `+create_plan(title: str, project_id: int, ctx: Context, goal: str | None, context:
  str | None, status: str, external_ref: str | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) unknown`
- Signature66: `+update_plan(plan_id: int, ctx: Context, title: str | None, goal: str | None,
  context: str | None, status: str | None, external_ref: str | None, source_repo: str | None,
  source_files: list[str] | None, source_url: str | None, confidence: float | None, encoding_agent:
  str | None, encoding_version: str | None, agent_id: str | None, agent_version: str | None,
  agent_model: str | None) unknown`
- Signature67: `+create_project(name: str, description: str, project_type: ProjectType, ctx:
  Context, status: ProjectStatus, repo_name: str | None, last_encoding_point: str | None, notes: str
  | None, source_repo: str | None, source_files: list[str] | None, source_url: str | None,
  confidence: float | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str
  | None, agent_version: str | None, agent_model: str | None) Project`
- Signature68: `+update_project(project_id: int, ctx: Context, name: str | None, description: str |
  None, project_type: ProjectType | None, status: ProjectStatus | None, repo_name: str | None,
  last_encoding_point: str | None, notes: str | None, source_repo: str | None, source_files:
  list[str] | None, source_url: str | None, confidence: float | None, encoding_agent: str | None,
  encoding_version: str | None, agent_id: str | None, agent_version: str | None, agent_model: str |
  None) Project`
- Signature69: `+create_skill(name: str, description: str, content: str, ctx: Context, license: str
  | None, compatibility: str | None, allowed_tools: list[str] | None, metadata: dict[str, Any] |
  None, tags: list[str] | None, importance: int, project_id: int | None, source_repo: str | None,
  source_files: list[str] | None, source_url: str | None, confidence: float | None, encoding_agent:
  str | None, encoding_version: str | None, agent_id: str | None, agent_version: str | None,
  agent_model: str | None) unknown`
- Signature70: `+list_skills(ctx: Context, project_id: int | None, tags: list[str] | None,
  importance_threshold: int | None) dict`
- Signature71: `+update_skill(skill_id: int, ctx: Context, name: str | None, description: str |
  None, content: str | None, license: str | None, compatibility: str | None, allowed_tools:
  list[str] | None, metadata: dict[str, Any] | None, tags: list[str] | None, importance: int | None,
  project_id: int | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature72: `+import_skill(skill_md_content: str, ctx: Context, project_id: int | None,
  importance: int) unknown`
- Signature73: `+unlink_skill_from_code_artifact(skill_id: int, code_artifact_id: int, ctx: Context)
  dict`
- Signature74: `+create_task(title: str, plan_id: int, ctx: Context, description: str | None,
  priority: str, assigned_agent: str | None, criteria: list[dict[str, Any]] | None, dependency_ids:
  list[int] | None, source_repo: str | None, source_files: list[str] | None, source_url: str | None,
  confidence: float | None, encoding_agent: str | None, encoding_version: str | None, agent_id: str
  | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature75: `+update_task(task_id: int, ctx: Context, title: str | None, description: str | None,
  priority: str | None, source_repo: str | None, source_files: list[str] | None, source_url: str |
  None, confidence: float | None, encoding_agent: str | None, encoding_version: str | None,
  agent_id: str | None, agent_version: str | None, agent_model: str | None) unknown`
- Signature76: `+query_tasks(plan_id: int, ctx: Context, state: str | None, priority: str | None,
  assigned_agent: str | None) unknown`
- Signature77: `+create_project_adapters(project_service: ProjectService, user_service: UserService)
  dict[str, Any]`
- Signature78: `+create_code_artifact_adapters(code_artifact_service: CodeArtifactService,
  user_service: UserService) dict[str, Any]`
- Signature79: `+create_document_adapters(document_service: DocumentService, user_service:
  UserService) dict[str, Any]`
- Signature80: `+register_simplified_tool(registry: ToolRegistry, name: str, category: ToolCategory,
  description: str, parameters: list[dict], returns: str, implementation: Any, examples: list[str],
  tags: list[str], mutates: bool) unknown`
- Signature81: `+register_all_tools_metadata(registry: ToolRegistry, user_service: UserService,
  memory_service: MemoryService, project_service: unknown, code_artifact_service: unknown,
  document_service: unknown, entity_service: unknown, plan_service: unknown, task_service: unknown,
  file_service: unknown, skill_service: unknown) unknown`
- Signature82: `+register(name: str, category: ToolCategory, description: str, parameters:
  list[ToolParameter], returns: str, implementation: Any, examples: list[str], tags: list[str],
  mutates: bool) None`
- Signature83: `+get_activity(user_id: UUID, entity_type: EntityType | None, action: ActionType |
  None, entity_id: int | None, actor: ActorType | None, since: datetime | None, until: datetime |
  None, limit: int, offset: int) ActivityListResponse`
- Signature84: `+get_entity_history(user_id: UUID, entity_type: EntityType, entity_id: int, limit:
  int, offset: int) ActivityListResponse`
- Signature85: `-_emit_event(user_id: UUID, entity_type: EntityType, entity_id: int, action:
  ActionType, snapshot: dict, changes: dict | None, metadata: dict | None) None`
- Signature86: `-_emit_event(user_id: UUID, entity_type: ActivityEntityType, entity_id: int, action:
  ActionType, snapshot: dict, changes: dict | None, metadata: dict | None) None`
- Signature87: `-__init__(memory_repo: MemoryRepository, entity_repo: EntityRepository,
  project_service: ProjectServiceProtocol | None, document_service: DocumentServiceProtocol | None,
  code_artifact_service: CodeArtifactServiceProtocol | None, file_service: FileServiceProtocol |
  None, skill_service: SkillServiceProtocol | None, plan_service: PlanServiceProtocol | None,
  task_service: TaskServiceProtocol | None) unknown`
- Signature88: `+get_subgraph(user_id: UUID, center_node_id: str, depth: int, node_types: list[str]
  | None, max_nodes: int) SubgraphResponse`
- Signature89: `-_fetch_node_data(user_id: UUID, memory_ids: list[int], entity_ids: list[int],
  project_ids: list[int], document_ids: list[int], code_artifact_ids: list[int], file_ids:
  list[int], skill_ids: list[int], depth_lookup: dict, plan_ids: list[int] | None, task_ids:
  list[int] | None, task_summaries: list | None) list[SubgraphNode]`
- Signature90: `-_fetch_edges(user_id: UUID, memory_ids: list[int], entity_ids: list[int],
  project_ids: list[int], document_ids: list[int], code_artifact_ids: list[int], file_ids: list[int]
  | None, skill_ids: list[int] | None, plan_ids: list[int] | None, task_ids: list[int] | None,
  task_summaries: list | None) list[SubgraphEdge]`
- Signature91: `+mark_memory_obsolete(user_id: UUID, memory_id: int, reason: str, superseded_by: int
  | None) bool`
- Signature92: `-_fetch_linked_memories(user_id: unknown, primary_memories: list[Memory],
  max_links_per_primary: int, project_ids: list[int] | None) list[LinkedMemory]`
- Signature93: `-_apply_token_budget(primary_memories: list[Memory], linked_memories:
  list[LinkedMemory], max_tokens: int, max_memories: int) tuple[list[Memory], list[LinkedMemory],
  int, bool]`
- Signature94: `+truncate_memories_by_budget(memories: list[Memory], max_tokens: int, max_count:
  int) tuple[list[Memory], int, bool]`
- Signature95: `-__init__(memory_repository: MemoryRepository, embedding_adapter: EmbeddingsAdapter,
  batch_size: int) unknown`
- Signature96: `+rebuild_targeted(user_id: UUID, memory_ids: list[int] | None, project_id: int |
  None, progress_callback: Callable[[int, int], None] | None) TargetedRebuildResult`
- Signature97: `-_record_unresolved_memory_ids(memory_ids: list[int] | None, project_id: int | None,
  result: TargetedRebuildResult) None`
- Signature98: `-_recompute_auto_links(user_id: UUID, memory_ids: list[int], result:
  TargetedRebuildResult) None`
- Signature99: `+import_skill(user_id: UUID, skill_md_content: str, project_id: int | None,
  importance: int) Skill`
- Signature100: `-__init__(task_repo: TaskRepository, plan_service: PlanService, event_bus:
  "EventBus | None") unknown`
- Signature101: `+transition_task(user_id: UUID, task_id: int, new_state: TaskState,
  expected_version: int) Task`
- Signature102: `-_validate_same_plan(user_id: UUID, task_id: int, dep_task_id: int,
  expected_plan_id: int) None`
- Signature103: `+run_session(skill: str, skill_dir: Path, workspace: Path, prompt: str, timeout:
  float) SessionOutcome`
- Signature104: `-__init__(config: HarnessConfig, runner: SessionRunner, server_url: str, run_dir:
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
