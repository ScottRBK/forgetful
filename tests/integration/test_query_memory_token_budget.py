"""query_memory token budgeting: special tokens, offline tokenizer, request threshold, truncation flag, link quota."""
import asyncio
import time
from uuid import uuid4

import pytest
import requests
import tiktoken
import tiktoken.registry

from app.models.memory_models import MemoryCreate, MemoryQueryRequest
from app.utils import token_counter as token_counter_module
from app.utils.token_counter import TokenCounter

SPECIAL_TOKEN_TEXTS = [
    "<|endoftext|>",
    "<|fim_prefix|>",
    "<|fim_middle|>",
    "<|fim_suffix|>",
    "<|endofprompt|>",
]


def _memory(title: str, importance: int = 5, content: str | None = None) -> MemoryCreate:
    return MemoryCreate(
        title=title,
        content=content or f"Content for {title} with detailed information",
        context="Token budget context",
        keywords=["budget"],
        tags=["tokens"],
        importance=importance,
    )


def _query(**overrides) -> MemoryQueryRequest:
    params = {"query": "memory", "query_context": "looking", "k": 20, "include_links": False}
    params.update(overrides)
    return MemoryQueryRequest(**params)


async def _seed_large(repo, user_id, count: int = 20):
    # ~1900 characters each, which is roughly 350-400 tokens per memory
    body = ("The quick brown fox jumps over the lazy dog while debugging token budgets. " * 25)[:1900]
    return [await repo.create_memory(user_id, _memory(f"Large {i}", content=body)) for i in range(count)]


def _fresh_container_no_network(monkeypatch, tmp_path, *, delay: float = 0.0):
    """Empty tiktoken cache, nothing loaded in-process and a network that always fails."""
    cache = tmp_path / "empty-tiktoken-cache"
    cache.mkdir()
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(cache))
    monkeypatch.delenv("DATA_GYM_CACHE_DIR", raising=False)
    monkeypatch.setattr(tiktoken.registry, "ENCODINGS", {})
    monkeypatch.setattr(token_counter_module, "_token_counter", None)

    calls = []

    def blackholed_get(url, *args, **kwargs):
        calls.append(url)
        time.sleep(delay)  # synchronous, exactly like requests.get
        raise requests.exceptions.ConnectionError("network unreachable")

    monkeypatch.setattr(requests, "get", blackholed_get)
    return calls


class TestSpecialTokenText:
    @pytest.mark.parametrize("special", SPECIAL_TOKEN_TEXTS)
    def test_token_counter_counts_special_token_literals_as_plain_text(self, special):
        count = TokenCounter().count_tokens(f"GPT models use the {special} marker")

        assert count > 0

    @pytest.mark.asyncio
    async def test_query_memory_returns_memory_containing_special_token(
        self, test_memory_service, mock_memory_repository,
    ):
        user_id = uuid4()
        stored = await mock_memory_repository.create_memory(
            user_id,
            _memory("Tokenizer notes", content="GPT models use the <|endoftext|> token to separate documents"),
        )

        result = await test_memory_service.query_memory(user_id, _query(k=3))

        assert [m.id for m in result.primary_memories] == [stored.id]
        assert result.token_count > 0


class TestOfflineTokenizer:
    def test_unloadable_encoding_falls_back_to_approximate_count(self, monkeypatch):
        def fail(model):
            raise requests.exceptions.ConnectionError("network unreachable")

        monkeypatch.setattr(tiktoken, "encoding_for_model", fail)
        monkeypatch.setattr(tiktoken, "get_encoding", fail)

        counter = TokenCounter()

        assert counter.count_tokens("a" * 400) == 100
        assert counter.count_tokens("hi") == 1
        assert counter.count_tokens("") == 0

    def test_unknown_model_name_uses_default_encoding(self, monkeypatch):
        loaded = []

        class FakeEncoding:
            def encode(self, text, **kwargs):
                return list(text.split())

        def unknown_model(model):
            raise KeyError(model)

        def get_encoding(name):
            loaded.append(name)
            return FakeEncoding()

        monkeypatch.setattr(tiktoken, "encoding_for_model", unknown_model)
        monkeypatch.setattr(tiktoken, "get_encoding", get_encoding)

        assert TokenCounter(model="not-a-model").count_tokens("one two three") == 3
        assert loaded == ["cl100k_base"]

    @pytest.mark.asyncio
    async def test_query_memory_survives_missing_tiktoken_cache_when_offline(
        self, test_memory_service, mock_memory_repository, monkeypatch, tmp_path,
    ):
        user_id = uuid4()
        for i in range(3):
            await mock_memory_repository.create_memory(user_id, _memory(f"Memory {i}", importance=5 + i))
        calls = _fresh_container_no_network(monkeypatch, tmp_path)

        result = await test_memory_service.query_memory(user_id, _query(k=3))

        assert len(result.primary_memories) == 3
        assert result.token_count > 0
        assert len(calls) == 1  # the unreachable file is requested once, not retried per memory or per fallback

    @pytest.mark.asyncio
    async def test_first_query_does_not_block_event_loop_on_tiktoken_download(
        self, test_memory_service, mock_memory_repository, monkeypatch, tmp_path,
    ):
        user_id = uuid4()
        await mock_memory_repository.create_memory(user_id, _memory("Memory"))
        _fresh_container_no_network(monkeypatch, tmp_path, delay=1.0)  # slow, failing download

        gaps = []
        stop = False

        async def heartbeat():
            last = time.perf_counter()
            while not stop:
                await asyncio.sleep(0.02)
                now = time.perf_counter()
                gaps.append(now - last)
                last = now

        beat = asyncio.create_task(heartbeat())
        await asyncio.sleep(0.1)  # let the heartbeat start ticking
        try:
            await test_memory_service.query_memory(user_id, _query(k=3))
        finally:
            stop = True
            await beat

        assert max(gaps) < 0.5, f"event loop stalled for {max(gaps):.2f}s during the first query"
