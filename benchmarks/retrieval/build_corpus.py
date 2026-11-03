"""Build a SQLite Forgetful DB from the synthetic retrieval corpus."""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = Path(__file__).resolve().parent
for _p in (ROOT, BENCH):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eval_lib import (  # noqa: E402
    HarnessError,
    backup_copy,
    corpus_profile,
    load_corpus_jsonl,
    load_curated_jsonl,
    remove_db_files,
    resolve_ref_placeholders,
    validate_curated_keys,
    write_jsonl,
)

from app.bootstrap import get_embedding_adapter  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.models.memory_models import MemoryCreate  # noqa: E402
from app.models.user_models import UserCreate  # noqa: E402
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository  # noqa: E402
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter  # noqa: E402
from app.repositories.sqlite.user_repository import SqliteUserRepository  # noqa: E402
from app.services.memory_service import MemoryService  # noqa: E402
from app.services.user_service import UserService  # noqa: E402

USER_EXTERNAL_ID = "ottervale-bench"
MIN_CURATED = 30


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the synthetic retrieval corpus DB")
    parser.add_argument(
        "--out",
        type=Path,
        default=BENCH / "output",
        help="Directory for corpus.db, resolved queries, and profile JSON",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional FastEmbed cache directory",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=BENCH / "corpus.jsonl",
    )
    parser.add_argument(
        "--curated",
        type=Path,
        default=BENCH / "queries_curated.jsonl",
    )
    return parser.parse_args(argv)


def configure_build_settings(*, db_path: Path, cache_dir: Path | None) -> None:
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = False
    settings.SQLITE_PATH = str(db_path)
    settings.RERANKING_ENABLED = False
    settings.HYBRID_SEARCH_ENABLED = False
    settings.MEMORY_NUM_AUTO_LINK = 0
    settings.OBSOLETE_WARNING_ENABLED = False
    settings.ACTIVITY_ENABLED = False
    settings.ACTIVITY_TRACK_READS = False
    if cache_dir is not None:
        settings.FASTEMBED_CACHE_DIR = str(cache_dir)


def successor_map(rows: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        old = row.get("supersedes")
        if old:
            out[str(old)] = str(row["key"])
    return out


def resolve_active_key(key: str, successor: dict[str, str]) -> str:
    seen: set[str] = set()
    current = key
    while current in successor and current not in seen:
        seen.add(current)
        current = successor[current]
    return current


async def build(args: argparse.Namespace) -> int:
    rows = load_corpus_jsonl(args.corpus)
    curated = load_curated_jsonl(args.curated)
    known = {str(r["key"]) for r in rows}
    validate_curated_keys(curated, known_keys=known)
    if len(curated) < MIN_CURATED:
        raise HarnessError(f"Need at least {MIN_CURATED} curated queries, got {len(curated)}", 4)

    args.out.mkdir(parents=True, exist_ok=True)
    dest_db = args.out / "corpus.db"
    remove_db_files(dest_db)

    work_dir = Path(tempfile.mkdtemp(prefix="forgetful-retrieval-build-"))
    work_db = work_dir / "corpus.db"
    configure_build_settings(db_path=work_db, cache_dir=args.cache_dir)

    t0 = time.perf_counter()
    adapter = SqliteDatabaseAdapter()
    embedder = None
    try:
        await adapter.init_db()
        embedder = get_embedding_adapter()
        user = await UserService(SqliteUserRepository(adapter)).get_or_create_user(
            UserCreate(
                external_id=USER_EXTERNAL_ID,
                name="Ottervale Bench",
                email="bench@ottervale.example.com",
            ),
        )
        if user is None:
            raise HarnessError("Failed to create benchmark user", 4)
        repo = SqliteMemoryRepository(adapter, embedder)
        service = MemoryService(memory_repo=repo)

        key_to_id: dict[str, int] = {}
        for index, row in enumerate(rows, start=1):
            payload = MemoryCreate(
                title=resolve_ref_placeholders(str(row["title"]), key_to_id),
                content=resolve_ref_placeholders(str(row["content"]), key_to_id),
                context=resolve_ref_placeholders(str(row.get("context") or ""), key_to_id),
                keywords=[
                    resolve_ref_placeholders(str(item), key_to_id)
                    for item in (row.get("keywords") or [])
                ],
                tags=list(row.get("tags") or []),
                importance=int(row.get("importance", 8)),
            )
            created = await service.create_memory(user.id, payload)
            key_to_id[str(row["key"])] = int(created.memory.id)
            if index % 50 == 0 or index == len(rows):
                print(f"created {index}/{len(rows)} memories")

        successor = successor_map(rows)
        obsolete_n = 0
        for row in rows:
            old_key = row.get("supersedes")
            if not old_key:
                continue
            await service.mark_memory_obsolete(
                user.id,
                key_to_id[str(old_key)],
                reason=f"Superseded by {row['key']}",
                superseded_by=key_to_id[str(row["key"])],
            )
            obsolete_n += 1
        print(f"marked obsolete: {obsolete_n}")
    finally:
        if embedder is not None and hasattr(embedder, "aclose"):
            await embedder.aclose()
        await adapter.dispose()

    backup_copy(work_db, dest_db)
    remove_db_files(work_db)
    shutil.rmtree(work_dir, ignore_errors=True)

    resolved = []
    for query in curated:
        ids: list[int] = []
        for key in query.relevant_keys:
            mid = key_to_id[resolve_active_key(key, successor)]
            if mid not in ids:
                ids.append(mid)
        resolved.append(
            {
                "qid": query.qid,
                "type": "curated",
                "subtype": None,
                "query": query.query,
                "relevant_ids": ids,
                "lang": query.lang,
            },
        )
    resolved_path = args.out / "curated_queries.resolved.jsonl"
    write_jsonl(resolved_path, resolved)

    profile = corpus_profile(rows)
    profile_path = args.out / "corpus_profile.json"
    profile_path.write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    meta = {
        "user_external_id": USER_EXTERNAL_ID,
        "db_path": str(dest_db),
        "n_memories": len(rows),
        "n_obsolete": obsolete_n,
        "elapsed_s": round(time.perf_counter() - t0, 1),
    }
    (args.out / "build_meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(profile, indent=2, sort_keys=True))
    print(f"DB path: {dest_db}")
    print(f"Resolved queries: {resolved_path}")
    print(f"Build elapsed_s={meta['elapsed_s']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return asyncio.run(build(parse_args(argv)))
    except HarnessError as exc:
        print(exc, file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
