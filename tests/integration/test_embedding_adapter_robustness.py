"""Robustness tests for the embedding provider adapters.

Each adapter is driven with its real SDK client where possible. Only the HTTP
transport is replaced by an in-process fake endpoint, so no network access or
provider account is needed.
"""
import logging
from unittest.mock import MagicMock

import pytest

from app.bootstrap import get_embedding_adapter
from app.config import logging_config
from app.config.settings import settings
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
