"""Integration tests for startup configuration wiring

Documented settings must either take effect or be rejected up front; they must never be
silently ignored or fail later with an opaque error:

- EMBEDDING_PROVIDER / RERANKING_PROVIDER / LOG_FORMAT match case-insensitively and an
  unknown value fails fast (like DATABASE) instead of selecting a different provider.
- ACTIVITY_RETENTION_DAYS accepts the documented empty / null spellings for "keep forever".
- SSE_MAX_QUEUE_SIZE reaches the EventBus built by the composition root.
- ENCODING_* / AGENT_* provenance defaults are length-checked against the model caps.
- On PostgreSQL, *_MAX_LENGTH settings are bounded by the fixed VARCHAR column widths.
- The root service-info document only advertises endpoints that exist.

Settings are built from environment variables with Settings(_env_file=None), which is what
startup does, so no database or network is needed.
"""
import asyncio
import importlib
import inspect
import logging
import os
import pkgutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel, ValidationError

import app.models as models_package
import main
from app import bootstrap
from app.bootstrap import build_runtime, dispose_runtime
from app.config import logging_config
from app.config.settings import (
    POSTGRES_COLUMN_WIDTHS,
    PROVENANCE_MAX_LENGTHS,
    Settings,
    settings,
)
from app.models.activity_models import ActionType, ActivityEvent, EntityType
from app.models.user_models import UserCreate
from app.repositories.embeddings import embedding_adapter as embedding_module
from app.repositories.embeddings import reranker_adapter as reranker_module
from app.repositories.postgres.postgres_tables import (
    CodeArtifactsTable,
    DocumentsTable,
    EntitiesTable,
    EntityRelationshipsTable,
    FilesTable,
    PlansTable,
    SkillsTable,
    TasksTable,
)
from app.utils.provenance import PROVENANCE_ENV_MAP


def _settings(monkeypatch, **env):
    """Build Settings the way startup does: from the environment, ignoring .env files."""
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return Settings(_env_file=None)


# ============================================================================
# Provider / format settings: case-insensitive, unknown values rejected
# ============================================================================

@pytest.fixture
def fake_adapters(monkeypatch):
    """Replace provider adapters with cheap fakes so no model is loaded."""
    def fake(name):
        return type(name, (), {"__init__": lambda self, *args, **kwargs: None})

    for name in (
        "AzureOpenAIAdapter",
        "GoogleEmbeddingsAdapter",
        "OpenAIEmbeddingsAdapter",
        "OllamaEmbeddingsAdapter",
        "FastEmbeddingAdapter",
    ):
        monkeypatch.setattr(embedding_module, name, fake(name))
    for name in ("HttpRerankAdapter", "FastEmbedCrossEncoderAdapter"):
        monkeypatch.setattr(reranker_module, name, fake(name))


@pytest.mark.parametrize(
    ("setting", "raw", "canonical"),
    [
        ("EMBEDDING_PROVIDER", "openai", "OpenAI"),
        ("EMBEDDING_PROVIDER", "OLLAMA", "Ollama"),
        ("EMBEDDING_PROVIDER", " azure ", "Azure"),
        ("EMBEDDING_PROVIDER", "google", "Google"),
        ("EMBEDDING_PROVIDER", "fastembed", "FastEmbed"),
        ("RERANKING_PROVIDER", "http", "HTTP"),
        ("RERANKING_PROVIDER", "fastembed", "FastEmbed"),
        ("LOG_FORMAT", "JSON", "json"),
        ("LOG_FORMAT", "Console", "console"),
    ],
)
def test_choice_settings_are_normalised_to_canonical_spelling(monkeypatch, setting, raw, canonical):
    loaded = _settings(monkeypatch, **{setting: raw})

    assert getattr(loaded, setting) == canonical


@pytest.mark.parametrize(
    ("setting", "typo"),
    [
        ("EMBEDDING_PROVIDER", "Opnai"),
        ("RERANKING_PROVIDER", "Htp"),
        ("LOG_FORMAT", "jsno"),
    ],
)
def test_unknown_choice_setting_fails_startup(monkeypatch, setting, typo):
    with pytest.raises(ValidationError, match=setting):
        _settings(monkeypatch, **{setting: typo})


