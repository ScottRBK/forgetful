"""Memory budgets for hot paths, enforced with pytest-memray (``--memray``, Linux/macOS).

Without ``--memray`` these run as ordinary smoke tests. Each budget is headroom over the measured
peak (about 15 MB for the bulk create, about 175 MB for the queries) so a test fails on a leak or an
accidental full-table load, not on noise or on a slower CPU.
"""

import pytest

pytestmark = pytest.mark.memory

MEMORY_COUNT = 60


@pytest.fixture(autouse=True)
async def _warm_models(embedding_adapter, reranker_adapter):
    """Load the ONNX models before the measured section so budgets cover our code only."""
    await embedding_adapter.generate_embedding("warm up")
    if reranker_adapter is not None:
        await reranker_adapter.rerank("warm up", ["warm up", "cold start"])


async def _seed(mcp_client, count: int = MEMORY_COUNT) -> None:
    for i in range(count):
        await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "create_memory",
                "arguments": {
                    "title": f"memory budget {i}",
                    "content": f"Content for memory {i}: " + "lorem ipsum dolor sit amet " * 8,
                    "context": "memory budget test",
                    "keywords": ["budget", f"k{i}"],
                    "tags": ["perf"],
                    "importance": 5,
                },
            },
        )


@pytest.mark.limit_memory("64 MB")
async def test_bulk_create_stays_within_budget(mcp_client):
    await _seed(mcp_client)


# measured ~175 MB peak (132 MB of it inside onnxruntime cross-encoder inference, CPU dependent)
@pytest.mark.limit_memory("384 MB")
async def test_query_stays_within_budget(mcp_client):
    await _seed(mcp_client, 20)
    for i in range(20):
        await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "query_memory",
                "arguments": {"query": f"memory budget {i}", "query_context": "budget", "k": 5},
            },
        )
