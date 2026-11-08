import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import sqlite_vec
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings

logger = logging.getLogger(__name__)

# FTS5 'rebuild' against a content view that uses json_each fails on the
# bundled SQLite (3.50.x: "no such table: main.json_each"). Keep one decoded
# representation in memories_fts_src and backfill with delete-all + INSERT.
_FTS_OBJECT_NAMES = (
    "memories_fts",
    "memories_fts_src",
    "memories_fts_ai",
    "memories_fts_ad",
    "memories_fts_bu",
    "memories_fts_au",
)
_CREATE_FTS_SRC_VIEW = """
CREATE VIEW memories_fts_src AS
SELECT
  id,
  title,
  content,
  context,
  (SELECT group_concat(value, ' ') FROM json_each(COALESCE(keywords, '[]')))
    AS keywords,
  (SELECT group_concat(value, ' ') FROM json_each(COALESCE(tags, '[]')))
    AS tags
FROM memories
"""
_CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE memories_fts USING fts5(
    title, content, context, keywords, tags,
    content='memories_fts_src', content_rowid='id', tokenize='unicode61'
)
"""
_CREATE_FTS_AI = """
CREATE TRIGGER memories_fts_ai AFTER INSERT ON memories BEGIN
  INSERT INTO memories_fts(rowid, title, content, context, keywords, tags)
  SELECT id, title, content, context, keywords, tags
  FROM memories_fts_src WHERE id = new.id;
END
"""
_CREATE_FTS_AD = """
CREATE TRIGGER memories_fts_ad BEFORE DELETE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, title, content, context, keywords, tags)
  SELECT 'delete', id, title, content, context, keywords, tags
  FROM memories_fts_src WHERE id = old.id;
END
"""
_CREATE_FTS_BU = """
CREATE TRIGGER memories_fts_bu BEFORE UPDATE OF
  title, content, context, keywords, tags ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, title, content, context, keywords, tags)
  SELECT 'delete', id, title, content, context, keywords, tags
  FROM memories_fts_src WHERE id = old.id;
END
"""
_CREATE_FTS_AU = """
CREATE TRIGGER memories_fts_au AFTER UPDATE OF
  title, content, context, keywords, tags ON memories BEGIN
  INSERT INTO memories_fts(rowid, title, content, context, keywords, tags)
  SELECT id, title, content, context, keywords, tags
  FROM memories_fts_src WHERE id = new.id;
