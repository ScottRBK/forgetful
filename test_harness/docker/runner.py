"""In-container session runner: streams one agent session and persists its events.

Standalone by design — stdlib plus agent_shell (baked into the image) only, so the
host-side harness never imports agent_shell. The event log is the truth artifact:
every event flushes as it arrives, so the external `timeout` kill still leaves
everything observed so far on disk. Session anomalies live in the events; a non-zero
exit from here means the runner itself broke.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

EVENT_FIELDS = ("type", "content", "cost", "duration", "session_id", "output_tokens")


def _shell():
    from agent_shell.models.agent import AgentType
    from agent_shell.shell import AgentShell

    return AgentShell(agent_type=AgentType(os.environ["AGENT_TYPE"]))


async def health() -> None:
    """Verdict via stdout markers, not exit code: agent CLIs (opencode especially)
    print provider errors and exit 0, so the caller reads HEALTHY=/EXCEPTION=."""
    try:
        result = await _shell().health_check(
            cwd="/tmp",
            model=os.environ["AGENT_MODEL"],
            timeout=float(os.environ.get("HEALTH_TIMEOUT", "120")),
        )
    except Exception as exc:  # noqa: BLE001 - any failure is the same verdict here
        print("HEALTHY=False")
        print(f"EXCEPTION={type(exc).__name__}: {exc}")
        return
    print(f"HEALTHY={result.healthy}")
    if not result.healthy:
        print(f"EXCEPTION={result.exception or ''}")


def _attach_debug_log(path: Path) -> None:
    """agent-shell's DEBUG stream carries full command args; tool_use events only
    carry tool names. The debug log is what the post-run analysis greps."""
    logger = logging.getLogger("agent_shell")
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


async def run_session(skill_dir: Path) -> None:
    shell = _shell()
    prompt = (skill_dir / "prompt.txt").read_text(encoding="utf-8")
    _attach_debug_log(skill_dir / "debug.log")
    disallowed = [name for name in os.environ.get("DISALLOWED_TOOLS", "").split(",") if name]
    with (skill_dir / "events.jsonl").open("w", encoding="utf-8") as event_log:
        stream = shell.stream(
            cwd=str(skill_dir / "workspace"),
            prompt=prompt,
            model=os.environ["AGENT_MODEL"],
            effort=os.environ.get("AGENT_EFFORT") or None,
            disallowed_tools=disallowed,
        )
        async for event in stream:
            record = {name: getattr(event, name, None) for name in EVENT_FIELDS}
            event_log.write(json.dumps(record) + "\n")
            event_log.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path)
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    if args.health:
        asyncio.run(health())
    else:
        asyncio.run(run_session(args.skill_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
