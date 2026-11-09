# Synthetic retrieval benchmark

Reproduce the hybrid-search numbers from a committed fictional corpus. Nothing here is sampled from a live store.

## Reproduce

From the repository root, with `uv` and the default FastEmbed models available (cached under the Forgetful data dir, or downloaded on first use):

```bash
uv run python benchmarks/retrieval/build_corpus.py
uv run python benchmarks/retrieval/run_eval.py          # full: 4 configs, ~80 min on CPU
uv run python benchmarks/retrieval/run_eval.py --quick  # vector + hybrid only, seconds to a few minutes
```

Full mode is the default and is what the go/no-go gate in the issue uses (`hybrid_rerank` vs `vector_rerank`). `--quick` skips the cross-encoder and gates `hybrid` vs `vector` instead (identifier MRR@10 hybrid > vector; curated and supersession hybrid ≥ vector − 0.02).

`build_corpus.py` writes `benchmarks/retrieval/output/corpus.db` (gitignored). `run_eval.py` copies that file to a temp DB and never writes back to it. Override the source with `--db <path>` to evaluate any SQLite Forgetful store the same way. For a read-only copy of your own store, add `--skip-curated` (and `--quick` for speed); those results are not reproducible and should be shared as aggregates only.

Outputs (gitignored) under `benchmarks/retrieval/output/`:

- `summary.json` / `summary.md` — MRR@10, R@5, R@10, bootstrap CIs, go/no-go gate
- `per_query.jsonl` — ranks per query and config
- `corpus_profile.json` — length/share histogram vs the target shape table

## Models

Default embedding `BAAI/bge-small-en-v1.5` (384-d) and reranker `Xenova/ms-marco-MiniLM-L-12-v2`. The keyword leg is SQLite FTS5. Configs: `vector`, `vector_rerank`, `hybrid`, `hybrid_rerank`. Identifier queries are exact-token labels, so they favour the keyword leg by construction (literal-match caveat).

## Query groups

Filled from the local run after `build_corpus.py` (mined with `seed=42`, `max_df=3`, `cap_per_subtype=100`):

| Group | n | Notes |
| --- | ---: | --- |
| curated | 30 | Natural questions; `curated_en` (26) drops the 4 French/mixed queries |
| identifier | 200 | 73 ticket keys, 32 code symbols, 95 `#id` refs |
| supersession | 45 | Obsolete title → active replacement |

A run exits non-zero if any group has fewer than 30 queries.

## Runtime (CPU)

Measured on this tree, 2026-11-03, Windows, FastEmbed models already cached:

- `build_corpus.py`: 102 s for 300 memories
- `run_eval.py` (full): ~80 min for 275 queries × 4 configs. Dominated by the reranker (~9 s/query p50); dense-only p50 ≈ 16–25 ms
- `run_eval.py --quick`: 67 s for 275 queries × 2 configs (vector, hybrid)

## Results (`--quick`, MRR@10)

Published numbers below skip the cross-encoder. Full mode (`run_eval.py` without `--quick`) still runs `vector_rerank` and `hybrid_rerank` and takes about 80 minutes on CPU; those rerank figures are not published for this corpus.

| Group | n | vector | hybrid |
| --- | ---: | ---: | ---: |
| curated | 30 | 0.917 | 0.926 |
| curated_en | 26 | 0.923 | 0.914 |
| identifier | 200 | 0.229 | 0.756 |
| identifier/code_symbol | 32 | 0.793 | 0.891 |
| identifier/memory_ref | 95 | 0.027 | 0.852 |
| identifier/ticket_key | 73 | 0.244 | 0.572 |
| supersession | 45 | 0.571 | 0.602 |
| overall | 275 | 0.360 | 0.749 |

Overall R@10: vector 0.480, hybrid 0.947. Go/no-go (`hybrid` vs `vector`): identifier PASS; curated PASS; supersession PASS. On English-only curated queries hybrid MRR@10 is slightly below vector (0.914 vs 0.923); the curated gate uses the full 30-query group, where hybrid is ahead.

## Caveats

Corpus shape (lengths, tag style, identifier and supersession density, ~12 % French/English mixed notes) is modelled on aggregate statistics of a real ~4k-memory personal store; no content is reused.

The default embedding model is English-centric, so mixed-language notes favour the keyword leg.
