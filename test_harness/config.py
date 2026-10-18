"""Harness configuration: init kwargs (CLI flags) > TEST_HARNESS_* env > defaults.

The walkthrough order is fixed by data dependencies — cli-setup verifies the connection
story first, the write-heavy skills populate the store, then the read skills consume what
they wrote. A skills filter selects from this order; it never reorders it. mcp-setup is
deliberately absent: it belongs to the MCP surface pass, a reserved (unimplemented) axis.
"""
import math
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SKILL_ORDER: tuple[str, ...] = (
    "forgetful-cli-setup",
    "forgetful-remember",
    "forgetful-entities",
    "forgetful-procedures",
    "forgetful-files",
    "forgetful-recall",
    "forgetful-explore",
    "forgetful-context-gather",
    "forgetful-encode-repo",
)

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _require_enforceable_timeout(seconds: float) -> float:
    # GNU `timeout 0` means "no limit" and the duration is whole seconds, so anything
    # below 1 (or nan/inf) would silently disable the in-container kill.
    if not (math.isfinite(seconds) and seconds >= 1):
        raise ValueError(f"timeout must be a finite number of seconds >= 1, got {seconds}")
    return seconds


class HarnessConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TEST_HARNESS_", extra="ignore")

    agent_type: str = "opencode"
    model: str = "opencode-go/deepseek-v4-flash"
    effort: str | None = None
    surface: Literal["cli"] = "cli"
    skills: list[str] = list(SKILL_ORDER)
    skill_timeout: float = 900
    skill_timeouts: dict[str, float] = {"forgetful-encode-repo": 1800}
    skills_dir: Path = _REPO_ROOT / "skills"
    output_dir: Path = _REPO_ROOT / "test_harness" / "runs"
    rebuild_image: bool = False

    @field_validator("surface", mode="before")
    @classmethod
    def _only_cli_is_implemented(cls, value: str) -> str:
        if value != "cli":
            raise ValueError(
                f"surface {value!r} is not implemented yet - v1 walks the cli surface only",
            )
        return value

    @field_validator("skill_timeout")
    @classmethod
    def _global_timeout_is_enforceable(cls, value: float) -> float:
        return _require_enforceable_timeout(value)

    @field_validator("skill_timeouts")
    @classmethod
    def _per_skill_timeouts_are_enforceable(cls, value: dict[str, float]) -> dict[str, float]:
        for seconds in value.values():
            _require_enforceable_timeout(seconds)
        return value

    @field_validator("skills")
    @classmethod
    def _subset_of_walkthrough_order(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if name not in SKILL_ORDER]
        if unknown:
            raise ValueError(
                f"unknown skills {unknown} - valid names: {', '.join(SKILL_ORDER)}",
            )
        return [name for name in SKILL_ORDER if name in value]

    def timeout_for(self, skill: str) -> float:
        # An explicit global timeout (flag or env) is the operator's answer for every
        # skill; the built-in per-skill defaults only apply when none was given. Explicit
        # per-skill timeouts still win for their own skill.
        if "skill_timeout" in self.model_fields_set and "skill_timeouts" not in self.model_fields_set:
            return self.skill_timeout
        return self.skill_timeouts.get(skill, self.skill_timeout)
