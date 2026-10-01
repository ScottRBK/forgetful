"""ONNX execution provider settings and their forwarding to local FastEmbed models."""
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.bootstrap import get_embedding_adapter, get_reranker_adapter
from app.config.settings import Settings, parse_onnx_providers, settings
from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter
from app.repositories.embeddings.reranker_adapter import (
    FastEmbedCrossEncoderAdapter,
    HttpRerankAdapter,
)

DML_AND_CPU = "DmlExecutionProvider,CPUExecutionProvider"
DML_AND_CPU_LIST = ["DmlExecutionProvider", "CPUExecutionProvider"]
SETTING_NAMES = ["RERANKING_ONNX_PROVIDERS", "EMBEDDING_ONNX_PROVIDERS"]
ONNX_PROVIDER_PROPERTIES = [
    ("embedding_onnx_providers", "EMBEDDING_ONNX_PROVIDERS"),
    ("reranking_onnx_providers", "RERANKING_ONNX_PROVIDERS"),
]


@pytest.fixture
def cross_encoder_calls(monkeypatch):
    calls = []

    def create_encoder(**options):
        calls.append(options)
        return MagicMock()

    monkeypatch.setattr("fastembed.rerank.cross_encoder.TextCrossEncoder", create_encoder)
    return calls


@pytest.fixture
def local_reranking(monkeypatch):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "FastEmbed")
    monkeypatch.setattr(settings, "RERANKING_WORKERS", 1)
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_parse_empty_keeps_fastembed_default(value):
    assert parse_onnx_providers(value) is None


def test_parse_strips_names_and_keeps_order():
    assert parse_onnx_providers(" DmlExecutionProvider , CPUExecutionProvider ") == DML_AND_CPU_LIST


@pytest.mark.parametrize("value", [",", "DmlExecutionProvider,,CPUExecutionProvider", "CPUExecutionProvider,"])
def test_parse_rejects_empty_entries(value):
    with pytest.raises(ValueError, match="empty entries"):
        parse_onnx_providers(value)


@pytest.mark.parametrize("name", SETTING_NAMES)
def test_settings_default_to_empty(monkeypatch, name):
    monkeypatch.delenv(name, raising=False)

    assert getattr(Settings(_env_file=None), name) == ""


@pytest.mark.parametrize("name", SETTING_NAMES)
def test_settings_read_environment(monkeypatch, name):
    monkeypatch.setenv(name, DML_AND_CPU)

    assert getattr(Settings(_env_file=None), name) == DML_AND_CPU


@pytest.mark.parametrize("name", SETTING_NAMES)
def test_settings_reject_empty_entries(monkeypatch, name):
    monkeypatch.setenv(name, "DmlExecutionProvider,,CPUExecutionProvider")

    with pytest.raises(ValidationError, match=name):
        Settings(_env_file=None)


def test_reranker_default_passes_no_providers(monkeypatch, cross_encoder_calls, local_reranking):
    monkeypatch.setattr(settings, "RERANKING_ONNX_PROVIDERS", "")

    assert isinstance(get_reranker_adapter(), FastEmbedCrossEncoderAdapter)
    assert len(cross_encoder_calls) == 1
    assert "providers" not in cross_encoder_calls[0]


def test_reranker_forwards_configured_providers(monkeypatch, cross_encoder_calls, local_reranking):
    monkeypatch.setattr(settings, "RERANKING_ONNX_PROVIDERS", DML_AND_CPU)

    get_reranker_adapter()

    assert cross_encoder_calls[0]["providers"] == DML_AND_CPU_LIST


def test_directml_rejects_concurrent_reranking_workers(cross_encoder_calls):
    with pytest.raises(ValueError, match="RERANKING_WORKERS=2.*DmlExecutionProvider"):
        FastEmbedCrossEncoderAdapter(workers=2, providers=DML_AND_CPU_LIST)

    assert cross_encoder_calls == []


def test_directml_accepts_a_single_reranking_worker(cross_encoder_calls):
    FastEmbedCrossEncoderAdapter(workers=1, providers=["DmlExecutionProvider"])

    assert cross_encoder_calls[0]["providers"] == ["DmlExecutionProvider"]


def test_other_providers_keep_concurrent_reranking_workers(cross_encoder_calls):
    FastEmbedCrossEncoderAdapter(workers=2, providers=["CUDAExecutionProvider"])

    assert cross_encoder_calls[0]["providers"] == ["CUDAExecutionProvider"]


def test_bootstrap_surfaces_directml_worker_conflict(monkeypatch, cross_encoder_calls, local_reranking):
    monkeypatch.setattr(settings, "RERANKING_ONNX_PROVIDERS", "DmlExecutionProvider")
    monkeypatch.setattr(settings, "RERANKING_WORKERS", 2)

    with pytest.raises(ValueError, match="RERANKING_WORKERS=1"):
        get_reranker_adapter()
    assert cross_encoder_calls == []


def test_http_reranking_ignores_local_onnx_settings(monkeypatch, cross_encoder_calls):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "HTTP")
    monkeypatch.setattr(settings, "RERANKING_ONNX_PROVIDERS", "DmlExecutionProvider")
    monkeypatch.setattr(settings, "RERANKING_WORKERS", 2)

    assert isinstance(get_reranker_adapter(), HttpRerankAdapter)
    assert cross_encoder_calls == []


def test_disabled_reranking_ignores_local_onnx_settings(monkeypatch, cross_encoder_calls):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)
    monkeypatch.setattr(settings, "RERANKING_ONNX_PROVIDERS", "DmlExecutionProvider")
    monkeypatch.setattr(settings, "RERANKING_WORKERS", 2)

    assert get_reranker_adapter() is None
    assert cross_encoder_calls == []


def test_settings_onnx_provider_properties(monkeypatch):
    for property_name, field_name in ONNX_PROVIDER_PROPERTIES:
        monkeypatch.setattr(settings, field_name, "")
        assert getattr(settings, property_name) is None
        monkeypatch.setattr(settings, field_name, DML_AND_CPU)
        assert getattr(settings, property_name) == DML_AND_CPU_LIST


def test_embedding_default_passes_no_providers(monkeypatch):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)

    with patch("fastembed.TextEmbedding") as mock_text_embedding:
        FastEmbeddingAdapter()

    mock_text_embedding.assert_called_once()
    assert "providers" not in mock_text_embedding.call_args.kwargs


def test_embedding_forwards_configured_providers(monkeypatch):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)

    with patch("fastembed.TextEmbedding") as mock_text_embedding:
        FastEmbeddingAdapter(providers=DML_AND_CPU_LIST)

    mock_text_embedding.assert_called_once()
    assert mock_text_embedding.call_args.kwargs["providers"] == DML_AND_CPU_LIST


def test_bootstrap_forwards_embedding_providers(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "FastEmbed")
    monkeypatch.setattr(settings, "EMBEDDING_ONNX_PROVIDERS", DML_AND_CPU)
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)

    with patch("fastembed.TextEmbedding") as mock_text_embedding:
        get_embedding_adapter()

    mock_text_embedding.assert_called_once()
    assert mock_text_embedding.call_args.kwargs["providers"] == DML_AND_CPU_LIST
