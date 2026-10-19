"""Integration tests: a token's scope claim must never widen access to the instance ceiling.

Covers how the OAuth access token's scope claim is turned into token scopes and
intersected with the instance ceiling (FORGETFUL_SCOPES):

- unknown scopes next to a recognised one (``openid read``) are ignored, the
  recognised one still narrows access
- a claim with scopes but none recognised denies everything instead of falling
  back to the full ceiling
- the claim may be a space-separated string or a list, under ``scope`` or ``scp``
- a token without any scope claim keeps falling back to the instance ceiling
"""
from unittest.mock import MagicMock, patch

import pytest
from fastmcp.server.auth.auth import AccessToken

from app.models.tool_registry_models import ToolCategory, ToolParameter
from app.routes.mcp.scope_resolver import (
    _extract_token_scopes,
    get_effective_scopes,
    parse_scopes,
    resolve_permitted_tools,
)
from app.routes.mcp.tool_registry import ToolRegistry

ALL_TOOLS = {
    "get_current_user",
    "update_user_notes",
    "query_memory",
    "create_memory",
    "list_projects",
    "create_project",
}
READ_TOOLS = {"get_current_user", "query_memory", "list_projects"}
MEMORY_READ_TOOLS = {"query_memory"}


@pytest.fixture
def registry():
    registry = ToolRegistry()
    params = [ToolParameter(name="ctx", type="Context", description="ctx", required=True)]

    async def noop(**kwargs):
        return {}

    tools = [
        ("get_current_user", ToolCategory.USER, False),
        ("update_user_notes", ToolCategory.USER, True),
        ("query_memory", ToolCategory.MEMORY, False),
        ("create_memory", ToolCategory.MEMORY, True),
        ("list_projects", ToolCategory.PROJECT, False),
        ("create_project", ToolCategory.PROJECT, True),
    ]
    for name, category, mutates in tools:
        registry.register(
            name=name,
            category=category,
            description=name,
            parameters=params,
            returns="Result",
            implementation=noop,
            mutates=mutates,
        )
    return registry


def _make_ctx(registry, instance_scopes: str = "*"):
    scopes = parse_scopes(instance_scopes)
    ctx = MagicMock()
    ctx.fastmcp.registry = registry
    ctx.fastmcp._instance_scopes = scopes
    ctx.fastmcp._instance_permitted_tools = resolve_permitted_tools(scopes, registry)
    return ctx


def _token(claims: dict, scopes: list[str] | None = None) -> AccessToken:
    return AccessToken(
        token="jwt",
        client_id="client",
        scopes=scopes or [],
        claims={"sub": "user-1", **claims},
    )


def _effective(registry, claims: dict, instance_scopes: str = "*", scopes: list[str] | None = None):
    ctx = _make_ctx(registry, instance_scopes)
    with patch(
        "fastmcp.server.dependencies.get_access_token",
        return_value=_token(claims, scopes),
    ):
        permitted, _ = get_effective_scopes(ctx)
    return permitted


class TestUnknownScopesAreIgnored:
    @pytest.mark.parametrize(
        "scope_claim",
        [
            "openid read",
            "read email profile",
            "read offline_access",
            "api://other-api/.default read",
            "  openid   read  ",
        ],
    )
    def test_read_still_narrows_next_to_foreign_scopes(self, registry, scope_claim):
        permitted = _effective(registry, {"scope": scope_claim})
        assert permitted == READ_TOOLS

    def test_category_scope_still_narrows_next_to_foreign_scopes(self, registry):
        permitted = _effective(registry, {"scope": "read:memories email"})
        assert permitted == MEMORY_READ_TOOLS

    def test_invalid_category_next_to_valid_scope_is_dropped_individually(self, registry):
        permitted = _effective(registry, {"scope": "read read:nonexistent delete:memories"})
        assert permitted == READ_TOOLS

    def test_foreign_scopes_never_widen_instance_ceiling(self, registry):
        permitted = _effective(
            registry,
            {"scope": "openid read write"},
            instance_scopes="read",
        )
        assert permitted == READ_TOOLS

    def test_extract_returns_only_recognised_scopes(self, registry):
        ctx = _make_ctx(registry)
        with patch(
            "fastmcp.server.dependencies.get_access_token",
            return_value=_token({"scope": "openid read write:memories profile"}),
        ):
            assert _extract_token_scopes(ctx) == frozenset({"read", "write:memories"})


