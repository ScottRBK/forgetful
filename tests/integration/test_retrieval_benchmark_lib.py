"""Tests for benchmarks/retrieval/eval_lib (no model download)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmarks" / "retrieval"
sys.path.insert(0, str(BENCH))

from eval_lib import (  # noqa: E402
    CuratedQuery,
    corpus_profile,
    d16_antitemplate_metrics,
    load_corpus_jsonl,
    mine_supersession,
    recall_at_k,
    reciprocal_rank,
    render_gate_verdict,
    resolve_ref_placeholders,
    validate_curated_keys,
)


def test_recall_and_mrr_hand_computed() -> None:
    ranked = [10, 20, 30, 40, 50]
    relevant = frozenset({30, 50})
    assert recall_at_k(ranked, relevant, k=3) == 0.5
    assert reciprocal_rank(ranked, relevant) == pytest.approx(1 / 3)


def test_resolve_ref_placeholders() -> None:
    text = "See {{ref:alpha}} and {{ref:beta}} for context."
    resolved = resolve_ref_placeholders(text, {"alpha": 12, "beta": 99})
    assert resolved == "See #12 and #99 for context."


def test_unknown_relevant_keys_raises() -> None:
    curated = [CuratedQuery("q1", "What happened?", ("missing-key",), "en")]
    with pytest.raises(ValueError, match="unknown relevant_keys"):
        validate_curated_keys(curated, known_keys={"other"})


def test_supersession_mining_fixture() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            is_obsolete INTEGER,
            superseded_by INTEGER
        );
        CREATE TABLE vec_memories (memory_id INTEGER PRIMARY KEY);
        """,
    )
    user = "u1"
    rows = [
        (1, user, "Old payout batch sizing note", 1, 2),
        (2, user, "Revised payout batch sizing note", 0, None),
        (3, user, "Short", 1, 4),
        (4, user, "Active replacement for short title", 0, None),
        (5, user, "Standalone active memory about retries", 0, None),
    ]
    conn.executemany(
        "INSERT INTO memories VALUES (?,?,?,?,?)",
        rows,
    )
    conn.executemany("INSERT INTO vec_memories VALUES (?)", [(2,), (4,), (5,)])

    queries = mine_supersession(conn, user_id=user)
    qids = {q.qid for q in queries}
    assert "sup-1" in qids
    assert all(len(q.relevant_ids) == 1 for q in queries)


def test_corpus_profile_four_line_fixture() -> None:
    lines = [
        {
            "key": "a1",
            "title": "DECISION: Keep idempotent webhook handler",
            "content": "We chose PAY-1001 retry semantics. Module billing.core.dispatcher handles it.",
            "context": "Webhook rollout for Acme Example Corp",
            "keywords": ["pay", "webhook", "retry", "idempotent", "dispatch", "queue", "ops"],
            "tags": ["proj-apex-ledger", "webhook", "billing-core"],
            "importance": 8,
        },
        {
            "key": "a2",
            "title": "STATUS: Ledger freeze window",
            "content": "Freeze starts 2026-04-01. Path /srv/ledger/config/freeze.yaml updated.",
            "context": "Quarter close",
            "keywords": ["freeze", "ledger", "yaml", "period", "close", "batch", "window"],
            "tags": ["proj-apex-ledger", "quarter_close", "ops-runbook"],
            "importance": 7,
            "supersedes": "a1",
        },
        {
            "key": "b1",
            "title": "GOTCHA: DriftConsole token refresh",
            "content": "Après le déploiement, vérifier OAuthRefreshManager loop. URL https://api.example.com/oauth",
            "context": "Console auth",
            "keywords": ["oauth", "refresh", "console", "token", "drift", "session", "bug"],
            "tags": ["proj-drift-console", "auth_bug", "oauth-flow"],
            "importance": 9,
        },
        {
            "key": "b2",
            "title": "GOTCHA: DriftConsole token refresh",
            "content": "Near-duplicate distractor about refresh timers, not the OAuth loop fix.",
            "context": "Console auth noise",
            "keywords": ["oauth", "refresh", "console", "timer", "noise", "distractor", "misc"],
            "tags": ["proj-drift-console", "auth_noise", "near-dup"],
            "importance": 7,
        },
    ]
    profile = corpus_profile(lines)
    assert profile["n_lines"] == 4
    assert profile["title_type_prefix_pct"] == 100.0
    assert profile["ticket_key_pct"] == 25.0
    assert profile["ref_placeholder_pct"] == 0.0
    assert profile["supersedes_line_pct"] == 25.0
    assert profile["fr_en_mixed_pct"] == 25.0
    assert profile["near_duplicate_pct"] == 50.0


def test_d16_antitemplate_gates_fixture() -> None:
    good = [
        {
            "key": f"g{i}",
            "title": f"DECISION: Sym{i}-codex-{i:03d}-only",
            "content": f"Unique rationale sentence number {i} explains the trade-off chosen that week.",
            "tags": ["proj-apex-ledger"],
        }
        for i in range(10)
    ]
    metrics = d16_antitemplate_metrics(good)
    assert metrics["d16_title_token_max_share_pct"] <= 15.0
    assert metrics["d16_duplicate_sentence_ge40_count"] == 0
    assert metrics["d16_max_same_content_opening_6w"] <= 3

    dup = good[0]["content"]
    bad = good + [
        {
            "key": "gx",
            "title": "STATUS: Checkout shard canary",
            "content": dup,
            "tags": ["proj-quarry-api"],
        },
    ]
    bad_metrics = d16_antitemplate_metrics(bad)
    assert bad_metrics["d16_duplicate_sentence_ge40_count"] >= 1


def test_load_corpus_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "mini.jsonl"
    row = {"key": "k1", "title": "T", "content": "C", "context": "", "keywords": [], "tags": [], "importance": 8}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    loaded = load_corpus_jsonl(path)
    assert loaded[0]["key"] == "k1"


def test_gate_verdict_omits_absent_curated() -> None:
    ident_h = {"mrr": 0.76, "n": 200}
    ident_v = {"mrr": 0.22, "n": 200}
    sup_h = {"mrr": 0.62, "n": 45}
    sup_v = {"mrr": 0.58, "n": 45}
    skipped = render_gate_verdict(
        {
            "configs": {
                "hybrid": {"groups": {"identifier": ident_h, "supersession": sup_h}},
                "vector": {"groups": {"identifier": ident_v, "supersession": sup_v}},
            },
        },
    )
    assert "curated" not in skipped
    assert "identifier MRR@10 hybrid vs vector" in skipped
    assert "PASS" in skipped
    missing_ident = render_gate_verdict(
        {
            "configs": {
                "hybrid": {"groups": {"supersession": sup_h}},
                "vector": {"groups": {"supersession": sup_v}},
            },
        },
    )
    assert "identifier" in missing_ident
    assert "FAIL" in missing_ident
