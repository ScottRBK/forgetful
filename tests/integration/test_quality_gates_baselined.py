"""Tool output becomes line-number-free findings, and the baselined gates judge them."""

import json

import pytest

from scripts.quality import baseline, cli, core, parsers, static
from scripts.quality.baseline import COUNT, RANK, Findings


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(baseline, "BASELINE_DIR", tmp_path / "baselines")
    return tmp_path / "baselines"


def counted(**entries: int) -> Findings:
    return Findings(COUNT, {k.replace("__", "::"): v for k, v in entries.items()})


def ranked(**entries: str) -> Findings:
    return Findings(RANK, {k.replace("__", "::"): v for k, v in entries.items()})


MYPY_JSON = "\n".join([
    json.dumps({"file": "app/a.py", "line": 3, "code": "attr-defined", "message": "no x", "severity": "error"}),
    json.dumps({"file": "app/a.py", "line": 90, "code": "attr-defined", "message": "no x", "severity": "error"}),
    json.dumps({"file": "app/b.py", "line": 1, "code": "note", "message": "hint", "severity": "note"}),
])


def test_mypy_keys_ignore_line_numbers_and_notes():
    found = parsers.parse_mypy(MYPY_JSON + "\nnot json\n")
    assert found.entries == {"app/a.py::attr-defined::no x": 2}
    assert found.where["app/a.py::attr-defined::no x"] == ["app/a.py:3", "app/a.py:90"]


def test_bandit_and_semgrep_keys_are_file_plus_rule():
    bandit = parsers.parse_bandit(json.dumps({"errors": [], "results": [
        {"filename": "./app/a.py", "test_id": "B603", "line_number": 4, "issue_text": "subprocess"},
        {"filename": "app\\a.py", "test_id": "B603", "line_number": 9, "issue_text": "subprocess"},
    ]}))
    assert bandit.entries == {"app/a.py::B603": 2}
    semgrep = parsers.parse_semgrep(json.dumps({"errors": [], "results": [
        {"path": "app/a.py", "check_id": "x.y.semgrep.forgetful-no-print-in-app", "start": {"line": 7}},
    ]}))
    assert semgrep.entries == {"app/a.py::forgetful-no-print-in-app": 1}


def test_tool_errors_are_not_baselined():
    with pytest.raises(parsers.ToolFailure):
        parsers.parse_bandit(json.dumps({"errors": [{"filename": "x.py"}], "results": []}))
    with pytest.raises(parsers.ToolFailure):
        parsers.parse_semgrep(json.dumps({"errors": [{"level": "error", "type": "boom"}], "results": []}))
    slow = {"errors": [{"level": "warn", "type": "Timeout"}], "results": []}
    assert parsers.parse_semgrep(json.dumps(slow)).entries == {}
    with pytest.raises(parsers.ToolFailure):
        parsers.parse_bandit("Traceback (most recent call last)")


def test_vulture_keys_are_file_kind_and_name():
    text = "\n".join([
        "app/a.py:10: unused function 'old' (60% confidence)",
        "app/a.py:50: unused variable 'x' (60% confidence)",
        "app/a.py:60: unused variable 'x' (60% confidence)",
        "app/a.py:70: unreachable code after 'return' (100% confidence)",
        "ignored line",
    ])
    assert parsers.parse_vulture(text).entries == {
        "app/a.py::function::old": 1,
        "app/a.py::variable::x": 2,
        "app/a.py::other::unreachable code after 'return'": 1,
    }


def test_radon_cc_keys_are_qualified_names_with_a_rank():
    payload = {"app/a.py": [
        {"type": "class", "rank": "F", "name": "Big", "lineno": 1, "complexity": 99},
        {"type": "function", "rank": "B", "name": "ok", "lineno": 5, "complexity": 8},
        {"type": "method", "rank": "C", "name": "go", "classname": "Bad", "lineno": 9, "complexity": 12},
        {"type": "function", "rank": "D", "name": "twin", "lineno": 30, "complexity": 25},
        {"type": "function", "rank": "C", "name": "twin", "lineno": 60, "complexity": 14},
    ]}
    found = parsers.parse_radon_cc(json.dumps(payload))
    assert found.entries == {"app/a.py::Bad.go": "C", "app/a.py::twin": "D", "app/a.py::twin#2": "C"}


def test_radon_mi_reports_grades_below_a_and_unreadable_files():
    payload = {
        "app/a.py": {"mi": 80.0, "rank": "A"},
        "app/b.py": {"mi": 12.5, "rank": "B"},
        "app/c.py": {"error": "invalid syntax"},
    }
    found, errors = parsers.parse_radon_mi(json.dumps(payload))
    assert found.entries == {"app/b.py": "B"}
    assert errors == ["app/c.py: radon could not analyse it (invalid syntax)"]


def fake_capture(code: int, stdout: str, stderr: str = ""):
    def capture(_argv, **_kwargs):
        return code, stdout, stderr

    return capture


