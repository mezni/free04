# Implementation Plan: Level 3 Advanced Retrieval

**Branch**: `004-level-3-advanced-retrieval` | **Date**: 2026-10-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-level-3-advanced-retrieval/spec.md`

## Summary

Add an advanced retrieval layer in front of the unchanged Level 2 grounding
pipeline: a BM25 lexical retriever over the same chunks as vector search,
generic metadata filtering, hybrid retrieval combined by Reciprocal Rank
Fusion (never raw-score averaging), an optional cross-encoder reranker, an
optional LLM query rewriter (off by default, original query always
preserved), and a retrieval controller that selects among four strategies
(`vector`, `bm25`, `hybrid`, `hybrid_reranked`) from configuration and CLI.
Every result carries stage provenance (vector/bm25 rank, RRF score,
reranker score) so `telco-rag retrieve --debug` and a decision-tree failure
analysis can attribute misses to the first stage that lost the chunk.
Technical approach: extend the flat `src/` package with a `retrieval/`
sub-module set (`bm25.py`, `fusion.py`, `hybrid.py`, `reranker.py`,
`query_rewriter.py`, `controller.py`), extend `RetrievalResult` with
optional provenance fields, add one new runtime dependency (`rank-bm25`),
and build a Python-implemented evaluation matrix + ablation harness
(four strategies × original/rewritten query, Recall/Precision/MRR +
per-stage latency) recorded in `docs/levels/level-03-advanced-retrieval/experiments.md`.

## Technical Context

**Language/Version**: Python 3.12+ (existing `pyproject.toml`, `requires-python = ">=3.12"`)

**Primary Dependencies**: existing stack unchanged — Pydantic v2,
pydantic-settings, PyYAML, Typer, httpx (OpenAI-compatible client against
OpenRouter), sentence-transformers (BAAI/bge-small-en-v1.5 embeddings),
ChromaDB. **New:** `rank-bm25` (lexical retrieval) and the already-present
sentence-transformers `CrossEncoder` for BAAI/bge-reranker-base. No
frameworks.

**Storage**: ChromaDB persistent store (`data/chroma/`) for vectors; BM25
index built in-process at ingestion from the same chunks (derived,
rebuildable — not a second source of truth); JSONL datasets
(`data/evaluation/`); Markdown corpus (`data/documents/`).

**Testing**: pytest + pytest-cov, Ruff, mypy. Deterministic tests for
BM25/fusion/filtering/controller; mocked LLM for rewriting tests (existing
`tests/test_rag_pipeline.py` pattern); mocked reranker scores in unit
tests, real cross-encoder isolated to manual/quickstart runs.

**Target Platform**: local Linux, CLI-only (`telco-rag` console script).

**Project Type**: CLI (single project, flat `src/` layout — no services,
no frontend).

**Performance Goals**: interactive CLI retrieval; establish the first
per-stage latency baseline (embedding, vector, BM25, fusion, reranking,
rewriting, total) — measured, not pre-declared; reranking bounded to
candidate_k=20 pairs; evaluation runs offline over ~30–60 dataset cases.

**Constraints**: no frameworks (constitution II/XXI/Out of Scope); hybrid
must fuse by ranks, not averaged scores (Principle XXV, NON-NEGOTIABLE);
index rebuildable from documents, never hand-edited (XXVIII); rewriting
off by default with original preserved (XXIX, NON-NEGOTIABLE); Level 2
grounding tests must pass unchanged (FR-027); every added stage must have
quality + latency measured (XXIV); new dependency must be locked in
`uv.lock` (IV).

**Scale/Scope**: 10 corpus documents / 20 chunks (existing); evaluation
dataset grows from 26 to ~40–50 cases across 8 categories; ~7 new test
modules + extensions to CLI/config/evaluation; one new CLI command with
`--debug`; docs level directory already scaffolded.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against `.specify/memory/constitution.md` v1.3.0 (Level 3 active).

| Gate | Status | Evidence |
|------|--------|----------|
| I. Learn From the Level | PASS | Every new component (BM25, fusion, controller, reranker, rewriter, matrix harness) maps to a Level 3 spec requirement; no component lacks a spec home. |
| II. Simple Before Sophisticated | PASS | Pure functions + Pydantic models + one small library (`rank-bm25`); no LangChain/LlamaIndex/agent/eval framework (spec Assumptions; Out of Scope). |
| III. Telco Domain From Day One | PASS | Corpus unchanged; new eval categories (error code, acronym, exact terminology) deepen the Telco domain. |
| IV. Reproducibility | PASS | `rank-bm25` added to `pyproject.toml` and locked via `uv.lock`; BM25 index rebuildable from documents; deterministic fusion; quickstart documents run/eval steps. |
| V. Explicit RAG Pipeline | PASS | New distinct stages per constitution Level 3 architecture: Query Processing → Controller → Vector+BM25+Filter → RRF → Reranker → RetrievalResult[] → Level 2 grounding unchanged. |
| VI. Retrieval Before Generation | PASS | `retrieve` command stops at RetrievalResult[]; generation still consumes evidence only (FR-007/FR-018). |
| VII. No Knowledge Outside the Corpus | PASS | Level 2 grounding pipeline untouched; rewriting changes the query, not the knowledge source; filters restrict corpus visibility. |
| VIII. Make Retrieval Inspectable | PASS | `--debug` exposes query, rewritten query, strategy, per-chunk vector/bm25 rank, RRF score, reranker score, final rank (FR-019, SC-011). |
| IX. Minimal Metadata | PASS | BM25 index stores document_id/chunk_id/text/metadata; filters generic over metadata keys (FR-002/FR-010/FR-011). |
| X. Configuration Over Hardcoding | PASS | strategy, top_k.*, fusion.method/k, filters, reranking.enabled/model/candidate_k/final_k, query_rewriting.enabled in `config/settings.yaml` + Pydantic Settings; no secrets added (FR-004/FR-013/FR-016). |
| XI. Tests From the Beginning | PASS | New suites: test_bm25, test_rrf, test_hybrid, test_metadata_filtering, test_reranker, test_query_rewriter, test_retrieval_controller; Level 0/1/2 regression preserved (FR-026/FR-027). |
| XII. CLI First | PASS | `telco-rag retrieve "..." [--strategy X] [--debug]`; no web UI (FR-018/FR-019). |
| XIII. No Premature Enterprise Architecture | PASS | No auth, RBAC, lifecycle, monitoring — filters only lay the foundation (constitution Level 3 Out of Scope). |
| XIV. Every Level Must Expose the Next Problem | PASS | experiments/lessons scaffolds record remaining limitations; plan.md transition to Level 4 preserved. |
| XV. Real Before Sophisticated | PASS | Real `rank-bm25` index over real chunks, real CrossEncoder scoring, real OpenRouter rewriting — disabled features are disabled, not stubbed. |
| XVI. Metrics Written, Not Hidden | PASS | Recall/Precision/MRR matrix, ablation A–G, latency measured in Python in-repo; results recorded in experiments.md, unmeasured cells marked unmeasured (FR-021/FR-022/FR-024). |
| XVII. Evidence Is a First-Class Object (NON-NEGOTIABLE) | PASS | Evidence builder contract unchanged; still consumes RetrievalResult[] (FR-027). |
| XVIII. Validated Citations Only (NON-NEGOTIABLE) | PASS | Citation validation untouched; Level 2 tests must pass unchanged (FR-027). |
| XIX. Abstention Is a Valid Result (NON-NEGOTIABLE) | PASS | Empty BM25/filter results flow into Level 2 sufficiency → abstention; unanswerable true-negatives preserved (edge cases, SC-001 dataset coverage). |
| XX. Prompt Constraints Alone Are Insufficient (NON-NEGOTIABLE) | PASS | Grounding enforcement untouched; retrieval claims backed by measured matrix, not prose (FR-024). |
| XXI. Separation of Retrieval, Generation, and Validation | PASS | Controller returns results only, never generates (FR-007); reranker only reorders; generator/validator untouched. |
| XXII. Two-Layer Evaluation (NON-NEGOTIABLE) | PASS | Strategy comparison reported inside retrieval layer; Level 1 metrics and Level 2 answer metrics preserved (FR-021). |
| XXIII. Surface Conflicts, Never Merge Them | PASS | Conflict behavior untouched in grounding; fusion duplicates appear once with both ranks, never silently double-counted (FR-006). |
| XXIV. Complexity Must Justify Itself (NON-NEGOTIABLE) | PASS | Ablation A–G isolates each stage's delta; every stage disable-able (reranking, rewriting); latency recorded per stage (FR-013/FR-016/FR-022/FR-023). |
| XXV. Rank Fusion, Not Score Averaging (NON-NEGOTIABLE) | PASS | RRF over ranks with configurable k; raw-score mixing prohibited and tested (FR-005/FR-006). |
| XXVI. Retrieval Provenance Is Mandatory | PASS | RetrievalResult gains vector_rank, bm25_rank, rrf_score, reranker_score, retrieval_method; absent = stage not run (FR-009). |
| XXVII. Failure Attribution by Decision Tree (NON-NEGOTIABLE) | PASS | Procedure + failure log + named regression tests specified (FR-025/FR-028, US8). |
| XXVIII. Documents Are Truth, Indexes Are Derived | PASS | BM25 index rebuilt from ingestion, never hand-edited; documents/chunks authoritative (FR-002). |
| XXIX. The Original Query Is Always Preserved (NON-NEGOTIABLE) | PASS | Original retained unmodified; rewrite default-off; fallback on failure; both queries in debug (FR-015/FR-016/FR-017). |
| Level 3 Technology Constitution | PASS | Python 3.12+, uv, Pydantic v2, PyYAML, Typer; + rank-bm25, CrossEncoder (BAAI/bge-reranker-base) — both explicitly admitted by the Level 3 constitution; OpenRouter for rewriting; pytest/Ruff/mypy. |
| Level 3 Out of Scope / Framework Constitution | PASS | No query decomposition, multi-hop, RBAC/ABAC, agents, memory, observability, CI/CD, frameworks. |

**Gate result: PASS — no violations, Complexity Tracking table stays empty.**

Post-Phase-1 re-check: PASS — design artifacts introduce no new technology
beyond the admitted `rank-bm25` + CrossEncoder, no new top-level components
beyond `src/retrieval/` sub-modules and one evaluation harness, and the
Level 2 grounding layer remains contractually untouched
(`contracts/retrieval-result-schema.md` keeps the evidence-builder input
compatible).

## Project Structure

### Documentation (this feature)

```text
specs/004-level-3-advanced-retrieval/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── retrieval-result-schema.md
│   ├── retrieval-config.md
│   └── cli-retrieve.md
├── checklists/
│   └── requirements.md  # from /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── domain.py                    # + RetrievalResult provenance fields
│                                #   (vector_rank, bm25_rank, rrf_score,
│                                #    reranker_score, retrieval_method)
├── config.py                    # + retrieval strategy/top_k/fusion/filters,
│                                #   reranking, query_rewriting settings
├── cli.py                       # + `retrieve` command (--strategy, --debug)
├── retrieval/
│   ├── __init__.py
│   ├── retriever.py             # existing vector retriever (unchanged)
│   ├── vector_store.py          # existing (unchanged)
│   ├── bm25.py                  # NEW: BM25Index, BM25Retriever
│   ├── fusion.py                # NEW: rrf_fuse() pure function
│   ├── hybrid.py                # NEW: HybridRetriever (vector + bm25 + RRF)
│   ├── reranker.py              # NEW: CrossEncoderReranker (optional)
│   ├── query_rewriter.py        # NEW: OpenRouter rewriter (default off)
│   └── controller.py            # NEW: RetrievalController (strategy select)
├── evaluation/
│   ├── metrics.py               # extended: strategy-matrix scoring (reuse)
│   └── retrieval_matrix.py      # NEW: 4 strategies × query modes, ablation,
│                                #   per-stage latency capture
├── ingestion/
│   └── (loader/chunker unchanged — BM25 index built from same chunks)
├── rag/pipeline.py              # + accepts controller results (contract
│                                #   unchanged: list[RetrievalResult])
└── (generation/, grounding/ unchanged)

