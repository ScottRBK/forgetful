"""query_memory token budgeting: special tokens, offline tokenizer, request threshold, truncation flag, link quota."""
import asyncio
import time
from uuid import uuid4

import pytest
import requests
import tiktoken
import tiktoken.registry

from app.config.settings import settings
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


class TestTokenContextThreshold:
    @pytest.mark.asyncio
    async def test_request_threshold_lowers_the_budget(
        self, test_memory_service, mock_memory_repository, monkeypatch,
    ):
        monkeypatch.setattr(settings, "MEMORY_TOKEN_BUDGET", 8000)
        user_id = uuid4()
        await _seed_large(mock_memory_repository, user_id)

        unrestricted = await test_memory_service.query_memory(user_id, _query())
        restricted = await test_memory_service.query_memory(user_id, _query(token_context_threshold=4000))

        assert unrestricted.token_count > 4000
        assert unrestricted.truncated is False
        assert restricted.token_count <= 4000
        assert restricted.truncated is True
        assert len(restricted.primary_memories) < len(unrestricted.primary_memories)

    @pytest.mark.asyncio
    async def test_omitted_threshold_uses_configured_budget(
        self, test_memory_service, mock_memory_repository, monkeypatch,
    ):
        monkeypatch.setattr(settings, "MEMORY_TOKEN_BUDGET", 3000)
        user_id = uuid4()
        await _seed_large(mock_memory_repository, user_id)

        result = await test_memory_service.query_memory(user_id, _query())

        assert 0 < result.token_count <= 3000
        assert result.truncated is True

    @pytest.mark.asyncio
    async def test_request_threshold_cannot_exceed_configured_budget(
        self, test_memory_service, mock_memory_repository, monkeypatch,
    ):
        monkeypatch.setattr(settings, "MEMORY_TOKEN_BUDGET", 3000)
        user_id = uuid4()
        await _seed_large(mock_memory_repository, user_id)

        result = await test_memory_service.query_memory(user_id, _query(token_context_threshold=25000))

        assert 0 < result.token_count <= 3000
        assert result.truncated is True

    def test_threshold_defaults_to_unset(self):
        assert _query().token_context_threshold is None


class TestTruncatedFlagForCountLimit:
    @staticmethod
    async def _seed_linked_pairs(repo, user_id, count: int):
        """`count` high importance primaries, each linked to one low importance memory."""
        primaries = [await repo.create_memory(user_id, _memory(f"primary {i}", importance=9)) for i in range(count)]
        others = [await repo.create_memory(user_id, _memory(f"linked {i}", importance=3)) for i in range(count)]
        for primary, other in zip(primaries, others, strict=True):
            await repo.create_links_batch(user_id, primary.id, [other.id])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("k", [20, 15])
    async def test_linked_memories_dropped_by_memory_cap_set_truncated(
        self, test_memory_service, mock_memory_repository, monkeypatch, k,
    ):
        monkeypatch.setattr(settings, "MEMORY_MAX_MEMORIES", 20)
        user_id = uuid4()
        await self._seed_linked_pairs(mock_memory_repository, user_id, 20)

        result = await test_memory_service.query_memory(user_id, _query(k=k, include_links=True))

        assert result.token_count < settings.MEMORY_TOKEN_BUDGET / 4  # the token budget is not the cause
        assert len(result.primary_memories) == k
        assert len(result.linked_memories) == 20 - k  # one linked memory was available per primary
        assert len(result.primary_memories) + len(result.linked_memories) == 20
        assert result.truncated is True

    @pytest.mark.asyncio
    async def test_primaries_dropped_by_memory_cap_set_truncated(
        self, test_memory_service, mock_memory_repository, monkeypatch,
    ):
        monkeypatch.setattr(settings, "MEMORY_MAX_MEMORIES", 2)
        user_id = uuid4()
        for i in range(3):
            await mock_memory_repository.create_memory(user_id, _memory(f"Memory {i}"))

        result = await test_memory_service.query_memory(user_id, _query(k=3))

        assert len(result.primary_memories) == 2
        assert result.truncated is True

    @pytest.mark.asyncio
    async def test_nothing_dropped_is_not_truncated(
        self, test_memory_service, mock_memory_repository, monkeypatch,
    ):
        monkeypatch.setattr(settings, "MEMORY_MAX_MEMORIES", 20)
        user_id = uuid4()
        await self._seed_linked_pairs(mock_memory_repository, user_id, 5)

        result = await test_memory_service.query_memory(user_id, _query(k=5, include_links=True))

        assert len(result.primary_memories) == 5
        assert len(result.linked_memories) == 5
        assert result.truncated is False


class TestLinkQuotaNotSpentOnPrimaries:
    @pytest.mark.asyncio
    async def test_primaries_do_not_consume_max_links_per_primary(
        self, test_memory_service, mock_memory_repository,
    ):
        user_id = uuid4()
        primaries = [
            await mock_memory_repository.create_memory(user_id, _memory(f"primary {i}", importance=9))
            for i in range(4)
        ]
        others = [
            await mock_memory_repository.create_memory(user_id, _memory(f"other {i}", importance=5))
            for i in range(6)
        ]
        # The first primary is linked to the 3 other primaries and to 6 non-primary memories
        await mock_memory_repository.create_links_batch(
            user_id, primaries[0].id, [m.id for m in primaries[1:] + others],
        )

        result = await test_memory_service.query_memory(
            user_id, _query(k=4, include_links=True, max_links_per_primary=3),
        )

        assert sorted(m.id for m in result.primary_memories) == sorted(m.id for m in primaries)
        linked_ids = [lm.memory.id for lm in result.linked_memories]
        assert len(linked_ids) == 3
        assert set(linked_ids) <= {m.id for m in others}
        assert {lm.link_source_id for lm in result.linked_memories} == {primaries[0].id}

    @pytest.mark.asyncio
    async def test_linked_memory_claimed_by_earlier_primary_does_not_consume_next_quota(
        self, test_memory_service, mock_memory_repository,
    ):
        user_id = uuid4()
        first = await mock_memory_repository.create_memory(user_id, _memory("primary first", importance=9))
        second = await mock_memory_repository.create_memory(user_id, _memory("primary second", importance=8))
        shared = await mock_memory_repository.create_memory(user_id, _memory("shared", importance=5))
        spare = await mock_memory_repository.create_memory(user_id, _memory("spare", importance=4))
        await mock_memory_repository.create_links_batch(user_id, first.id, [shared.id])
        await mock_memory_repository.create_links_batch(user_id, second.id, [shared.id, spare.id])

        result = await test_memory_service.query_memory(
            user_id, _query(k=2, include_links=True, max_links_per_primary=1),
        )

        linked = {lm.memory.id: lm.link_source_id for lm in result.linked_memories}
        assert linked == {shared.id: first.id, spare.id: second.id}
