"""E2E tests: the throwaway server boots and seeds whatever the host looks like.

Boots the real `forgetful serve` console script as an OS subprocess (file-backed SQLite,
no auth) from hosts that used to break the harness: a shell or user-config dotenv file
restricting the instance's scopes, and an un-activated venv with a proxy configured for
every non-loopback request. Seeding (import_skill) is the canary - it needs the write
scopes and a working harness-to-server connection.
"""
import pytest

from test_harness.config import HarnessConfig
from test_harness.server import ThrowawayForgetful, _ephemeral_port

SKILL = "forgetful-recall"


async def _boot_and_seed(run_dir) -> list[str]:
    server = ThrowawayForgetful(run_dir=run_dir)
    server.start()
    try:
        seeded = await server.seed_skills(HarnessConfig().skills_dir, [SKILL])
    finally:
        server.stop()
    return [skill["name"] for skill in seeded]


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    path = tmp_path / "run"
    path.mkdir()
    return path


@pytest.mark.asyncio
async def test_scopes_exported_in_the_shell_do_not_restrict_the_instance(
    run_dir, monkeypatch,
):
    # Arrange: a developer shell with a read-only instance ceiling exported
    monkeypatch.setenv("FORGETFUL_SCOPES", "read")

    # Act
    seeded = await _boot_and_seed(run_dir)

    # Assert: import_skill needs write:skills, so the instance is unrestricted
    assert seeded == [SKILL]


@pytest.mark.asyncio
async def test_scopes_in_the_user_config_do_not_restrict_the_instance(
    run_dir, tmp_path, monkeypatch,
):
    # Arrange: <config dir>/forgetful/.env is read by Settings whatever the cwd;
    # XDG_CONFIG_HOME stands in for ~/.config so the real one is never touched
    config_home = tmp_path / "xdg"
    (config_home / "forgetful").mkdir(parents=True)
    (config_home / "forgetful" / ".env").write_text("FORGETFUL_SCOPES=read\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.delenv("FORGETFUL_SCOPES", raising=False)

    # Act
    seeded = await _boot_and_seed(run_dir)

    # Assert
    assert seeded == [SKILL]


@pytest.mark.asyncio
async def test_boots_and_seeds_from_an_unactivated_venv_behind_a_proxy(
    run_dir, monkeypatch,
):
    # Arrange: no venv bin dir on PATH (`.venv/bin/python -m pytest`), and a proxy that
    # cannot serve anything - loopback traffic that went through it would fail
    dead_proxy = f"http://127.0.0.1:{_ephemeral_port()}"
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    for var in ("NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy",
                "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HTTP_PROXY", dead_proxy)
    monkeypatch.setenv("http_proxy", dead_proxy)

    # Act
    seeded = await _boot_and_seed(run_dir)

    # Assert
    assert seeded == [SKILL]
