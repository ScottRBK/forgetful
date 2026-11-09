"""Pure helpers for the retrieval benchmark (read-only, no app imports)."""
from __future__ import annotations

import hashlib
import json
import random
import re
import sqlite3
import statistics
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

SUPERSESSION = "supersession"
IDENTIFIER = "identifier"
CURATED = "curated"
TICKET_KEY = "ticket_key"
CODE_SYMBOL = "code_symbol"
MEMORY_REF = "memory_ref"

TICKET_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{1,6}\b")
TICKET_PREFIX_STOPLIST = frozenset({"UTF", "ISO", "SHA", "RFC", "PEP"})
BACKTICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.:\-]{5,59})`")
MEMORY_REF_RE = re.compile(r"(?<![A-Za-z0-9&])#\d{2,5}\b")
REF_PLACEHOLDER_RE = re.compile(r"\{\{ref:([a-z0-9_-]+)\}\}")
SECRET_RE = re.compile(r"(sk-|ghp_|gho_|xox[abpr]-|AKIA|eyJ)")
MAX_TOKEN_LEN = 60
MAX_CHAIN_HOPS = 10
MIN_TITLE_LEN = 8
RANK_DEPTH = 10
TITLE_TYPE_PREFIX_RE = re.compile(r"^(?:[A-Z][A-Z0-9 _\-]{3,}:)")
SNAKE_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
PASCAL_TOKEN_RE = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b")
DOTTED_MODULE_RE = re.compile(r"\b[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]+){2,}\b")
ISO_DATE_RE = re.compile(r"\b20[0-9]{2}-[0-1][0-9]-[0-3][0-9]\b")
POSIX_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/[\w.-]+(?:/[\w.-]+)+\.(?:py|ts|yaml|json|md|toml)\b")
WIN_PATH_RE = re.compile(r"\b[A-Z]:\\[\w\\.-]+\.(?:py|ts|yaml|json|md|toml)\b")
URL_RE = re.compile(r"https?://[\w.-]+\.example\.(?:com|net|org|io)/[\w./?=&%-]*", re.I)
MARKDOWN_LIST_RE = re.compile(r"(?:^|\n)\s*[-*]\s+\S", re.M)
FRENCH_HINT_RE = re.compile(
    r"\b(?:après|avant|donc|également|échec|étape|mémoire|problème|résumé|vérifier)\b",
    re.I,
)
SENTENCE_SPLIT_RE = re.compile(r"[.!?]+\s+")
SNAKE_TAG_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
KEBAB_TAG_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")

MEMORY_CONTENT_MAX_LENGTH = 2000
MEMORY_KEYWORDS_MAX_COUNT = 10
MEMORY_TAGS_MAX_COUNT = 10

TYPE_PREFIX_WORDS = frozenset(
    {
        "decision",
        "pattern",
        "outcome",
        "status",
        "gotcha",
        "runbook",
        "incident",
        "note",
        "weekly",
        "engineering",
    },
)
PROJECT_SLUG_WORDS = frozenset(
    {
        "apex",
        "ledger",
        "drift",
        "console",
        "helix",
        "batch",
        "quarry",
        "api",
        "signal",
        "watch",
        "proj",
    },
)


class HarnessError(Exception):
    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class EvalQuery:
    qid: str
    type: str
    subtype: str | None
    query: str
    relevant_ids: tuple[int, ...]


@dataclass(frozen=True)
class CuratedQuery:
    qid: str
    query: str
    relevant_keys: tuple[str, ...]
    lang: str


def open_readonly(db_path: Path) -> sqlite3.Connection:
    resolved = db_path.resolve()
    uri_path = resolved.as_posix()
    if len(resolved.drive) == 2 and uri_path[1] == ":":
        uri = f"file:///{uri_path}?mode=ro"
    else:
        uri = f"file:{uri_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _dedupe(ranked: Sequence[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for mid in ranked:
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def recall_at_k(ranked: Sequence[int], relevant: frozenset[int], k: int) -> float:
    if not relevant:
        raise ValueError("relevant set must not be empty")
    return len(set(_dedupe(ranked)[:k]) & relevant) / len(relevant)


def first_rank(ranked: Sequence[int], relevant: frozenset[int], depth: int = RANK_DEPTH) -> int | None:
    for position, mid in enumerate(_dedupe(ranked)[:depth], start=1):
        if mid in relevant:
            return position
    return None


def reciprocal_rank(ranked: Sequence[int], relevant: frozenset[int], depth: int = RANK_DEPTH) -> float:
    rank = first_rank(ranked, relevant, depth)
    return 0.0 if rank is None else 1.0 / rank


def is_secret_like(token: str) -> bool:
    return len(token) > MAX_TOKEN_LEN or SECRET_RE.search(token) is not None


def searchable_ids(conn: sqlite3.Connection, user_id: str) -> set[int]:
    active = {
        int(r[0])
        for r in conn.execute(
            "SELECT id FROM memories WHERE is_obsolete = 0 AND user_id = ?",
            (user_id,),
        )
    }
    with_vec = {int(r[0]) for r in conn.execute("SELECT memory_id FROM vec_memories")}  # noqa: S608
    return active & with_vec


def resolve_active_target(next_by_id: dict[int, int], searchable: set[int], start: int) -> int | None:
    seen: set[int] = set()
    current = start
    for _ in range(MAX_CHAIN_HOPS):
        if current in searchable:
            return current
        if current in seen or current not in next_by_id:
            return None
        seen.add(current)
        current = next_by_id[current]
    return None


def mine_supersession(conn: sqlite3.Connection, *, user_id: str) -> list[EvalQuery]:
    searchable = searchable_ids(conn, user_id)
    next_by_id = {
        int(a): int(b)
        for a, b in conn.execute(
            "SELECT id, superseded_by FROM memories WHERE superseded_by IS NOT NULL AND user_id = ?",
            (user_id,),
        )
    }
    rows = conn.execute(
        "SELECT id, title, superseded_by FROM memories "
        "WHERE superseded_by IS NOT NULL AND is_obsolete = 1 AND user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    out: list[EvalQuery] = []
    seen: set[tuple[str, int]] = set()
    for obsolete_id, title, replacement in rows:
        text = (title or "").strip()
        if len(text) < MIN_TITLE_LEN:
            continue
        target = resolve_active_target(next_by_id, searchable, int(replacement))
        if target is None or (text, target) in seen:
            continue
        seen.add((text, target))
        out.append(EvalQuery(f"sup-{obsolete_id}", SUPERSESSION, None, text, (target,)))
    return out


def _qualifies_code_symbol(token: str) -> bool:
    return "_" in token or "." in token or re.search(r"[a-z][A-Z]", token) is not None


def _candidate_tokens(text: str) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {TICKET_KEY: set(), CODE_SYMBOL: set(), MEMORY_REF: set()}
    for tok in TICKET_KEY_RE.findall(text):
        if tok.split("-", 1)[0] not in TICKET_PREFIX_STOPLIST:
            found[TICKET_KEY].add(tok)
    for tok in BACKTICK_RE.findall(text):
        if _qualifies_code_symbol(tok):
            found[CODE_SYMBOL].add(tok)
    found[MEMORY_REF].update(MEMORY_REF_RE.findall(text))
    return found


def _boundary_pattern(token: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])")


def mine_identifiers(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    seed: int,
    cap_per_subtype: int,
    max_df: int,
) -> list[EvalQuery]:
    searchable = searchable_ids(conn, user_id)
    docs: dict[int, str] = {}
    for mid, title, content, keywords in conn.execute(
        "SELECT id, title, content, keywords FROM memories "
        "WHERE is_obsolete = 0 AND user_id = ? ORDER BY id",
        (user_id,),
    ):
        if int(mid) in searchable:
            docs[int(mid)] = "\n".join(str(x) for x in (title or "", content or "", keywords or ""))
    candidates: dict[str, set[str]] = {TICKET_KEY: set(), CODE_SYMBOL: set(), MEMORY_REF: set()}
    for text in docs.values():
        for subtype, toks in _candidate_tokens(text).items():
            candidates[subtype].update(t for t in toks if not is_secret_like(t))
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not crypto
    out: list[EvalQuery] = []
    for subtype in (TICKET_KEY, CODE_SYMBOL, MEMORY_REF):
        pool = sorted(candidates[subtype])
        rng.shuffle(pool)
        kept = 0
        for token in pool:
            if kept >= cap_per_subtype:
                break
            pattern = _boundary_pattern(token)
            relevant = tuple(sorted(mid for mid, text in docs.items() if pattern.search(text)))
            if not 1 <= len(relevant) <= max_df:
                continue
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()[:8]  # noqa: S324 - stable id
            out.append(EvalQuery(f"id-{subtype}-{digest}", IDENTIFIER, subtype, token, relevant))
            kept += 1
    return out


def validate_queries(
    conn: sqlite3.Connection,
    queries: Iterable[EvalQuery],
    *,
    user_id: str,
) -> list[str]:
    searchable = searchable_ids(conn, user_id)
    errors: list[str] = []
    for q in queries:
        missing = [mid for mid in q.relevant_ids if mid not in searchable]
        if not q.relevant_ids or missing:
            errors.append(f"{q.qid}: relevant ids not active+embedded: {missing or 'empty'}")
    return errors


def validate_curated_keys(
    curated: Iterable[CuratedQuery],
    *,
    known_keys: set[str],
) -> None:
    for q in curated:
        unknown = [k for k in q.relevant_keys if k not in known_keys]
        if unknown:
            raise ValueError(f"{q.qid}: unknown relevant_keys: {unknown}")


def resolve_ref_placeholders(text: str, key_to_id: Mapping[str, int]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in key_to_id:
            raise ValueError(f"unknown ref key: {key}")
        return f"#{key_to_id[key]}"

    return REF_PLACEHOLDER_RE.sub(repl, text)


def write_jsonl(path: Path, items: Iterable[EvalQuery | dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for item in items:
        payload = asdict(item) if isinstance(item, EvalQuery) else item
        if isinstance(item, EvalQuery):
            payload["relevant_ids"] = list(item.relevant_ids)
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    body = "\n".join(lines) + ("\n" if lines else "")
    path.write_text(body, encoding="utf-8", newline="\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[EvalQuery]:
    out: list[EvalQuery] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            out.append(
                EvalQuery(
                    raw["qid"],
                    raw["type"],
                    raw.get("subtype"),
                    raw["query"],
                    tuple(int(x) for x in raw["relevant_ids"]),
                ),
            )
    return out


def load_corpus_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_curated_jsonl(path: Path) -> list[CuratedQuery]:
    out: list[CuratedQuery] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        out.append(
            CuratedQuery(
                raw["qid"],
                raw["query"],
                tuple(raw["relevant_keys"]),
                raw.get("lang", "en"),
            ),
        )
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(db_path: Path) -> dict[str, dict | None]:
    out: dict[str, dict | None] = {}
    for suffix in ("", "-wal"):
        p = Path(f"{db_path}{suffix}")
        out[suffix or "main"] = (
            {"sha256": sha256_file(p), "size": p.stat().st_size} if p.is_file() else None
        )
    return out


def _same_source(before: dict, after: dict) -> bool:
    if before["main"] != after["main"]:
        return False
    if before["-wal"] is None:
        return after["-wal"] is None or after["-wal"]["size"] == 0
    return before["-wal"] == after["-wal"]


def backup_copy(source: Path, dest: Path) -> None:
    """Consistent copy through the SQLite backup API; source opened mode=ro."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = open_readonly(source)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


def remove_db_files(db_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{db_path}{suffix}").unlink(missing_ok=True)


def snapshot_db(source: Path, dest: Path, *, retries: int = 3, sleep_s: float = 2.0) -> tuple[dict, dict]:
    if not source.is_file():
        raise HarnessError(f"Database not found: {source}", 2)
    for _attempt in range(retries):
        before = fingerprint(source)
        backup_copy(source, dest)
        after = fingerprint(source)
        if _same_source(before, after):
            return before, after
        remove_db_files(dest)
        time.sleep(sleep_s)
    raise HarnessError("Source DB changed during backup (concurrent writer?). Retry later.", 3)


def bootstrap_ci(values: Sequence[float], *, seed: int, n_resamples: int) -> list[float]:
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)  # noqa: S311 - reproducible resampling
    n = len(values)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(n_resamples))
    return [
        round(means[int(0.025 * (n_resamples - 1))], 4),
        round(means[int(0.975 * (n_resamples - 1))], 4),
    ]


def _group_keys(row: dict) -> list[str]:
    keys = ["overall", row["type"]]
    if row.get("subtype"):
        keys.append(f"{row['type']}/{row['subtype']}")
    return keys


def aggregate(rows: Sequence[dict], *, seed: int, n_resamples: int) -> dict[str, dict]:
    buckets: dict[str, list[dict]] = {}
    for row in rows:
        for key in _group_keys(row):
            buckets.setdefault(key, []).append(row)
    out: dict[str, dict] = {}
    for key in sorted(buckets):
        group = buckets[key]
        stats: dict = {"n": len(group)}
        for metric, field in (("r5", "recall_at_5"), ("r10", "recall_at_10"), ("mrr", "rr")):
            values = [float(r[field]) for r in group]
            stats[metric] = round(statistics.fmean(values), 4)
            stats[f"{metric}_ci"] = bootstrap_ci(values, seed=seed, n_resamples=n_resamples)
        out[key] = stats
    return out


def percentile(values: Sequence[float | int], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    return round(ordered[max(0, min(len(ordered) - 1, int(round(p * (len(ordered) - 1)))))], 1)


def _share(count: int, total: int) -> float:
    return round(100.0 * count / total, 1) if total else 0.0


def _importance_histogram(rows: Sequence[dict]) -> dict[str, float]:
    total = len(rows)
    counts: dict[int, int] = {}
    for row in rows:
        imp = int(row.get("importance", 8))
        counts[imp] = counts.get(imp, 0) + 1
    low = sum(counts.get(i, 0) for i in range(1, 7))
    return {
        "importance_8_pct": _share(counts.get(8, 0), total),
        "importance_7_pct": _share(counts.get(7, 0), total),
        "importance_9_pct": _share(counts.get(9, 0), total),
        "importance_10_pct": _share(counts.get(10, 0), total),
        "importance_1_6_pct": _share(low, total),
    }


def _tag_style_shares(rows: Sequence[dict]) -> dict[str, float]:
    total_tags = 0
    snake = 0
    kebab = 0
    for row in rows:
        for tag in row.get("tags") or []:
            total_tags += 1
            if SNAKE_TAG_RE.match(tag):
                snake += 1
            elif KEBAB_TAG_RE.match(tag):
                kebab += 1
    return {
        "tag_snake_case_pct": _share(snake, total_tags),
        "tag_kebab_pct": _share(kebab, total_tags),
    }


def _title_tokens_for_d16(title: str) -> list[str]:
    stripped = TITLE_TYPE_PREFIX_RE.sub("", str(title or "")).strip()
    tokens: list[str] = []
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9_-]*", stripped):
        low = raw.lower()
        if low in TYPE_PREFIX_WORDS or low in PROJECT_SLUG_WORDS:
            continue
        if low.startswith("proj"):
            continue
        tokens.append(low)
    return tokens


def d16_antitemplate_metrics(rows: Sequence[dict]) -> dict[str, float | int]:
    n = len(rows)
    token_counts: dict[str, int] = {}
    for row in rows:
        for tok in _title_tokens_for_d16(str(row.get("title") or "")):
            token_counts[tok] = token_counts.get(tok, 0) + 1
    max_token_share = _share(max(token_counts.values(), default=0), n)

    sentence_counts: dict[str, int] = {}
    for row in rows:
        content = str(row.get("content") or "")
        for sent in SENTENCE_SPLIT_RE.split(content):
            s = sent.strip()
            if len(s) >= 40:
                sentence_counts[s] = sentence_counts.get(s, 0) + 1
    duplicate_sentences_ge40 = sum(1 for c in sentence_counts.values() if c > 1)

    opening_groups: dict[tuple[str, ...], int] = {}
    for row in rows:
        words = [w for w in re.split(r"\s+", str(row.get("content") or "").strip()) if w][:6]
        if len(words) < 6:
            continue
        key = tuple(w.lower() for w in words)
        opening_groups[key] = opening_groups.get(key, 0) + 1
    max_same_opening_6w = max(opening_groups.values(), default=0)

    return {
        "d16_title_token_max_share_pct": max_token_share,
        "d16_duplicate_sentence_ge40_count": duplicate_sentences_ge40,
        "d16_max_same_content_opening_6w": max_same_opening_6w,
    }


def _near_duplicate_keys(rows: Sequence[dict]) -> set[str]:
    prefix_map: dict[str, list[str]] = {}
    for row in rows:
        title = str(row.get("title") or "")
        prefix = title[:48].strip().lower()
        if len(prefix) < 12:
            continue
        prefix_map.setdefault(prefix, []).append(str(row["key"]))
    dup_keys: set[str] = set()
    for keys in prefix_map.values():
        if len(keys) >= 2:
            dup_keys.update(keys)
    return dup_keys


def _supersedes_chains(rows: Sequence[dict]) -> dict[str, int | list[int]]:
    by_key = {str(r["key"]): r for r in rows}
    chains: list[int] = []
    visited: set[str] = set()
    for row in rows:
        key = str(row["key"])
        if key in visited:
            continue
        if "supersedes" not in row:
            continue
        length = 1
        cur = key
        seen: set[str] = {cur}
        while True:
            sup = by_key.get(cur, {}).get("supersedes")
            if not sup:
                break
            sup_key = str(sup)
            if sup_key in seen:
                break
            length += 1
            cur = sup_key
            seen.add(cur)
        chains.append(length)
        visited.update(seen)
    return {
        "supersedes_line_pct": _share(sum(1 for r in rows if r.get("supersedes")), len(rows)),
        "supersedes_chain_lengths": chains,
        "supersedes_chain_len3_count": sum(1 for n in chains if n >= 3),
    }


def corpus_profile(lines: Sequence[dict]) -> dict:
    """Aggregate corpus shape metrics for the phase-5 target profile table."""
    rows = list(lines)
    n = len(rows)
    content_lens = [len(str(r.get("content") or "")) for r in rows]
    title_lens = [len(str(r.get("title") or "")) for r in rows]
    context_lens = [len(str(r.get("context") or "")) for r in rows]
    kw_counts = [len(r.get("keywords") or []) for r in rows]
    tag_counts = [len(r.get("tags") or []) for r in rows]
    sentence_counts = [
        max(1, len([s for s in SENTENCE_SPLIT_RE.split(str(r.get("content") or "")) if s.strip()]))
        for r in rows
    ]

    dup_keys = _near_duplicate_keys(rows)

    def has_ticket_key(row: dict) -> bool:
        parts = [str(row.get(f) or "") for f in ("title", "content", "context")]
        parts.extend(str(k) for k in (row.get("keywords") or []))
        blob = " ".join(parts)
        return any(
            t.split("-", 1)[0] not in TICKET_PREFIX_STOPLIST for t in TICKET_KEY_RE.findall(blob)
        )

    def blob(row: dict) -> str:
        return "\n".join(
            str(row.get(f) or "") if not isinstance(row.get(f), list) else " ".join(row.get(f) or [])
            for f in ("title", "content", "context")
        )

    ticket_n = sum(1 for r in rows if has_ticket_key(r))
    ref_n = sum(1 for r in rows if REF_PLACEHOLDER_RE.search(blob(r)))
    snake_n = sum(1 for r in rows if SNAKE_TOKEN_RE.search(blob(r)))
    pascal_n = sum(1 for r in rows if PASCAL_TOKEN_RE.search(blob(r)))
    dotted_n = sum(1 for r in rows if DOTTED_MODULE_RE.search(blob(r)))
    iso_n = sum(1 for r in rows if ISO_DATE_RE.search(blob(r)))
    path_n = sum(
        1
        for r in rows
        if POSIX_PATH_RE.search(blob(r)) or WIN_PATH_RE.search(blob(r))
    )
    posix_n = sum(1 for r in rows if POSIX_PATH_RE.search(blob(r)))
    win_n = sum(1 for r in rows if WIN_PATH_RE.search(blob(r)))
    url_n = sum(1 for r in rows if URL_RE.search(blob(r)))
    md_n = sum(1 for r in rows if MARKDOWN_LIST_RE.search(str(r.get("content") or "")))
    prefix_n = sum(1 for r in rows if TITLE_TYPE_PREFIX_RE.match(str(r.get("title") or "")))
    fr_n = sum(1 for r in rows if FRENCH_HINT_RE.search(blob(r)))
    near_dup_n = sum(1 for r in rows if str(r["key"]) in dup_keys)

    project_counts: dict[str, int] = {}
    for row in rows:
        tags = row.get("tags") or []
        for tag in tags:
            if tag.startswith("fict-"):
                project_counts[tag] = project_counts.get(tag, 0) + 1

    profile: dict = {
        "n_lines": n,
        "content_chars_p10": percentile(content_lens, 0.10),
        "content_chars_p50": percentile(content_lens, 0.50),
        "content_chars_p90": percentile(content_lens, 0.90),
        "content_chars_max": max(content_lens) if content_lens else 0,
        "title_chars_p50": percentile(title_lens, 0.50),
        "context_chars_p50": percentile(context_lens, 0.50),
        "kw_p50": percentile(kw_counts, 0.50),
        "kw_p90": percentile(kw_counts, 0.90),
        "tags_p50": percentile(tag_counts, 0.50),
        "tags_p90": percentile(tag_counts, 0.90),
        "sentences_p50": percentile(sentence_counts, 0.50),
        "title_type_prefix_pct": _share(prefix_n, n),
        "ticket_key_pct": _share(ticket_n, n),
        "ref_placeholder_pct": _share(ref_n, n),
        "snake_case_pct": _share(snake_n, n),
        "pascal_case_pct": _share(pascal_n, n),
        "dotted_module_pct": _share(dotted_n, n),
        "iso_date_pct": _share(iso_n, n),
        "file_path_pct": _share(path_n, n),
        "file_path_posix_pct": _share(posix_n, n),
        "file_path_windows_pct": _share(win_n, n),
        "url_pct": _share(url_n, n),
        "markdown_list_pct": _share(md_n, n),
        "fr_en_mixed_pct": _share(fr_n, n),
        "near_duplicate_pct": _share(near_dup_n, n),
        "project_tag_counts": project_counts,
    }
    profile.update(_importance_histogram(rows))
    profile.update(_tag_style_shares(rows))
    profile.update(_supersedes_chains(rows))
    profile.update(d16_antitemplate_metrics(rows))
    return profile


def render_report(summary: dict) -> str:
    configs = list(summary["configs"])
    groups = sorted({g for c in configs for g in summary["configs"][c]["groups"]})
    lines = [
        "# Retrieval benchmark",
        "",
        (
            f"Generated: {summary['generated_at']} | git `{summary['git_head'][:8]}` | "
            f"snapshot sha256 `{summary['snapshot']['sha256'][:12]}`"
        ),
        "",
        (
            "Reproduce: `uv run python benchmarks/retrieval/run_eval.py "
            "--cache-dir <models>` after `build_corpus.py`."
        ),
        "",
        "## Corpus",
        "",
        (
            f"- Memories: {summary['corpus']['total']} total, {summary['corpus']['active']} active, "
            f"{summary['corpus']['obsolete']} obsolete"
        ),
        f"- Embedding: {summary['settings']['EMBEDDING_MODEL']} ({summary['settings']['EMBEDDING_DIMENSIONS']} dims)",
        (
            f"- Reranker: {summary['settings']['RERANKING_MODEL']}, "
            f"candidates {summary['settings']['DENSE_SEARCH_CANDIDATES']}"
        ),
        "",
        "## Datasets",
        "",
        "| Dataset | n | sha256 |",
        "| --- | ---: | --- |",
    ]
    for name, meta in summary["datasets"].items():
        lines.append(f"| {name} | {meta['n']} | `{meta['sha256'][:12]}` |")
    for metric, label in (("r5", "R@5"), ("r10", "R@10"), ("mrr", "MRR@10")):
        lines += [
            "",
            f"## {label} (95% bootstrap CI)",
            "",
            "| Group | n | " + " | ".join(configs) + " |",
            "| --- | ---: |" + " --- |" * len(configs),
        ]
        for g in groups:
            n = next(
                summary["configs"][c]["groups"][g]["n"]
                for c in configs
                if g in summary["configs"][c]["groups"]
            )
            cells = []
            for c in configs:
                s = summary["configs"][c]["groups"].get(g)
                if s is None:
                    cells.append("—")
                else:
                    cells.append(
                        f"{s[metric]:.3f} [{s[f'{metric}_ci'][0]:.3f}, {s[f'{metric}_ci'][1]:.3f}]",
                    )
            lines.append(f"| {g} | {n} | " + " | ".join(cells) + " |")
    lines += ["", "## Latency (ms per query)", "", "| Config | p50 | p95 |", "| --- | ---: | ---: |"]
    for c in configs:
        lat = summary["configs"][c]["latency_ms"]
        lines.append(f"| {c} | {lat['p50']} | {lat['p95']} |")
    lines += [
        "",
        "## Caveats",
        "",
        (
            "- Obsolete-chain pairs were found by title similarity during curation: "
            "this set favours dense retrieval."
        ),
        (
            "- Identifier labels are containment by construction: they measure exact-token recall."
        ),
        "- Single embedding model; global corpus (no project or importance filter).",
    ]
    body = "\n".join(lines) + "\n"
    body += render_gate_verdict(summary)
    return body


