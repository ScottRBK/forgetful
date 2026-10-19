"""Shared plumbing for the quality gates: context, results, subprocess and git helpers."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - runs the quality tools with fixed argv lists, never a shell
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = ".githooks"

# Static-analysis scopes. Tests are measured by radon (complexity/maintainability) only.
SOURCE_PATHS = ["app", "main.py", "alembic", "test_harness", "scripts"]
RADON_PATHS = [*SOURCE_PATHS, "tests"]
TYPED_PATHS = ["app", "main.py", "scripts"]
PYLINT_PATHS = ["app", "main.py", "test_harness", "scripts"]
SUITES_SQLITE = ["tests/architecture", "tests/integration", "tests/e2e_sqlite"]


@dataclass
class Ctx:
    """What a gate may look at."""

    stage: str
    files: list[str] | None  # None => whole project
    env: dict[str, str] = field(default_factory=dict)

    @property
    def scoped(self) -> bool:
        return self.files is not None

    def py_files(self, prefixes: tuple[str, ...] | None = None) -> list[str]:
        files = [f for f in (self.files or []) if f.endswith(".py")]
        if prefixes:
            files = [f for f in files if f.startswith(prefixes)]
        return files


@dataclass
class Result:
    name: str
    status: str  # PASS | FAIL | SKIP
    seconds: float = 0.0
    output: str = ""
    note: str = ""


class Skip(Exception):  # noqa: N818 - control-flow signal, not an error
    """Raised by a gate that cannot or need not run (reason in args[0])."""


GateFn = Callable[[Ctx], tuple[bool, str]]


def venv_tool(name: str) -> list[str]:
    """Command prefix for a tool installed in the interpreter's environment."""
    exe = Path(sys.executable).with_name(name + (".exe" if os.name == "nt" else ""))
    return [str(exe)] if exe.exists() else [sys.executable, "-m", name]


def capture(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    cwd: Path | None = None,
    scrub_git: bool = False,
) -> tuple[int, str, str]:
    """Run ``argv``; returns (exit code, stdout, stderr) so machine-readable output stays clean.

    ``scrub_git`` drops every ``GIT_*`` variable from the child's environment. A Git hook exports
    ``GIT_INDEX_FILE`` and friends, and test suites that create temporary repositories must not
    inherit them (git would act on the repository being committed to instead).
    """
    base = {k: v for k, v in os.environ.items() if not (scrub_git and k.startswith("GIT_"))}
    merged = {**base, **(env or {})}
    try:
        proc = subprocess.run(  # nosec B603 - gate-defined argv list, no shell, bounded by timeout
            argv,
            cwd=cwd or ROOT,
            env=merged,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, "", f"command not found: {exc.filename}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s: {' '.join(argv)}"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def run(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    cwd: Path | None = None,
    scrub_git: bool = False,
) -> tuple[int, str]:
    code, out, err = capture(argv, env=env, timeout=timeout, cwd=cwd, scrub_git=scrub_git)
    return code, out + err


def check(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    scrub_git: bool = False,
) -> tuple[bool, str]:
    code, out = run(argv, env=env, timeout=timeout, scrub_git=scrub_git)
    return code == 0, out


def git_lines(*args: str) -> list[str]:
    code, out = run(["git", *args], timeout=60)
    return [line for line in out.splitlines() if line.strip()] if code == 0 else []


def staged_files() -> list[str]:
    files = git_lines("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [f for f in files if (ROOT / f).exists()]


def dotenv_paths() -> list[Path]:
    """This checkout's git-ignored dotenv file, then the main worktree's.

    A linked worktree (``git worktree add``) has no dotenv file of its own; the secrets live in the
    main checkout and are read from there in place, never copied.
    """
    paths = [ROOT / ".env"]
    common = git_lines("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common and (main := Path(common[0]).parent / ".env") not in paths:
        paths.append(main)
    return paths


def parse_dotenv(path: Path, keys: tuple[str, ...]) -> dict[str, str]:
    """The requested ``KEY=value`` pairs of one dotenv file (comments and other keys ignored)."""
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for raw in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = raw.strip().partition("=")
        key = key.removeprefix("export ").strip()
        value = value.strip().strip("'\"")
        if sep and key in keys and value:
            found[key] = value
    return found


def load_dotenv_values(keys: tuple[str, ...]) -> dict[str, str]:
    """Return only the requested keys: the process env first, then the dotenv files in order."""
    found = {k: os.environ[k] for k in keys if os.environ.get(k)}
    for path in dotenv_paths():
        for key, value in parse_dotenv(path, keys).items():
            found.setdefault(key, value)
    return found


def docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    code, _ = run(["docker", "info"], timeout=20)
    return code == 0


def scoped_paths(ctx: Ctx, default: list[str], prefixes: tuple[str, ...]) -> list[str]:
    """Whole-project default, or the matching changed files (Skip when none)."""
    if not ctx.scoped:
        return default
    files = ctx.py_files(prefixes)
    if not files:
        raise Skip("no matching staged Python files")
    return files
