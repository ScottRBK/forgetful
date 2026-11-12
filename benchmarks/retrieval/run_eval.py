"""Run the synthetic retrieval benchmark (vector / hybrid, with and without rerank)."""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import sqlite_vec

ROOT = Path(__file__).resolve().parents[2]
BENCH = Path(__file__).resolve().parent
for _p in (ROOT, BENCH):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eval_lib import (  # noqa: E402
    EvalQuery,
    HarnessError,
    aggregate,
    first_rank,
    load_curated_jsonl,
    load_jsonl,
    mine_identifiers,
    mine_supersession,
    percentile,
    recall_at_k,
    reciprocal_rank,
    remove_db_files,
    render_report,
    searchable_ids,
    sha256_file,
    snapshot_db,
    validate_queries,
    write_jsonl,
)

import app.repositories.sqlite.memory_repository as memory_repository_module  # noqa: E402
from app.bootstrap import get_embedding_adapter  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.repositories.embeddings.reranker_adapter import (  # noqa: E402
    FastEmbedCrossEncoderAdapter,
)
from app.repositories.sqlite.memory_repository import (  # noqa: E402
    SqliteMemoryRepository,
)
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter  # noqa: E402
from app.repositories.sqlite.user_repository import SqliteUserRepository  # noqa: E402

CONFIGS = ("vector", "vector_rerank", "hybrid", "hybrid_rerank")
QUICK_CONFIGS = ("vector", "hybrid")
MIN_GROUP = 30
USER_EXTERNAL_ID = "ottervale-bench"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the synthetic retrieval benchmark")
    parser.add_argument(
        "--db",
        type=Path,
        default=BENCH / "output" / "corpus.db",
        help="Built corpus DB (copied to a temp file; never mutated)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=BENCH / "output",
        help="Directory for summary.json / summary.md (gitignored)",
    )
    parser.add_argument(
        "--curated",
        type=Path,
        default=BENCH / "output" / "curated_queries.resolved.jsonl",
    )
    parser.add_argument(
        "--curated-source",
        type=Path,
        default=BENCH / "queries_curated.jsonl",
        help="Original curated JSONL, used for lang tags (R10)",
    )
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip rerank configs; run vector and hybrid only",
    )
    parser.add_argument(
        "--skip-curated",
        action="store_true",
        help="Omit curated queries (for a foreign store that has no resolved curated set)",
    )
    parser.add_argument("--configs", type=str, default=",".join(CONFIGS))
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--candidates", type=int, default=20)
    parser.add_argument("--rerank-threads", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--cap-per-subtype", type=int, default=100)
    parser.add_argument("--max-df", type=int, default=3)
    parser.add_argument(
        "--user-external-id",
        type=str,
        default=USER_EXTERNAL_ID,
    )
    args = parser.parse_args(argv)
    if args.quick:
        args.configs = list(QUICK_CONFIGS)
        return args
    selected = [c.strip() for c in args.configs.split(",") if c.strip()]
    bad = [c for c in selected if c not in CONFIGS]
    if bad:
        parser.error(f"Unknown config(s): {bad}; allowed: {CONFIGS}")
    args.configs = selected
    return args


def git_head() -> str:
    proc = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() or "unknown"


def open_snapshot(path: Path) -> sqlite3.Connection:
    resolved = path.resolve()
    uri_path = resolved.as_posix()
    if len(resolved.drive) == 2 and uri_path[1] == ":":
        uri = f"file:///{uri_path}?mode=ro"
    else:
        uri = f"file:{uri_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    conn.enable_load_extension(False)
    return conn


def configure_settings(
    *,
    db_path: Path,
    rerank: bool,
    hybrid: bool,
    candidates: int,
    cache_dir: Path | None,
) -> None:
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = False
    settings.SQLITE_PATH = str(db_path)
    settings.RERANKING_ENABLED = rerank
    settings.HYBRID_SEARCH_ENABLED = hybrid
    settings.RERANKING_PROVIDER = "FastEmbed"
    settings.DENSE_SEARCH_CANDIDATES = candidates
    settings.ACTIVITY_ENABLED = False
    settings.ACTIVITY_TRACK_READS = False
    if cache_dir is not None:
        settings.FASTEMBED_CACHE_DIR = str(cache_dir)
    if memory_repository_module.settings is not settings:
        raise HarnessError("memory_repository.settings is not the shared singleton", 5)
    if memory_repository_module.settings.RERANKING_ENABLED is not rerank:
        raise HarnessError(
            f"Repository RERANKING_ENABLED={memory_repository_module.settings.RERANKING_ENABLED}, "
            f"expected {rerank}",
            5,
        )
    if memory_repository_module.settings.HYBRID_SEARCH_ENABLED is not hybrid:
        raise HarnessError(
            f"Repository HYBRID_SEARCH_ENABLED={memory_repository_module.settings.HYBRID_SEARCH_ENABLED}, "
            f"expected {hybrid}",
            5,
        )


async def resolve_user_uuid(*, work_db: Path, external_id: str, args: argparse.Namespace) -> UUID:
    configure_settings(
        db_path=work_db,
        rerank=False,
        hybrid=False,
        candidates=args.candidates,
        cache_dir=args.cache_dir,
    )
    adapter = SqliteDatabaseAdapter()
    try:
        user = await SqliteUserRepository(db_adapter=adapter).get_user_by_external_id(external_id)
    finally:
        await adapter.dispose()
    if user is None:
        raise HarnessError(f"No user with external_id {external_id!r}", 4)
    return user.id


def corpus_counts(conn: sqlite3.Connection, user_id: str) -> dict[str, int]:
    total = conn.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)).fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE user_id = ? AND is_obsolete = 0",
        (user_id,),
    ).fetchone()[0]
    obsolete = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE user_id = ? AND is_obsolete = 1",
        (user_id,),
    ).fetchone()[0]
    return {"total": int(total), "active": int(active), "obsolete": int(obsolete)}