def render_gate_verdict(summary: dict) -> str:
    """Synthetic go/no-go gates from the spec (measured on this run)."""
    cfg = summary.get("configs", {})
    if "hybrid_rerank" in cfg and "vector_rerank" in cfg:
        h_name, v_name = "hybrid_rerank", "vector_rerank"
    elif "hybrid" in cfg and "vector" in cfg:
        h_name, v_name = "hybrid", "vector"
    else:
        return ""

    hr = cfg[h_name]["groups"]
    vr = cfg[v_name]["groups"]

    def row(metric: str, value: str, threshold: str, passed: bool) -> str:
        status = "PASS" if passed else "FAIL"
        return f"| {metric} | {value} | {threshold} | {status} |"

    lines = [
        "",
        "## Go/no-go verdict",
        "",
        "| Metric | Value | Threshold | Result |",
        "| --- | --- | --- | --- |",
    ]
    if "identifier" in hr and "identifier" in vr:
        id_pass = hr["identifier"]["mrr"] > vr["identifier"]["mrr"]
        lines.append(
            row(
                f"identifier MRR@10 {h_name} vs {v_name}",
                f"{hr['identifier']['mrr']:.4f} vs {vr['identifier']['mrr']:.4f}",
                f"{h_name} > {v_name}",
                id_pass,
            ),
        )
    else:
        lines.append(
            row(
                f"identifier MRR@10 {h_name} vs {v_name}",
                "missing",
                f"{h_name} > {v_name}",
                False,
            ),
        )
    if "curated" in hr and "curated" in vr:
        cur_pass = hr["curated"]["mrr"] >= vr["curated"]["mrr"] - 0.02
        lines.append(
            row(
                f"curated MRR@10 {h_name}",
                f"{hr['curated']['mrr']:.4f}",
                f"≥ {v_name} − 0.02 ({vr['curated']['mrr'] - 0.02:.4f})",
                cur_pass,
            ),
        )
    if "supersession" in hr and "supersession" in vr:
        sup_pass = hr["supersession"]["mrr"] >= vr["supersession"]["mrr"] - 0.02
        lines.append(
            row(
                f"supersession MRR@10 {h_name}",
                f"{hr['supersession']['mrr']:.4f}",
                f"≥ {v_name} − 0.02 ({vr['supersession']['mrr'] - 0.02:.4f})",
                sup_pass,
            ),
        )
    return "\n".join(lines) + "\n"
