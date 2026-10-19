"""Command line: run stages/gates, install the Git hooks.

    uv run python -m scripts.quality list
    uv run python -m scripts.quality stage pre-commit      # what the hook runs
    uv run python -m scripts.quality stage pre-push
    uv run python -m scripts.quality gate mypy             # one gate, whole project
    uv run python -m scripts.quality gate ruff --staged    # one gate, staged files only
    uv run python -m scripts.quality baseline update mypy  # re-measure a baselined gate's debt
    uv run python -m scripts.quality install               # point core.hooksPath at .githooks

Environment knobs:

    SKIP=a,b         skip the named gates (e.g. SKIP=qodana,trivy git push)
    ONLY=a,b         run only the named gates of the stage
    MUTATION=1       include the (slow) mutation gate in pre-push
    QUALITY_FULL=1   treat pre-commit as project-wide instead of staged-files-only
    SEMGREP_PACKS    extra registry packs, e.g. "p/python p/security-audit" (needs network)
    TRIVY_BIN        explicit trivy binary (otherwise PATH, then the docker image)
    MUTATION_MAX_SURVIVORS  survivors tolerated by the mutation gate (default 0)

Secrets such as QODANA_TOKEN are read from the git-ignored .env file by the gates that
declare them and are never printed.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from . import registry, static
from .core import HOOKS_DIR, ROOT, Ctx, Result, Skip, run, staged_files


def run_gate(name: str, ctx: Ctx) -> Result:
    fn, _ = registry.GATES[name]
    started = time.monotonic()
    try:
        ok, out = fn(ctx)
    except Skip as why:
        return Result(name, "SKIP", time.monotonic() - started, note=str(why))
    # A baselined gate states how much accepted debt is left; other gates stay silent on success.
    note = out.strip() if ok and name in static.BASELINED else ""
    return Result(name, "PASS" if ok else "FAIL", time.monotonic() - started, out, note)


def print_results(results: list[Result]) -> None:
    width = max((len(r.name) for r in results), default=4)
    for r in results:
        tail = f"  ({r.note})" if r.note else ""
        print(f"  {r.status:<4}  {r.name:<{width}}  {r.seconds:6.1f}s{tail}", flush=True)


def print_failures(results: list[Result], limit: int = 80) -> None:
    for r in results:
        if r.status != "FAIL":
            continue
        lines = r.output.rstrip().splitlines()
        print(f"\n--- {r.name} " + "-" * max(0, 60 - len(r.name)))
        if len(lines) > limit:
            print(f"... ({len(lines) - limit} earlier lines omitted)")
        print("\n".join(lines[-limit:]))


def stage_files(stage: str) -> list[str] | None:
    if stage == "pre-commit" and os.environ.get("QUALITY_FULL") != "1":
        return staged_files()
    return None


def run_group(names: list[str], ctx: Ctx) -> list[Result]:
    """Run independent gates concurrently and report them."""
    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        results = list(pool.map(lambda n: run_gate(n, ctx), names))
    print_results(results)
    return results


def run_stage_groups(stage: str, ctx: Ctx) -> bool:
    """Run the stage's selected groups in order; print failures and stop at the first bad group."""
    groups = ([n for n in group if registry.selected(n)] for group in registry.STAGES[stage])
    for names in filter(None, groups):
        results = run_group(names, ctx)
        if any(r.status == "FAIL" for r in results):
            print_failures(results)
            return False
    return True


def run_stage(stage: str) -> int:
    if stage not in registry.STAGES:
        print(f"unknown stage {stage!r}; choose from {', '.join(registry.STAGES)}", file=sys.stderr)
        return 2
    files = stage_files(stage)
    ctx = Ctx(stage=stage, files=files)
    if files is not None and not files:
        print(f"[{stage}] nothing staged; nothing to check")
        return 0
    print(f"[{stage}] {'staged files' if ctx.scoped else 'whole project'}", flush=True)
    if not run_stage_groups(stage, ctx):
        print(f"\n[{stage}] FAILED (bypass a gate with SKIP=<gate>; see docs/quality-gates.md)")
        return 1
    print(f"[{stage}] OK")
    return 0


def run_single(name: str, scope: str, extra: list[str]) -> int:
    if name not in registry.GATES:
        print(f"unknown gate {name!r}; try `list`", file=sys.stderr)
        return 2
    files: list[str] | None = None
    if scope == "staged":
        files = staged_files()
    elif scope == "files":
        files = extra
    result = run_gate(name, Ctx(stage="manual", files=files))
    print_results([result])
    print_failures([result], limit=400)
    return 1 if result.status == "FAIL" else 0


def update_baselines(names: list[str], *, allow_growth: bool) -> int:
    """Re-measure baselined gates over the whole project and rewrite their baseline files."""
    gates = list(static.BASELINED) if names == ["all"] else names
    unknown = [n for n in gates if n not in static.BASELINED]
    if unknown:
        print(f"not baselined gate(s): {', '.join(unknown)}; choose from "
              f"{', '.join(static.BASELINED)} or 'all'", file=sys.stderr)
        return 2
    failed = False
    for name in gates:
        ok, message = static.update_baseline(name, allow_growth=allow_growth)
        print(message, flush=True)
        failed = failed or not ok
    return 1 if failed else 0


def install_hooks() -> int:
    hooks = ROOT / HOOKS_DIR
    if not hooks.is_dir():
        print(f"{HOOKS_DIR}/ not found", file=sys.stderr)
        return 1
    for hook in hooks.iterdir():
        if hook.is_file():
            hook.chmod(hook.stat().st_mode | 0o111)
    code, out = run(["git", "config", "core.hooksPath", HOOKS_DIR])
    print(out.strip() or f"core.hooksPath -> {HOOKS_DIR}")
    return code


def uninstall_hooks() -> int:
    code, out = run(["git", "config", "--unset", "core.hooksPath"])
    print(out.strip() or "core.hooksPath unset")
    return 0 if code in (0, 5) else code


def list_everything() -> int:
    for name, (_, desc) in registry.GATES.items():
        print(f"{name:<14} {desc}{'  [opt-in]' if name in registry.OPT_IN else ''}")
    for stage, groups in registry.STAGES.items():
        print(f"\n{stage}: " + "  ->  ".join("+".join(g) for g in groups))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.quality",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list gates and stages")
    sub.add_parser("install", help="enable the hooks in .githooks/")
    sub.add_parser("uninstall", help="disable the hooks")
    st = sub.add_parser("stage", help="run a stage (pre-commit, pre-push, ci)")
    st.add_argument("stage")
    gt = sub.add_parser("gate", help="run a single gate")
    gt.add_argument("name")
    gt.add_argument("--staged", action="store_true", help="only staged files")
    gt.add_argument("--files", nargs="+", help="only these files")
    bl = sub.add_parser("baseline", help="rewrite the baselines of the ratcheted gates")
    bl.add_argument("action", choices=["update"])
    bl.add_argument("gates", nargs="+", help=f"{', '.join(static.BASELINED)} or 'all'")
    bl.add_argument(
        "--allow-growth", action="store_true",
        help="accept MORE debt than recorded; needs a reviewer's agreement",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "list":
        return list_everything()
    if args.cmd == "install":
        return install_hooks()
    if args.cmd == "uninstall":
        return uninstall_hooks()
    if args.cmd == "stage":
        return run_stage(args.stage)
    if args.cmd == "baseline":
        return update_baselines(args.gates, allow_growth=args.allow_growth)
    scope = "staged" if args.staged else "files" if args.files else "all"
    return run_single(args.name, scope, args.files or [])
