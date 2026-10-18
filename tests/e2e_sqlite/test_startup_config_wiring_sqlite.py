"""E2E tests for startup configuration wiring on the in-memory SQLite stack

Provenance defaults (ENCODING_* / AGENT_*) that the settings validator accepts must never
break a create.
"""
import pytest

from app.config.settings import PROVENANCE_MAX_LENGTHS, settings


@pytest.mark.parametrize(("setting", "limit"), sorted(PROVENANCE_MAX_LENGTHS.items()))
async def test_create_succeeds_with_provenance_defaults_at_the_allowed_cap(http_client, monkeypatch, setting, limit):
    """Settings reject over-long provenance defaults up front; a value at the cap must still
    flow through create and be returned (previously over-long values failed after the insert)."""
    monkeypatch.setattr(settings, setting, "v" * limit)

    response = await http_client.post("/api/v1/memories", json={
        "title": "Provenance cap memory",
        "content": "Created with an env provenance default at its maximum length",
        "context": "Boundary of the ENCODING_* / AGENT_* settings",
        "keywords": ["provenance"],
        "tags": ["config"],
        "importance": 5,
    })

    assert response.status_code == 201, response.text
    stored = await http_client.get(f"/api/v1/memories/{response.json()['id']}")
    assert stored.json()[setting.lower()] == "v" * limit
