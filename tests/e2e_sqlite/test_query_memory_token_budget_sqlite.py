"""query_memory token budgeting through the full stack on in-memory SQLite (REST and MCP)."""
import pytest

from app.config.settings import settings

SPECIAL_TOKEN_CONTENT = "GPT models use the <|endoftext|> special token to separate documents"


class KnownEmbeddings:
    """Predictable embeddings: Query and Primary are identical, Other is close enough to auto-link."""

    async def generate_embedding(self, text: str) -> list[float]:
        vectors = {
            "Primary": (1.0, 0.0),
            "Query": (1.0, 0.0),
            "Other": (0.9, 0.4359),  # cosine ~0.90 to Primary, above the 0.7 auto-link threshold
            "Tokenizer": (1.0, 0.0),
            "Large": (1.0, 0.0),
        }
        x, y = vectors[text.split(maxsplit=1)[0]]
        return [x, y, *([0.0] * 382)]


@pytest.fixture(scope="module")
def embedding_adapter():
    return KnownEmbeddings()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


async def _call(client, tool, arguments):
    result = await client.call_tool("execute_forgetful_tool", {"tool_name": tool, "arguments": arguments})
    return result.data


async def _create(client, title, importance=5, content="content"):
    created = await _call(client, "create_memory", {
        "title": title,
        "content": content,
        "context": "ctx",
        "keywords": [],
        "tags": [],
        "importance": importance,
    })
    return created["id"]


async def _create_large_memories_via_rest(http_client, count=20):
    # ~1900 characters each, which is roughly 350-400 tokens per memory
    body = ("The quick brown fox jumps over the lazy dog while debugging token budgets. " * 25)[:1900]
    for i in range(count):
        response = await http_client.post("/api/v1/memories", json={
            "title": f"Large budget memory {i}",
            "content": body,
            "context": "token budget",
            "keywords": ["token", "budget"],
            "tags": ["budget"],
            "importance": 5,
        })
        assert response.status_code == 201, response.text


@pytest.fixture(autouse=True)
def _no_rerank(monkeypatch):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)


@pytest.mark.asyncio
async def test_rest_search_returns_memory_containing_special_token(http_client):
    created = await http_client.post("/api/v1/memories", json={
        "title": "Tokenizer notes",
        "content": SPECIAL_TOKEN_CONTENT,
        "context": "Notes about tokenizers",
        "keywords": ["tokenizer", "gpt"],
        "tags": ["nlp"],
        "importance": 8,
    })
    assert created.status_code == 201, created.text

    response = await http_client.post(
        "/api/v1/memories/search",
        json={"query": "Tokenizer special token", "query_context": "tokenizers"},
    )

    assert response.status_code == 200, response.text
    assert created.json()["id"] in [m["id"] for m in response.json()["primary_memories"]]


@pytest.mark.asyncio
async def test_mcp_query_memory_returns_memory_containing_special_token(mcp_client):
    memory_id = await _create(mcp_client, "Tokenizer notes", 8, SPECIAL_TOKEN_CONTENT)

    result = await _call(mcp_client, "query_memory", {
        "query": "Tokenizer special token", "query_context": "tokenizers",
    })

    assert memory_id in [m["id"] for m in result["primary_memories"]]
