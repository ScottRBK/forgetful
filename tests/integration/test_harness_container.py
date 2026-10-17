"""Integration tests for the container plumbing (test_harness/container.py).

Everything here is pure host-side mechanics — env fencing, exec command shape,
credential staging, provisioning guards — exercised without a docker daemon. The real
container round-trip is deliberately left to live harness runs, like the agent
walkthrough itself.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

from test_harness.config import HarnessConfig
from test_harness.container import (
    DECOY_DB,
    HARNESS_MOUNT,
    SKILLS_MOUNT,
    build_container_env,
    exec_command,
    provision_agent,
    requirements_hash,
    staged_mount,
)
from test_harness.server import HarnessInfraError

THROWAWAY_URL = "http://host.docker.internal:59999"


@pytest.fixture
def staged():
    """Staging registry that cleans up its /tmp dirs (in production stop() owns this)."""
    dirs: list[Path] = []
    yield dirs
    for staging in dirs:
        shutil.rmtree(staging, ignore_errors=True)


def test_container_env_fences_both_routes():
    # Arrange / Act: the container is born with ONLY this env - the remote route
    # points at the throwaway server and any --local detour lands in a decoy that
    # dies with the container (mem 1701: fence both routes)
    env = build_container_env(THROWAWAY_URL)

    # Assert
    assert env["FORGETFUL_SERVER"] == THROWAWAY_URL
    assert env["DATABASE"] == "SQLite"
    assert env["SQLITE_MEMORY"] == "false"
    assert env["SQLITE_PATH"] == DECOY_DB
    assert env["RERANKING_ENABLED"] == "false"
    assert env["EMBEDDING_PROVIDER"] == "FastEmbed"
    # A fresh container inherits nothing, so there must be no token to scrub - and
    # none accidentally introduced either
    assert "FORGETFUL_TOKEN" not in env


def test_exec_command_wraps_runner_in_os_level_timeout():
    # Arrange: host-side asyncio cancellation cannot kill a process inside the
    # container (mem 1654) - the in-container `timeout` wrapper is the real guard
    config = HarnessConfig()

    # Act
    cmd = exec_command(config.timeout_for("forgetful-recall"), "forgetful-recall")

    # Assert
    assert cmd[:3] == ["timeout", "--kill-after=30s", "900"]
    assert "python" in cmd and "-u" in cmd
    assert f"{HARNESS_MOUNT}/runner.py" in cmd
    assert cmd[-1] == f"{SKILLS_MOUNT}/forgetful-recall"


def test_staged_mount_copies_and_opens_permissions(tmp_path, staged):
    # Arrange: the container's non-root user must traverse the staging dir, and the
    # originals (host secrets) must never be the mounted files
    secret = tmp_path / "auth.json"
    secret.write_text('{"token": "real"}')

    # Act
    volumes = staged_mount([secret], "/home/node/.local/share/opencode", staged)

    # Assert
    (host_dir,) = staged
    assert volumes == {str(host_dir): {"bind": "/home/node/.local/share/opencode", "mode": "rw"}}
    copy = host_dir / "auth.json"
    assert copy.read_text() == '{"token": "real"}'
    assert copy != secret
    if sys.platform != "win32":
        assert host_dir.stat().st_mode & 0o777 == 0o777
        assert copy.stat().st_mode & 0o777 == 0o644


def test_provision_opencode_stages_auth_and_config(tmp_path, staged):
    # Arrange
    auth = tmp_path / "auth.json"
    auth.write_text("{}")

    # Act
    volumes = provision_agent("opencode", staged, auth_path=auth)

    # Assert: credentials + the harness-owned config, both as writable staged copies
    # (agent-shell rewrites config files in place - a read-only bind would break it)
    binds = {spec["bind"] for spec in volumes.values()}
    assert binds == {"/home/node/.local/share/opencode", "/home/node/.config/opencode"}
    assert all(spec["mode"] == "rw" for spec in volumes.values())
    assert len(staged) == 2


def test_provision_opencode_missing_auth_is_infra_error(tmp_path):
    # Arrange
    missing = tmp_path / "auth.json"

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="opencode auth login"):
        provision_agent("opencode", [], auth_path=missing)


def test_provision_unknown_agent_is_infra_error():
    # Act / Assert: v1 containerizes the opencode vertical only
    with pytest.raises(HarnessInfraError, match="opencode"):
        provision_agent("codex", [])


def test_harness_opencode_config_is_strict_json():
    # Arrange: agent-shell round-trips opencode.json through json.loads - JSONC
    # trailing commas break it (mem 1643), and autoupdate must be pinned off so the
    # container does not self-update mid-walkthrough
    config_path = Path("test_harness/docker/opencode.json")

    # Act
    parsed = json.loads(config_path.read_text())

    # Assert
    assert parsed["autoupdate"] is False


def test_requirements_hash_tracks_content():
    # Arrange / Act / Assert: same content -> same tag; any dep change -> new tag
    assert requirements_hash("a==1\n") == requirements_hash("a==1\n")
    assert requirements_hash("a==1\n") != requirements_hash("a==2\n")
