"""E2E tests for the field limits published by GET /.well-known.

A client reads the limits before it writes. Each published limit must be the limit that the
REST API enforces, so a value at the limit is accepted and a value over it is rejected.
"""
import pytest

MEMORY = {
    "title": "Limit check",
    "content": "Content for the limit check.",
    "context": "Published limits must match REST validation",
    "keywords": ["limit"],
    "tags": ["test"],
    "importance": 7,
}
DOCUMENT = {
    "title": "Limit check document",
    "description": "Document for the limit check",
    "content": "Reference content for the limit check.",
}


async def published_limits(http_client) -> dict:
    response = await http_client.get("/.well-known")
    assert response.status_code == 200
    return response.json()["limits"]


def rejected_fields(response) -> list[list[str]]:
    assert response.status_code == 400, response.text[:300]
    return [item["loc"] for item in response.json()["error"]]


@pytest.mark.asyncio
async def test_published_memory_limits_match_rest_validation(http_client):
    # Arrange
    memory = (await published_limits(http_client))["memory"]
    content = memory["content"]["max_length"]
    keywords = memory["keywords"]["max_items"]

    # Act
    at_limit = await http_client.post(
        "/api/v1/memories", json={**MEMORY, "content": "x" * content},
    )
    long_content = await http_client.post(
        "/api/v1/memories", json={**MEMORY, "content": "x" * (content + 1)},
    )
    many_keywords = await http_client.post(
        "/api/v1/memories",
        json={**MEMORY, "keywords": [f"k{index}" for index in range(keywords + 1)]},
    )

    # Assert
    assert at_limit.status_code == 201, at_limit.text[:300]
    assert rejected_fields(long_content) == [["content"]]
    assert rejected_fields(many_keywords) == [["keywords"]]


@pytest.mark.asyncio
async def test_published_document_limit_matches_rest_validation(http_client):
    # Arrange
    title = (await published_limits(http_client))["document"]["title"]["max_length"]

    # Act
    at_limit = await http_client.post(
        "/api/v1/documents", json={**DOCUMENT, "title": "t" * title},
    )
    long_title = await http_client.post(
        "/api/v1/documents", json={**DOCUMENT, "title": "t" * (title + 1)},
    )

    # Assert
    assert at_limit.status_code == 201, at_limit.text[:300]
    assert rejected_fields(long_title) == [["title"]]
