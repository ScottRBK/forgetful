"""PostgreSQL auto-links only memories above the cosine similarity cutoff."""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


class KnownEmbeddings:
    async def generate_embedding(self, text: str) -> list[float]:
        vectors = {
            "Anchor": (1.0, 0.0),
            "Unrelated": (0.0, 1.0),
            "Related": (0.8, 0.6),
        }
        x, y = vectors[text.split(maxsplit=1)[0]]
        return [x, y, *([0.0] * 382)]


@pytest.fixture(scope="session")
def embedding_adapter():
    return KnownEmbeddings()


@pytest.fixture(scope="session")
def reranker_adapter():
    return None


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
