"""FastAPI application for a python service
"""
import argparse
import asyncio
import atexit

# NOTE: Logging is configured inside lifespan() to avoid STDIO pollution
# before MCP handshake completes. Do NOT add module-level logging here.
import logging
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.bootstrap import build_runtime, dispose_runtime
from app.config.auth import build_auth_provider
from app.config.settings import settings
from app.routes.api import (
    activity,
    auth,
    code_artifacts,
    documents,
    entities,
    files,
    graph,
    health,
    memories,
    plans,
    projects,
    skills,
    tasks,
)
from app.routes.mcp import meta_tools
from app.version import get_version

# Global references - initialized in lifespan()
_queue_listener = None
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Manages application lifecycle.
    """
    global _queue_listener

    from app.config.logging_config import configure_logging, shutdown_logging
    _queue_listener = configure_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
    )
    atexit.register(shutdown_logging)

    logger.info("Starting session", extra={"service": settings.SERVICE_NAME})

    runtime = await build_runtime()
    services = runtime.services

    mcp.user_service = services.user
    mcp.memory_service = services.memory
    mcp.project_service = services.project
    mcp.code_artifact_service = services.code_artifact
    mcp.document_service = services.document
    mcp.entity_service = services.entity
    mcp.graph_service = services.graph
    mcp.activity_service = services.activity
    mcp.event_bus = runtime.event_bus

    if services.file:
        mcp.file_service = services.file

    if services.skill:
        mcp.skill_service = services.skill

    if services.plan:
        mcp.plan_service = services.plan
    if services.task:
        mcp.task_service = services.task

    logger.info("Services initialized and attached to FastMCP instance")

    # Initialize token cache for HTTP auth performance
    if settings.TOKEN_CACHE_ENABLED:
        from app.middleware.auth import TokenCache
        mcp.token_cache = TokenCache(
            ttl_seconds=settings.TOKEN_CACHE_TTL_SECONDS,
            max_size=settings.TOKEN_CACHE_MAX_SIZE,
        )
        logger.info(f"Token cache initialized (TTL: {settings.TOKEN_CACHE_TTL_SECONDS}s, max: {settings.TOKEN_CACHE_MAX_SIZE})")
    else:
        mcp.token_cache = None
        logger.info("Token cache disabled")

    mcp.registry = runtime.registry
    mcp._instance_permitted_tools = runtime.permitted_tools
    mcp._instance_scopes = runtime.instance_scopes
    logger.info("Registry and scope ceiling attached to FastMCP instance")

    yield

    logger.info("Shutting down session", extra={"service": settings.SERVICE_NAME})
    await dispose_runtime(runtime)
    logger.info("Database connections closed")
    logger.info("Session shutdown complete")


mcp = FastMCP(settings.SERVICE_NAME, lifespan=lifespan, auth=build_auth_provider())


@mcp.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Root endpoint with basic service information."""
    logger.info("Root endpoint accessed")
    return JSONResponse({
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
        },
    })


health.register(mcp)
auth.register(mcp)
memories.register(mcp)
entities.register(mcp)
projects.register(mcp)
documents.register(mcp)
code_artifacts.register(mcp)
graph.register(mcp)
activity.register(mcp)

if settings.FILES_ENABLED:
    files.register(mcp)

if settings.SKILLS_ENABLED:
    skills.register(mcp)

if settings.PLANNING_ENABLED:
    plans.register(mcp)
    tasks.register(mcp)

meta_tools.register(mcp)


