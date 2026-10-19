"""Turn the output of a tool into baseline-ready findings (keys without line numbers)."""

from __future__ import annotations

import json
import re
from typing import Any

from .baseline import COUNT, RANK, RANKS, SEPARATOR, Findings

RADON_BAD_CC = "CDEF"
VULTURE_LINE = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<text>.*?) \(\d+% confidence\)$")
VULTURE_UNUSED = re.compile(r"^unused (?P<kind>[a-z ]+?) '(?P<name>.*)'$")


class ToolFailure(Exception):
    """The tool could not run, or printed something other than the format that was asked for."""


def posix(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


def key_of(*parts: str) -> str:
    return SEPARATOR.join(parts)


def loads(text: str, tool: str) -> Any:
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ToolFailure(f"{tool} did not print JSON ({exc}):\n{text[:2000]}") from exc


def parse_mypy(stdout: str) -> Findings:
    """``mypy --output json`` prints one JSON object per line."""
    found = Findings(COUNT)
    for line in stdout.splitlines():
        if not line.startswith("{"):
            continue
        item = loads(line, "mypy")
        if item.get("severity") != "error":
            continue
        path = posix(item["file"])
        found.add(key_of(path, str(item.get("code")), item["message"]), f"{path}:{item['line']}")
    return found


def parse_bandit(stdout: str) -> Findings:
    data = loads(stdout, "bandit")
    if data.get("errors"):
        raise ToolFailure(f"bandit could not analyse some files: {data['errors']}")
    found = Findings(COUNT)
    for item in data["results"]:
        path = posix(item["filename"])
        place = f"{path}:{item['line_number']} {item['issue_text']}"
        found.add(key_of(path, item["test_id"]), place)
    return found


def parse_semgrep(stdout: str) -> Findings:
    data = loads(stdout, "semgrep")
    fatal = [e for e in data.get("errors", []) if e.get("level") == "error"]
    if fatal:  # warn-level entries (a rule timing out on a busy machine) must not flake the gate
        raise ToolFailure(f"semgrep reported errors: {fatal}")
    found = Findings(COUNT)
    for item in data["results"]:
        path = posix(item["path"])
        rule = item["check_id"]
        rule = rule[rule.index("forgetful-"):] if "forgetful-" in rule else rule
        found.add(key_of(path, rule), f"{path}:{item['start']['line']}")
    return found


def parse_vulture(stdout: str) -> Findings:
    """Vulture prints ``file:line: unused <kind> '<name>' (NN% confidence)``, no JSON mode."""
    found = Findings(COUNT)
    for line in stdout.splitlines():
        match = VULTURE_LINE.match(line.strip())
        if not match:
            continue
        path = posix(match["file"])
        unused = VULTURE_UNUSED.match(match["text"])
        kind, name = (unused["kind"], unused["name"]) if unused else ("other", match["text"])
        found.add(key_of(path, kind, name), f"{path}:{match['line']}")
    return found


def _unique(seen: dict[str, int], key: str) -> str:
    """Disambiguate two definitions that share a qualified name (``#2`` for the second)."""
    seen[key] = seen.get(key, 0) + 1
    return key if seen[key] == 1 else f"{key}#{seen[key]}"


def parse_radon_cc(stdout: str) -> Findings:
    """Functions and methods rated C or worse, keyed by their qualified name."""
    found = Findings(RANK)
    seen: dict[str, int] = {}
    for path, blocks in loads(stdout, "radon cc").items():
        for block in sorted(blocks, key=lambda b: b["lineno"]):
            if block.get("type") == "class" or block["rank"] not in RADON_BAD_CC:
                continue
            owner = f"{block['classname']}." if block.get("classname") else ""
            name = owner + block["name"]
            found.add(
                _unique(seen, key_of(posix(path), name)),
                f"{posix(path)}:{block['lineno']} complexity {block['complexity']}",
                block["rank"],
            )
    return found


def parse_radon_mi(stdout: str) -> tuple[Findings, list[str]]:
    """Files below grade A, plus the files radon could not analyse (never baselined)."""
    found = Findings(RANK)
    errors: list[str] = []
    for path, info in loads(stdout, "radon mi").items():
        if "error" in info:
            errors.append(f"{posix(path)}: radon could not analyse it ({info['error']})")
        elif info["rank"] != RANKS[0]:
            found.add(key_of(posix(path)), f"{posix(path)} MI {info['mi']:.2f}", info["rank"])
    return found, errors
