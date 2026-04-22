"""Tests for the configurable MAX_GRAPH_LIMIT setting on /api/v1/graph (issue #23).

Replaces the legacy hardcoded 500-node cap with settings.MAX_GRAPH_LIMIT
(default 2000). Verified against the in-memory SQLite e2e fixture so the
tests run by default (no Docker required).

Covers three scenarios:
    1. Default setting value is 2000 and is echoed by the route.
    2. Monkeypatching the setting to a small value is honored.
    3. A client-provided limit below the cap is preserved as-is.
"""
import pytest

from app.config.settings import settings


class TestGraphMaxGraphLimitSetting:
    """Verify /api/v1/graph honors settings.MAX_GRAPH_LIMIT instead of a hardcoded 500 cap."""

    @pytest.mark.asyncio
    async def test_default_max_graph_limit_is_2000(self, http_client):
        """MAX_GRAPH_LIMIT default value is 2000, replacing the legacy 500 cap."""
        assert settings.MAX_GRAPH_LIMIT == 2000, (
            "Default MAX_GRAPH_LIMIT changed unexpectedly; was 500 before issue #23"
        )

        response = await http_client.get("/api/v1/graph?limit=99999")
        assert response.status_code == 200
        meta = response.json()["meta"]
        assert meta["limit"] == 2000, (
            f"Expected meta.limit=2000 (MAX_GRAPH_LIMIT default), got {meta['limit']}"
        )

    @pytest.mark.asyncio
    async def test_setting_override_is_respected(self, http_client, monkeypatch):
        """Overriding settings.MAX_GRAPH_LIMIT is honored by the route."""
        monkeypatch.setattr(settings, "MAX_GRAPH_LIMIT", 50)

        response = await http_client.get("/api/v1/graph?limit=9999")
        assert response.status_code == 200
        meta = response.json()["meta"]
        assert meta["limit"] == 50, (
            f"Expected meta.limit=50 after monkeypatch, got {meta['limit']}"
        )

    @pytest.mark.asyncio
    async def test_user_value_below_cap_is_preserved(self, http_client, monkeypatch):
        """When the client ?limit is below MAX_GRAPH_LIMIT, the client value wins."""
        monkeypatch.setattr(settings, "MAX_GRAPH_LIMIT", 50)

        response = await http_client.get("/api/v1/graph?limit=10")
        assert response.status_code == 200
        meta = response.json()["meta"]
        assert meta["limit"] == 10, (
            f"Expected meta.limit=10 (user value, below cap), got {meta['limit']}"
        )
