"""Native backend mixed-batch policy and genuine request cancellation."""
import pytest

from tests.memory_link_plugin_cases import native_policy_case

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize("operation", ["link", "unlink"])
@pytest.mark.parametrize("mode", ["enforce", "warn"])
async def test_native_mixed_link_policy(sqlite_app, mcp_client, monkeypatch, mode, operation):
    await native_policy_case(sqlite_app, monkeypatch, mode, operation=operation)


async def test_native_link_request_cancellation(sqlite_app, mcp_client, monkeypatch):
    await native_policy_case(sqlite_app, monkeypatch, "enforce", cancel=True)
