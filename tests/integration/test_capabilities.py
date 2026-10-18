"""HTTP capability discovery without initializing database or model services."""

import pytest
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.routing import Mount

from app.config.settings import settings
from app.routes.api import capabilities


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
    assert response.json() == {
        "schema_version": 1,
        "capabilities": {
            "planning": False,
            "skills": False,
            "files": False,
            "activity_stream": False,
        },
    }


@pytest.mark.parametrize(
    "flag, expected",
    [
        ("PLANNING_ENABLED", {
            "planning": True, "skills": False, "files": False, "activity_stream": False,
        }),
        ("SKILLS_ENABLED", {
            "planning": False, "skills": True, "files": False, "activity_stream": False,
        }),
        ("FILES_ENABLED", {
            "planning": False, "skills": False, "files": True, "activity_stream": False,
        }),
        ("ACTIVITY_ENABLED", {
            "planning": False, "skills": False, "files": False, "activity_stream": True,
        }),
    ],
)
async def test_capabilities_map_settings_directly(capability_server, monkeypatch, flag, expected):
    # Arrange
    monkeypatch.setattr(settings, flag, True)
    async with AsyncClient(
        transport=ASGITransport(app=capability_server.http_app()), base_url="http://test",
    ) as client:
        # Act
        response = await client.get("/.well-known")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"schema_version": 1, "capabilities": expected}


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
