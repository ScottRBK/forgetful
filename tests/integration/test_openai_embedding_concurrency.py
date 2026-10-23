"""Real async SDK requests against synthetic HTTP; no provider or model calls."""
import asyncio
import inspect
import json
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIStatusError, APITimeoutError, AsyncOpenAI, DefaultAsyncHttpxClient

from app.repositories.embeddings import embedding_adapter as module


def embedding_response(request):
    text = json.loads(request.content)["input"][0]
    return httpx.Response(200, json={
        "object": "list", "model": "synthetic-model",
        "data": [{"object": "embedding", "index": 0, "embedding": [float(len(text))]}],
        "usage": {"prompt_tokens": 1, "total_tokens": 1},
    })


@pytest.fixture
async def make_adapter(monkeypatch):
    # A real loopback socket exercises httpx's pool; MockTransport bypasses it.
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    handler_box = [embedding_response]
    connections = set()
    errors = []

    async def serve(reader, writer):
        task = asyncio.current_task()
        connections.add(task)
        try:
            header = await reader.readuntil(b"\r\n\r\n")
            lines = header.decode("latin1").split("\r\n")
            method, path, _ = lines[0].split(" ", 2)
            headers = dict(line.split(": ", 1) for line in lines[1:] if line)
            size = int(next(value for key, value in headers.items() if key.lower() == "content-length"))
            body = await reader.readexactly(size)
            request = httpx.Request(method, endpoint + path, headers=headers, content=body)
            response = handler_box[0](request)
            if inspect.isawaitable(response):
                response = await response
            output = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\r\n".encode()
            output += b"".join(f"{key}: {value}\r\n".encode() for key, value in response.headers.items()
                               if key.lower() != "connection")
            writer.write(output + b"Connection: close\r\n\r\n" + response.content)
            await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass  # A cancelled client can disconnect before a request or response finishes.
        except asyncio.CancelledError:
            raise
        except Exception as error:
            errors.append(error)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass
            connections.discard(task)

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    endpoint = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
    monkeypatch.setattr(module.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(module.settings, "OPENAI_BASE_URL", endpoint + "/v1")
    monkeypatch.setattr(module.settings, "EMBEDDING_MODEL", "synthetic-model")
    monkeypatch.setattr(module.settings, "EMBEDDING_DIMENSIONS", 1)
    monkeypatch.setattr(module.settings, "OPENAI_SUPPORTS_DIMENSIONS", True)
    adapters = []
    http_clients = []

    def http_client(**kwargs):
        client = DefaultAsyncHttpxClient(**kwargs)
        http_clients.append((client, kwargs["limits"]))
        return client

    # raising=False lets the unchanged-head contract control use the same fixture.
    monkeypatch.setattr(module, "DefaultAsyncHttpxClient", http_client, raising=False)

    def make(handler=embedding_response, capacity=None, **sdk_options):
        handler_box[0] = handler
        sdk_options.setdefault("max_retries", 0)
        monkeypatch.setattr(module, "AsyncOpenAI", lambda **kwargs: AsyncOpenAI(**kwargs, **sdk_options))
        adapter = module.OpenAIEmbeddingsAdapter() if capacity is None else module.OpenAIEmbeddingsAdapter(max_concurrency=capacity)
        adapters.append(adapter)
        return adapter

    make.http_clients = http_clients
    try:
        yield make
    finally:
        for adapter in adapters:
            await adapter.aclose()
        server.close()
        tasks = list(connections)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await server.wait_closed()
        assert not errors, errors


@pytest.mark.parametrize("capacity", [None, 2, 4])
async def test_configured_limits_reach_the_shared_sdk_http_client(make_adapter, capacity):
    adapter = make_adapter(capacity=capacity)
    client, limits = make_adapter.http_clients[-1]
    assert adapter.client._client is client
    assert limits.max_connections == (capacity or 1)
    assert limits.max_keepalive_connections == (capacity or 1)
    assert await adapter.generate_embedding("configured") == [10.0]


async def test_native_async_does_not_use_shared_thread_pool(make_adapter, monkeypatch):
    adapter = make_adapter()
    # The SDK performs its own one-time platform-metadata lookup in a worker.
    # Warm that path before checking that embedding HTTP calls need no worker.
    assert await adapter.generate_embedding("warmup") == [6.0]
    monkeypatch.setattr(asyncio, "to_thread", AsyncMock(side_effect=AssertionError("shared thread pool used")))
    assert await adapter.generate_embedding("hello") == [5.0]


@pytest.mark.parametrize("capacity", [1, 2, 4])
async def test_real_sdk_overlap_is_bounded_and_results_stay_associated(make_adapter, capacity):
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []
    active = 0
    peak = 0

    async def handler(request):
        nonlocal active, peak
        calls.append(json.loads(request.content)["input"][0])
        active += 1
        peak = max(peak, active)
        if active == capacity:
            entered.set()
        try:
            await release.wait()
            return embedding_response(request)
        finally:
            active -= 1

    adapter = make_adapter(handler, capacity)
    tasks = [asyncio.create_task(adapter.generate_embedding("x" * i)) for i in range(1, capacity + 2)]
    try:
        await asyncio.wait_for(entered.wait(), 2)
        # A scheduling interval allows the excess caller to attempt admission.
        await asyncio.sleep(0.3)
        assert len(calls) == capacity
        assert not any(task.done() for task in tasks)
        release.set()
        assert await asyncio.gather(*tasks) == [[float(i)] for i in range(1, capacity + 2)]
        assert peak == capacity
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)


