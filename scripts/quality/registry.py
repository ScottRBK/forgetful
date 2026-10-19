"""Gate registry and stage pipelines (cheapest checks first, fail fast)."""

from __future__ import annotations

import os

from . import security, static, testing
from .core import GateFn

GATES: dict[str, tuple[GateFn, str]] = {
    "ruff": (static.gate_ruff, "ruff lint"),
    "imports": (static.gate_imports, "import-linter layer contracts"),
    "bandit": (static.gate_bandit, "bandit security lint (baselined)"),
    "semgrep": (static.gate_semgrep, "semgrep custom rules (baselined)"),
    "vulture": (static.gate_vulture, "dead code (baselined)"),
    "radon-cc": (static.gate_radon_cc, "cyclomatic complexity, nothing new below B (baselined)"),
    "radon-mi": (static.gate_radon_mi, "maintainability index, no new file below A (baselined)"),
    "mypy": (static.gate_mypy, "static typing (baselined)"),
    "pylint": (static.gate_pylint, f"pylint score >= {static.PYLINT_FAIL_UNDER}/10"),
    "snapshots": (testing.gate_snapshots, "syrupy snapshot tests"),
    "tests-fast": (testing.gate_tests_fast, "architecture + integration tests"),
    "gitnexus": (security.gate_gitnexus, "GitNexus change/impact analysis"),
    "tests": (testing.gate_tests, "architecture + integration + SQLite e2e with coverage"),
    "e2e-postgres": (testing.gate_e2e_postgres, "PostgreSQL e2e (docker) with coverage"),
    "coverage": (testing.gate_coverage, "combined line+branch coverage floor (pyproject.toml)"),
    "compat": (testing.gate_compat, f"suites on Python {testing.COMPAT_PYTHON}"),
    "memray": (testing.gate_memray, "memory budgets (pytest-memray)"),
    "trivy": (security.gate_trivy, "trivy vuln/secret/misconfig scan"),
    "qodana": (security.gate_qodana, "Qodana Ultimate Plus (QODANA_TOKEN from .env)"),
    "mutation": (testing.gate_mutation, "mutmut mutation testing (MUTATION=1)"),
}

_STATIC = ["ruff", "imports", "bandit", "semgrep", "vulture", "radon-cc", "radon-mi"]

# Gates inside a group run in parallel; groups run in order and a failed group stops the stage.
STAGES: dict[str, list[list[str]]] = {
    "pre-commit": [
        _STATIC,
        ["mypy", "pylint"],
        ["snapshots", "tests-fast"],
        ["gitnexus"],
    ],
    "pre-push": [
        _STATIC,
        ["mypy", "pylint"],
        ["tests"],
        ["e2e-postgres"],
        ["coverage"],
        ["compat", "memray"],
        ["trivy"],
        ["qodana"],
        ["mutation"],
        ["gitnexus"],
    ],
    "ci": [
        _STATIC,
        ["mypy", "pylint"],
        ["tests"],
        ["e2e-postgres"],
        ["coverage"],
        ["memray"],
        ["trivy"],
    ],
}

# Slow gates that only run when asked for (MUTATION=1 or ONLY=mutation).
OPT_IN = {"mutation"}


def selected(name: str) -> bool:
    skip = {s for s in os.environ.get("SKIP", "").replace(" ", "").split(",") if s}
    only = {s for s in os.environ.get("ONLY", "").replace(" ", "").split(",") if s}
    if name in skip:
        return False
    if only:
        return name in only
    if name == "mutation":
        return os.environ.get("MUTATION") == "1"
    return name not in OPT_IN
