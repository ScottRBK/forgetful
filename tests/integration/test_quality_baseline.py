"""Ratchet baselines: new or worse findings fail, fixed ones pass, update rewrites the file."""

import json

import pytest

from scripts.quality import baseline
from scripts.quality.baseline import COUNT, RANK, Findings


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(baseline, "BASELINE_DIR", tmp_path / "baselines")
    return tmp_path / "baselines"


def counted(**entries: int) -> Findings:
    return Findings(COUNT, {k.replace("__", "::"): v for k, v in entries.items()})


def ranked(**entries: str) -> Findings:
    return Findings(RANK, {k.replace("__", "::"): v for k, v in entries.items()})


def test_matching_findings_pass_and_report_what_remains():
    baseline.save("mypy", counted(a__x=2, b__y=1))
    ok, message = baseline.check("mypy", counted(a__x=2, b__y=1))
    assert ok
    assert "3 baselined finding(s) remain, none new" in message


def test_a_new_finding_fails_and_names_where_it_is():
    baseline.save("mypy", counted(a__x=1))
    current = counted(a__x=1, b__new=1)
    current.where["b::new"] = ["b.py:12"]
    ok, message = baseline.check("mypy", current)
    assert not ok
    assert "NEW    b  new" in message
    assert "at b.py:12" in message
    assert "1 baselined finding(s) are tolerated" in message


def test_more_findings_under_an_existing_key_fail():
    baseline.save("bandit", counted(a__B603=1))
    ok, message = baseline.check("bandit", counted(a__B603=2))
    assert not ok
    assert "MORE   a  B603  (1 -> 2)" in message


def test_fixed_findings_pass_and_are_counted():
    baseline.save("vulture", counted(a__x=3, b__y=1))
    ok, message = baseline.check("vulture", counted(a__x=1))
    assert ok
    assert "1 baselined finding(s) remain" in message
    assert "3 fixed since the baseline" in message


def test_a_worse_rank_fails_and_a_better_one_passes():
    baseline.save("radon-cc", ranked(a__f="C", a__g="D"))
    worse = baseline.check("radon-cc", ranked(a__f="D", a__g="D"))
    assert not worse[0]
    assert "WORSE  a  f  (rank C -> D)" in worse[1]
    better = baseline.check("radon-cc", ranked(a__f="B", a__g="D"))
    assert better[0]
    assert "1 fixed" in better[1]


def test_a_new_function_below_the_bar_fails_even_if_others_are_baselined():
    baseline.save("radon-cc", ranked(a__f="C"))
    ok, message = baseline.check("radon-cc", ranked(a__f="C", a__h="C"))
    assert not ok
    assert "NEW    a  h  (rank C)" in message


def test_without_a_baseline_file_a_gate_is_strict():
    assert baseline.check("mypy", counted())[0]
    assert not baseline.check("mypy", counted(a__x=1))[0]


def test_scoped_comparison_only_looks_at_the_given_files():
    baseline.save("bandit", counted(a__B603=1, b__B603=4))
    only_a = counted(a__B603=1)
    ok, message = baseline.check("bandit", only_a, ["a"])
    assert ok
    assert "1 baselined finding(s) remain" in message
    assert "fixed" not in message  # b was simply not scanned
    assert not baseline.check("bandit", counted(a__B603=1, a__B101=1), ["a"])[0]


def test_save_is_deterministic_and_round_trips(store):
    path = baseline.save("mypy", counted(b__y=1, a__x=2))
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    payload = json.loads(text)
    assert list(payload["findings"]) == ["a::x", "b::y"]
    assert payload["total"] == 3
    assert baseline.load("mypy", COUNT).entries == {"a::x": 2, "b::y": 1}
    assert payload["kind"] == COUNT
    assert path.parent == store


def test_a_broken_or_mismatched_baseline_fails_the_gate(store):
    store.mkdir()
    (store / "mypy.json").write_text("{not json", encoding="utf-8")
    ok, message = baseline.check("mypy", counted())
    assert not ok
    assert "not a valid baseline" in message
    baseline.save("radon-cc", ranked(a__f="C"))
    ok, message = baseline.check("radon-cc", counted())
    assert not ok
    assert "needs 'count'" in message


def test_update_rewrites_the_file_with_the_fixed_state():
    baseline.save("mypy", counted(a__x=3, b__y=1))
    ok, message = baseline.update("mypy", counted(a__x=1))
    assert ok
    assert "rewritten with 1 finding(s)" in message
    assert baseline.load("mypy", COUNT).entries == {"a::x": 1}


def test_update_creates_the_first_baseline_with_existing_debt(store):
    ok, message = baseline.update("mypy", counted(a__x=5))
    assert ok
    assert "created with 5 finding(s)" in message
    assert (store / "mypy.json").exists()


def test_update_refuses_to_grow_unless_explicitly_allowed():
    baseline.save("mypy", counted(a__x=1))
    ok, message = baseline.update("mypy", counted(a__x=2, c__z=1))
    assert not ok
    assert "baseline would grow" in message
    assert "--allow-growth" in message
    assert baseline.load("mypy", COUNT).entries == {"a::x": 1}
    ok, _ = baseline.update("mypy", counted(a__x=2, c__z=1), allow_growth=True)
    assert ok
    assert baseline.load("mypy", COUNT).entries == {"a::x": 2, "c::z": 1}


def test_failure_message_is_capped():
    current = counted(**{f"f{i}__r": 1 for i in range(baseline.SHOWN + 5)})
    ok, message = baseline.check("mypy", current)
    assert not ok
    assert "... and 5 more" in message
