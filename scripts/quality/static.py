"""Static-analysis gates: lint, boundaries, security lint, dead code, complexity, types.

ruff, imports and pylint are strict. The six whole-project gates in ``BASELINED`` (mypy, bandit,
semgrep, vulture, radon-cc, radon-mi) compare their findings with ``baselines/<gate>.json`` and
fail only on findings that are new or worse (see ``baseline.py``).
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass

from . import baseline, parsers
from .baseline import Findings
from .core import (
    PYLINT_PATHS,
    RADON_PATHS,
    ROOT,
    SOURCE_PATHS,
    TYPED_PATHS,
    Ctx,
    Skip,
    capture,
    check,
    docker_ready,
    scoped_paths,
    venv_tool,
)
from .parsers import ToolFailure

SEMGREP_VERSION = "1.181.0"
PYLINT_FAIL_UNDER = "8.0"


@dataclass
class Collected:
    """Current findings of a baselined gate and the files the comparison is limited to."""

    findings: Findings
    files: list[str] | None = None  # None => whole project


def tool_output(argv: list[str], ok_codes: tuple[int, ...] = (0,)) -> str:
    """Run a tool and return its stdout; any exit code outside ``ok_codes`` is a gate failure."""
    code, out, err = capture(argv)
    if code not in ok_codes:
        raise ToolFailure(f"{argv[0]} exited with {code}:\n{out}{err}")
    return out


def gate_ruff(ctx: Ctx) -> tuple[bool, str]:
    return check([*venv_tool("ruff"), "check", *scoped_paths(ctx, ["."], ("",))])


def gate_imports(ctx: Ctx) -> tuple[bool, str]:
    if ctx.scoped and not ctx.py_files(("app/",)):
        raise Skip("no app/ changes")
    return check([*venv_tool("lint-imports"), "--no-cache"])


def gate_pylint(ctx: Ctx) -> tuple[bool, str]:
    paths = scoped_paths(ctx, PYLINT_PATHS, tuple(PYLINT_PATHS))
    argv = [*venv_tool("pylint"), f"--fail-under={PYLINT_FAIL_UNDER}"]
    if ctx.scoped:
        # A score over a handful of changed files is meaningless for convention/refactor
        # messages; those count in the project-wide score checked on push and in CI.
        argv.append("--disable=C,R")
    return check([*argv, *paths])


def collect_mypy(ctx: Ctx) -> Collected:
    if ctx.scoped and not ctx.py_files(tuple(TYPED_PATHS)):
        raise Skip("no typed-path changes")
    # Whole project even for staged files: a changed signature breaks unchanged callers.
    out = tool_output([*venv_tool("mypy"), "--output", "json"], ok_codes=(0, 1))
    return Collected(parsers.parse_mypy(out))


BANDIT_BASE = ["-c", "pyproject.toml", "-q", "-f", "json"]


def collect_bandit(ctx: Ctx) -> Collected:
    if not ctx.scoped:
        out = tool_output([*venv_tool("bandit"), *BANDIT_BASE, "-r", *SOURCE_PATHS], (0, 1))
        return Collected(parsers.parse_bandit(out))
    paths = [f for f in ctx.py_files() if not f.startswith("tests/")]
    if not paths:
        raise Skip("no non-test Python files")
    out = tool_output([*venv_tool("bandit"), *BANDIT_BASE, *paths], (0, 1))
    return Collected(parsers.parse_bandit(out), paths)


def collect_vulture(ctx: Ctx) -> Collected:
    if ctx.scoped and not ctx.py_files():
        raise Skip("no Python changes")
    # Dead-code detection is meaningful only across the whole code base. Exit 3 = dead code found.
    return Collected(parsers.parse_vulture(tool_output([*venv_tool("vulture")], (0, 3))))


def collect_radon_cc(ctx: Ctx) -> Collected:
    paths = scoped_paths(ctx, RADON_PATHS, ("",))
    out = tool_output([*venv_tool("radon"), "cc", "-j", *paths])
    return Collected(parsers.parse_radon_cc(out), paths if ctx.scoped else None)


def collect_radon_mi(ctx: Ctx) -> Collected:
    paths = scoped_paths(ctx, RADON_PATHS, ("",))
    findings, errors = parsers.parse_radon_mi(
        tool_output([*venv_tool("radon"), "mi", "-j", "-s", *paths]),
    )
    if errors:  # a file radon cannot read is a tool problem, not debt: never baselined
        raise ToolFailure("\n".join(errors))
    return Collected(findings, paths if ctx.scoped else None)


def semgrep_cmd() -> list[str]:
    if shutil.which("semgrep"):
        return ["semgrep"]
    if shutil.which("uvx"):
        return ["uvx", "--from", f"semgrep=={SEMGREP_VERSION}", "semgrep"]
    if docker_ready():
        return [
            "docker", "run", "--rm", "-v", f"{ROOT}:/src", "-w", "/src",
            f"semgrep/semgrep:{SEMGREP_VERSION}", "semgrep",
        ]
    raise Skip("semgrep unavailable (install semgrep, uv, or docker)")


def collect_semgrep(ctx: Ctx) -> Collected:
    argv = [
        *semgrep_cmd(), "scan", "--config", ".semgrep", "--metrics=off", "--json", "--quiet",
        "--disable-version-check", "--timeout", "30",
    ]
    for pack in os.environ.get("SEMGREP_PACKS", "").split():  # opt-in extras: no baseline, strict
        argv += ["--config", pack]
    if not ctx.scoped:
        out = tool_output([*argv, *(p for p in SOURCE_PATHS if (ROOT / p).exists())])
        return Collected(parsers.parse_semgrep(out))
    files = [f for f in ctx.py_files() if not f.startswith("tests/")]
    if not files:
        raise Skip("no non-test Python files")
    return Collected(parsers.parse_semgrep(tool_output([*argv, *files])), files)


BASELINED: dict[str, Callable[[Ctx], Collected]] = {
    "mypy": collect_mypy,
    "bandit": collect_bandit,
    "semgrep": collect_semgrep,
    "vulture": collect_vulture,
    "radon-cc": collect_radon_cc,
    "radon-mi": collect_radon_mi,
}


def baselined_gate(gate: str, ctx: Ctx) -> tuple[bool, str]:
    """Run ``gate``'s tool and fail only on findings that are new or worse than its baseline."""
    try:
        collected = BASELINED[gate](ctx)
    except ToolFailure as exc:
        return False, str(exc)
    return baseline.check(gate, collected.findings, collected.files)


def update_baseline(gate: str, *, allow_growth: bool = False) -> tuple[bool, str]:
    """Re-measure ``gate`` over the whole project and rewrite its baseline file."""
    try:
        collected = BASELINED[gate](Ctx(stage="manual", files=None))
    except ToolFailure as exc:
        return False, str(exc)
    return baseline.update(gate, collected.findings, allow_growth=allow_growth)


def gate_mypy(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("mypy", ctx)


def gate_bandit(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("bandit", ctx)


def gate_vulture(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("vulture", ctx)


def gate_radon_cc(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("radon-cc", ctx)


def gate_radon_mi(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("radon-mi", ctx)


def gate_semgrep(ctx: Ctx) -> tuple[bool, str]:
    return baselined_gate("semgrep", ctx)