async def test_waiter_and_active_cancellation_release_without_sending_waiter(make_adapter):
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def handler(request):
        text = json.loads(request.content)["input"][0]
        calls.append(text)
        if text == "active":
            entered.set()
            await release.wait()
        return embedding_response(request)

    adapter = make_adapter(handler, 1)
    active = asyncio.create_task(adapter.generate_embedding("active"))
    await asyncio.wait_for(entered.wait(), 2)
    waiting = asyncio.create_task(adapter.generate_embedding("waiting"))
    await asyncio.sleep(0)
    waiting.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiting
    active.cancel()
    with pytest.raises(asyncio.CancelledError):
        await active
    assert await adapter.generate_embedding("next") == [4.0]
    assert calls == ["active", "next"]


async def test_sdk_retry_backoff_releases_http_capacity(make_adapter):
    first_attempt = asyncio.Event()
    calls = []

    async def handler(request):
        text = json.loads(request.content)["input"][0]
        calls.append(text)
        if text == "first" and calls.count("first") == 1:
            first_attempt.set()
            return httpx.Response(429, headers={"retry-after": "1"}, json={"error": {"message": "synthetic retry"}})
        return embedding_response(request)

    adapter = make_adapter(handler, 1, max_retries=1)
    first = asyncio.create_task(adapter.generate_embedding("first"))
    await asyncio.wait_for(first_attempt.wait(), 5)
    second = asyncio.create_task(adapter.generate_embedding("second"))
    try:
        assert await asyncio.wait_for(asyncio.gather(first, second), 10) == [[5.0], [6.0]]
        print("RETRY_SERVER_ORDER=" + json.dumps(calls))
        assert calls == ["first", "second", "first"]
    finally:
        await asyncio.gather(first, second, return_exceptions=True)


@pytest.mark.parametrize("timeout", [False, True])
async def test_http_failure_releases_capacity(make_adapter, timeout):
    async def handler(request):
        if json.loads(request.content)["input"] == ["fail"]:
            if timeout:
                await asyncio.sleep(3.0)
                return embedding_response(request)
            return httpx.Response(503, json={"error": {"message": "synthetic failure"}})
        return embedding_response(request)

    adapter = make_adapter(handler, 1, timeout=1.0 if timeout else 5.0)
    with pytest.raises(APITimeoutError if timeout else APIStatusError):
        await adapter.generate_embedding("fail")
    assert await adapter.generate_embedding("ok") == [2.0]


