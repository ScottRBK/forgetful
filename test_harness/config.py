"""Harness configuration: init kwargs (CLI flags) > TEST_HARNESS_* env > defaults.

The walkthrough order is fixed by data dependencies — cli-setup verifies the connection
story first, the write-heavy skills populate the store, then the read skills consume what
they wrote. A skills filter selects from this order; it never reorders it. mcp-setup is
deliberately absent: it belongs to the MCP surface pass, a reserved (unimplemented) axis.
"""
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

    @field_validator("skills_dir", "output_dir")
    @classmethod
    def _absolute(cls, value: Path) -> Path:
        # Bind-mount sources and the `uv build -o` target are handed to other processes
        # (dockerd, a subprocess with another cwd): dockerd reads a source that does not
        # start with "/" as a named volume, so a relative path must be pinned down here.
        return value.expanduser().resolve()

    @field_validator("surface", mode="before")
    @classmethod
    def _only_cli_is_implemented(cls, value: str) -> str:
        if value != "cli":
            raise ValueError(
                f"surface {value!r} is not implemented yet - v1 walks the cli surface only",
            )
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
        return self.skill_timeouts.get(skill, self.skill_timeout)