END
"""
_FTS_BACKFILL = """
INSERT INTO memories_fts(rowid, title, content, context, keywords, tags)
SELECT id, title, content, context, keywords, tags FROM memories_fts_src
"""


def _fts_uses_src_view(fts_sql: str) -> bool:
    compact = fts_sql.replace('"', "'").replace(" ", "").lower()
    return "content='memories_fts_src'" in compact


def _sqlite_connection_creator():
    """Create a SQLite connection with sqlite-vec extension loaded.
    This is used as a creator function for SQLAlchemy's engine.
    """
    import sqlite3

    # Construct connection string
    if settings.SQLITE_MEMORY:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
    else:
        conn = sqlite3.connect(settings.SQLITE_PATH, check_same_thread=False)

    # Load sqlite-vec extension
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    conn.enable_load_extension(False)

    # Set pragmas
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


class SqliteDatabaseAdapter:
    """SQLite database adapter for async operations.

    Key differences from Postgres:
    - No Row-Level Security (RLS) - user isolation via application-level filtering
    - Uses sqlite-vec extension for vector operations
    - WAL mode enabled for better concurrency
    - Dialect-default pooling: StaticPool in memory, AsyncAdaptedQueuePool for files
    """

    def __init__(self):

        if not settings.SQLITE_MEMORY:
            from pathlib import Path
            db_path = Path(settings.SQLITE_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Validated DB directory exists", extra={
                "SQL Lite Path": settings.SQLITE_PATH,
            })
        # Construct connection string
        connection_string = self._construct_connection_string()

        # Create async engine with SQLite-specific settings
        self._engine: AsyncEngine = create_async_engine(
            url=connection_string,
            echo=settings.DB_LOGGING,
            future=True,
            # Use the SQLite dialect's default pool for memory/file databases.
            poolclass=None,
            connect_args={
                "check_same_thread": False,  # Required for async
            },
        )

        # Register the extension on every new connection, including pooled connections.
        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Load sqlite-vec extension on every connection"""
            # For aiosqlite, dbapi_conn is AsyncAdapt_aiosqlite_connection
            # Access the underlying aiosqlite Connection via _connection
            if hasattr(dbapi_conn, "_connection"):
                aio_conn = dbapi_conn._connection
                # aiosqlite.Connection has a _conn attribute with the raw sqlite3.Connection
                if hasattr(aio_conn, "_conn"):
                    raw_conn = aio_conn._conn
                    # Load extension on raw connection
                    raw_conn.enable_load_extension(True)
                    raw_conn.load_extension(sqlite_vec.loadable_path())
                    raw_conn.enable_load_extension(False)
                    # Set pragmas
                    raw_conn.execute("PRAGMA journal_mode=WAL")
                    raw_conn.execute("PRAGMA synchronous=NORMAL")
                    raw_conn.execute("PRAGMA foreign_keys=ON")
                    raw_conn.execute("PRAGMA busy_timeout=5000")
                    logger.debug("sqlite-vec extension loaded on connection")

        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine, expire_on_commit=False, autoflush=False,
        )

    @asynccontextmanager
    async def session(self, user_id: UUID) -> AsyncIterator[AsyncSession]:
        """Create a user-scoped session.

        Note: Unlike Postgres, SQLite doesn't have RLS.
        User isolation MUST be enforced at the application level
        by including user_id in all WHERE clauses.
        """
        session = self._session_factory()
        try:
            # No RLS setup needed - user filtering happens in queries
            yield session
            await session.commit()
        except Exception as e:
            logger.exception(
                msg="Database session initialization failed", extra={"error": str(e)},
            )
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def system_session(self) -> AsyncIterator[AsyncSession]:
        """Create a system session for admin operations"""
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.exception(
                msg="Database system session initialization failed",
                extra={"error": str(e)},
            )
            await session.rollback()
            raise
        finally:
            await session.close()

    async def init_db(self) -> None:
        """Initialize database via Alembic migrations.

        Alembic handles both fresh and existing databases:
        - Fresh database: Creates full schema via migrations
        - Existing database: Runs pending migrations

        Note: sqlite-vec extension is loaded automatically via event listener on first connection
        """
        async with self._engine.begin() as conn:
            logger.info("Initializing SQLite database")

            # Run migrations (Alembic handles fresh vs existing database)
            await conn.run_sync(self._run_migrations)
            logger.info("Database schema initialized via Alembic")

            # Create virtual tables for vector storage (not managed by Alembic)
            await conn.execute(
                text(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
                    memory_id TEXT PRIMARY KEY,
                    embedding FLOAT[{settings.EMBEDDING_DIMENSIONS}]
                )
            """),
            )

            await conn.execute(
                text(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_skills USING vec0(
                    skill_id TEXT PRIMARY KEY,
                    embedding FLOAT[{settings.EMBEDDING_DIMENSIONS}]
                )
            """),
            )
            logger.info("sqlite-vec virtual tables created for vector storage")

            await self.ensure_memory_fts(conn)

    async def ensure_memory_fts(self, conn) -> bool:
        """Create or repair FTS5 index/triggers; reindex when anything was missing or stale."""
        result = await conn.execute(
            text(
                "SELECT name, sql FROM sqlite_master WHERE name IN "
                "('memories_fts','memories_fts_src','memories_fts_ai',"
                "'memories_fts_ad','memories_fts_bu','memories_fts_au')",
            ),
        )
        rows = result.fetchall()
        existing = {row[0] for row in rows}
        sql_by_name = {row[0]: row[1] or "" for row in rows}
        missing_before = set(_FTS_OBJECT_NAMES) - existing
        stale_content = bool(sql_by_name.get("memories_fts")) and not _fts_uses_src_view(
            sql_by_name.get("memories_fts", ""),
        )
        if not missing_before and not stale_content:
            return False

        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ai"))
        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ad"))
        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_bu"))
        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_au"))
        await conn.execute(text("DROP TABLE IF EXISTS memories_fts"))
        await conn.execute(text("DROP VIEW IF EXISTS memories_fts_src"))

        await conn.execute(text(_CREATE_FTS_SRC_VIEW))
        await conn.execute(text(_CREATE_FTS_TABLE))
        await conn.execute(text(_CREATE_FTS_AI))
        await conn.execute(text(_CREATE_FTS_AD))
        await conn.execute(text(_CREATE_FTS_BU))
        await conn.execute(text(_CREATE_FTS_AU))
        await conn.execute(text("INSERT INTO memories_fts(memories_fts) VALUES('delete-all')"))
        await conn.execute(text(_FTS_BACKFILL))
        count_result = await conn.execute(text("SELECT COUNT(*) FROM memories"))
        row_count = count_result.scalar()
        logger.info("Rebuilt memories_fts", extra={"row_count": row_count})
        return True

    def _run_migrations(self, connection) -> None:
        """Run pending Alembic migrations synchronously (called via run_sync)."""
        from pathlib import Path

        from alembic.config import Config

        from alembic import command

        # Find alembic.ini relative to package root
        package_root = Path(__file__).parent.parent.parent.parent
        alembic_ini = package_root / "alembic.ini"

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini))

        # Override database URL in config
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            self._construct_connection_string(),
        )

        # Configure to use existing connection
        alembic_cfg.attributes["connection"] = connection

        try:
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic upgrade completed successfully")
        except Exception as e:
            logger.error(f"Alembic migration failed: {e}", exc_info=True)
            raise

    async def dispose(self) -> None:
        """Dispose of the database engine and close all connections"""
        await self._engine.dispose()

    def _construct_connection_string(self) -> str:
        """Construct SQLite connection string"""
        if settings.SQLITE_MEMORY:
            # In-memory database (for testing)
            return "sqlite+aiosqlite:///:memory:"
        # File-based database
        return f"sqlite+aiosqlite:///{settings.SQLITE_PATH}"
