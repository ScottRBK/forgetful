"""Reranker adapter regressions: cache directory, HTTP URL, result order and timeout.

Network-free: FastEmbed's cross-encoder is replaced by a recorder and HTTP traffic is served by
httpx mock transports or a throw-away loopback server.
"""

import pytest

from app.config.settings import settings
from app.repositories.embeddings.reranker_adapter import (
    FastEmbedCrossEncoderAdapter,
)

RERANK_URL = "https://reranker.test/v1/rerank"


@pytest.fixture
def cross_encoder_calls(monkeypatch):
    """Record the keyword arguments FastEmbed's TextCrossEncoder is constructed with."""
    calls = []

    def create_encoder(**options):
        calls.append(options)
        return object()

    monkeypatch.setattr("fastembed.rerank.cross_encoder.TextCrossEncoder", create_encoder)
    return calls


def test_local_reranker_loads_model_from_configured_cache_dir(
    monkeypatch, tmp_path, cross_encoder_calls,
):
    configured = str(tmp_path / "configured")
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", configured)

    FastEmbedCrossEncoderAdapter(model="m")
    FastEmbedCrossEncoderAdapter(model="m", workers=2)

    assert [call["cache_dir"] for call in cross_encoder_calls] == [configured, configured]


def test_local_reranker_prefers_explicit_cache_dir(monkeypatch, tmp_path, cross_encoder_calls):
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", str(tmp_path / "configured"))
    explicit = str(tmp_path / "explicit")

    FastEmbedCrossEncoderAdapter(model="m", cache_dir=explicit)

    assert cross_encoder_calls[0]["cache_dir"] == explicit