@pytest.mark.parametrize("setting", ["EMBEDDING_PROVIDER", "RERANKING_PROVIDER", "LOG_FORMAT"])
def test_blank_choice_setting_keeps_the_default(monkeypatch, setting):
    default = Settings.model_fields[setting].default

    assert getattr(_settings(monkeypatch, **{setting: ""}), setting) == default


@pytest.mark.parametrize(
    ("value", "adapter"),
    [
        ("openai", "OpenAIEmbeddingsAdapter"),
        ("OPENAI", "OpenAIEmbeddingsAdapter"),
        ("ollama", "OllamaEmbeddingsAdapter"),
        ("azure", "AzureOpenAIAdapter"),
        ("google", "GoogleEmbeddingsAdapter"),
        ("fastembed", "FastEmbeddingAdapter"),
        ("FastEmbed", "FastEmbeddingAdapter"),
    ],
)
def test_embedding_factory_selects_provider_ignoring_case(monkeypatch, fake_adapters, value, adapter):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", value)

    assert type(bootstrap.get_embedding_adapter()).__name__ == adapter


def test_embedding_factory_rejects_unknown_provider(monkeypatch, fake_adapters):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "Opnai")

    with pytest.raises(ValueError, match="EMBEDDING_PROVIDER"):
        bootstrap.get_embedding_adapter()


@pytest.mark.parametrize(
    ("value", "adapter"),
    [
        ("HTTP", "HttpRerankAdapter"),
        ("http", "HttpRerankAdapter"),
        ("hTTP", "HttpRerankAdapter"),
        ("fastembed", "FastEmbedCrossEncoderAdapter"),
        ("FastEmbed", "FastEmbedCrossEncoderAdapter"),
    ],
)
def test_reranker_factory_selects_provider_ignoring_case(monkeypatch, fake_adapters, value, adapter):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", value)

    assert type(bootstrap.get_reranker_adapter()).__name__ == adapter


def test_reranker_factory_rejects_unknown_provider(monkeypatch, fake_adapters):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "Htp")

    with pytest.raises(ValueError, match="RERANKING_PROVIDER"):
        bootstrap.get_reranker_adapter()


def test_reranker_factory_returns_none_when_reranking_disabled(monkeypatch, fake_adapters):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)

    assert bootstrap.get_reranker_adapter() is None


