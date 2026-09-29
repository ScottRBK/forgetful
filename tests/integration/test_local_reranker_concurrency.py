"""Exercise the public rerank API with controlled, network-free FastEmbed inference."""
import asyncio
from threading import Lock, Semaphore

import pytest
from pydantic import ValidationError

from app.bootstrap import get_reranker_adapter
from app.config.settings import Settings, settings
from app.repositories.embeddings.reranker_adapter import FastEmbedCrossEncoderAdapter


class GatedCrossEncoder:
    """External model substitute: hold inference until the test releases a permit."""

    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.started = asyncio.Queue()
        self.finished = asyncio.Queue()
        self.release = Semaphore(0)
        self.lock = Lock()
        self.active = 0
        self.peak_active = 0
        self.options = {}

    def rerank(self, query, documents):
        with self.lock:
            self.active += 1
            self.peak_active = max(self.peak_active, self.active)
        self.loop.call_soon_threadsafe(self.started.put_nowait, query)
        try:
            if not self.release.acquire(timeout=5):
                raise TimeoutError("Test did not release model inference")
            if query == "failure":
                raise ValueError("Model inference failed")
            return [float(document == query) for document in documents]
        finally:
            with self.lock:
                self.active -= 1
            self.loop.call_soon_threadsafe(self.finished.put_nowait, query)


@pytest.fixture
async def encoder(monkeypatch):
    model = GatedCrossEncoder()

    def create_encoder(**options):
        model.options = options
        return model

    monkeypatch.setattr("fastembed.rerank.cross_encoder.TextCrossEncoder", create_encoder)
    return model


async def assert_rerank_capacity(adapter, encoder, workers):
    requests = [
        ("redis", ["postgres", "redis"]),
        ("postgres", ["postgres", "redis"]),
        ("python", ["python", "redis"]),
    ]

    tasks = [asyncio.create_task(adapter.rerank(query, docs)) for query, docs in requests]
    try:
        # All configured workers must enter inference before any job is released.
        for _ in range(workers):
            await asyncio.wait_for(encoder.started.get(), timeout=3)
        # Queued jobs can start as the occupied workers finish.
        for _ in range(len(requests) - workers):
            encoder.release.release()
            await asyncio.wait_for(encoder.started.get(), timeout=3)
        encoder.release.release(workers)
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=3)

        assert encoder.peak_active == workers
        assert results == [
            [(1, 1.0), (0, 0.0)],
            [(0, 1.0), (1, 0.0)],
            [(0, 1.0), (1, 0.0)],
        ]
    finally:
        encoder.release.release(len(tasks))
        await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.parametrize("options, workers", [({}, 1), ({"workers": 2}, 2)])
async def test_rerank_bounds_overlap_and_keeps_results_separate(encoder, options, workers):
    adapter = FastEmbedCrossEncoderAdapter(**options)

    await assert_rerank_capacity(adapter, encoder, workers)


@pytest.mark.parametrize("configure", [False, True], ids=["defaults", "environment"])
async def test_rerank_uses_configured_threads_and_workers(monkeypatch, encoder, configure):
    monkeypatch.delenv("RERANKING_THREADS", raising=False)
    monkeypatch.delenv("RERANKING_WORKERS", raising=False)
    if configure:
        monkeypatch.setenv("RERANKING_THREADS", "4")
        monkeypatch.setenv("RERANKING_WORKERS", "2")
    configured = Settings(_env_file=None)
    for name in ("RERANKING_THREADS", "RERANKING_WORKERS"):
        monkeypatch.setattr(settings, name, getattr(configured, name))
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "FastEmbed")
    adapter = get_reranker_adapter()

    await assert_rerank_capacity(adapter, encoder, workers=2 if configure else 1)

    assert encoder.options["threads"] == (4 if configure else 1)


@pytest.mark.parametrize("name", ["RERANKING_THREADS", "RERANKING_WORKERS"])
@pytest.mark.parametrize("value", ["0", "-1", "1.5"])
def test_rerank_configuration_rejects_invalid_limits(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError, match=name):
        Settings(_env_file=None)


async def test_failed_inference_does_not_block_later_reranks(encoder):
    adapter = FastEmbedCrossEncoderAdapter(workers=1)
    encoder.release.release(2)

    results = await asyncio.wait_for(
        asyncio.gather(
            adapter.rerank("failure", ["redis"]),
            adapter.rerank("redis", ["postgres", "redis"]),
            return_exceptions=True,
        ),
        timeout=3,
    )

    assert isinstance(results[0], ValueError)
    assert str(results[0]) == "Model inference failed"
    assert results[1] == [(1, 1.0), (0, 0.0)]


@pytest.mark.parametrize("cancel_index", [0, 2], ids=["running", "queued"])
async def test_cancelled_rerank_does_not_block_later_jobs(encoder, cancel_index):
    adapter = FastEmbedCrossEncoderAdapter(workers=2)
    tasks = [
        asyncio.create_task(adapter.rerank(query, ["postgres", "redis"]))
        for query in ("redis", "postgres", "redis")
    ]
    try:
        for _ in range(2):
            await asyncio.wait_for(encoder.started.get(), timeout=3)

        tasks[cancel_index].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[cancel_index]
        # Cancelling the awaiter cannot stop inference already running in a thread.
        encoder.release.release(3)
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True), timeout=3,
        )
        for _ in range(3 if cancel_index == 0 else 2):
            await asyncio.wait_for(encoder.finished.get(), timeout=3)
        encoder.release.release()
        later_result = await asyncio.wait_for(
            adapter.rerank("redis", ["postgres", "redis"]), timeout=3,
        )

        expected = [[(1, 1.0), (0, 0.0)], [(0, 1.0), (1, 0.0)], [(1, 1.0), (0, 0.0)]]
        for index, result in enumerate(results):
            if index == cancel_index:
                assert isinstance(result, asyncio.CancelledError)
            else:
                assert result == expected[index]
        assert later_result == [(1, 1.0), (0, 0.0)]
        assert encoder.peak_active == 2
    finally:
        encoder.release.release(len(tasks))
        await asyncio.gather(*tasks, return_exceptions=True)