tests/
├── test_bm25.py                 # NEW
├── test_rrf.py                  # NEW
├── test_hybrid.py               # NEW
├── test_metadata_filtering.py   # NEW
├── test_reranker.py             # NEW
├── test_query_rewriter.py       # NEW
├── test_retrieval_controller.py # NEW
├── test_regressions_level3.py   # NEW (failure-attribution regressions)
└── (existing Level 0/1/2 tests unchanged and passing)

config/
└── settings.yaml                # + retrieval.strategy/top_k/fusion/filters,
                                 #   reranking.*, query_rewriting.enabled

data/
├── documents/                   # unchanged (metadata fields added where
                                 #   needed for filter test cases)
└── evaluation/
    └── retrieval_questions.jsonl  # + categories: exact terminology,
                                  #   error code, acronym, multi-concept,
                                  #   ambiguous, metadata-filtered;
                                  #   + relevant_chunks labels

scripts/
└── run_retrieval_experiments.py # NEW (optional runner): matrix + ablation
                                 #   → docs/levels/.../experiments.md

docs/levels/level-03-advanced-retrieval/
├── constitution.md              # exists
├── plan.md                      # exists
├── experiments.md               # filled from recorded runs
└── lessons-learned.md           # filled from recorded runs
```

**Structure Decision**: extend the existing single-project flat `src/`
layout. All new retrieval code lands as sub-modules inside the existing
`src/retrieval/` package (which today holds `retriever.py` +
`vector_store.py`) — the controller consumes the existing `Retriever` and
`VectorStore` rather than replacing them. The conceptual
`src/telco_rag/retrieval/...` tree in the level plan is realized with the
repository's actual package layout (same reasoning as Level 2, Principle I).
`RetrievalResult` is extended with optional fields only, so the Level 2
Evidence Builder keeps working without changes (FR-027).

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
