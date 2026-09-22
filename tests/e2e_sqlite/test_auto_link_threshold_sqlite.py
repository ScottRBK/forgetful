"""Auto-linking only connects memories with sufficient cosine similarity."""

import pytest

from app.config.settings import settings


class KnownEmbeddings:
    """Predictable embeddings keep the threshold test independent of a model download."""

    async def generate_embedding(self, text: str) -> list[float]:
        vectors = {
            "Anchor": (1.0, 0.0),
            "Unrelated": (0.0, 1.0),
            "Related": (0.8, 0.6),
        }
        x, y = vectors[text.split(maxsplit=1)[0]]
        return [x, y, *([0.0] * 382)]


@pytest.fixture(scope="module")
def embedding_adapter():
    return KnownEmbeddings()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


@pytest.mark.asyncio
async def test_create_memory_links_only_above_similarity_cutoff(mcp_client):
    async def create(title: str):
        return await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "create_memory",
            "arguments": {
                "title": title,
                "content": "A test memory",
                "context": "Checking automatic links",
                "keywords": [],
                "tags": [],
                "importance": 7,
            },
        })

    # Arrange: the closest existing memory can still be unrelated.
    anchor = await create("Anchor")

    # Act: create an unrelated memory, then one whose cosine similarity is 0.8.
    unrelated = await create("Unrelated")
    related = await create("Related")

    # Assert: only the related memory is auto-linked.
    assert unrelated.data["similar_memories"] == []
    assert [memory["id"] for memory in related.data["similar_memories"]] == [
        anchor.data["id"],
    ]


@pytest.mark.asyncio
async def test_rebuild_embeddings_respects_similarity_cutoff(mcp_client, monkeypatch):
    async def create(title: str):
        return await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "create_memory",
            "arguments": {
                "title": title,
                "content": "A test memory",
                "context": "Checking rebuilt links",
                "keywords": [],
                "tags": [],
                "importance": 7,
            },
        })

    # Arrange: create memories without links, then enable auto-linking for rebuild.
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    anchor = await create("Anchor")
    unrelated = await create("Unrelated")
    related = await create("Related")
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 3)

    # Act: rebuild the anchor through the public tool.
    rebuilt = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "rebuild_embeddings",
        "arguments": {"memory_ids": [anchor.data["id"]]},
    })
    fetched = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "get_memory",
        "arguments": {"memory_id": anchor.data["id"]},
    })

    # Assert: rebuilding links the related memory and leaves the unrelated one alone.
    assert rebuilt.data["rebuilt_ids"] == [anchor.data["id"]]
    assert fetched.data["linked_memory_ids"] == [related.data["id"]]
    assert unrelated.data["id"] not in fetched.data["linked_memory_ids"]
