"""Harness entrypoint: `uv run python -m test_harness [flags]`.

Exit codes: 0 = every session completed (issues found are the product's problem, not the
harness's); 1 = one or more sessions did not complete (timeout/error) so the UAT is
partial; 2 = harness infrastructure failure (docker/image/container problem, server
boot/seed failed, agent unhealthy).
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path

from test_harness.config import HarnessConfig
from test_harness.container import AgentContainer, ensure_image
from test_harness.server import HarnessInfraError, ThrowawayForgetful
from test_harness.walkthrough import SkillRunResult, Walkthrough


def config_from_argv(argv: list[str]) -> HarnessConfig:
    parser = argparse.ArgumentParser(
        prog="test_harness",
        description="Walk a real agent through the canonical skills against a "
        "throwaway local Forgetful, inside a sandbox container.",
    )
    parser.add_argument("--agent", help="agent-shell agent type (default: opencode)")
    parser.add_argument("--model", help="model to pin (default: opencode-go/deepseek-v4-flash)")
    parser.add_argument("--effort", help="reasoning effort passthrough")
    parser.add_argument("--surface", help="surface to walk (v1: cli)")
    parser.add_argument("--skills", help="comma-separated subset of the walkthrough skills")
    parser.add_argument("--timeout", type=float, help="per-skill timeout in seconds")
    parser.add_argument("--output", type=Path, help="artifacts root (default: test_harness/runs)")
    parser.add_argument(
        "--rebuild-image", action="store_true",
        help="force a rebuild of the sandbox image (it also rebuilds itself when "
        "locked dependencies change)",
    )
    args = parser.parse_args(argv)

    overrides = {
        "agent_type": args.agent,
        "model": args.model,
        "effort": args.effort,
        "surface": args.surface,
        "skills": args.skills,  # raw text: HarnessConfig splits and validates it
        "skill_timeout": args.timeout,
        "output_dir": args.output,
        "rebuild_image": args.rebuild_image or None,
    }
    return HarnessConfig(**{name: value for name, value in overrides.items() if value is not None})


def _print_summary(results: list[SkillRunResult], run_dir: Path) -> None:
    print(f"\n{'skill':<28} {'status':<10} {'report':<12} {'verdict':<8} issues breaches")
    for result in results:
        report = result.report_load
        verdict = report.report.verdict if report.report else "-"
        issues = len(report.report.issues) if report.report else "-"
        print(
            f"{result.skill:<28} {result.status:<10} {report.status:<12} "
            f"{verdict:<8} {issues!s:<6} {len(result.breaches)}",
        )
    print(f"\nartifacts: {run_dir}")


async def _run(config: HarnessConfig) -> int:
    run_dir = config.output_dir / f"{time.strftime('%Y%m%d-%H%M%S')}-{config.agent_type}"
    run_dir.mkdir(parents=True, exist_ok=False)

    ensure_image(rebuild=config.rebuild_image)

    server = ThrowawayForgetful(run_dir=run_dir)
    print("booting throwaway Forgetful ...")
    server.start()
    # From inside the container 127.0.0.1 is the container itself; Docker Desktop
    # routes host.docker.internal back to the WSL host (verified empirically).
    container = AgentContainer(
        config, run_dir,
        server_url=server.url.replace("127.0.0.1", "host.docker.internal"),
    )
    try:
        catalog = sorted(
            path.name for path in config.skills_dir.iterdir()
            if (path / "SKILL.md").is_file()
        )
        print(f"seeding {len(catalog)} skills into the throwaway instance ...")
        await server.seed_skills(config.skills_dir, catalog)

        print("starting sandbox container (installs the working tree) ...")
        await asyncio.to_thread(container.start)
        print(f"preflight: in-container health check for {config.agent_type} / {config.model} ...")
        await asyncio.to_thread(container.health_check)

        walkthrough = Walkthrough(
            config=config, runner=container, server_url=server.url, run_dir=run_dir,
        )
        results = []
        for skill in config.skills:
            print(f"walking {skill} ...")
            results.append(await walkthrough.run_skill(skill))
        walkthrough.write_summary(results)
    finally:
        container.stop()
        server.stop()

    _print_summary(results, run_dir)
    return 0 if all(result.status == "completed" for result in results) else 1


def main(argv: list[str] | None = None) -> int:
    config = config_from_argv(sys.argv[1:] if argv is None else argv)
    try:
        return asyncio.run(_run(config))
    except HarnessInfraError as exc:
        print(f"infra error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