async def _run_reembed(args):
    """Run the re-embedding workflow"""
    from app.config.logging_config import configure_logging, shutdown_logging
    configure_logging(log_level="INFO", log_format="console")
    atexit.register(shutdown_logging)

    from app.bootstrap import (
        create_db_adapter,
        create_repositories,
        get_embedding_adapter,
    )
    from app.services.backup_service import BackupService
    from app.services.re_embedding_service import ReEmbeddingService

    embeddings_adapter = get_embedding_adapter()
    backup_service = BackupService()

    print("\n[1/5] Validating configuration...")
    model_display = settings.AZURE_DEPLOYMENT if settings.EMBEDDING_PROVIDER == "Azure" else settings.EMBEDDING_MODEL
    print(f"  Provider: {settings.EMBEDDING_PROVIDER} ({model_display})")
    print(f"  Dimensions: {settings.EMBEDDING_DIMENSIONS}")
    if settings.DATABASE == "SQLite":
        print(f"  Database: SQLite ({settings.SQLITE_PATH})")
    else:
        print(f"  Database: PostgreSQL ({settings.POSTGRES_HOST}:{settings.PGPORT}/{settings.POSTGRES_DB})")
    print(f"  Batch size: {args.batch_size}")

    # Initialize database
    db_adapter = create_db_adapter()

    if settings.DATABASE == "SQLite" and not settings.SQLITE_MEMORY:
        data_dir = Path(settings.SQLITE_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    await db_adapter.init_db()

    # Create memory repository (reranker not needed for re-embedding)
    repos = create_repositories(db_adapter, embeddings_adapter, None)
    memory_repository = repos["memory"]

    # Count memories for dry run / estimation
    total = await memory_repository.count_all_memories()
    print(f"  Memories to process: {total}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would re-embed {total} memories with the above configuration.")
        print("  No changes were made.")
        await db_adapter.dispose()
        return

    if total == 0:
        print("\n  No memories to re-embed. Done.")
        await db_adapter.dispose()
        return

    # Create backup (skip for in-memory SQLite)
    backup_path = None
    if settings.DATABASE == "SQLite" and settings.SQLITE_MEMORY:
        print("\n[2/5] Skipping backup (in-memory database)...")
    else:
        print("\n[2/5] Creating backup...")
        backup_path = await backup_service.create_backup()
        print(f"  Backup saved: {backup_path}")

    # Set up signal handling for graceful restore
    restore_triggered = False

    def signal_handler(signum, frame):
        nonlocal restore_triggered
        if restore_triggered:
            return
        restore_triggered = True
        print("\n\nInterrupted! Restoring from backup...")
        if backup_path:
            asyncio.get_event_loop().run_until_complete(
                backup_service.restore_backup(backup_path),
            )
            print(f"  Restored: {backup_path}")
        sys.exit(1)

    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Reset schema
        print("\n[3/5] Updating vector schema...")
        await memory_repository.reset_embedding_storage()
        if settings.DATABASE == "SQLite":
            print(f"  Recreated vec_memories table with {settings.EMBEDDING_DIMENSIONS} dimensions")
        else:
            print(f"  Altered embedding column to vector({settings.EMBEDDING_DIMENSIONS})")

        # Re-embed
        print("\n[4/5] Re-embedding memories...")

        def progress(processed, total_count):
            pct = int((processed / total_count) * 100) if total_count > 0 else 100
            bar_filled = int(pct / 4)
            bar = "\u2588" * bar_filled + "\u2591" * (25 - bar_filled)
            print(f"\r  [{bar}] {processed}/{total_count} memories ({pct}%)", end="", flush=True)

        service = ReEmbeddingService(
            memory_repository=memory_repository,
            embedding_adapter=embeddings_adapter,
            batch_size=args.batch_size,
        )

        result = await service.re_embed_all(progress_callback=progress)
        print()  # newline after progress bar

        # Validate
        print("\n[5/5] Validating...")
        if result.validation:
            print(f"  Count check: {result.total_memories} memories, "
                  f"{result.total_processed} embeddings "
                  f"{'✓' if result.validation.count_ok else '✗'}")
            print(f"  Dimension check: {'✓' if result.validation.dimensions_ok else '✗'}")
            print(f"  Search check: {'✓' if result.validation.search_ok else '✗'}")

            if not result.validation.all_passed:
                print("\n  Validation FAILED!")
                if backup_path:
                    print("  Restoring from backup...")
                    await backup_service.restore_backup(backup_path)
                    print(f"  Restored: {backup_path}")
                    print("  Database returned to pre-migration state.")
                await db_adapter.dispose()
                sys.exit(1)

        print(f"\n  Successfully re-embedded {result.total_processed} memories")
        if backup_path:
            print(f"  Backup retained at: {backup_path}")
            print("  (Delete manually when satisfied with results)")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        if backup_path:
            print("\n  Restoring from backup...")
            await backup_service.restore_backup(backup_path)
            print(f"  Restored: {backup_path}")
            print("  Database returned to pre-migration state.")
        await db_adapter.dispose()
        raise
    finally:
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)

    await db_adapter.dispose()


def _serve(transport, host, port):
    """Run the MCP server on the given transport (shared by legacy and new spellings)."""
    if transport == "stdio":
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        mcp.run(show_banner=False)
    elif not settings.CORS_ENABLED:
        # No CORS - use existing code path (zero behavioral change)
        mcp.run(transport="http", host=host, port=port, show_banner=False)
    else:
        # CORS enabled - use http_app with middleware
        from starlette.middleware import Middleware
        from starlette.middleware.cors import CORSMiddleware

        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=settings.CORS_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=[
                    "mcp-protocol-version",
                    "mcp-session-id",
                    "Authorization",
                    "Content-Type",
                ],
                expose_headers=["mcp-session-id"],
            ),
        ]

        import uvicorn
        app = mcp.http_app(middleware=middleware)
        uvicorn.run(app, host=host, port=port)


def _legacy_launcher(argv):
    """Pre-subcommand argument surface, kept working indefinitely."""
    # cli()'s KNOWN-gate sends a bare `--help` here, so this epilog is the only place
    # a top-level `forgetful --help` can surface the subcommands. Canonical per-verb
    # help lives in app/routes/cli/parser.py; this is just a discoverability pointer.
    parser = argparse.ArgumentParser(
        description="Forgetful - MCP Server for AI Agent Memory",
        epilog=(
            "Subcommands (run 'forgetful <command> --help' for details):\n"
            "  memory    Curated memory commands (search, save, get, recent)\n"
            "  tools     Inspect the available Forgetful tools (list, info)\n"
            "  call      Execute any Forgetful tool by name\n"
            "  auth      Authenticate against a remote deployment "
            "(login, status, logout)\n"
            "  project   Curated project commands (list)\n"
            "  serve     Run the Forgetful MCP server\n"
            "  re-embed  Re-embed all memories with the configured provider\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method (default: stdio for MCP clients)",
    )
    parser.add_argument(
        "--host",
        default=settings.SERVER_HOST,
        help=f"HTTP host (default: {settings.SERVER_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.SERVER_PORT,
        help=f"HTTP port (default: {settings.SERVER_PORT})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    # Re-embed arguments
    parser.add_argument(
        "--re-embed",
        action="store_true",
        help="Re-embed all memories with the currently configured provider",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Batch size for re-embedding (default: 20)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    args = parser.parse_args(argv)

    if args.re_embed:
        asyncio.run(_run_reembed(args))
        return None

    return _serve(transport=args.transport, host=args.host, port=args.port)


def cli():
    """Command-line entry point: subcommand dispatch with a permanent legacy fallback."""
    argv = sys.argv[1:]

    from app.routes.cli.parser import KNOWN, dispatch
    if argv and argv[0] in KNOWN:
        return dispatch(argv, serve_runner=_serve, reembed_runner=_run_reembed)

    return _legacy_launcher(argv)


if __name__ == "__main__":
    # The console script wraps cli() in sys.exit(); direct execution must too,
    # or failed commands would exit 0.
    sys.exit(cli())