async def test_close_delegates_to_sdk_and_closes_the_shared_http_client(make_adapter):
    adapter = make_adapter()
    await adapter.generate_embedding("open")
    client = adapter.client._client
    sdk_close = AsyncMock(wraps=adapter.client.close)
    adapter.client.close = sdk_close
    await adapter.aclose()
    sdk_close.assert_awaited_once()
    assert client.is_closed
    assert adapter.client.is_closed()


@pytest.mark.parametrize("dimensions", [False, True])
async def test_real_sdk_preserves_compatible_endpoint_request(make_adapter, monkeypatch, dimensions):
    requests = []

    async def handler(request):
        requests.append(request)
        return embedding_response(request)

    monkeypatch.setattr(module.settings, "OPENAI_SUPPORTS_DIMENSIONS", dimensions)
    adapter = make_adapter(handler)
    assert await adapter.generate_embedding("input") == [5.0]
    request = requests[0]
    body = json.loads(request.content)
    assert request.url.path == "/v1/embeddings"
    assert request.url.host == "127.0.0.1"
    assert request.headers["authorization"] == "Bearer no-key-required"
    assert body["model"] == "synthetic-model"
    assert body["input"] == ["input"]
    assert ("dimensions" in body) is dimensions
    if dimensions:
        assert body["dimensions"] == 1


@pytest.mark.parametrize("capacity", [0, -1])
def test_invalid_capacity_is_rejected(make_adapter, capacity):
    with pytest.raises(ValueError, match="at least 1"):
        make_adapter(capacity=capacity)


async def test_runtime_memory_and_skill_searches_share_configured_limit(sqlite_runtime_settings, make_adapter, monkeypatch):
    from uuid import uuid4

    from app import bootstrap

    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []
    active = 0
    peak = 0

    async def handler(request):
        nonlocal active, peak
        calls.append(json.loads(request.content)["input"][0])
        active += 1
        peak = max(peak, active)
        if active == 2:
            entered.set()
        try:
            await release.wait()
            return embedding_response(request)
        finally:
            active -= 1

    # Install the synthetic SDK factory that bootstrap uses for its own adapter.
    make_adapter(handler)
    monkeypatch.setattr(module.settings, "EMBEDDING_PROVIDER", "OpenAI")
    monkeypatch.setattr(module.settings, "EMBEDDING_MAX_CONCURRENCY", 2)
    monkeypatch.setattr(module.settings, "SKILLS_ENABLED", True)
    runtime = await bootstrap.build_runtime()
    user_id = uuid4()
    tasks = [asyncio.create_task(runtime.repos["memory"].search(
        user_id=user_id, query="memory", query_context="search", k=1,
        importance_threshold=None, project_ids=None, exclude_ids=None,
    ))]
    tasks.extend(asyncio.create_task(runtime.services.skill.search_skills(
        user_id=user_id, query=query,
    )) for query in ("skill-one", "skill-two"))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        await asyncio.sleep(0.3)
        assert len(calls) == 2
        release.set()
        assert await asyncio.gather(*tasks) == [[], [], []]
        assert peak == 2
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        await bootstrap.dispose_runtime(runtime)
    assert runtime.embedding_adapter.client.is_closed()


async def test_runtime_startup_failure_closes_real_async_client(sqlite_runtime_settings, make_adapter, monkeypatch):
    from app import bootstrap

    adapter = make_adapter()
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: adapter)
    monkeypatch.setattr(module.settings, "EMBEDDING_PROVIDER", "OpenAI")

    def fail_database():
        raise RuntimeError("synthetic startup failure")

    monkeypatch.setattr(bootstrap, "create_db_adapter", fail_database)
    with pytest.raises(RuntimeError, match="synthetic startup failure"):
        await bootstrap.build_runtime()
    assert adapter.client.is_closed()


async def test_reembed_cli_exit_closes_real_async_client(sqlite_runtime_settings, make_adapter, monkeypatch):
    from argparse import Namespace

    import main
    from app import bootstrap

    adapter = make_adapter()
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", lambda: adapter)
    monkeypatch.setattr(module.settings, "EMBEDDING_PROVIDER", "OpenAI")
    await main._run_reembed(Namespace(batch_size=1, dry_run=True))
    assert adapter.client.is_closed()
