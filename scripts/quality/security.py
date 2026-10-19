"""Supply-chain, deep-analysis and code-graph gates: trivy, Qodana, GitNexus."""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from .core import (
    ROOT,
    Ctx,
    Skip,
    check,
    docker_ready,
    git_lines,
    load_dotenv_values,
    run,
)

QODANA_LINTER = "jetbrains/qodana-python:2026.2"
TRIVY_IMAGE = "aquasec/trivy:latest"


def trivy_cmd() -> list[str]:
    # A dedicated, user-owned cache: the default one is often root-owned after docker runs.
    cache = Path.home() / ".cache" / "forgetful-trivy"
    cache.mkdir(parents=True, exist_ok=True)
    explicit = os.environ.get("TRIVY_BIN")
    found = explicit or shutil.which("trivy")
    if found and Path(found).exists():
        return [found, "--cache-dir", str(cache)]
    if docker_ready():
        user = ["--user", f"{os.getuid()}:{os.getgid()}"] if hasattr(os, "getuid") else []
        return [
            "docker", "run", "--rm", *user,
            "-v", f"{ROOT}:/src", "-v", f"{cache}:/cache", "-w", "/src",
            TRIVY_IMAGE, "--cache-dir", "/cache",
        ]
    raise Skip("trivy unavailable (install trivy or docker)")


def gate_trivy(_ctx: Ctx) -> tuple[bool, str]:
    config = ["--config", "trivy.yaml", "--ignorefile", ".trivyignore"]
    return check([*trivy_cmd(), "fs", *config, "."])


def gate_qodana(_ctx: Ctx) -> tuple[bool, str]:
    if not shutil.which("qodana"):
        raise Skip("qodana CLI not installed")
    secrets = load_dotenv_values(("QODANA_TOKEN",))
    if "QODANA_TOKEN" not in secrets:
        # Like the CI job: not every contributor has a licence, so this is a skip, not a failure.
        raise Skip("QODANA_TOKEN is not set (git-ignored dotenv file or the environment)")
    # Analyse a clean export of HEAD: host virtualenvs and caches mounted into the container
    # leave the Python SDK unresolved and flood the report with false type-hint findings.
    with tempfile.TemporaryDirectory(prefix="qodana-src-") as tmp:
        archive = Path(tmp) / "head.tar"
        code, out = run(["git", "archive", "--format=tar", "-o", str(archive), "HEAD"], timeout=300)
        if code != 0:
            return False, f"could not export HEAD: {out}"
        with tarfile.open(archive) as tar:
            tar.extractall(Path(tmp) / "src", filter="data")
        archive.unlink()
        return check(
            ["qodana", "scan", "--image", QODANA_LINTER, "--project-dir", str(Path(tmp) / "src"),
             "--results-dir", str(ROOT / ".qodana-results"),
             "--cache-dir", str(Path.home() / ".cache" / "qodana")],
            env=secrets,
            timeout=3600,
        )


def gate_gitnexus(ctx: Ctx) -> tuple[bool, str]:
    runner = ROOT / ".gitnexus" / "run.cjs"
    if not runner.exists() or not shutil.which("node"):
        raise Skip("no local GitNexus index (.gitnexus/run.cjs) or node")
    scope = ["--scope", "staged"] if ctx.stage == "pre-commit" else ["--scope", "all"]
    if ctx.stage == "pre-push":
        has_main = git_lines("rev-parse", "--verify", "-q", "origin/main")
        scope = ["--scope", "compare", "--base-ref", "origin/main" if has_main else "HEAD~1"]
    out = ""
    for _ in range(2):  # a partial/truncated answer is "unseen", not "clean": retry once
        code, out = run(
            ["node", str(runner), "detect-changes", *scope, "--repo", str(ROOT)], timeout=300,
        )
        if code != 0:
            return False, out
        if "partial" not in out.lower() and "truncated" not in out.lower():
            return True, out
    return False, "GitNexus change analysis stayed partial/truncated:\n" + out
