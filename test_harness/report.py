"""The walkthrough report contract.

The agent ends each skill walkthrough by writing report.json in its workspace. Parsing is
tolerant: a missing or malformed report is a recorded finding about the run (the agent
failed the contract), never a harness crash. The example below is embedded verbatim in the
walkthrough prompt, so the prompt and the parser cannot drift.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from test_harness.safe_io import UnsafePathError, read_bytes

_CONTRACT_EXAMPLE = {
    "skill": "forgetful-example",
    "verdict": "issues",
    "steps": [
        {
            "step": "Step 1 - what the skill asked for",
            "commands": ["the exact command or operation you ran"],
            "observed": "what actually came back",
            "verdict": "ok",
        },
    ],
    "issues": [
        {
            "severity": "major",
            "where": "Step 1",
            "what": "one-sentence statement of the problem",
            "evidence": "the output or behaviour that proves it",
        },
    ],
}


def _lowercase(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value


def _normalize_step_verdict(value: Any) -> Any:
    value = _lowercase(value)
    # The report-level "issues" bleeding into a step is unambiguous in intent
    return "issue" if value == "issues" else value


def _normalize_report_verdict(value: Any) -> Any:
    value = _lowercase(value)
    return "issues" if value == "issue" else value


_SEVERITY_ALIASES = {"trivial": "nit", "critical": "blocker"}


def _normalize_severity(value: Any) -> Any:
    value = _lowercase(value)
    # Only a string can be an alias: a list/dict value is unhashable, and must fall
    # through to the Literal check so it is rejected as a normal schema error
    return _SEVERITY_ALIASES.get(value, value) if isinstance(value, str) else value


class ReportStep(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step: str
    commands: list[str] = []
    observed: str = ""
    verdict: Literal["ok", "issue"] = "ok"

    _normalize_verdict = field_validator("verdict", mode="before")(_normalize_step_verdict)


class ReportIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: Literal["blocker", "major", "minor", "nit"]
    where: str = ""
    what: str
    evidence: str = ""

    _normalize_severity = field_validator("severity", mode="before")(_normalize_severity)


class WalkthroughReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill: str
    verdict: Literal["pass", "issues", "blocked"]
    steps: list[ReportStep] = []
    issues: list[ReportIssue] = []

    _normalize_verdict = field_validator("verdict", mode="before")(_normalize_report_verdict)


@dataclass
class ReportLoad:
    """Outcome of reading an agent-produced report.json."""

    status: Literal["ok", "missing", "invalid_json", "schema_error"]
    report: WalkthroughReport | None = None
    detail: str = ""


def report_contract_example() -> str:
    """The canonical report.json example shown to the walkthrough agent."""
    return json.dumps(_CONTRACT_EXAMPLE, indent=2)


def load_report(path: Path, root: Path | None = None) -> ReportLoad:
    """Read and validate an agent-produced report; failures are findings, not errors.

    `root` is the agent-writable directory the report sits in: a report reached through
    a symlink planted below it is ignored, never read."""
    try:
        raw = json.loads(read_bytes(path, root).decode("utf-8"))
    except (FileNotFoundError, NotADirectoryError):
        return ReportLoad(status="missing", detail=f"no report at {path}")
    except UnsafePathError as exc:
        return ReportLoad(status="missing", detail=f"report ignored: {exc}")
    except (OSError, ValueError, RecursionError) as exc:
        # ValueError covers JSONDecodeError, UnicodeDecodeError and the int digit limit;
        # RecursionError is pathological nesting; OSError an unreadable file
        return ReportLoad(status="invalid_json", detail=str(exc))
    try:
        return ReportLoad(status="ok", report=WalkthroughReport.model_validate(raw))
    except ValidationError as exc:
        return ReportLoad(status="schema_error", detail=str(exc))
