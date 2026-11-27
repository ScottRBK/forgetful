"""HTTP capability discovery without initializing database or model services."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.routing import Mount

from app.config.settings import settings
from app.routes.api import capabilities

ROOT = Path(__file__).resolve().parents[2]
FLAGS = ("PLANNING_ENABLED", "SKILLS_ENABLED", "FILES_ENABLED", "ACTIVITY_ENABLED")
CORE_LIMITS = {"memory", "entity", "entity_relationship", "document", "code_artifact", "project"}
BOUND_KEYS = {"max_length", "max_items", "max_decoded_bytes"}


@pytest.fixture
def capability_server(monkeypatch):
    """No domain services are attached: discovery must not need or create them."""
    for flag in ("PLANNING_ENABLED", "SKILLS_ENABLED", "FILES_ENABLED", "ACTIVITY_ENABLED"):
        monkeypatch.setattr(settings, flag, False)
    server = FastMCP("Capability test")
    capabilities.register(server)
    return server


@pytest.mark.parametrize("prefix", ["", "/forgetful"])
async def test_capabilities_available_with_all_features_disabled(monkeypatch, prefix):
    # Arrange: use the production routes, without starting the domain runtime.
    for flag in ("PLANNING_ENABLED", "SKILLS_ENABLED", "FILES_ENABLED", "ACTIVITY_ENABLED"):
        monkeypatch.setattr(settings, flag, False)
    import main

    monkeypatch.setattr(main.mcp, "auth", None)
    app = main.mcp.http_app()
    if prefix:
        app = Starlette(routes=[Mount(prefix, app=app)])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        # Act
        response = await client.get(f"{prefix}/.well-known")

    # Assert: the exact public contract, with no settings or user data leaked.
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert set(body) == {"schema_version", "capabilities", "limits"}
    assert body["schema_version"] == 1
    assert body["capabilities"] == {
        "planning": False,
        "skills": False,
        "files": False,
        "activity_stream": False,
    }
    assert set(body["limits"]) == CORE_LIMITS


@pytest.mark.parametrize(
    "flag, expected, feature_limits",
    [
        ("PLANNING_ENABLED", {
            "planning": True, "skills": False, "files": False, "activity_stream": False,
        }, {"plan", "task", "criterion"}),
        ("SKILLS_ENABLED", {
            "planning": False, "skills": True, "files": False, "activity_stream": False,
        }, {"skill", "skill_bundle"}),
        ("FILES_ENABLED", {
            "planning": False, "skills": False, "files": True, "activity_stream": False,
        }, {"file"}),
        ("ACTIVITY_ENABLED", {
            "planning": False, "skills": False, "files": False, "activity_stream": True,
        }, set()),
    ],
)
async def test_capabilities_map_settings_directly(
    capability_server, monkeypatch, flag, expected, feature_limits,
):
    # Arrange
    monkeypatch.setattr(settings, flag, True)
    async with AsyncClient(
        transport=ASGITransport(app=capability_server.http_app()), base_url="http://test",
    ) as client:
        # Act
        response = await client.get("/.well-known")

    # Assert: a disabled feature publishes no limits.
    assert response.status_code == 200
    assert response.json()["capabilities"] == expected
    assert set(response.json()["limits"]) == CORE_LIMITS | feature_limits


async def test_capabilities_read_settings_on_each_request(capability_server, monkeypatch):
    # Arrange
    async with AsyncClient(
        transport=ASGITransport(app=capability_server.http_app()), base_url="http://test",
    ) as client:
        # Act
        before = await client.get("/.well-known")
        monkeypatch.setattr(settings, "PLANNING_ENABLED", True)
        after = await client.get("/.well-known")

    # Assert
    assert before.status_code == after.status_code == 200
    assert before.json()["capabilities"]["planning"] is False
    assert after.json()["capabilities"]["planning"] is True


async def test_capabilities_public_without_weakening_feature_auth(monkeypatch, test_user_service):
    # Arrange: production routes with a real local verifier, no database/model runtime.
    import main

    verifier = StaticTokenVerifier(tokens={
        "test-token": {"client_id": "capability-test", "scopes": [], "sub": "test-user"},
    })
    monkeypatch.setattr(main.mcp, "auth", verifier)
    monkeypatch.setattr(main.mcp, "user_service", test_user_service, raising=False)
    async with AsyncClient(
        transport=ASGITransport(app=main.mcp.http_app()), base_url="http://test",
    ) as client:
        # Act
        anonymous = await client.get("/.well-known")
        authenticated = await client.get(
            "/.well-known", headers={"Authorization": "Bearer test-token"},
        )
        feature = await client.get("/api/v1/memories/1")
        mcp = await client.post("/mcp", json={})

    # Assert
    assert anonymous.status_code == authenticated.status_code == 200
    assert anonymous.json() == authenticated.json()
    assert feature.status_code == mcp.status_code == 401


async def test_limits_publish_only_named_field_bounds(capability_server, monkeypatch):
    # Arrange: every optional feature on, so every limit group is published.
    for flag in FLAGS:
        monkeypatch.setattr(settings, flag, True)
    async with AsyncClient(
        transport=ASGITransport(app=capability_server.http_app()), base_url="http://test",
    ) as client:
        # Act
        response = await client.get("/.well-known")

    # Assert: only bounds for named fields; no tuning settings or other configuration.
    limits = response.json()["limits"]
    assert limits["memory"]["content"].keys() == {"max_length"}
    assert limits["memory"]["keywords"].keys() == {"max_items"}
    assert limits["file"]["data"].keys() == {"max_decoded_bytes"}
    assert limits["skill_bundle"].keys() == {"resources", "content"}
    for group, fields in limits.items():
        for field, bound in fields.items():
            assert bound and set(bound) <= BOUND_KEYS, (group, field, bound)
            assert all(isinstance(value, int) and value > 0 for value in bound.values())


def test_limits_report_values_configured_at_startup():
    # Arrange: a separate process, because field limits are fixed when models are imported.
    script = """
import asyncio, json
from httpx import ASGITransport, AsyncClient
import main

main.mcp.auth = None

async def run():
    app = main.mcp.http_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print(json.dumps((await client.get("/.well-known")).json()["limits"]["memory"]))

asyncio.run(run())
"""
    env = {**os.environ, "MEMORY_CONTENT_MAX_LENGTH": "1000", "MEMORY_KEYWORDS_MAX_COUNT": "4"}

    # Act
    result = subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
        [sys.executable, "-c", script], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=120, check=False,
    )

    # Assert
    assert result.returncode == 0, result.stderr[-2000:]
    memory = json.loads(result.stdout.strip().splitlines()[-1])
    assert memory["content"] == {"max_length": 1000}
    assert memory["keywords"] == {"max_items": 4}
