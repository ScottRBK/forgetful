"""End-to-end tests: OAuth token scopes must narrow, never widen, the instance ceiling.

Drives the in-process FastMCP app (in-memory SQLite, real meta-tools, real scope
resolver). Access tokens are produced by FastMCP's own JWTVerifier from a signed
JWT, and installed the way the MCP SDK's auth middleware does (auth_context_var).
The instance ceiling is the default FORGETFUL_SCOPES="*".
"""
from contextlib import asynccontextmanager

import pytest
from fastmcp import Client
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser

ISSUER = "https://idp.example.com"

CREATE_MEMORY_ARGS = {
    "title": "Token scope probe",
    "content": "A token without write scope must not be able to create this",
    "context": "token scope e2e test",
    "keywords": ["probe"],
    "tags": ["probe"],
    "importance": 5,
}


async def _access_token_for(claims: dict):
    """Sign a JWT with the given extra claims and let the real verifier build the AccessToken."""
    pair = RSAKeyPair.generate()
    verifier = JWTVerifier(public_key=pair.public_key, issuer=ISSUER)
    jwt = pair.create_token(subject="user-1", issuer=ISSUER, additional_claims=claims)
    access_token = await verifier.load_access_token(jwt)
    assert access_token is not None, "the verifier must accept the token"
    return verifier, access_token


async def _discovered_tools(client) -> list[dict]:
    result = await client.call_tool("discover_forgetful_tools", {})
    return [tool for tools in result.data["tools_by_category"].values() for tool in tools]


async def _execute(client, tool_name: str, arguments: dict):
    return await client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
        raise_on_error=False,
    )


@asynccontextmanager
async def authenticated_client(app, claims: dict):
    """Connect a client while a token verified from the given claims is the current access token."""
    verifier, access_token = await _access_token_for(claims)
    app.auth = verifier
    reset_token = auth_context_var.set(AuthenticatedUser(access_token))
    try:
        async with Client(app) as client:
            yield client
    finally:
        auth_context_var.reset(reset_token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims",
    [
        pytest.param({"scope": "read"}, id="scope-string"),
        pytest.param({"scope": "openid read"}, id="scope-string-with-openid"),
        pytest.param({"scope": "read email profile"}, id="scope-string-with-oidc-scopes"),
        pytest.param({"scope": "read offline_access"}, id="scope-string-with-offline-access"),
        pytest.param({"scope": "api://other-api/.default read"}, id="scope-string-with-other-api"),
        pytest.param({"scope": ["read"]}, id="scope-list"),
        pytest.param({"scp": "read"}, id="scp-string"),
        pytest.param({"scp": ["read"]}, id="scp-list"),
    ],
)
async def test_read_only_token_cannot_write_whatever_the_claim_shape(sqlite_app, claims):
    async with authenticated_client(sqlite_app, claims) as client:
        tools = await _discovered_tools(client)
        mutating = sorted(tool["name"] for tool in tools if tool["mutates"])
        assert tools, "read tools must stay discoverable"
        assert not mutating, f"a read-only token must not see mutating tools, got {mutating[:3]}"

        denied = await _execute(client, "create_memory", dict(CREATE_MEMORY_ARGS))
        assert denied.is_error
        assert "not permitted" in str(denied.content).lower()

        allowed = await _execute(client, "get_current_user", {})
        assert not allowed.is_error


@pytest.mark.asyncio
async def test_category_scope_next_to_foreign_scope_still_limits_to_that_category(sqlite_app):
    async with authenticated_client(sqlite_app, {"scope": "read:memories email"}) as client:
        tools = await _discovered_tools(client)
        assert tools
        assert {tool["category"] for tool in tools} == {"memory"}
        assert not [tool for tool in tools if tool["mutates"]]

        denied = await _execute(client, "get_current_user", {})
        assert denied.is_error
        assert "not permitted" in str(denied.content).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims",
    [
        pytest.param({"scope": "openid profile"}, id="only-oidc-scopes"),
        pytest.param({"scope": "READ"}, id="wrong-case"),
        pytest.param({"scp": ["api://other-api/.default"]}, id="only-other-api-scope"),
    ],
)
async def test_token_scopes_without_any_recognised_scope_deny_everything(sqlite_app, claims):
    async with authenticated_client(sqlite_app, claims) as client:
        assert await _discovered_tools(client) == []

        for tool_name, arguments in (
            ("get_current_user", {}),
            ("create_memory", dict(CREATE_MEMORY_ARGS)),
        ):
            result = await _execute(client, tool_name, arguments)
            assert result.is_error, f"{tool_name} must be refused"
            assert "not permitted" in str(result.content).lower()


@pytest.mark.asyncio
async def test_token_without_scope_claim_keeps_instance_ceiling(sqlite_app):
    async with authenticated_client(sqlite_app, {}) as client:
        tools = await _discovered_tools(client)
        assert any(tool["mutates"] for tool in tools)

        created = await _execute(client, "create_memory", dict(CREATE_MEMORY_ARGS))
        assert not created.is_error
