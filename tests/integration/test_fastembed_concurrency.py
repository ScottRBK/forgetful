"""FastEmbed work must be bounded without blocking the caller's event loop."""
import asyncio
import threading
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter


async def test_default_embedding_does_not_block_event_loop(monkeypatch):
    active = threading.Event()
    observed = []

    def embed(text):
        active.set()
        time.sleep(0.1)
        active.clear()
        return [[1.0]]

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter()

    async def ticker():
        for _ in range(30):
            observed.append(active.is_set())
            await asyncio.sleep(0.005)

    try:
        result, _ = await asyncio.gather(adapter.generate_embedding("hello"), ticker())
        assert result == [1.0]
        assert any(observed), "embedding blocked the event loop throughout inference"
    finally:
        if hasattr(adapter, "aclose"):
            await adapter.aclose()


async def test_embedding_requests_overlap_with_capacity_two(monkeypatch):
    barrier = threading.Barrier(2, timeout=1)

    def embed(text):
        barrier.wait()
        return [[float(text)]]

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter(max_concurrency=2)
    try:
        assert await asyncio.gather(
            adapter.generate_embedding("1"), adapter.generate_embedding("2"),
        ) == [[1.0], [2.0]]
    finally:
        await adapter.aclose()


@pytest.mark.parametrize("capacity", [1, 2, 4])
async def test_capacity_is_shared_and_bounds_active_inference(monkeypatch, capacity):
    lock = threading.Lock()
    active = peak = 0
    barrier = threading.Barrier(capacity, timeout=2)

    def embed(text):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(active, peak)
        try:
            barrier.wait()
            time.sleep(0.01)
            return [[float(text)]]
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter(max_concurrency=capacity)
    try:
        result = await asyncio.gather(*(adapter.generate_embedding(str(i)) for i in range(8)))
        assert result == [[float(i)] for i in range(8)]
        assert peak == capacity
    finally:
        await adapter.aclose()


async def test_cancelled_running_request_retains_capacity_and_waiter_never_runs(monkeypatch):
    started, release = threading.Event(), threading.Event()
    calls = []

    def embed(text):
        calls.append(text)
        if text == "running":
            started.set()
            assert release.wait(timeout=3)
        if text == "error":
            raise ValueError("inference failed")
        return [[1.0]]

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter()
    try:
        running = asyncio.create_task(adapter.generate_embedding("running"))
        assert await asyncio.to_thread(started.wait, 1)
        cancelled = asyncio.create_task(adapter.generate_embedding("cancelled waiter"))
        await asyncio.sleep(0)
        cancelled.cancel()
        with pytest.raises(asyncio.CancelledError):
            await cancelled
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        successor = asyncio.create_task(adapter.generate_embedding("successor"))
        await asyncio.sleep(0.02)
        assert calls == ["running"]
        release.set()
        assert await successor == [1.0]
        with pytest.raises(ValueError, match="inference failed"):
            await adapter.generate_embedding("error")
        assert await adapter.generate_embedding("after error") == [1.0]
        assert "cancelled waiter" not in calls
    finally:
        release.set()
        await adapter.aclose()


async def test_close_wakes_waiters_and_drains_workers_without_blocking_loop(monkeypatch):
    started, release = threading.Event(), threading.Event()
    calls = []

    def embed(text):
        calls.append(text)
        started.set()
        assert release.wait(timeout=3)
        return [[1.0]]

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter()
    try:
        running = asyncio.create_task(adapter.generate_embedding("running"))
        assert await asyncio.to_thread(started.wait, 1)
        waiter = asyncio.create_task(adapter.generate_embedding("waiting"))
        await asyncio.sleep(0)
        closing = asyncio.create_task(adapter.aclose())
        with pytest.raises(RuntimeError, match="closed"):
            await asyncio.wait_for(waiter, 1)
        assert not closing.done()
        assert calls == ["running"]
        release.set()
        assert await running == [1.0]
        await closing
        await adapter.aclose()
        with pytest.raises(RuntimeError, match="closed"):
            await adapter.generate_embedding("after close")
    finally:
        release.set()
        await adapter.aclose()


async def test_cancelled_caller_worker_failure_is_retrieved(monkeypatch):
    started, release = threading.Event(), threading.Event()
    errors = []

    def embed(text):
        started.set()
        assert release.wait(timeout=3)
        raise ValueError("late worker error")

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter()
    loop = asyncio.get_running_loop()
    old_handler = loop.get_exception_handler()
    loop.set_exception_handler(lambda _loop, context: errors.append(context))
    try:
        task = asyncio.create_task(adapter.generate_embedding("x"))
        assert await asyncio.to_thread(started.wait, 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()
        await adapter.aclose()
        await asyncio.sleep(0)
        assert not errors
    finally:
        release.set()
        await adapter.aclose()
        loop.set_exception_handler(old_handler)


@pytest.mark.parametrize("providers", [None, ["CPUExecutionProvider"], ["CUDAExecutionProvider"]])
async def test_non_directml_provider_lists_allow_overlap(monkeypatch, providers):
    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=lambda text: [[1.0]]),
    )
    adapter = FastEmbeddingAdapter(providers=providers, max_concurrency=2)
    await adapter.aclose()