@pytest.fixture
def restored_root_logger():
    """configure_logging() replaces the root handlers and starts a listener thread."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    logging_config.shutdown_logging()
    root.handlers[:] = handlers
    root.setLevel(level)


@pytest.mark.parametrize(
    ("log_format", "formatter"),
    [
        ("json", "JSONFormatter"),
        ("JSON", "JSONFormatter"),
        ("Json", "JSONFormatter"),
        ("console", "ConsoleFormatter"),
        ("CONSOLE", "ConsoleFormatter"),
    ],
)
def test_configure_logging_format_is_case_insensitive(restored_root_logger, log_format, formatter):
    listener = logging_config.configure_logging(log_level="INFO", log_format=log_format)

    assert type(listener.handlers[0].formatter).__name__ == formatter


def test_configure_logging_rejects_unknown_format(restored_root_logger):
    with pytest.raises(ValueError, match="LOG_FORMAT"):
        logging_config.configure_logging(log_level="INFO", log_format="jsno")


# ============================================================================
# ACTIVITY_RETENTION_DAYS: documented "empty / null = keep forever"
# ============================================================================

@pytest.mark.parametrize("raw", ["", "  ", "null", "NULL", "None", "none"])
def test_activity_retention_blank_or_null_means_keep_forever(monkeypatch, raw):
    assert _settings(monkeypatch, ACTIVITY_RETENTION_DAYS=raw).ACTIVITY_RETENTION_DAYS is None


def test_activity_retention_days_still_parses_numbers(monkeypatch):
    assert _settings(monkeypatch, ACTIVITY_RETENTION_DAYS="90").ACTIVITY_RETENTION_DAYS == 90


def test_activity_retention_days_still_rejects_garbage(monkeypatch):
    with pytest.raises(ValidationError, match="ACTIVITY_RETENTION_DAYS"):
        _settings(monkeypatch, ACTIVITY_RETENTION_DAYS="soon")


# ============================================================================
# SSE_MAX_QUEUE_SIZE reaches the EventBus built by the composition root
# ============================================================================

async def test_sse_max_queue_size_bounds_each_stream_queue(sqlite_runtime_settings, monkeypatch):
    """A slow SSE client may buffer at most SSE_MAX_QUEUE_SIZE events; the rest are dropped."""
    queue_limit = 3
    emitted = 12
    monkeypatch.setattr(settings, "ACTIVITY_ENABLED", True)
    monkeypatch.setattr(settings, "SSE_MAX_QUEUE_SIZE", queue_limit)
    runtime = await build_runtime()

    try:
        bus = runtime.event_bus
        assert bus is not None
        user = await runtime.services.user.get_or_create_user(
            user=UserCreate(
                external_id=settings.DEFAULT_USER_ID,
                name=settings.DEFAULT_USER_NAME,
                email=settings.DEFAULT_USER_EMAIL,
            ),
        )
        user_id = user.id
        stream = bus.subscribe_stream(user_id)

        async def emit(index):
            await bus.emit(ActivityEvent(
                entity_type=EntityType.MEMORY,
                entity_id=index,
                action=ActionType.CREATED,
                snapshot={},
                user_id=str(user_id),
            ))

        # The client consumes one event, then stalls while the rest pile up.
        first_read = asyncio.ensure_future(stream.__anext__())
        await asyncio.sleep(0)
        await emit(0)
        await first_read
        for index in range(1, emitted):
            await emit(index)

        buffered = 0
        while True:
            try:
                await asyncio.wait_for(stream.__anext__(), timeout=0.1)
            except (TimeoutError, StopAsyncIteration):
                break
            buffered += 1
    finally:
        await dispose_runtime(runtime)

    assert buffered == queue_limit


# ============================================================================
# Provenance defaults: validated against the caps of the models they are copied into
# ============================================================================

def _model_provenance_caps():
    """Collect, per provenance setting, the max_length every model field enforces."""
    caps: dict[str, set[int]] = {}
    for module_info in pkgutil.iter_modules(models_package.__path__):
        module = importlib.import_module(f"app.models.{module_info.name}")
        for _, model in inspect.getmembers(module, inspect.isclass):
            if not issubclass(model, BaseModel) or model.__module__ != module.__name__:
                continue
            for field_name, setting_name in PROVENANCE_ENV_MAP.items():
                field = model.model_fields.get(field_name)
                if field is None:
                    continue
                limits = {m.max_length for m in field.metadata if hasattr(m, "max_length")}
                caps.setdefault(setting_name, set()).update(limits)
    return caps


def test_provenance_limits_match_what_the_models_accept():
    caps = _model_provenance_caps()

    assert set(PROVENANCE_MAX_LENGTHS) == set(PROVENANCE_ENV_MAP.values())
    for setting_name, limit in PROVENANCE_MAX_LENGTHS.items():
        assert caps[setting_name] == {limit}, f"{setting_name} cap disagrees with the models"


@pytest.mark.parametrize("setting", sorted(PROVENANCE_MAX_LENGTHS))
def test_overlong_provenance_default_fails_startup_with_a_clear_error(monkeypatch, setting):
    limit = PROVENANCE_MAX_LENGTHS[setting]

    with pytest.raises(ValidationError, match=f"{setting}.*at most {limit} characters"):
        _settings(monkeypatch, **{setting: "x" * (limit + 1)})


@pytest.mark.parametrize("setting", sorted(PROVENANCE_MAX_LENGTHS))
def test_provenance_default_at_the_cap_is_accepted(monkeypatch, setting):
    limit = PROVENANCE_MAX_LENGTHS[setting]

    assert getattr(_settings(monkeypatch, **{setting: "x" * limit}), setting) == "x" * limit


# ============================================================================
# *_MAX_LENGTH settings are bounded by the fixed PostgreSQL VARCHAR widths
# ============================================================================

POSTGRES_COLUMNS = {
    "PLAN_TITLE_MAX_LENGTH": (PlansTable, "title"),
    "TASK_TITLE_MAX_LENGTH": (TasksTable, "title"),
    "TASK_AGENT_MAX_LENGTH": (TasksTable, "assigned_agent"),
    "SKILL_NAME_MAX_LENGTH": (SkillsTable, "name"),
    "SKILL_DESCRIPTION_MAX_LENGTH": (SkillsTable, "description"),
    "SKILL_LICENSE_MAX_LENGTH": (SkillsTable, "license"),
    "SKILL_COMPATIBILITY_MAX_LENGTH": (SkillsTable, "compatibility"),
    "CODE_ARTIFACT_TITLE_MAX_LENGTH": (CodeArtifactsTable, "title"),
    "DOCUMENT_TITLE_MAX_LENGTH": (DocumentsTable, "title"),
    "FILE_FILENAME_MAX_LENGTH": (FilesTable, "filename"),
    "ENTITY_NAME_MAX_LENGTH": (EntitiesTable, "name"),
    "ENTITY_TYPE_MAX_LENGTH": (EntitiesTable, "custom_type"),
    "ENTITY_RELATIONSHIP_TYPE_MAX_LENGTH": (EntityRelationshipsTable, "relationship_type"),
}


def test_width_table_matches_the_real_postgres_columns():
    assert set(POSTGRES_COLUMN_WIDTHS) == set(POSTGRES_COLUMNS)
    for setting_name, (table, column) in POSTGRES_COLUMNS.items():
        assert POSTGRES_COLUMN_WIDTHS[setting_name] == table.__table__.c[column].type.length


def test_default_max_lengths_fit_the_postgres_columns(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING):
        loaded = _settings(monkeypatch, DATABASE="Postgres")

    assert not caplog.records
    for setting_name, width in POSTGRES_COLUMN_WIDTHS.items():
        assert getattr(loaded, setting_name) <= width


def test_postgres_clamps_oversized_max_lengths_to_the_column_width(monkeypatch, caplog):
    overrides = {name: str(width * 2) for name, width in POSTGRES_COLUMN_WIDTHS.items()}
    with caplog.at_level(logging.WARNING):
        loaded = _settings(monkeypatch, DATABASE="Postgres", **overrides)

    for setting_name, width in POSTGRES_COLUMN_WIDTHS.items():
        assert getattr(loaded, setting_name) == width
        assert setting_name in caplog.text


def test_clamp_warning_reaches_stderr_at_real_startup(tmp_path):
    """Settings() runs at import, before logging is configured; the warning must still be visible."""
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "DATABASE": "Postgres",
        "PLAN_TITLE_MAX_LENGTH": "1000",
    }

    result = subprocess.run(
        [sys.executable, "-c", "from app.config.settings import settings; print(settings.PLAN_TITLE_MAX_LENGTH)"],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=True,
    )

    assert result.stdout.strip() == "500"
    assert "PLAN_TITLE_MAX_LENGTH" in result.stderr


def test_postgres_keeps_max_lengths_within_the_column_width(monkeypatch):
    loaded = _settings(monkeypatch, DATABASE="Postgres", PLAN_TITLE_MAX_LENGTH="120")

    assert loaded.PLAN_TITLE_MAX_LENGTH == 120


def test_sqlite_does_not_clamp_max_lengths(monkeypatch):
    """SQLite does not enforce VARCHAR length, so the tunable value stays authoritative."""
    loaded = _settings(monkeypatch, DATABASE="SQLite", PLAN_TITLE_MAX_LENGTH="1000")

    assert loaded.PLAN_TITLE_MAX_LENGTH == 1000


# ============================================================================
# Root service-info document
# ============================================================================

async def test_root_endpoint_only_advertises_routes_that_exist():
    transport = httpx.ASGITransport(app=main.mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        info = (await client.get("/")).json()
        advertised = [info["endpoints"][name] for name in info["endpoints"]]
        advertised += [value for value in info.values() if isinstance(value, str) and value.startswith("/")]
        statuses = {path: (await client.get(path)).status_code for path in advertised}

    assert "/docs" not in advertised
    assert "docs" not in info
    assert statuses
    assert all(status != 404 for status in statuses.values()), statuses
