"""E2E tests for the memory link routes.

Covers GET/POST /api/v1/memories/{id}/links: limit validation, related_ids
validation, and soft-deleted neighbours.

Auto-linking is disabled so every memory contains exactly the links the test
creates.
"""
import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def disable_auto_linking():
    """Keep graphs exactly as built by each test."""
    from app.config.settings import settings

    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _create_memory(client, n: int) -> int:
    response = await client.post("/api/v1/memories", json={
        "title": f"Link route node {n}",
        "content": f"unique content about topic number {n} {'x' * n}",
        "context": "link and subgraph route tests",
        "keywords": [f"linkroute{n}"],
        "tags": ["link-routes"],
        "importance": 7,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_memories(client, count: int) -> list[int]:
    return [await _create_memory(client, n) for n in range(1, count + 1)]


async def _link(client, source: int, targets: list[int]) -> None:
    response = await client.post(f"/api/v1/memories/{source}/links", json={"related_ids": targets})
    assert response.status_code == 200, response.text


async def _linked_ids(client, memory_id: int) -> list[int]:
    response = await client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200, response.text
    return response.json()["linked_memory_ids"]


async def _soft_delete(client, memory_id: int) -> None:
    response = await client.request(
        "DELETE", f"/api/v1/memories/{memory_id}", json={"reason": "no longer needed"},
    )
    assert response.status_code == 200, response.text


class TestGetMemoryLinksLimit:
    """GET /api/v1/memories/{id}/links limit handling."""

    @pytest.mark.parametrize("bad_limit", ["0", "-1", "-2"])
    async def test_limit_below_one_is_rejected(self, http_client, bad_limit):
        root, a, b, c = await _create_memories(http_client, 4)
        await _link(http_client, root, [a, b, c])

        response = await http_client.get(f"/api/v1/memories/{root}/links?limit={bad_limit}")

        assert response.status_code == 400, response.text
        assert "limit" in response.json()["error"]

    async def test_non_integer_limit_is_rejected(self, http_client):
        root, a = await _create_memories(http_client, 2)
        await _link(http_client, root, [a])

        response = await http_client.get(f"/api/v1/memories/{root}/links?limit=abc")

        assert response.status_code == 400, response.text

    async def test_limit_returns_leading_links(self, http_client):
        root, a, b, c = await _create_memories(http_client, 4)
        await _link(http_client, root, [a, b, c])

        response = await http_client.get(f"/api/v1/memories/{root}/links?limit=2")

        assert response.status_code == 200, response.text
        assert [m["id"] for m in response.json()["linked_memories"]] == [a, b]

    async def test_limit_above_maximum_is_still_clamped(self, http_client):
        root, a = await _create_memories(http_client, 2)
        await _link(http_client, root, [a])

        response = await http_client.get(f"/api/v1/memories/{root}/links?limit=1000")

        assert response.status_code == 200, response.text
        assert [m["id"] for m in response.json()["linked_memories"]] == [a]


class TestGetMemoryLinksObsolete:
    """GET /api/v1/memories/{id}/links and soft-deleted neighbours."""

    async def test_obsolete_neighbour_is_omitted_by_default(self, http_client):
        root, alive, gone = await _create_memories(http_client, 3)
        await _link(http_client, root, [alive, gone])
        await _soft_delete(http_client, gone)

        response = await http_client.get(f"/api/v1/memories/{root}/links")

        assert response.status_code == 200, response.text
        assert [m["id"] for m in response.json()["linked_memories"]] == [alive]

    async def test_include_obsolete_returns_flagged_neighbour(self, http_client):
        root, alive, gone = await _create_memories(http_client, 3)
        await _link(http_client, root, [alive, gone])
        await _soft_delete(http_client, gone)

        response = await http_client.get(f"/api/v1/memories/{root}/links?include_obsolete=true")

        assert response.status_code == 200, response.text
        linked = {m["id"]: m["is_obsolete"] for m in response.json()["linked_memories"]}
        assert linked == {alive: False, gone: True}

    async def test_limit_counts_only_returned_links(self, http_client):
        root, gone, first_alive, second_alive = await _create_memories(http_client, 4)
        await _link(http_client, root, [gone, first_alive, second_alive])
        await _soft_delete(http_client, gone)

        response = await http_client.get(f"/api/v1/memories/{root}/links?limit=2")

        assert response.status_code == 200, response.text
        assert [m["id"] for m in response.json()["linked_memories"]] == [first_alive, second_alive]


class TestPostMemoryLinksValidation:
    """POST /api/v1/memories/{id}/links request validation."""

    @pytest.mark.parametrize("bad_related_ids", [5, "abc", "13", ["x", None], [1.5], {"a": 1}])
    async def test_invalid_related_ids_are_rejected(self, http_client, bad_related_ids):
        first, second, third = await _create_memories(http_client, 3)

        response = await http_client.post(
            f"/api/v1/memories/{second}/links", json={"related_ids": bad_related_ids},
        )

        assert response.status_code == 400, response.text
        assert await _linked_ids(http_client, second) == []
        assert await _linked_ids(http_client, first) == []
        assert await _linked_ids(http_client, third) == []

    @pytest.mark.parametrize("bad_body", [b"[1, 2]", b'"text"', b"5", b"null", b"not json"])
    async def test_non_object_body_is_rejected(self, http_client, bad_body):
        (memory_id,) = await _create_memories(http_client, 1)

        response = await http_client.post(
            f"/api/v1/memories/{memory_id}/links",
            content=bad_body,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400, response.text

    @pytest.mark.parametrize("body", [{}, {"related_ids": []}, {"related_ids": None}])
    async def test_missing_or_empty_related_ids_are_rejected(self, http_client, body):
        (memory_id,) = await _create_memories(http_client, 1)

        response = await http_client.post(f"/api/v1/memories/{memory_id}/links", json=body)

        assert response.status_code == 400, response.text
        assert response.json()["error"] == "related_ids is required"

    async def test_valid_related_ids_still_link(self, http_client):
        source, first, second = await _create_memories(http_client, 3)

        response = await http_client.post(
            f"/api/v1/memories/{source}/links", json={"related_ids": [first, second]},
        )

        assert response.status_code == 200, response.text
        assert response.json() == {"linked_ids": [first, second]}
        assert await _linked_ids(http_client, source) == [first, second]

    async def test_linking_a_memory_to_itself_is_rejected(self, http_client):
        source, other = await _create_memories(http_client, 2)

        response = await http_client.post(
            f"/api/v1/memories/{source}/links", json={"related_ids": [source, other]},
        )

        assert response.status_code == 400, response.text
        assert "itself" in str(response.json()["error"])
        assert await _linked_ids(http_client, source) == []

    async def test_unknown_memory_is_not_found(self, http_client):
        (target,) = await _create_memories(http_client, 1)

        response = await http_client.post("/api/v1/memories/99999/links", json={"related_ids": [target]})

        assert response.status_code == 404, response.text
