"""SQL logging (DB_LOGGING) must never write to stdout, the stdio MCP transport.

SQLAlchemy's ``echo=True`` installs its own ``StreamHandler(sys.stdout)`` on the engine
logger, bypassing the stderr logging pipeline and the sensitive-data filter. SQL logging is
therefore driven through ``configure_logging(db_logging=...)`` instead.

- The subprocess test drives the real ``main._serve("stdio")`` on in-memory SQLite and checks
  that stdout carries nothing but JSON-RPC.
- The in-process test checks the SQL really is logged, to stderr, without parameter values.
"""
import io
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from app.config import logging_config
from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

ROOT = Path(__file__).resolve().parents[2]
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "db-logging-test", "version": "0"},
    },
}


# Runs the real stdio server entry point, with the embedding model swapped for a stub so the
# subprocess never downloads a FastEmbed model (and so never needs the network).
SERVER_SCRIPT = """
import main
from app import bootstrap


class StubEmbeddings:
    async def generate_embedding(self, text):
        return [0.0] * bootstrap.settings.EMBEDDING_DIMENSIONS


bootstrap.get_embedding_adapter = StubEmbeddings
main._serve("stdio", None, None)
"""


def _run_stdio_server(tmp_path: Path, db_logging: str) -> tuple[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DB_", "SQLITE", "DATABASE", "POSTGRES", "FASTMCP"))
    }
    env.update(
        HOME=str(tmp_path),
        XDG_CONFIG_HOME=str(tmp_path / "cfg"),
        XDG_DATA_HOME=str(tmp_path / "data"),
        PYTHONPATH=str(ROOT),
        PYTHONUNBUFFERED="1",
        DATABASE="SQLite",
        SQLITE_MEMORY="true",
        RERANKING_ENABLED="false",
        DB_LOGGING=db_logging,
    )
    proc = subprocess.run(  # noqa: S603 - fixed argv, test-controlled script
        [sys.executable, "-c", SERVER_SCRIPT],
        input=json.dumps(INITIALIZE) + "\n",
        cwd=tmp_path,  # empty directory: no local dotenv file is discovered
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.stdout, proc.stderr


def _non_jsonrpc_lines(stdout: str) -> list[str]:
    bad = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            bad.append(line)
            continue
        if not (isinstance(message, dict) and message.get("jsonrpc") == "2.0"):
            bad.append(line)
    return bad


def test_stdio_stdout_carries_only_jsonrpc_with_db_logging(tmp_path):
    stdout, stderr = _run_stdio_server(tmp_path, "true")

    # Guards against a setup error: the handshake really happened.
    assert '"serverInfo"' in stdout, f"server never answered initialize.\nSTDERR:\n{stderr[-2000:]}"

    assert _non_jsonrpc_lines(stdout) == [], "DB_LOGGING=true: non-JSON-RPC data on stdio stdout"


async def test_db_logging_sends_sql_to_stderr_pipeline_without_parameters(monkeypatch):
    secret = "PRIVATE-NOTE-SECRET-XYZ-9876"
    root = logging.getLogger()
    engine_logger = logging.getLogger("sqlalchemy.engine")
    saved = (list(root.handlers), root.level, engine_logger.level)
    stderr, stdout = io.StringIO(), io.StringIO()
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    monkeypatch.setattr(settings, "DB_LOGGING", True)
    # pytest re-installs its own sys.stderr/stdout when the test body starts: patch here
    monkeypatch.setattr(sys, "stderr", stderr)
    monkeypatch.setattr(sys, "stdout", stdout)

    logging_config.configure_logging("WARNING", "console", db_logging=settings.DB_LOGGING)
    adapter = SqliteDatabaseAdapter()
    try:
        async with adapter.session(uuid4()) as session:
            await session.execute(text("SELECT :value AS probe"), {"value": secret})
    finally:
        await adapter.dispose()
        logging_config.shutdown_logging()  # flushes queued records
        root.handlers[:] = saved[0]
        root.setLevel(saved[1])
        engine_logger.setLevel(saved[2])

    assert stdout.getvalue() == ""
    assert "SELECT" in stderr.getvalue()
    assert "AS probe" in stderr.getvalue()
    assert secret not in stderr.getvalue()
