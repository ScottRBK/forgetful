"""Test-driven gates: fast tests, snapshots, coverage, Postgres e2e, py3.14, memory, mutation."""

from __future__ import annotations

import os
import shutil

from .core import (
    SUITES_SQLITE,
    Ctx,
    Skip,
    check,
    docker_ready,
    git_lines,
    run,
    venv_tool,
)

COMPAT_PYTHON = "3.14"
CODE_PREFIXES = ("app/", "tests/", "main.py", "alembic/", "scripts/", "test_harness/")
PYTEST = ["-q", "-p", "no:cacheprovider"]


def check_tests(argv: list[str], **kwargs) -> tuple[bool, str]:
    """Run a test command without the ``GIT_*`` variables a Git hook exports.

    Tests create temporary repositories; inheriting ``GIT_DIR``/``GIT_INDEX_FILE`` would make their
    git commands act on the repository being committed to.
    """
    return check(argv, scrub_git=True, **kwargs)


def gate_snapshots(ctx: Ctx) -> tuple[bool, str]:
    if ctx.scoped and not ctx.py_files(CODE_PREFIXES):
        raise Skip("no code or test changes")
    return check_tests([*venv_tool("pytest"), "-m", "snapshot", *PYTEST])


def gate_tests_fast(ctx: Ctx) -> tuple[bool, str]:
    if ctx.scoped and not ctx.py_files(CODE_PREFIXES):
        raise Skip("no code or test changes")
    return check_tests([*venv_tool("pytest"), "tests/architecture", "tests/integration", "-x", *PYTEST])


def gate_tests(_ctx: Ctx) -> tuple[bool, str]:
    """Architecture + integration + SQLite end-to-end, collecting branch coverage."""
    run([*venv_tool("coverage"), "erase"])
    return check_tests(
        [*venv_tool("pytest"), *SUITES_SQLITE, *PYTEST,
         "--cov", "--cov-branch", "--cov-report=", "--cov-fail-under=0"],
    )


def gate_e2e_postgres(_ctx: Ctx) -> tuple[bool, str]:
    if not docker_ready():
        raise Skip("docker daemon unavailable (PostgreSQL e2e needs it)")
    return check_tests(
        [*venv_tool("pytest"), "tests/e2e", "-m", "e2e", *PYTEST,
         "--cov", "--cov-branch", "--cov-append", "--cov-report=", "--cov-fail-under=0"],
    )


def gate_coverage(_ctx: Ctx) -> tuple[bool, str]:
    # The floor is [tool.coverage.report] fail_under in pyproject.toml, the single place to ratchet.
    return check([*venv_tool("coverage"), "report"])


def gate_compat(_ctx: Ctx) -> tuple[bool, str]:
    if not shutil.which("uv"):
        raise Skip("uv unavailable")
    return check_tests(
        ["uv", "run", "--frozen", "--python", COMPAT_PYTHON, "--all-extras",
         "pytest", *SUITES_SQLITE, *PYTEST],
        env={"UV_PROJECT_ENVIRONMENT": ".venv314"},
    )


def gate_memray(_ctx: Ctx) -> tuple[bool, str]:
    if os.name == "nt":
        raise Skip("memray is not available on Windows")
    return check_tests([*venv_tool("pytest"), "tests/e2e_sqlite", "-m", "memory", "--memray", *PYTEST])


def mutation_targets(ctx: Ctx) -> list[str]:
    """mutmut selects mutants by dotted name pattern; whole-app runs (~33k mutants) are too slow."""
    explicit = os.environ.get("MUTATION_TARGETS", "").split()
    if explicit:
        return explicit
    if ctx.scoped:
        changed = ctx.py_files(("app/",))
    else:  # pre-push / ci: whatever the branch changed relative to main
        diff = git_lines("diff", "--name-only", "--diff-filter=ACMR", "origin/main...HEAD")
        changed = [f for f in diff if f.startswith("app/") and f.endswith(".py")]
    if not changed:
        raise Skip("no changed app/ modules; or set MUTATION_TARGETS='app.utils.*'")
    return [f.removesuffix(".py").replace("/", ".") + ".*" for f in changed]


def mutant_statuses(results: str, targets: list[str]) -> dict[str, str]:
    """`mutmut results` lines ('<dotted name>: <status>') belonging to the targeted modules."""
    prefixes = tuple(t.removesuffix("*") for t in targets)
    found: dict[str, str] = {}
    for line in results.splitlines():
        name, sep, status = line.strip().partition(": ")
        if sep and name.startswith(prefixes):
            found[name] = status.strip()
    return found


def gate_mutation(ctx: Ctx) -> tuple[bool, str]:
    tolerated = int(os.environ.get("MUTATION_MAX_SURVIVORS", "0"))
    targets = mutation_targets(ctx)
    code, out = run([*venv_tool("mutmut"), "run", *targets], timeout=7200, scrub_git=True)
    tail = "\n".join(out.replace("\r", "\n").splitlines()[-40:])
    if code != 0 or "failed to collect stats" in out:
        return False, f"mutmut could not run the test suite (exit {code}):\n{tail}"
    _, results = run([*venv_tool("mutmut"), "results"])
    statuses = mutant_statuses(results, targets)
    untested = [name for name, status in statuses.items() if status == "not checked"]
    if untested:
        header = f"{len(untested)} targeted mutants were never tested (first: {untested[0]}):"
        return False, f"{header}\n{tail}"
    survivors = [f"{name}: {status}" for name, status in statuses.items()]
    if len(survivors) > tolerated:
        header = f"{len(survivors)} mutants not killed (tolerated {tolerated}):\n"
        return False, header + "\n".join(survivors[:200])
    return True, ""
