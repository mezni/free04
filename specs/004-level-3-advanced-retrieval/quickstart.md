# Quickstart Validation: Level 3 Advanced Retrieval

**Feature**: specs/004-level-3-advanced-retrieval
**Purpose**: end-to-end validation scenarios proving every retrieval
strategy, the debug trail, and the evaluation matrix work — without
breaking Level 2. Run from the repository root. Implementation details
live in `tasks.md` (Phase 2).

## Prerequisites

- Python 3.12+, `uv` environment synced (`uv sync` — pulls new
  `rank-bm25` dependency and refreshed `uv.lock`)
- Corpus ingested: `uv run telco-rag ingest` (rebuilds ChromaDB **and**
  the derived BM25 index from `data/documents/`)
- `.env` with `LLM_*` credentials only for scenarios marked *gateway*
  (rewriting, answer generation); all retrieval scenarios and unit tests
  run offline
- Baseline green before starting: `uv run pytest` (Level 0/1/2 suites)

## Scenario matrix

| # | Scenario | Command | Expected outcome |
|---|----------|---------|------------------|
| V1 | Vector baseline (unchanged behavior) | `uv run telco-rag retrieve "What causes packet loss on 5G?" --strategy vector` | ranked results, same quality as Level 1 retrieval |
| V2 | BM25 lexical retrieval | `... retrieve "core network node failure" --strategy bm25` | results ranked by BM25 score; exact-terminology hits surface |
| V3 | Hybrid fusion | `... retrieve "..." --strategy hybrid --debug` | each result shows `vector_rank` + `bm25_rank` + `rrf_score`; duplicates appear once (FR-006) |
| V4 | Hybrid + reranking | `... retrieve "..." --strategy hybrid_reranked --debug` | results additionally show `reranker_score`; order may differ from V3; latency block includes `rerank` |
| V5 | Determinism | run V3 twice | byte-identical output (SC-004) |
| V6 | Reranking disabled | set `reranking.enabled: false`, run `hybrid_reranked --debug` | output identical to V3; `Stages skipped: rerank`; no `reranker_score` printed (SC-005) |
| V7 | Metadata filtering, all strategies | `... retrieve "..." --filter category=5g` (× 4 strategies) | identical filter semantics everywhere; only matching metadata rows returned (FR-010/FR-011) |
| V8 | Invalid strategy rejected | `... retrieve "..." --strategy souped` | exit 1, message lists valid strategies (FR-008, SC-009) |
| V9 | Query rewriting off by default | `... retrieve "..." --debug` with default config | `Rewritten query: (not run)`; `Query:` = original (Principle XXIX) |
| V10 | Query rewriting on (*gateway*) | set `query_rewriting.enabled: true`, `... retrieve "..." --debug` | both `Query:` (original) and `Rewritten query:` shown; retrieval uses rewritten (FR-017); with gateway unreachable: warning + fallback, exit 0 |
| V11 | Provenance completeness | any V3/V4 run | every result line shows only stages that ran; `absent = not run`, never `0` (Principle XXVI) |
| V12 | Level 2 regression | `uv run telco-rag query "What causes packet loss on 5G?"` | grounded answer + Sources unchanged; `Citation validation: PASS` |
| V13 | Two-layer evaluation preserved | `uv run telco-rag evaluate --answers` | retrieval metrics block **and** answer metrics block unchanged (Principle XXII) |
| V14 | Evaluation matrix + ablation | `uv run python scripts/run_retrieval_experiments.py` | Markdown table: 4 strategies × (original/rewritten) with Recall@5 / Precision@5 / MRR + per-stage latency; unmeasured cells `TBD`; written to `docs/levels/level-03-advanced-retrieval/experiments.md` |
| V15 | Failure analysis recorded | inspect experiments.md §7 | ≥ 1 analyzed failure with first failing stage + regression test name (FR-025/FR-028); if none: explicit "no failures" note |
| V16 | Full regression | `uv run pytest -q` | all Level 0/1/2 tests + new Level 3 suites pass (FR-026/FR-027) |
| V17 | Static gates | `uv run ruff check . && uv run ruff format --check . && uv run mypy` | clean |

## Validation commands (copy-paste)

```bash
# 0. baseline + static checks
uv run pytest -q
uv run ruff check . && uv run mypy

# 1. rebuild knowledge base (vector store + BM25 index)
uv run telco-rag ingest

# 2. four strategies
uv run telco-rag retrieve "What causes packet loss on 5G?" --strategy vector
uv run telco-rag retrieve "core network node failure" --strategy bm25
uv run telco-rag retrieve "What causes packet loss on 5G?" --strategy hybrid --debug
uv run telco-rag retrieve "What causes packet loss on 5G?" --strategy hybrid_reranked --debug

# 3. determinism (diff must be empty)
uv run telco-rag retrieve "5G packet loss" --strategy hybrid --debug > /tmp/r1.txt
uv run telco-rag retrieve "5G packet loss" --strategy hybrid --debug > /tmp/r2.txt
diff /tmp/r1.txt /tmp/r2.txt

# 4. filtering across strategies
for s in vector bm25 hybrid hybrid_reranked; do
  uv run telco-rag retrieve "network outage" --strategy $s --filter category=5g --debug
done

# 5. invalid strategy → exit 1
uv run telco-rag retrieve "x" --strategy souped; echo "exit=$?"

# 6. Level 2 regression (needs .env)
uv run telco-rag query "What causes packet loss on a 5G network?"
uv run telco-rag evaluate --answers

# 7. matrix + ablation (rewriting runs only with --rewrite)
uv run python scripts/run_retrieval_experiments.py

# 8. full suite + static
uv run pytest -q && uv run ruff check . && uv run mypy
```

## Reading the results

- **Quality**: matrix Recall@5 / Precision@5 / MRR per strategy — each
  ablation row must show the stage toggle it isolates (constitution
  Principle XXIV).
- **Latency**: per-stage ms in `--debug` and the matrix — these are the
  first recorded baselines; no number appears in experiments.md unless
  measured.
- **Failures**: any question where a strategy misses a relevant chunk →
  follow the decision tree in `lessons-learned.md` §10
  (failure-analysis procedure), log it in experiments.md §7, add the
  named regression test.
