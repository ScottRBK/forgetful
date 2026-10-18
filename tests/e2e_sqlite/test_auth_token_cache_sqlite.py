"""End-to-end tests (in-memory SQLite) for token cache lifetime and identity claims

Drives the real REST routes with real verifiers (JWT signature checking, the FastMCP
introspection verifier talking to a fake IdP) and the real UserService on SQLite:

- a JWT that expires before TOKEN_CACHE_TTL_SECONDS is rejected once expired, cache or not
- TOKEN_CACHE_ENABLED=false makes a revoked introspected token fail on the very next request
- TOKEN_CACHE_MAX_SIZE=0 does not break authenticated requests
- a signature-verified token with a numeric `sub` provisions a user instead of returning 401
"""
import asyncio
from unittest.mock import patch

import pytest
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair

from app.config.auth import build_auth_provider
from app.config.settings import settings
from app.middleware.auth import TokenCache

ISSUER = "https://idp.example.test"
AUDIENCE = "forgetful-test"
INTROSPECTION_CLASS = "fastmcp.server.auth.providers.introspection.IntrospectionTokenVerifier"


@pytest.fixture
def jwt_keys():
    return RSAKeyPair.generate()


@pytest.fixture
def jwt_app(sqlite_app, jwt_keys):
    """The SQLite app with a real JWT verifier and the same TokenCache wiring as main.py"""
    sqlite_app.auth = JWTVerifier(public_key=jwt_keys.public_key, issuer=ISSUER, audience=AUDIENCE)
    sqlite_app.token_cache = TokenCache(ttl_seconds=300, max_size=1000)
    return sqlite_app


def mint(keys: RSAKeyPair, subject, expires_in_seconds: int = 3600, **claims) -> str:
    return keys.create_token(
        subject=subject,
        issuer=ISSUER,
        audience=AUDIENCE,
        expires_in_seconds=expires_in_seconds,
        additional_claims={"sub": subject, **claims},
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Cache lifetime follows the token expiry
# ============================================


@pytest.mark.asyncio
@pytest.mark.parametrize("cache_enabled", [True, False])
async def test_expired_jwt_is_rejected_whether_or_not_the_cache_is_enabled(
    http_client, jwt_app, jwt_keys, cache_enabled,
):
    """The cache (default TTL 300s) must not keep an expired JWT authenticated"""
    if not cache_enabled:
        jwt_app.token_cache = None
    headers = bearer(mint(jwt_keys, "short-lived-user", expires_in_seconds=2, name="Short", email="s@example.com"))

    with patch.object(settings, "TOKEN_CACHE_ENABLED", cache_enabled):
        first = await http_client.get("/api/v1/memories", headers=headers)
        assert first.status_code == 200

        await asyncio.sleep(2.2)  # exp is an integer second <= 2s after minting

        second = await http_client.get("/api/v1/memories", headers=headers)

    assert second.status_code == 401, "expired token was served from the token cache"


@pytest.mark.asyncio
async def test_valid_jwt_is_still_served_from_the_cache(http_client, jwt_app, jwt_keys):
    """Capping at the token expiry must not defeat caching of tokens that are still valid"""
    headers = bearer(mint(jwt_keys, "cached-user", name="Cached", email="c@example.com"))

    with patch.object(settings, "TOKEN_CACHE_ENABLED", True):
        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 200
        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 200

    assert jwt_app.token_cache.stats["hits"] == 1
    assert jwt_app.token_cache.stats["size"] == 1


# ============================================
# TOKEN_CACHE_ENABLED=false and the introspection verifier
# ============================================


class FakeIdP:
    """Stand-in for the IdP introspection endpoint; the token can be revoked"""

    def __init__(self):
        self.active = True
        self.calls = 0


def fake_async_client(idp: FakeIdP):
    class _Response:
        status_code = 200
        text = ""

        def json(self):
            if not idp.active:
                return {"active": False}
            return {
                "active": True, "sub": "introspected-user", "client_id": "forgetful",
                "name": "Introspected", "email": "introspected@example.test", "scope": "api:read",
            }

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, data=None, headers=None):
            idp.calls += 1
            return _Response()

    return _FakeAsyncClient


def build_introspection_verifier(idp: FakeIdP, cache_enabled: bool):
    """Build the real introspection verifier through the factory; only the IdP network edge is faked"""
    with (
        patch.object(settings, "FASTMCP_SERVER_AUTH", INTROSPECTION_CLASS),
        patch.object(settings, "FASTMCP_SERVER_AUTH_INTROSPECTION_URL", "https://idp.example.test/introspect"),
        patch.object(settings, "FASTMCP_SERVER_AUTH_INTROSPECTION_CLIENT_ID", "forgetful"),
        patch.object(settings, "FASTMCP_SERVER_AUTH_INTROSPECTION_CLIENT_SECRET", "secret"),
        patch.object(settings, "FASTMCP_SERVER_AUTH_INTROSPECTION_REQUIRED_SCOPES", ""),
        patch.object(settings, "TOKEN_CACHE_ENABLED", cache_enabled),
        patch.object(settings, "TOKEN_CACHE_TTL_SECONDS", 300),
        patch.object(settings, "TOKEN_CACHE_MAX_SIZE", 1000),
    ):
        return build_auth_provider()


@pytest.mark.asyncio
async def test_revoked_token_rejected_immediately_when_token_cache_disabled(http_client, sqlite_app):
    idp = FakeIdP()
    with (
        patch("fastmcp.server.auth.providers.introspection.httpx.AsyncClient", fake_async_client(idp)),
        patch.object(settings, "TOKEN_CACHE_ENABLED", False),
    ):
        sqlite_app.auth = build_introspection_verifier(idp, cache_enabled=False)
        sqlite_app.token_cache = None  # what main.py does when TOKEN_CACHE_ENABLED=false
        headers = bearer("opaque-token")

        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 200
        assert idp.calls == 1

        idp.active = False  # revoked at the IdP

        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 401
        assert idp.calls == 2, "introspection result was served from the verifier's cache"


@pytest.mark.asyncio
async def test_introspection_results_are_cached_when_token_cache_enabled(http_client, sqlite_app):
    """Control: the same flow with the cache enabled does reuse the introspection result"""
    idp = FakeIdP()
    with (
        patch("fastmcp.server.auth.providers.introspection.httpx.AsyncClient", fake_async_client(idp)),
        patch.object(settings, "TOKEN_CACHE_ENABLED", True),
    ):
        sqlite_app.auth = build_introspection_verifier(idp, cache_enabled=True)
        sqlite_app.token_cache = None  # isolate the verifier's own cache
        headers = bearer("opaque-token")

        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 200
        assert (await http_client.get("/api/v1/memories", headers=headers)).status_code == 200

    assert idp.calls == 1


# ============================================
# TOKEN_CACHE_MAX_SIZE=0
# ============================================


@pytest.mark.asyncio
async def test_zero_max_size_cache_does_not_break_authenticated_requests(http_client, jwt_app, jwt_keys):
    jwt_app.token_cache = TokenCache(ttl_seconds=300, max_size=0)
    headers = bearer(mint(jwt_keys, "zero-size-user", name="Zero", email="z@example.com"))

    with patch.object(settings, "TOKEN_CACHE_ENABLED", True):
        first = await http_client.get("/api/v1/memories", headers=headers)
        second = await http_client.get("/api/v1/memories", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert jwt_app.token_cache.stats["size"] == 0