def test_gate_uses_the_baseline_and_ignores_unchanged_debt(monkeypatch):
    baseline.save("mypy", counted(**{"app/a.py__attr-defined__no x": 2}))
    monkeypatch.setattr(static, "capture", fake_capture(1, MYPY_JSON))
    ok, message = static.gate_mypy(core.Ctx(stage="ci", files=None))
    assert ok
    assert "2 baselined finding(s) remain" in message
    extra = MYPY_JSON + "\n" + json.dumps(
        {"file": "app/c.py", "line": 1, "code": "arg-type", "message": "bad", "severity": "error"},
    )
    monkeypatch.setattr(static, "capture", fake_capture(1, extra))
    ok, message = static.gate_mypy(core.Ctx(stage="ci", files=None))
    assert not ok
    assert "app/c.py  arg-type  bad" in message


def test_gate_fails_when_the_tool_itself_breaks(monkeypatch):
    monkeypatch.setattr(static, "capture", fake_capture(2, "", "mypy: fatal error"))
    ok, message = static.gate_mypy(core.Ctx(stage="ci", files=None))
    assert not ok
    assert "fatal error" in message


def test_radon_cc_gate_fails_on_new_rank_c_functions_but_not_classes_or_baselined_ones(monkeypatch):
    payload = {"app/x.py": [
        {"type": "class", "rank": "F", "name": "Big", "lineno": 1, "complexity": 99},
        {"type": "function", "rank": "B", "name": "ok", "lineno": 5, "complexity": 8},
        {"type": "method", "rank": "C", "name": "go", "classname": "Bad", "lineno": 9, "complexity": 12},
    ]}
    monkeypatch.setattr(static, "capture", fake_capture(0, json.dumps(payload)))
    ok, message = static.gate_radon_cc(core.Ctx(stage="ci", files=None))
    assert not ok
    assert "Bad.go" in message
    assert "Big" not in message
    baseline.save("radon-cc", ranked(**{"app/x.py__Bad.go": "C"}))
    assert static.gate_radon_cc(core.Ctx(stage="ci", files=None))[0]


def test_radon_mi_gate_fails_on_new_files_below_grade_a(monkeypatch):
    payload = {"app/a.py": {"mi": 80.0, "rank": "A"}, "app/b.py": {"mi": 12.5, "rank": "B"}}
    monkeypatch.setattr(static, "capture", fake_capture(0, json.dumps(payload)))
    ok, message = static.gate_radon_mi(core.Ctx(stage="ci", files=None))
    assert not ok
    assert "app/b.py" in message
    assert "app/a.py" not in message
    baseline.save("radon-mi", ranked(**{"app/b.py": "B"}))
    assert static.gate_radon_mi(core.Ctx(stage="ci", files=None))[0]
    unreadable = {"app/a.py": {"error": "invalid syntax"}}
    monkeypatch.setattr(static, "capture", fake_capture(0, json.dumps(unreadable)))
    ok, message = static.gate_radon_mi(core.Ctx(stage="ci", files=None))
    assert not ok
    assert "radon could not analyse it" in message


def test_scoped_gate_compares_only_the_staged_files(monkeypatch):
    baseline.save("bandit", counted(**{"app/a.py__B603": 1, "app/other.py__B603": 3}))
    report = {"errors": [], "results": [
        {"filename": "app/a.py", "test_id": "B603", "line_number": 4, "issue_text": "subprocess"},
    ]}
    monkeypatch.setattr(static, "capture", fake_capture(1, json.dumps(report)))
    ctx = core.Ctx(stage="pre-commit", files=["app/a.py", "README.md"])
    ok, message = static.gate_bandit(ctx)
    assert ok
    assert "1 baselined finding(s) remain" in message
    with pytest.raises(core.Skip):
        static.gate_bandit(core.Ctx(stage="pre-commit", files=["tests/t.py"]))


def test_cli_update_rewrites_baselines_and_guards_growth(monkeypatch, capsys):
    current = {"value": counted(a__x=1)}
    monkeypatch.setitem(static.BASELINED, "mypy", lambda _ctx: static.Collected(current["value"]))
    assert cli.main(["baseline", "update", "mypy"]) == 0
    assert "mypy: baseline created with 1 finding(s)" in capsys.readouterr().out
    current["value"] = counted(a__x=1, b__y=1)
    assert cli.main(["baseline", "update", "mypy"]) == 1
    assert "baseline would grow" in capsys.readouterr().out
    assert cli.main(["baseline", "update", "mypy", "--allow-growth"]) == 0
    assert baseline.load("mypy", COUNT).total() == 2
    assert cli.main(["baseline", "update", "ruff"]) == 2


def test_a_passing_baselined_gate_prints_its_remaining_debt(monkeypatch, capsys):
    baseline.save("vulture", counted(**{"app/a.py__variable__x": 1}))
    monkeypatch.setattr(static, "capture", fake_capture(3, "app/a.py:1: unused variable 'x' (60% confidence)"))
    assert cli.run_single("vulture", "all", []) == 0
    assert "1 baselined finding(s) remain, none new" in capsys.readouterr().out