class TestNothingRecognisedDenies:
    @pytest.mark.parametrize(
        "scope_claim",
        [
            "openid profile",
            "READ",
            "read:memory",
            "api:read api:write",
            "forgetful:read",
        ],
    )
    def test_claim_without_recognised_scope_denies_everything(self, registry, scope_claim):
        permitted = _effective(registry, {"scope": scope_claim})
        assert permitted == set()

    def test_extract_returns_empty_set_not_none(self, registry):
        ctx = _make_ctx(registry)
        with patch(
            "fastmcp.server.dependencies.get_access_token",
            return_value=_token({"scope": "openid profile"}),
        ):
            assert _extract_token_scopes(ctx) == frozenset()

    def test_list_claim_without_recognised_scope_denies_everything(self, registry):
        permitted = _effective(registry, {"scp": ["openid", "profile"]})
        assert permitted == set()

    def test_malformed_claim_type_denies_everything(self, registry):
        permitted = _effective(registry, {"scope": {"read": True}})
        assert permitted == set()


class TestClaimShapes:
    @pytest.mark.parametrize(
        "claims",
        [
            pytest.param({"scope": ["read"]}, id="scope-list"),
            pytest.param({"scope": ["openid", "read"]}, id="scope-list-with-foreign"),
            pytest.param({"scope": ("openid", "read")}, id="scope-tuple"),
            pytest.param({"scope": ["openid read"]}, id="scope-list-space-separated-item"),
            pytest.param({"scp": "read"}, id="scp-string"),
            pytest.param({"scp": "openid read"}, id="scp-string-with-foreign"),
            pytest.param({"scp": ["read"]}, id="scp-list"),
            pytest.param({"scp": ["email", "read"]}, id="scp-list-with-foreign"),
            pytest.param({"scope": "", "scp": ["read"]}, id="empty-scope-falls-back-to-scp"),
        ],
    )
    def test_read_scope_narrows_for_every_claim_shape(self, registry, claims):
        assert _effective(registry, claims) == READ_TOOLS

    def test_scope_claim_takes_precedence_over_scp(self, registry):
        permitted = _effective(registry, {"scope": "read", "scp": ["write"]})
        assert permitted == READ_TOOLS

    def test_comma_separated_token_within_claim_is_still_accepted(self, registry):
        permitted = _effective(registry, {"scope": "read,write:memories openid"})
        assert permitted == READ_TOOLS | {"create_memory"}


class TestNoScopeClaimKeepsInstanceCeiling:
    def test_no_access_token(self, registry):
        ctx = _make_ctx(registry)
        with patch("fastmcp.server.dependencies.get_access_token", return_value=None):
            permitted, scopes = get_effective_scopes(ctx)
        assert permitted == ALL_TOOLS
        assert scopes == frozenset({"*"})

    def test_access_token_lookup_failure(self, registry):
        ctx = _make_ctx(registry)
        with patch(
            "fastmcp.server.dependencies.get_access_token",
            side_effect=RuntimeError("no request context"),
        ):
            permitted, _ = get_effective_scopes(ctx)
        assert permitted == ALL_TOOLS

    @pytest.mark.parametrize(
        "claims",
        [
            pytest.param({}, id="no-claim"),
            pytest.param({"scope": ""}, id="empty-string"),
            pytest.param({"scope": "   "}, id="blank-string"),
            pytest.param({"scope": []}, id="empty-list"),
            pytest.param({"scope": None, "scp": []}, id="null-and-empty"),
        ],
    )
    def test_token_without_scope_claim(self, registry, claims):
        assert _effective(registry, claims) == ALL_TOOLS

    def test_upstream_provider_scopes_on_token_are_not_forgetful_scopes(self, registry):
        # OAuth proxy providers (GitHub, Google) fill AccessToken.scopes with the
        # upstream provider's scopes and carry no scope claim: ceiling applies.
        permitted = _effective(registry, {"login": "octocat"}, scopes=["user", "read:user"])
        assert permitted == ALL_TOOLS

    def test_wildcard_scope_in_claim_keeps_instance_ceiling(self, registry):
        assert _effective(registry, {"scope": "openid *"}) == ALL_TOOLS
        assert _effective(registry, {"scope": "openid *"}, instance_scopes="read") == READ_TOOLS


class TestDenyIsLogged:
    def test_ignored_scopes_are_warned_about_when_nothing_is_recognised(self, registry):
        ctx = _make_ctx(registry)
        with patch(
            "fastmcp.server.dependencies.get_access_token",
            return_value=_token({"scope": "openid profile"}),
        ), patch("app.routes.mcp.scope_resolver.logger") as mock_logger:
            _extract_token_scopes(ctx)
        mock_logger.warning.assert_called_once()
        message = mock_logger.warning.call_args.args[0]
        assert "openid" in message
        assert "denying" in message

    def test_ignored_scopes_next_to_recognised_ones_do_not_warn(self, registry):
        ctx = _make_ctx(registry)
        with patch(
            "fastmcp.server.dependencies.get_access_token",
            return_value=_token({"scope": "openid read"}),
        ), patch("app.routes.mcp.scope_resolver.logger") as mock_logger:
            _extract_token_scopes(ctx)
        mock_logger.warning.assert_not_called()