async def _execute_one(
    name: str,
    q: EvalQuery,
    *,
    repo: SqliteMemoryRepository,
    user_id: UUID,
    args: argparse.Namespace,
) -> tuple[list[int], list[float | None], bool]:
    scored = await repo.search_scored(
        user_id=user_id,
        query=q.query,
        query_context="synthetic retrieval benchmark",
        k=args.k,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    ranked = [m.id for m, _ in scored]
    rerank_scores = [s.rerank_score for _, s in scored]
    saw_keyword_rank = False
    if name.startswith("hybrid"):
        saw_keyword_rank = any(s.keyword_rank is not None for _, s in scored)
    return ranked, rerank_scores, saw_keyword_rank


async def run_config(
    name: str,
    queries: list[EvalQuery],
    *,
    work_db: Path,
    user_id: UUID,
    embedder,
    args: argparse.Namespace,
) -> list[dict]:
    rerank = name in ("vector_rerank", "hybrid_rerank")
    hybrid = name.startswith("hybrid")
    configure_settings(
        db_path=work_db,
        rerank=rerank,
        hybrid=hybrid,
        candidates=args.candidates,
        cache_dir=args.cache_dir,
    )
    adapter = SqliteDatabaseAdapter()
    reranker: FastEmbedCrossEncoderAdapter | None = None
    saw_keyword_rank = False
    try:
        if rerank:
            try:
                reranker = FastEmbedCrossEncoderAdapter(
                    model=settings.RERANKING_MODEL,
                    threads=args.rerank_threads,
                    workers=1,
                    cache_dir=settings.FASTEMBED_CACHE_DIR,
                )
            except Exception as exc:
                raise HarnessError(f"Reranker unavailable for {name}: {exc}", 2) from exc
        repo = SqliteMemoryRepository(
            db_adapter=adapter,
            embedding_adapter=embedder,
            rerank_adapter=reranker,
        )
        if hybrid:
            async with adapter._engine.begin() as conn:
                await adapter.ensure_memory_fts(conn)

        rows: list[dict] = []
        for q in queries:
            t0 = time.perf_counter()
            ranked, rerank_scores, keyword_seen = await _execute_one(
                name,
                q,
                repo=repo,
                user_id=user_id,
                args=args,
            )
            saw_keyword_rank = saw_keyword_rank or keyword_seen
            ms = (time.perf_counter() - t0) * 1000
            if rerank and any(s is None for s in rerank_scores):
                raise HarnessError("rerank path skipped (stale settings?)", 5)
            if (not rerank) and any(s is not None for s in rerank_scores):
                raise HarnessError("unexpected rerank scores on dense-only config", 5)
            rel = frozenset(q.relevant_ids)
            rows.append(
                {
                    "qid": q.qid,
                    "type": q.type,
                    "subtype": q.subtype,
                    "config": name,
                    "relevant_ids": list(q.relevant_ids),
                    "ranked_ids": ranked[:10],
                    "first_rank": first_rank(ranked, rel),
                    "recall_at_5": recall_at_k(ranked, rel, 5),
                    "recall_at_10": recall_at_k(ranked, rel, 10),
                    "rr": reciprocal_rank(ranked, rel),
                    "latency_ms": round(ms, 1),
                },
            )
        if hybrid and not saw_keyword_rank:
            raise HarnessError(
                f"hybrid config {name!r} returned no keyword_rank — "
                "keyword leg did not run or FTS not populated",
                5,
            )
        return rows
    finally:
        await adapter.dispose()


def lang_by_qid(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {q.qid: q.lang for q in load_curated_jsonl(path)}


async def main_async(args: argparse.Namespace) -> int:
    source = Path(args.db)
    if not source.is_file():
        raise HarnessError(f"Database not found: {source} (run build_corpus.py first)", 2)
    if not args.skip_curated and not args.curated.is_file():
        raise HarnessError(f"Resolved curated queries not found: {args.curated}", 2)

    args.out.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="forgetful-retrieval-eval-"))
    work_db = work_dir / "work.db"
    embedder = None
    try:
        source_before, source_after = snapshot_db(source, work_db)
        snapshot_sha = sha256_file(work_db)
        print(f"Work snapshot sha256: {snapshot_sha}")
        user_id = await resolve_user_uuid(
            work_db=work_db,
            external_id=args.user_external_id,
            args=args,
        )
        uid = str(user_id)
        conn = open_snapshot(work_db)
        try:
            curated: list[EvalQuery] = []
            if not args.skip_curated:
                curated = load_jsonl(args.curated)
            identifier = mine_identifiers(
                conn,
                user_id=uid,
                seed=args.seed,
                cap_per_subtype=args.cap_per_subtype,
                max_df=args.max_df,
            )
            supersession = mine_supersession(conn, user_id=uid)
            counts = {
                "identifier": len(identifier),
                "supersession": len(supersession),
            }
            if not args.skip_curated:
                counts["curated"] = len(curated)
            short = {name: n for name, n in counts.items() if n < MIN_GROUP}
            if short:
                raise HarnessError(
                    f"Need at least {MIN_GROUP} queries per group, got {counts}",
                    4,
                )
            errors = validate_queries(
                conn,
                curated + identifier + supersession,
                user_id=uid,
            )
            if errors:
                for err in errors:
                    print(err, file=sys.stderr)
                raise HarnessError("curated/mined query validation failed", 4)
            if not searchable_ids(conn, uid):
                raise HarnessError("No searchable memories for this user", 4)
            corpus = corpus_counts(conn, uid)
        finally:
            conn.close()

        dataset_dir = args.out / "datasets"
        datasets: dict[str, dict] = {}
        if not args.skip_curated:
            curated_sha = write_jsonl(dataset_dir / "curated.jsonl", curated)
            datasets["curated"] = {"n": len(curated), "sha256": curated_sha}
            print(f"Datasets: curated n={len(curated)} sha256={curated_sha[:12]}…")
        id_sha = write_jsonl(dataset_dir / "identifier.jsonl", identifier)
        sup_sha = write_jsonl(dataset_dir / "supersession.jsonl", supersession)
        datasets["identifier"] = {"n": len(identifier), "sha256": id_sha}
        datasets["supersession"] = {"n": len(supersession), "sha256": sup_sha}
        print(f"Datasets: identifier n={len(identifier)} sha256={id_sha[:12]}…")
        print(f"Datasets: supersession n={len(supersession)} sha256={sup_sha[:12]}…")

        queries = curated + identifier + supersession
        configure_settings(
            db_path=work_db,
            rerank=False,
            hybrid=False,
            candidates=args.candidates,
            cache_dir=args.cache_dir,
        )
        try:
            embedder = get_embedding_adapter()
        except Exception as exc:
            raise HarnessError(f"Embedding model unavailable: {exc}", 2) from exc

        langs = {} if args.skip_curated else lang_by_qid(args.curated_source)
        all_rows: list[dict] = []
        config_summaries: dict[str, dict] = {}
        for cfg in args.configs:
            print(f"Running config {cfg} n={len(queries)}")
            rows = await run_config(
                cfg,
                queries,
                work_db=work_db,
                user_id=user_id,
                embedder=embedder,
                args=args,
            )
            all_rows.extend(rows)
            groups = aggregate(rows, seed=args.seed, n_resamples=args.bootstrap)
            curated_en_rows = [
                r
                for r in rows
                if r["type"] == "curated" and langs.get(r["qid"], "en") == "en"
            ]
            if curated_en_rows:
                extra = aggregate(
                    curated_en_rows,
                    seed=args.seed,
                    n_resamples=args.bootstrap,
                )
                groups["curated_en"] = extra.get("curated") or extra.get("overall")
            latencies = [float(r["latency_ms"]) for r in rows]
            config_summaries[cfg] = {
                "groups": groups,
                "latency_ms": {
                    "p50": percentile(latencies, 0.5),
                    "p95": percentile(latencies, 0.95),
                },
            }
            overall = groups.get("overall", {})
            print(
                f"{cfg}: n={overall.get('n', 0)} "
                f"R@5={overall.get('r5', 0):.4f} R@10={overall.get('r10', 0):.4f} "
                f"MRR={overall.get('mrr', 0):.4f}",
            )
    finally:
        if embedder is not None and hasattr(embedder, "aclose"):
            await embedder.aclose()
        remove_db_files(work_db)
        shutil.rmtree(work_dir, ignore_errors=True)

    if sha256_file(source) != source_before["main"]["sha256"]:
        raise HarnessError("Source DB changed during the run", 5)

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "snapshot": {
            "path": source.name,
            "sha256": snapshot_sha,
            "source_before": source_before,
            "source_after": source_after,
        },
        "user_external_id": args.user_external_id,
        "corpus": corpus,
        "query_counts": counts,
        "settings": {
            "EMBEDDING_MODEL": settings.EMBEDDING_MODEL,
            "EMBEDDING_DIMENSIONS": settings.EMBEDDING_DIMENSIONS,
            "RERANKING_MODEL": settings.RERANKING_MODEL,
            "DENSE_SEARCH_CANDIDATES": args.candidates,
            "HYBRID_SEARCH_ENABLED": "per-config",
            "k": args.k,
            "skip_curated": args.skip_curated,
        },
        "datasets": datasets,
        "configs": config_summaries,
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_jsonl(args.out / "per_query.jsonl", all_rows)
    report = render_report(summary)
    (args.out / "summary.md").write_text(report, encoding="utf-8", newline="\n")
    print(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return asyncio.run(main_async(parse_args(argv)))
    except HarnessError as exc:
        print(exc, file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
