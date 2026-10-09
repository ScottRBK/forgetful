"""Per-skill walkthrough orchestration.

The session runner is injected (anything with `run_session()`'s shape): the real one
execs the agent inside the harness container, writing events.jsonl/debug.log into the
mounted skill dir as the session streams; tests inject a stub that writes scripted
records. The host side owns everything derivable from those files — status, report,
breach scan, meta — so the orchestration is testable with no docker and no model calls.

Trust boundary: harness defects raise; agent-side anomalies (timeout, no result event,
missing/malformed report) become recorded findings in meta.json.
"""
import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from test_harness.config import HarnessConfig
from test_harness.prompts import build_prompt
from test_harness.report import ReportLoad, load_report

_FIXTURE_ORIGIN = "https://github.com/scottrbk/uat-fixture-calc.git"
_FIXTURE_FILES = {
    "README.md": "# uat-fixture-calc\n\nA tiny calculator used as an encoding target.\n",
    "src/calc.py": (
        "def add(a: float, b: float) -> float:\n"
        "    return a + b\n"
        "\n"
        "def divide(a: float, b: float) -> float:\n"
        '    """Raises ZeroDivisionError on b == 0 by design - callers must guard."""\n'
        "    return a / b\n"
    ),
    "pyproject.toml": (
        '[project]\nname = "uat-fixture-calc"\nversion = "0.1.0"\n'
        'description = "Fixture calculator"\n'
    ),
}


@dataclass
class SessionOutcome:
    """How a session ended from the runner's perspective. Infra failures (docker
    daemon gone, exec refused) raise from the runner instead."""

    kind: Literal["ran", "timeout"]
    detail: str = ""


class SessionRunner(Protocol):
    async def run_session(
        self, *, skill: str, skill_dir: Path, workspace: Path, prompt: str, timeout: float,
    ) -> SessionOutcome: ...


@dataclass
class SkillRunResult:
    skill: str
    status: str  # completed | timeout | error
    report_load: ReportLoad
    breaches: list[str] = field(default_factory=list)
    cost: float = 0.0
    duration: float = 0.0
    output_tokens: int = 0
    session_id: str | None = None
    error: str = ""


def prepare_workspace(skill_dir: Path, skill: str, skills_dir: Path) -> Path:
    """Create the agent's working directory: the SKILL.md under review, plus the
    fixture repo when the skill needs an encoding target."""
    workspace = skill_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(skills_dir / skill / "SKILL.md", workspace / "SKILL.md")
    if skill == "forgetful-encode-repo":
        _build_fixture_repo(workspace / "fixture-repo")
    return workspace


def _build_fixture_repo(root: Path) -> None:
    for name, content in _FIXTURE_FILES.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "uat-fixture@localhost")
    git("config", "user.name", "UAT Fixture")
    git("add", "-A")
    git("commit", "-q", "-m", "Initial fixture")
    git("remote", "add", "origin", _FIXTURE_ORIGIN)


def load_events(path: Path) -> list[dict[str, Any]]:
    """Read the runner-written event log. The timeout kill can land mid-write, so a
    torn (unparsable) line is dropped rather than failing the whole session read."""
    if not path.is_file():
        return []
    events = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def scan_for_breaches(events: list[dict[str, Any]]) -> list[str]:
    """Flag tool_use events that look like a forgetful MCP tool: reaching a configured
    forgetful server directly instead of the fenced CLI route. MCP tool names carry no
    spaces; CLI command strings (codex-style tool_use content) always do."""
    breaches = []
    for event in events:
        if event.get("type") != "tool_use":
            continue
        name = (event.get("content") or "").strip()
        if "forgetful" in name.lower() and " " not in name and name.lower() != "forgetful":
            breaches.append(name)
    return breaches


class Walkthrough:
    def __init__(
        self, config: HarnessConfig, runner: SessionRunner, server_url: str, run_dir: Path,
    ):
        self.config = config
        self.runner = runner
        self.server_url = server_url
        self.run_dir = run_dir

    async def run(self) -> list[SkillRunResult]:
        results = [await self.run_skill(skill) for skill in self.config.skills]
        self.write_summary(results)
        return results

    async def run_skill(self, skill: str) -> SkillRunResult:
        # Everything under skills/ is bind-mounted into the container; server-side
        # artifacts (forgetful.db, server.log) stay outside it at the run-dir root.
        skill_dir = self.run_dir / "skills" / skill
        workspace = prepare_workspace(skill_dir, skill, self.config.skills_dir)
        prompt = build_prompt(skill)
        (skill_dir / "prompt.txt").write_text(prompt)
        started = time.time()

        outcome = await self.runner.run_session(
            skill=skill,
            skill_dir=skill_dir,
            workspace=workspace,
            prompt=prompt,
            timeout=self.config.timeout_for(skill),
        )

        events = load_events(skill_dir / "events.jsonl")
        result_events = [e for e in events if e.get("type") == "result"]
        error_events = [e for e in events if e.get("type") == "error"]

        if outcome.kind == "timeout":
            status, error = "timeout", outcome.detail or "session timed out"
        elif error_events:
            status = "error"
            error = "; ".join(e.get("content") or "" for e in error_events)
        elif not any(e.get("content") == "ok" for e in result_events):
            # A turn can truncate with no result and no error yet exit 0 (mem 1690)
            status = "error"
            error = "stream ended without a result event with content 'ok'"
        else:
            status, error = "completed", ""

        terminal = result_events[-1] if result_events else {}
        result = SkillRunResult(
            skill=skill,
            status=status,
            report_load=load_report(workspace / "report.json"),
            breaches=scan_for_breaches(events),
            cost=terminal.get("cost") or 0.0,
            duration=terminal.get("duration") or time.time() - started,
            output_tokens=terminal.get("output_tokens") or 0,
            session_id=terminal.get("session_id"),
            error=error,
        )
        (skill_dir / "meta.json").write_text(json.dumps(self._meta(result, started), indent=2))
        return result

    def _meta(self, result: SkillRunResult, started: float) -> dict[str, Any]:
        return {
            "skill": result.skill,
            "status": result.status,
            "error": result.error,
            "agent_type": self.config.agent_type,
            "model": self.config.model,
            "effort": self.config.effort,
            "surface": self.config.surface,
            "started": started,
            "wall_seconds": round(time.time() - started, 3),
            "duration": result.duration,
            "cost": result.cost,
            "output_tokens": result.output_tokens,
            "session_id": result.session_id,
            "breaches": result.breaches,
            "report_status": result.report_load.status,
            "report_detail": result.report_load.detail,
        }

    def write_summary(self, results: list[SkillRunResult]) -> None:
        summary = {
            "agent_type": self.config.agent_type,
            "model": self.config.model,
            "surface": self.config.surface,
            "server_url": self.server_url,
            "skills": [
                {
                    "skill": r.skill,
                    "status": r.status,
                    "report_status": r.report_load.status,
                    "verdict": r.report_load.report.verdict if r.report_load.report else None,
                    "issues": len(r.report_load.report.issues) if r.report_load.report else None,
                    "breaches": r.breaches,
                    "cost": r.cost,
                    "duration": r.duration,
                }
                for r in results
            ],
        }
        (self.run_dir / "run.json").write_text(json.dumps(summary, indent=2))
