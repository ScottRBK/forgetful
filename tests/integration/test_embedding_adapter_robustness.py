"""Robustness tests for the embedding provider adapters.

Each adapter is driven with its real SDK client where possible. Only the HTTP
transport is replaced by an in-process fake endpoint, so no network access or
provider account is needed.
"""
import functools
import json
import logging
from unittest.mock import MagicMock

import httpx
import pytest

from app.bootstrap import get_embedding_adapter
from app.config import logging_config
from app.config.settings import Settings, settings
from app.repositories.embeddings import embedding_adapter as ea
from app.utils.url_helpers import redact_url

SECRET = "s3cr3t-PASSWORD-value"

AZURE_FIELDS = ("AZURE_ENDPOINT", "AZURE_API_KEY", "AZURE_API_VERSION", "AZURE_DEPLOYMENT")
AZURE_CONFIG = {
    "AZURE_ENDPOINT": "https://my-resource.openai.azure.com/",
    "AZURE_API_KEY": "test-key",
    "AZURE_API_VERSION": "2023-05-15",
    "AZURE_DEPLOYMENT": "text-embedding-ada-002",
}


def _init_record(caplog: pytest.LogCaptureFixture, message: str) -> logging.LogRecord:
    matches = [r for r in caplog.records if r.getMessage() == message]
    assert matches, f"no '{message}' record was emitted"
    return matches[0]


def _as_json_log_line(record: logging.LogRecord) -> str:
    return logging_config.JSONFormatter().format(record)


# --------------------------------------------------------------------------
# Base URLs carrying credentials must not reach the startup logs
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://alice:pw@llm.internal/v1", "https://***:***@llm.internal/v1"),
        ("http://token@host:11434", "http://***:***@host:11434"),
        ("http://alice:p@ss@host:11434/api", "http://***:***@host:11434/api"),
        ("alice:pw@host:11434", "***:***@host:11434"),
        ("http://host:11434/path@x?mail=a@b#frag@z", "http://host:11434/path@x?mail=a@b#frag@z"),
        ("http://localhost:11434", "http://localhost:11434"),
        ("localhost:11434", "localhost:11434"),
        ("http://[::1]:11434", "http://[::1]:11434"),
        ("", ""),
    ],
)
def test_redact_url_masks_only_userinfo(url, expected):
    assert redact_url(url) == expected


@pytest.mark.parametrize("url", ["http://[bad:pw@host", "://:@", "@", "http://@@@/"])
def test_redact_url_never_raises_on_malformed_input(url):
    assert isinstance(redact_url(url), str)


def test_openai_adapter_does_not_log_base_url_credentials(monkeypatch, caplog):
    base_url = f"https://alice:{SECRET}@llm.internal/v1"
    client_cls = MagicMock()
    monkeypatch.setattr(ea, "OpenAI", client_cls)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "OPENAI_BASE_URL", base_url)

    with caplog.at_level(logging.INFO, logger=ea.logger.name):
        ea.OpenAIEmbeddingsAdapter()

    record = _init_record(caplog, "Initialising OpenAI embeddings adapter")
    assert record.base_url == "https://***:***@llm.internal/v1"
    assert SECRET not in _as_json_log_line(record)
    # The client itself must still receive the real, usable URL.
    assert client_cls.call_args.kwargs["base_url"] == base_url


def test_openai_adapter_logs_default_when_no_base_url(monkeypatch, caplog):
    monkeypatch.setattr(ea, "OpenAI", MagicMock())
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "OPENAI_BASE_URL", "")

    with caplog.at_level(logging.INFO, logger=ea.logger.name):
        ea.OpenAIEmbeddingsAdapter()

    record = _init_record(caplog, "Initialising OpenAI embeddings adapter")
    assert record.base_url == "(default)"


def test_ollama_adapter_does_not_log_base_url_credentials(monkeypatch, caplog):
    base_url = f"http://alice:{SECRET}@host:11434"
    client_cls = MagicMock()
    monkeypatch.setattr("ollama.AsyncClient", client_cls)
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", base_url)

    with caplog.at_level(logging.INFO, logger=ea.logger.name):
        ea.OllamaEmbeddingsAdapter()

    record = _init_record(caplog, "Initialising Ollama embeddings adapter")
    assert record.base_url == "http://***:***@host:11434"
    assert SECRET not in _as_json_log_line(record)
    assert client_cls.call_args.kwargs["host"] == base_url


