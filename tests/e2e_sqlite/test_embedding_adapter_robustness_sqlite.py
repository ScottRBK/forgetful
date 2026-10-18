"""E2E test (in-memory SQLite) that a slow embedding provider does not freeze the server.

Full stack: MCP client -> execute_forgetful_tool -> MemoryService -> SQLite
repository -> AzureOpenAIAdapter (real openai SDK, in-process fake endpoint).
"""
import asyncio
import functools
import json
import threading

import httpx
import pytest

from app.config.settings import settings
from app.repositories.embeddings import embedding_adapter as ea

GATE_TIMEOUT = 3.0


class EmbeddingEndpointGate:
    """Fake Azure endpoint that holds the request until the test releases it.

    The test releases the gate from a coroutine. That only works while the
    embedding request is in flight if the event loop is still free, so an
    adapter that blocks the loop thread leaves the gate closed until it times out.
    """

    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.released_in_time = False

    def __call__(self, request: httpx.Request) -> httpx.Response:
        json.loads(request.content)
        self.started.set()
        self.released_in_time = self.release.wait(timeout=GATE_TIMEOUT)
        return httpx.Response(200, json={
            "object": "list",
            "model": "fake",
            "usage": {"prompt_tokens": 1, "total_tokens": 1},
            "data": [{
                "object": "embedding",
                "index": 0,
                "embedding": [0.01] * settings.EMBEDDING_DIMENSIONS,
            }],
        })


@pytest.fixture
def embedding_gate():
    return EmbeddingEndpointGate()


@pytest.fixture
def embedding_adapter(embedding_gate, monkeypatch):
    """Override the module-scoped fixture: real Azure adapter, gated fake endpoint."""
    for name, value in {
        "AZURE_ENDPOINT": "https://fake.openai.azure.com/",
        "AZURE_API_KEY": "fake-key",
        "AZURE_API_VERSION": "2024-02-01",
        "AZURE_DEPLOYMENT": "fake-deployment",
    }.items():
        monkeypatch.setattr(settings, name, value)

    http_client = httpx.Client(transport=httpx.MockTransport(embedding_gate))
    monkeypatch.setattr(
        ea, "AzureOpenAI", functools.partial(ea.AzureOpenAI, http_client=http_client),
    )
    yield ea.AzureOpenAIAdapter()
    http_client.close()


async def test_create_memory_keeps_the_event_loop_free(mcp_client, embedding_gate):
    create = asyncio.create_task(mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory",
        "arguments": {
            "title": "Event loop probe",
            "content": "Embedding calls must not block the server's event loop",
            "context": "Regression test for blocking embedding calls",
            "keywords": ["probe"],
            "tags": ["probe"],
            "importance": 5,
        },
    }))

    while not embedding_gate.started.is_set():
        await asyncio.sleep(0.001)
    embedding_gate.release.set()
    result = await create

    assert embedding_gate.released_in_time, "embedding request ran on the event loop thread"
    assert result.data["id"] is not None
