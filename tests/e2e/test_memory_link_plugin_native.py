"""Native backend mixed-batch policy and genuine request cancellation."""
import pytest

from tests.memory_link_plugin_cases import native_policy_case

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.e2e
@pytest.mark.parametrize("operation", ["link", "unlink"])
@pytest.mark.parametrize("mode", ["enforce", "warn"])
async def test_native_mixed_link_policy(postgres_app, mcp_client, monkeypatch, mode, operation):
    await native_policy_case(postgres_app, monkeypatch, mode, operation=operation)


@pytest.mark.e2e
async def test_native_link_request_cancellation(postgres_app, mcp_client, monkeypatch):
    await native_policy_case(postgres_app, monkeypatch, "enforce", cancel=True)
