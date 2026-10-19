"""Ratchet baselines for the whole-project gates that cannot be strict on day one.

A baselined gate compares its findings with ``scripts/quality/baselines/<gate>.json`` and fails
only on findings that are *new* or *worse* than the recorded ones, so existing debt does not block
unrelated work while no new debt can enter. The keys carry no line numbers (an edit above a
finding must not turn it into a "new" one):

* ``count`` baselines map a key to how many findings share it (mypy, bandit, semgrep, vulture);
  a key whose count rises above the baseline, or an unknown key, is a regression.
* ``rank`` baselines map a key to a letter grade, ``A`` best (radon); an unknown key, or a grade
  later in the alphabet than the recorded one, is a regression.

Fixing debt never fails a gate; ``python -m scripts.quality baseline update <gate>`` then
rewrites the file so the fix is locked in. The command refuses to *add* debt unless
``--allow-growth`` is given, and a growing baseline needs a reviewer's explicit agreement
(see docs/quality-gates.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .core import ROOT

BASELINE_DIR = ROOT / "scripts" / "quality" / "baselines"
COUNT = "count"
RANK = "rank"
RANKS = "ABCDEF"
SEPARATOR = "::"
SHOWN = 40  # regressions listed in a failure message

Value = int | str


class BaselineError(Exception):
    """A baseline file is unreadable or does not describe the gate it is named after."""


@dataclass
class Findings:
    """What a tool reported, keyed without line numbers."""

    kind: str
    entries: dict[str, Value] = field(default_factory=dict)
    where: dict[str, list[str]] = field(default_factory=dict)  # key -> "path:line"; display only

    def add(self, key: str, location: str, value: Value = 1) -> None:
        """Count one finding (``count`` kind), or record the grade ``value`` (``rank`` kind)."""
        if self.kind == COUNT:
            self.entries[key] = int(self.entries.get(key, 0)) + 1
        else:
            self.entries[key] = value
        self.where.setdefault(key, []).append(location)

    def total(self) -> int:
        if self.kind == COUNT:
            return sum(int(v) for v in self.entries.values())
        return len(self.entries)


@dataclass
class Regression:
    key: str
    before: Value | None  # None => the finding is not in the baseline at all
    after: Value


@dataclass
class Diff:
    regressions: list[Regression] = field(default_factory=list)
    remaining: int = 0  # baselined findings that are still there
    fixed: int = 0  # baselined findings that are gone or improved

    @property
    def ok(self) -> bool:
        return not self.regressions


def file_of(key: str) -> str:
    return key.partition(SEPARATOR)[0]


def path_for(gate: str) -> Path:
    return BASELINE_DIR / f"{gate}.json"


def _shown(gate: str) -> str:
    path = path_for(gate)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def load(gate: str, kind: str) -> Findings:
    """The recorded baseline; a missing file is an empty one, i.e. the gate is strict."""
    path = path_for(gate)
    if not path.exists():
        return Findings(kind)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = dict(data["findings"])
        recorded = data["kind"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BaselineError(f"{path.name} is not a valid baseline: {exc}") from exc
    if recorded != kind:
        raise BaselineError(f"{path.name} is a {recorded!r} baseline, the gate needs {kind!r}")
    return Findings(kind, entries)


def save(gate: str, findings: Findings) -> Path:
    """Write the baseline deterministically (sorted keys) so reviews see only real changes."""
    path = path_for(gate)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gate": gate,
        "kind": findings.kind,
        "total": findings.total(),
        "findings": dict(sorted(findings.entries.items())),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _rank_index(grade: Value) -> int:
    letter = str(grade)
    return RANKS.index(letter) if letter in RANKS else len(RANKS)


def _compare(kind: str, before: Value | None, after: Value) -> tuple[bool, int, int]:
    """(regressed, still baselined, improved) for one key present in the current findings."""
    if before is None:
        return True, 0, 0
    if kind == COUNT:
        old, new = int(before), int(after)
        return new > old, min(old, new), max(old - new, 0)
    worse = _rank_index(after) > _rank_index(before)
    return worse, 0 if worse else 1, 1 if _rank_index(after) < _rank_index(before) else 0


def _scoped(entries: dict[str, Value], files: list[str] | None) -> dict[str, Value]:
    if files is None:
        return entries
    wanted = set(files)
    return {k: v for k, v in entries.items() if file_of(k) in wanted}


def _fixed_and_gone(kind: str, before: dict[str, Value], now: dict[str, Value]) -> int:
    """Baselined findings that disappeared altogether."""
    gone = [before[key] for key in before if key not in now]
    return sum(int(value) for value in gone) if kind == COUNT else len(gone)


def diff(baseline: Findings, current: Findings, files: list[str] | None = None) -> Diff:
    """Compare ``current`` with ``baseline``; ``files`` restricts both sides to those paths."""
    before = _scoped(baseline.entries, files)
    now = _scoped(current.entries, files)
    result = Diff(fixed=_fixed_and_gone(current.kind, before, now))
    for key in sorted(now):
        regressed, remaining, improved = _compare(current.kind, before.get(key), now[key])
        if regressed:
            result.regressions.append(Regression(key, before.get(key), now[key]))
        result.remaining += remaining
        result.fixed += improved
    return result


def _describe(kind: str, item: Regression) -> str:
    shown = item.key.replace(SEPARATOR, "  ")
    if item.before is None:
        detail = f"x{item.after}" if kind == COUNT else f"rank {item.after}"
        return f"NEW    {shown}  ({detail})"
    if kind == COUNT:
        return f"MORE   {shown}  ({item.before} -> {item.after})"
    return f"WORSE  {shown}  (rank {item.before} -> {item.after})"


def render_failure(gate: str, current: Findings, result: Diff) -> str:
    lines = [f"{gate}: {len(result.regressions)} finding(s) are new or worse than the baseline"]
    for item in result.regressions[:SHOWN]:
        lines.append("  " + _describe(current.kind, item))
        lines.extend(f"      at {place}" for place in current.where.get(item.key, [])[:3])
    if len(result.regressions) > SHOWN:
        lines.append(f"  ... and {len(result.regressions) - SHOWN} more")
    lines.append(
        f"Fix them. {result.remaining} baselined finding(s) are tolerated ({_shown(gate)}).",
    )
    return "\n".join(lines)


def render_success(gate: str, result: Diff) -> str:
    note = f"{result.remaining} baselined finding(s) remain, none new"
    if result.fixed:
        note += (f"; {result.fixed} fixed since the baseline "
                 f"(run `baseline update {gate}` to lock that in)")
    return note


def check(gate: str, current: Findings, files: list[str] | None = None) -> tuple[bool, str]:
    """Gate verdict for ``current`` against the recorded baseline."""
    try:
        recorded = load(gate, current.kind)
    except BaselineError as exc:
        return False, str(exc)
    result = diff(recorded, current, files)
    if result.ok:
        return True, render_success(gate, result)
    return False, render_failure(gate, current, result)


def update(gate: str, current: Findings, *, allow_growth: bool = False) -> tuple[bool, str]:
    """Rewrite the baseline from ``current``; refuses to add debt unless ``allow_growth``."""
    path = path_for(gate)
    first_time = not path.exists()
    try:
        recorded = load(gate, current.kind)
    except BaselineError as exc:
        return False, str(exc)
    result = diff(recorded, current)
    if result.regressions and not first_time and not allow_growth:
        return False, (
            render_failure(gate, current, result)
            + "\nThe baseline would grow, so it was not rewritten. Growth needs a reviewer's "
            "agreement: rerun with --allow-growth and say why in the pull request."
        )
    save(gate, current)
    verb = "created" if first_time else "rewritten"
    return True, (
        f"{gate}: baseline {verb} with {current.total()} finding(s) in {len(current.entries)} "
        f"entries (before: {recorded.total()} in {len(recorded.entries)})"
    )