@pytest.mark.parametrize("providers", [["DmlExecutionProvider"], ["CPUExecutionProvider", " DmlExecutionProvider "]])
def test_directml_guard_precedes_model_loading(monkeypatch, providers):
    def unexpected_load(**kwargs):
        pytest.fail("DirectML restriction must be checked before model loading")
    monkeypatch.setattr("app.repositories.embeddings.embedding_adapter.load_fastembed_model", unexpected_load)
    with pytest.raises(ValueError, match="EMBEDDING_MAX_CONCURRENCY=1"):
        FastEmbeddingAdapter(providers=providers, max_concurrency=2)


@pytest.mark.parametrize("value", [0, -1])
def test_concurrency_setting_rejects_invalid_capacity(value):
    from pydantic import ValidationError

    from app.config.settings import Settings
    with pytest.raises(ValidationError, match="EMBEDDING_MAX_CONCURRENCY"):
        Settings(_env_file=None, EMBEDDING_MAX_CONCURRENCY=value)


@pytest.mark.parametrize("failure_stage", ["reranker", "database", "init", "repositories"])
async def test_startup_failure_closes_embedding_adapter(monkeypatch, failure_stage):
    from app import bootstrap
    adapter = SimpleNamespace(aclose=AsyncMock())
    error = ValueError("startup failed")
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(bootstrap, "check_first_run_models", lambda: None)
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: adapter)
    monkeypatch.setattr(bootstrap, "get_reranker_adapter", fail if failure_stage == "reranker" else lambda: None)
    database = SimpleNamespace(init_db=AsyncMock(side_effect=error if failure_stage == "init" else None))
    monkeypatch.setattr(bootstrap, "create_db_adapter", fail if failure_stage == "database" else lambda: database)
    monkeypatch.setattr(bootstrap, "create_repositories", fail)
    with pytest.raises(ValueError) as caught:
        await bootstrap.build_runtime()
    assert caught.value is error
    adapter.aclose.assert_awaited_once()


async def test_bootstrap_shares_one_adapter_between_memory_and_skills(sqlite_runtime_settings, monkeypatch):
    from app import bootstrap
    from app.config.settings import settings
    settings.SKILLS_ENABLED = True
    adapter = SimpleNamespace(aclose=AsyncMock())
    monkeypatch.setattr(bootstrap, "check_first_run_models", lambda: None)
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: adapter)
    runtime = await bootstrap.build_runtime()
    assert runtime.embedding_adapter is adapter
    assert runtime.repos["memory"].embedding_adapter is adapter
    assert runtime.repos["skill"].embedding_adapter is adapter
    await bootstrap.dispose_runtime(runtime)
    adapter.aclose.assert_awaited_once()


async def test_reembed_initialization_failure_closes_workers(monkeypatch):
    import main
    from app import bootstrap
    adapter = SimpleNamespace(aclose=AsyncMock())
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: adapter)
    def fail():
        raise ValueError("backup init failed")
    monkeypatch.setattr(bootstrap, "create_backup_service", fail)
    with pytest.raises(ValueError, match="backup init failed"):
        await main._run_reembed(SimpleNamespace())
    adapter.aclose.assert_awaited_once()


def test_bootstrap_passes_capacity_and_provider_settings(monkeypatch):
    from unittest.mock import Mock

    from app import bootstrap
    from app.config.settings import settings

    factory = Mock()
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "FastEmbed")
    monkeypatch.setattr(settings, "EMBEDDING_MAX_CONCURRENCY", 3)
    monkeypatch.setattr(settings, "EMBEDDING_ONNX_PROVIDERS", "CPUExecutionProvider")
    monkeypatch.setattr("app.repositories.embeddings.embedding_adapter.FastEmbeddingAdapter", factory)
    assert bootstrap.get_embedding_adapter() is factory.return_value
    factory.assert_called_once_with(providers=["CPUExecutionProvider"], max_concurrency=3)


async def test_inference_iteration_and_float_conversion_stay_on_worker(monkeypatch):
    class WorkerFloat:
        def __float__(self):
            assert threading.current_thread().name.startswith("embedding")
            return 1.0

    def embed(text):
        assert threading.current_thread().name.startswith("embedding")
        yield [WorkerFloat()]

    monkeypatch.setattr(
        "app.repositories.embeddings.embedding_adapter.load_fastembed_model",
        lambda **kwargs: SimpleNamespace(embed=embed),
    )
    adapter = FastEmbeddingAdapter(providers=["DmlExecutionProvider"], max_concurrency=1)
    try:
        assert await adapter.generate_embedding("x") == [1.0]
    finally:
        await adapter.aclose()


async def test_empty_provider_list_uses_fastembed_default_not_ort_all_providers(monkeypatch):
    from unittest.mock import Mock

    from app.config.settings import settings

    monkeypatch.setattr(settings, "FASTEMBED_LOCAL_FILES_ONLY", False)
    factory = Mock(return_value=SimpleNamespace(embed=lambda text: [[1.0]]))
    monkeypatch.setattr("fastembed.TextEmbedding", factory)
    adapter = FastEmbeddingAdapter(providers=[], max_concurrency=2)
    try:
        assert "providers" not in factory.call_args.kwargs
    finally:
        await adapter.aclose()
