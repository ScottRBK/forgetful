"""Network-free tests for FastEmbed offline/cache-only startup."""
import os
from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import settings
from app.repositories.embeddings.fastembed_offline import (
    get_fastembed_kwargs,
    load_fastembed_model,
)


@pytest.fixture(autouse=True)
def clean_hf_hub_offline(monkeypatch):
    """Keep HF_HUB_OFFLINE changes isolated to each test."""
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)


@pytest.fixture
def fastembed_cache_dir(tmp_path):
    return str(tmp_path / "fastembed")


def test_get_fastembed_kwargs_default_does_not_force_offline(monkeypatch):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)

    assert get_fastembed_kwargs() == {}
    assert "HF_HUB_OFFLINE" not in os.environ


def test_get_fastembed_kwargs_local_files_only_sets_hf_offline(monkeypatch):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)

    assert get_fastembed_kwargs() == {"local_files_only": True}
    assert os.environ["HF_HUB_OFFLINE"] == "1"


def test_load_fastembed_model_wraps_errors_in_local_files_only_mode(
    monkeypatch,
    fastembed_cache_dir,
):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)

    def fail(_kwargs):
        raise ValueError("raw fastembed failure")

    with pytest.raises(RuntimeError, match="FASTEMBED_LOCAL_FILES_ONLY=true") as exc:
        load_fastembed_model(
            model_role="embedding",
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir=fastembed_cache_dir,
            factory=fail,
        )

    assert isinstance(exc.value.__cause__, ValueError)


def test_load_fastembed_model_preserves_default_errors(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)

    def fail(_kwargs):
        raise ValueError("raw fastembed failure")

    with pytest.raises(ValueError, match="raw fastembed failure"):
        load_fastembed_model(
            model_role="embedding",
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir=fastembed_cache_dir,
            factory=fail,
        )


def test_fast_embedding_adapter_passes_local_files_only(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", fastembed_cache_dir)

    with patch("fastembed.TextEmbedding") as mock_text_embedding:
        from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter

        adapter = FastEmbeddingAdapter()

    mock_text_embedding.assert_called_once_with(
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=fastembed_cache_dir,
        local_files_only=True,
    )
    assert adapter.model is mock_text_embedding.return_value


def test_fast_embedding_adapter_keeps_default_constructor(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", fastembed_cache_dir)

    with patch("fastembed.TextEmbedding") as mock_text_embedding:
        from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter

        FastEmbeddingAdapter()

    mock_text_embedding.assert_called_once_with(
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=fastembed_cache_dir,
    )


def test_fast_embedding_adapter_wraps_offline_load_error(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", fastembed_cache_dir)

    with patch("fastembed.TextEmbedding", side_effect=ValueError("missing model")):
        from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter

        with pytest.raises(RuntimeError, match="Could not load FastEmbed embedding model"):
            FastEmbeddingAdapter()


def test_fastembed_reranker_passes_local_files_only(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", fastembed_cache_dir)
    mock_encoder = MagicMock()

    with patch(
        "fastembed.rerank.cross_encoder.TextCrossEncoder",
        return_value=mock_encoder,
    ) as mock_cls:
        from app.repositories.embeddings.reranker_adapter import (
            FastEmbedCrossEncoderAdapter,
        )

        adapter = FastEmbedCrossEncoderAdapter(
            model="Xenova/ms-marco-MiniLM-L-12-v2",
            threads=2,
            cache_dir=fastembed_cache_dir,
        )

    mock_cls.assert_called_once_with(
        model_name="Xenova/ms-marco-MiniLM-L-12-v2",
        threads=2,
        cache_dir=fastembed_cache_dir,
        local_files_only=True,
    )
    assert adapter._model is mock_encoder


def test_fastembed_reranker_wraps_offline_load_error(monkeypatch, fastembed_cache_dir):
    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", True)
    monkeypatch.setattr(settings, "FASTEMBED_CACHE_DIR", fastembed_cache_dir)

    with patch(
        "fastembed.rerank.cross_encoder.TextCrossEncoder",
        side_effect=ValueError("missing model"),
    ):
        from app.repositories.embeddings.reranker_adapter import (
            FastEmbedCrossEncoderAdapter,
        )

        with pytest.raises(RuntimeError, match="Could not load FastEmbed reranking model"):
            FastEmbedCrossEncoderAdapter(
                model="Xenova/ms-marco-MiniLM-L-12-v2",
                cache_dir=fastembed_cache_dir,
            )
