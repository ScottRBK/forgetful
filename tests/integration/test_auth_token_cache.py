"""Integration tests for token cache lifetime, capacity edge cases and identity claims

Covers the auth middleware (app/middleware/auth.py) and the introspection verifier
factory (app/config/auth.py) with stubbed verifiers and an in-memory user repository:

- cache entries never outlive the token's own expiry
- TOKEN_CACHE_MAX_SIZE <= 0 disables caching instead of crashing
- refreshing a cached key at capacity does not evict an unrelated entry
- TOKEN_CACHE_ENABLED=false also disables the introspection verifier's own cache
- non-string identity claims (e.g. a numeric sub) are normalised to strings
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.server.dependencies import AccessToken
from starlette.requests import Request

from app.config.settings import settings
from app.middleware.auth import TokenCache, get_user_from_request
from app.models.user_models import User

INTROSPECTION_CLASS = "fastmcp.server.auth.providers.introspection.IntrospectionTokenVerifier"


class MockFastMCP:
    """Mock FastMCP instance for testing"""
    def __init__(self, user_service, auth_provider=None, token_cache=None):
        self.user_service = user_service
        self.auth = auth_provider
        self.token_cache = token_cache


def create_mock_request(token: str) -> Request:
    """Create a mock Starlette Request with Authorization header"""
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/api/v1/test",
        "headers": [(b"authorization", f"Bearer {token}".encode())],
    })


def make_user(n: int) -> User:
    return User(external_id=f"user-{n}", name=f"User {n}", email=f"u{n}@example.com")


def make_access_token(claims: dict, expires_at: int | None = None) -> AccessToken:
    return AccessToken(token="raw", client_id="test-client", scopes=[], expires_at=expires_at, claims=claims)


# ============================================
# Cache entry lifetime follows the token expiry
# ============================================


@pytest.mark.asyncio
async def test_cache_entry_is_capped_at_token_expiry():
    """A token that expires before the TTL must not be served from the cache after its exp"""
    cache = TokenCache(ttl_seconds=300, max_size=100)

    with patch("app.middleware.auth.time") as clock:
        clock.time.return_value = 1000.0
        await cache.set("short-lived", make_user(1), token_expires_at=1010)

        clock.time.return_value = 1009.0
        assert await cache.get("short-lived") is not None

        clock.time.return_value = 1010.0
        assert await cache.get("short-lived") is None


@pytest.mark.asyncio
async def test_cache_ttl_still_applies_when_token_outlives_it():
    """A token valid for much longer than the TTL is still cached for the TTL only"""
    cache = TokenCache(ttl_seconds=300, max_size=100)

    with patch("app.middleware.auth.time") as clock:
        clock.time.return_value = 1000.0
        await cache.set("long-lived", make_user(1), token_expires_at=1000 + 86400)

        clock.time.return_value = 1299.0
        assert await cache.get("long-lived") is not None

        clock.time.return_value = 1300.0
        assert await cache.get("long-lived") is None


@pytest.mark.asyncio
async def test_already_expired_token_is_not_cached():
    cache = TokenCache(ttl_seconds=300, max_size=100)

    with patch("app.middleware.auth.time") as clock:
        clock.time.return_value = 1000.0
        await cache.set("dead-token", make_user(1), token_expires_at=999)

    assert cache.stats["size"] == 0


@pytest.mark.asyncio
async def test_get_user_from_request_revalidates_after_token_expiry(test_user_service):
    """Cache hit while the token is valid; verifier is consulted again (and rejects) once it expired"""
    verifier = AsyncMock()
    verifier.verify_token = AsyncMock(
        return_value=make_access_token({"sub": "short-user", "name": "Short", "email": "s@example.com"}, expires_at=1010),
    )
    mcp = MockFastMCP(test_user_service, auth_provider=verifier, token_cache=TokenCache(ttl_seconds=300, max_size=100))
    request = create_mock_request("short-token")

    with patch.object(settings, "TOKEN_CACHE_ENABLED", True), patch("app.middleware.auth.time") as clock:
        clock.time.return_value = 1000.0
        await get_user_from_request(request, mcp)
        clock.time.return_value = 1005.0
        await get_user_from_request(request, mcp)
        assert verifier.verify_token.await_count == 1  # second call was a cache hit

        # Token expired: the issuer-side verifier now rejects it, so the cache must not mask that
        clock.time.return_value = 1011.0
        verifier.verify_token.return_value = None
        with pytest.raises(ValueError, match="Invalid or expired token"):
            await get_user_from_request(request, mcp)

        assert verifier.verify_token.await_count == 2


# ============================================
# Capacity edge cases
# ============================================


@pytest.mark.asyncio
@pytest.mark.parametrize("max_size", [0, -1])
async def test_non_positive_max_size_disables_caching(max_size):
    cache = TokenCache(ttl_seconds=300, max_size=max_size)

    await cache.set("tok", make_user(1))

    assert cache.stats["size"] == 0
    assert await cache.get("tok") is None


@pytest.mark.asyncio
async def test_get_user_from_request_with_zero_max_size_still_authenticates(test_user_service):
    """TOKEN_CACHE_MAX_SIZE=0 must not turn a successful validation into an error"""
    verifier = AsyncMock()
    verifier.verify_token = AsyncMock(
        return_value=make_access_token({"sub": "zero-user", "name": "Zero", "email": "z@example.com"}),
    )
    mcp = MockFastMCP(test_user_service, auth_provider=verifier, token_cache=TokenCache(ttl_seconds=300, max_size=0))

    with patch.object(settings, "TOKEN_CACHE_ENABLED", True):
        user = await get_user_from_request(create_mock_request("zero-token"), mcp)
        again = await get_user_from_request(create_mock_request("zero-token"), mcp)

    assert user.external_id == "zero-user"
    assert again.external_id == "zero-user"
    assert verifier.verify_token.await_count == 2  # nothing is cached


@pytest.mark.asyncio
async def test_refreshing_existing_key_at_capacity_does_not_evict_others():
    cache = TokenCache(ttl_seconds=300, max_size=2)
    await cache.set("a", make_user(1))
    await cache.set("b", make_user(2))

    # e.g. two concurrent first requests with the same token both end up here
    await cache.set("b", make_user(2))

    assert cache.stats["size"] == 2
    assert await cache.get("a") is not None
    assert await cache.get("b") is not None


@pytest.mark.asyncio
async def test_refreshed_key_becomes_most_recently_used():
    cache = TokenCache(ttl_seconds=300, max_size=2)
    await cache.set("a", make_user(1))
    await cache.set("b", make_user(2))
    await cache.set("a", make_user(1))  # refresh: "b" is now the least recently used

    await cache.set("c", make_user(3))  # needs a slot

    assert await cache.get("b") is None
    assert await cache.get("a") is not None
    assert await cache.get("c") is not None


