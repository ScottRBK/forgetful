"""Reranker adapter regressions: cache directory, HTTP URL, result order and timeout.

Network-free: FastEmbed's cross-encoder is replaced by a recorder and HTTP traffic is served by
httpx mock transports or a throw-away loopback server.
"""

import httpx
import pytest

from app.bootstrap import get_reranker_adapter
from app.config.settings import settings
from app.repositories.embeddings.reranker_adapter import (
    FastEmbedCrossEncoderAdapter,
    HttpRerankAdapter,
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


@pytest.fixture
def http_reranker(monkeypatch):
    """Build HttpRerankAdapter instances whose requests are answered by ``handler``."""
    client_class = httpx.AsyncClient

    def install(handler):
        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(httpx, "AsyncClient", lambda: client_class(transport=transport))
        return HttpRerankAdapter(model="m", url=RERANK_URL, api_key="")

    return install


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


@pytest.mark.parametrize("url", ["", "   "])
def test_http_reranker_rejects_missing_url(monkeypatch, url):
    monkeypatch.setattr(settings, "RERANKING_URL", url)

    with pytest.raises(ValueError, match="RERANKING_URL"):
        HttpRerankAdapter()


def test_http_reranker_rejects_explicit_empty_url(monkeypatch):
    monkeypatch.setattr(settings, "RERANKING_URL", RERANK_URL)

    with pytest.raises(ValueError, match="RERANKING_URL"):
        HttpRerankAdapter(url="")


def test_http_reranker_accepts_url_argument_without_setting(monkeypatch):
    monkeypatch.setattr(settings, "RERANKING_URL", "")

    assert HttpRerankAdapter(url=RERANK_URL).url == RERANK_URL


def test_enabling_http_reranking_without_url_fails_at_startup(monkeypatch):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "HTTP")
    monkeypatch.setattr(settings, "RERANKING_URL", "")

    with pytest.raises(ValueError, match="RERANKING_URL"):
        get_reranker_adapter()


async def test_http_reranker_returns_results_by_descending_score(http_reranker):
    def handler(_request):
        return httpx.Response(200, json={"results": [
            {"index": 0, "relevance_score": 0.1},
            {"index": 1, "relevance_score": 0.9},
            {"index": 2, "relevance_score": 0.5},
        ]})

    adapter = http_reranker(handler)

    assert await adapter.rerank("q", ["a", "b", "c"]) == [(1, 0.9), (2, 0.5), (0, 0.1)]


async def test_http_reranker_keeps_server_order_for_tied_scores(http_reranker):
    def handler(_request):
        return httpx.Response(200, json={"results": [
            {"index": 2, "relevance_score": 0.5},
            {"index": 0, "relevance_score": 0.5},
            {"index": 1, "relevance_score": 0.7},
        ]})

    adapter = http_reranker(handler)

    assert await adapter.rerank("q", ["a", "b", "c"]) == [(1, 0.7), (2, 0.5), (0, 0.5)]