# --------------------------------------------------------------------------
# Azure configuration is validated at startup, like the other adapters
# --------------------------------------------------------------------------
@pytest.fixture
def azure_config(monkeypatch):
    """Complete Azure settings, with ambient SDK fallbacks removed."""
    for env in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
                "OPENAI_API_VERSION", "OPENAI_BASE_URL"):
        monkeypatch.delenv(env, raising=False)
    for name, value in AZURE_CONFIG.items():
        monkeypatch.setattr(settings, name, value)
    return dict(AZURE_CONFIG)


def test_azure_adapter_rejects_unconfigured_settings(azure_config, monkeypatch):
    for name in AZURE_FIELDS:
        monkeypatch.setattr(settings, name, "")

    with pytest.raises(ValueError) as excinfo:
        ea.AzureOpenAIAdapter()

    assert f"missing: {', '.join(AZURE_FIELDS)}" in str(excinfo.value)


@pytest.mark.parametrize("missing", AZURE_FIELDS)
@pytest.mark.parametrize("blank", ["", "   "], ids=["empty", "whitespace"])
def test_azure_adapter_names_the_missing_setting(azure_config, monkeypatch, missing, blank):
    monkeypatch.setattr(settings, missing, blank)

    with pytest.raises(ValueError) as excinfo:
        ea.AzureOpenAIAdapter()

    message = str(excinfo.value)
    assert f"missing: {missing}" in message
    for present in set(AZURE_FIELDS) - {missing}:
        assert f"missing: {present}" not in message


def test_bootstrap_rejects_unconfigured_azure_provider(azure_config, monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "Azure")
    monkeypatch.setattr(settings, "AZURE_ENDPOINT", "")

    with pytest.raises(ValueError, match="AZURE_ENDPOINT"):
        get_embedding_adapter()


def test_azure_adapter_accepts_complete_configuration(azure_config):
    adapter = ea.AzureOpenAIAdapter()

    assert adapter.model == "text-embedding-ada-002"


# --------------------------------------------------------------------------
# Fake Azure endpoint (real openai SDK, only the HTTP transport is replaced)
# --------------------------------------------------------------------------
class FakeAzureEndpoint:
    """In-process stand-in for an Azure OpenAI embeddings deployment."""

    def __init__(self, vector_size: int = 1536):
        self.vector_size = vector_size
        self.rejects_dimensions = False
        self.on_request = None
        self.bodies: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.bodies.append(body)
        if self.on_request is not None:
            self.on_request()
        if self.rejects_dimensions and "dimensions" in body:
            return httpx.Response(400, json={"error": {
                "code": "BadRequest",
                "message": "Unrecognized request argument supplied: dimensions",
            }})
        return httpx.Response(200, json={
            "object": "list",
            "model": "text-embedding-ada-002",
            "usage": {"prompt_tokens": 1, "total_tokens": 1},
            "data": [{
                "object": "embedding",
                "index": 0,
                "embedding": [0.01] * self.vector_size,
            }],
        })


@pytest.fixture
def fake_azure(azure_config, monkeypatch):
    endpoint = FakeAzureEndpoint()
    http_client = httpx.Client(transport=httpx.MockTransport(endpoint))
    monkeypatch.setattr(
        ea, "AzureOpenAI", functools.partial(ea.AzureOpenAI, http_client=http_client),
    )
    yield endpoint
    http_client.close()


# --------------------------------------------------------------------------
# `dimensions` is only sent to Azure deployments that accept it
# --------------------------------------------------------------------------
def test_azure_supports_dimensions_defaults_to_true(monkeypatch):
    monkeypatch.delenv("AZURE_SUPPORTS_DIMENSIONS", raising=False)

    assert Settings(_env_file=None).AZURE_SUPPORTS_DIMENSIONS is True


def test_azure_supports_dimensions_reads_environment(monkeypatch):
    monkeypatch.setenv("AZURE_SUPPORTS_DIMENSIONS", "false")

    assert Settings(_env_file=None).AZURE_SUPPORTS_DIMENSIONS is False


async def test_azure_adapter_sends_dimensions_by_default(fake_azure, monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", 256)

    await ea.AzureOpenAIAdapter().generate_embedding("hello")

    assert fake_azure.bodies[0]["dimensions"] == 256


async def test_azure_adapter_omits_dimensions_when_unsupported(fake_azure, monkeypatch):
    """Documented ada-002 setup: the deployment answers 400 to a `dimensions` argument."""
    fake_azure.rejects_dimensions = True
    monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", 1536)
    monkeypatch.setattr(settings, "AZURE_SUPPORTS_DIMENSIONS", False)

    adapter = ea.AzureOpenAIAdapter()
    embedding = await adapter.generate_embedding("hello world")

    assert len(embedding) == 1536
    assert "dimensions" not in fake_azure.bodies[0]
    assert adapter.supports_dimensions is False
