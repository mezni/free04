---

description: "Task list template for feature implementation"
---

# Tasks: Level 3 Advanced Retrieval

**Input**: Design documents from `/specs/004-level-3-advanced-retrieval/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests ARE requested — FR-026 explicitly requires suite coverage for lexical retrieval, fusion, reranking, rewriting, filtering, strategy selection, determinism, and invalid configuration.

**Organization**: Tasks are grouped by user story (US1–US8 from spec.md) so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1…US8)
- Include exact file paths in every description

## Path Conventions

Single project: flat `src/`, `tests/` at repository root (see plan.md Project Structure). New retrieval code lands in `src/retrieval/`; evaluation additions in `src/evaluation/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dependency + shared data-model extensions every story depends on

- [X] T001 Add `rank-bm25` to `[project].dependencies` in pyproject.toml and refresh uv.lock via `uv sync` (research R9, Principle IV)
- [X] T002 Extend `RetrievalResult` with optional provenance fields (`retrieval_method`, `vector_rank`, `bm25_rank`, `rrf_score`, `reranker_score`) per contracts/retrieval-result-schema.md in src/domain.py
- [X] T003 Add contract tests for RetrievalResult provenance semantics (absent = stage not run; Level 2 fields unchanged) in tests/test_retrieval_result.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: validated configuration that ALL user stories read

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `retrieval` (strategy/top_k/fusion/filters), `reranking`, `query_rewriting` settings blocks with Pydantic validation (closed strategy set, k ≥ 1, rrf-only) per contracts/retrieval-config.md in src/config.py
- [X] T005 [P] Add matching defaults (`strategy: vector`, top_k 20/20/20/5, `fusion: {method: rrf, k: 60}`, `filters: {}`, `reranking.enabled: true`, `query_rewriting.enabled: false`) to config/settings.yaml (depends: T004)
- [X] T006 [P] Add config validation tests (invalid strategy → clear error, defaults, final_k > candidate_k warning/clamp) in tests/test_retrieval_config.py (depends: T004)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Lexical Retrieval Finds Exact Technical Identifiers (Priority: P1) 🎯 MVP

**Goal**: BM25 lexical retriever over the same chunks as semantic retrieval, with reproducible index and top-K behavior (FR-001…FR-003)

**Independent Test**: `uv run pytest tests/test_bm25.py -q` — query "X2 timeout 504" through the BM25 retriever and verify the exact chunk returns in top-K with document ID, chunk ID, and metadata intact; rebuild produces identical index.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [US1] Write failing tests for lexical retrieval: exact terms, error codes, acronyms, no-result queries (empty set, no error), top-K bound, descending order, metadata preservation, rebuild reproducibility in tests/test_bm25.py

### Implementation for User Story 1

- [X] T008 [US1] Implement `BM25Index` (lowercase `[a-z0-9]+` tokenization, entries with chunk_id/document_id/text/metadata, `build_from_chunks()`) in src/retrieval/bm25.py
- [X] T009 [US1] Implement `BM25Retriever.retrieve(query, top_k)` returning `RetrievalResult[]` ordered by descending BM25 score with `bm25_rank` + `retrieval_method="bm25"` provenance in src/retrieval/bm25.py (depends: T008)
- [X] T010 [US1] Wire index construction from source documents into ingestion (`uv run telco-rag ingest` builds the BM25 index alongside ChromaDB) and expose `build_bm25_index()` for on-demand construction in src/cli.py + src/retrieval/bm25.py
- [X] T011 [US1] Run `uv run pytest tests/test_bm25.py -q` green, then full `uv run pytest -q` to confirm no Level 0/1/2 regressions (FR-027)

**Checkpoint**: BM25 strategy independently functional and testable

---

## Phase 4: User Story 2 - Configurable Retrieval Strategies With Hybrid Rank Fusion (Priority: P1)

**Goal**: RetrievalController selecting vector/bm25/hybrid/hybrid_reranked from config and CLI, fusing via deterministic RRF, never averaging raw scores (FR-004…FR-009)

**Independent Test**: run the same question under each strategy via `uv run telco-rag retrieve "..." --strategy <s>` (all four exit 0 with ranked results + strategy recorded); run hybrid twice and diff the outputs (byte-identical, SC-004); `--strategy souped` exits 1.

### Tests for User Story 2

> Write these FIRST

- [X] T012 [P] [US2] Write failing RRF fusion tests: both systems, single/one-system results, equal & differing ranks, duplicates appear once, missing results, deterministic ordering across runs, empty input in tests/test_rrf.py
- [X] T013 [P] [US2] Write failing controller tests: strategy resolution (config vs explicit), invalid strategy fails loudly (no silent fallback), results record strategy, empty results are exit-0 in tests/test_retrieval_controller.py
- [X] T014 [P] [US2] Write failing hybrid tests: hybrid ⊇ parts behavior, one retriever empty → other's rank order preserved, disabled-stage baseline equivalence (SC-005 groundwork) in tests/test_hybrid.py

### Implementation for User Story 2

- [X] T015 [US2] Implement pure `rrf_fuse(result_lists, k)` with `Σ 1/(k + rank_i)`, chunk_id dedup, stable first-seen tie-break per research R2 in src/retrieval/fusion.py
- [X] T016 [US2] Implement `HybridRetriever` (vector + BM25 → filter hook → RRF, per-stage top_k, provenance `vector_rank`/`bm25_rank`/`rrf_score`) in src/retrieval/hybrid.py (depends: T015)
- [X] T017 [US2] Implement `RetrievalController` (strategy resolution with loud failure, orchestration of rewrite→retrieve→filter→fuse→rerank, returns `RetrievalDebug`) consuming existing `Retriever` + `BM25Retriever` in src/retrieval/controller.py (depends: T004, T009, T015, T016)
- [X] T018 [US2] Add `telco-rag retrieve` command with `--strategy`, `--top-k` (normal output mode) per contracts/cli-retrieve.md in src/cli.py (depends: T017)
- [X] T019 [US2] Run `uv run pytest tests/test_rrf.py tests/test_hybrid.py tests/test_retrieval_controller.py -q` then full `uv run pytest -q` (depends: T011, T012–T018)

**Checkpoint**: all four strategies selectable from config and CLI with deterministic fusion

---

## Phase 5: User Story 3 - Per-Stage Retrieval Diagnostics (Priority: P2)

**Goal**: per-result provenance display + original/rewritten queries + per-stage latency sufficient for first-failing-stage attribution (FR-019, FR-023 partial, SC-011)

**Independent Test**: `uv run telco-rag retrieve "..." --strategy hybrid --debug` shows for every result: strategy, semantic rank, lexical rank, fusion score, final rank; stages that did not run are visibly absent; latency block present; `Query:` always the original.

### Tests for User Story 3

> Write these FIRST

- [X] T020 [US3] Write failing tests: debug output shows all applicable provenance per result, absent stages omitted (never fabricated 0), original query always shown, latency keys only for stages that ran in tests/test_cli_retrieve_debug.py

### Implementation for User Story 3

- [X] T021 [US3] Instrument per-stage `time.perf_counter()` latency capture (`rewrite`, `embed`, `vector`, `bm25`, `filter`, `fuse`, `rerank`, `total`) + `stages_skipped` on RetrievalDebug in src/retrieval/controller.py (depends: T017)
- [X] T022 [US3] Render `--debug` output per contracts/cli-retrieve.md §3 (Query line, provenance per result, `Stages skipped`, Latency block) in src/cli.py (depends: T018, T021)
- [X] T023 [US3] Run `uv run pytest tests/test_cli_retrieve_debug.py -q` then full `uv run pytest -q` (depends: T020–T022)

**Checkpoint**: retrieval failures attributable to the first stage that lost the chunk, from CLI output alone

---

## Phase 6: User Story 4 - Metadata Filtering (Priority: P2)

**Goal**: generic key/value filters applied uniformly to every strategy, restriction-only (FR-010, FR-011)

**Independent Test**: `uv run telco-rag retrieve "..." --filter department=network --strategy <s>` returns only matching chunks under all four strategies; empty filter set is byte-identical to unfiltered baseline; filter matching nothing → `Results: 0`, exit 0.

### Tests for User Story 4

> Write these FIRST

- [X] T024 [P] [US4] Write failing unit tests for generic `matches_filters()`: all-keys match, partial mismatch excluded, unknown key on chunk → empty, empty filters → baseline identity, filter never reorders/scores in tests/test_metadata_filtering.py
- [X] T025 [P] [US4] Write failing controller-level tests: filter applied uniformly across vector/bm25/hybrid/hybrid_reranked, new metadata key works without code changes in tests/test_metadata_filtering.py (append to same file after T024)

### Implementation for User Story 4

- [X] T026 [US4] Implement generic `matches_filters(metadata, filters)` (all-equality semantics) in src/retrieval/filters.py
- [X] T027 [US4] Apply filters centrally in `RetrievalController` after retrieval, before fusion/reranking, for every strategy in src/retrieval/controller.py (depends: T026)
- [X] T028 [US4] Add repeatable `--filter key=value` CLI option (YAML scalar parsing, merges over config filters) in src/cli.py (depends: T018, T027)
- [X] T029 [US4] Ensure corpus metadata supports the filter test cases (add missing metadata fields such as department/product to data/documents/*.md front matter where needed for `metadata_filtered` category)
- [X] T030 [US4] Run `uv run pytest tests/test_metadata_filtering.py -q` then full `uv run pytest -q` (depends: T024–T029)

**Checkpoint**: filters demonstrably uniform and restriction-only across all strategies

---

## Phase 7: User Story 5 - Cross-Encoder Reranking of the Candidate Pool (Priority: P2)

**Goal**: optional cross-encoder reranking of the fused pool with candidate_k/final_k bounds, disable-able with exact hybrid fall-through (FR-012…FR-014)

**Independent Test**: `uv run telco-rag retrieve "..." --strategy hybrid_reranked --debug` shows `reranker_score` per result ordered descending; with `reranking.enabled: false` output equals `--strategy hybrid` byte-for-byte and `Stages skipped: rerank` appears (SC-005).

### Tests for User Story 5

> Write these FIRST — inject a fake scorer, no model download

- [X] T031 [US5] Write failing tests with injected fake scorer: order by reranker score, candidate pool bounds (nothing outside pool), final_k slice, pool < final_k → all returned no error, scores recorded, disabled → fusion order identical + no reranker_score in tests/test_reranker.py

### Implementation for User Story 5

- [X] T032 [US5] Implement `CrossEncoderReranker` with lazy model load (`BAAI/bge-reranker-base` from config) and injectable scorer for tests in src/retrieval/reranker.py
- [X] T033 [US5] Wire `hybrid_reranked` strategy into `RetrievalController` honoring `reranking.enabled` (graceful fall-through = fusion order, recorded as skipped) in src/retrieval/controller.py (depends: T032, T017)
- [X] T034 [US5] Run `uv run pytest tests/test_reranker.py -q` then full `uv run pytest -q` (depends: T031–T033)

**Checkpoint**: reranker measurable against fusion ordering, toggleable for ablation

---

## Phase 8: User Story 6 - Optional Query Rewriting With the Original Preserved (Priority: P2)

**Goal**: default-off LLM query rewriting that always preserves the original and falls back on failure (FR-015…FR-017, Principle XXIX)

**Independent Test**: with `query_rewriting.enabled: true`, `retrieve ... --debug` shows both `Query:` (original, unchanged) and `Rewritten query:`; with default config, `Rewritten query: (not run)`; with gateway down, warning on stderr and retrieval still succeeds with original query (exit 0).

### Tests for User Story 6

> Write these FIRST — mock the gateway, hermetic (tests/test_rag_pipeline.py pattern)

- [X] T035 [US6] Write failing tests: default disabled (no rewrite attempted), rewrite preserves original field, output validated as exactly one non-empty query, gateway error/empty/garbage → fallback to original, debug shows both, separate modes in tests/test_query_rewriter.py

### Implementation for User Story 6

- [X] T036 [US6] Implement `QueryRewriter` using existing gateway src/generation/llm.py (temperature 0, mandate: preserve intent/identifiers, exactly one query, no assumptions) with validation + fallback per research R6 in src/retrieval/query_rewriter.py
- [X] T037 [US6] Wire rewrite stage into `RetrievalController` behind `query_rewriting.enabled`, populate `rewritten_query` on RetrievalDebug in src/retrieval/controller.py (depends: T036, T017)
- [X] T038 [US6] Run `uv run pytest tests/test_query_rewriter.py -q` then full `uv run pytest -q` (depends: T035–T037)

**Checkpoint**: rewriting measurable as a separate experimental mode, original never lost

---

## Phase 9: User Story 7 - Strategy Comparison, Ablation, and Latency Baseline (Priority: P3)

**Goal**: full evaluation matrix (4 strategies × query modes), ablation A–G, per-stage latency recorded — numbers not assumptions (FR-020…FR-024)

**Independent Test**: `uv run python scripts/run_retrieval_experiments.py` produces a matrix where every question × strategy cell has Recall@1/3/5/10, Precision@1/3/5/10, MRR, and every ablation row has latency figures (unmeasured cells visibly `TBD`).

### Tests for User Story 7

> Write these FIRST

- [X] T039 [P] [US7] Write failing tests for matrix computation: all questions × 4 strategies scored, metric reuse matches evaluation/metrics.py values, missing labels handled, latency aggregation keys in tests/test_retrieval_matrix.py

### Implementation for User Story 7

- [X] T040 [US7] Extend `EvaluationQuestion` with `relevant_chunks` (default `[]`) and extend data/evaluation/retrieval_questions.jsonl to the eight categories (semantic, exact_terminology, error_code, acronym, multi_concept, ambiguous, metadata_filtered, unanswerable) with chunk-level labels in src/domain.py + data/evaluation/retrieval_questions.jsonl
- [X] T041 [US7] Implement retrieval matrix (per question × strategy × query mode: Recall@1/3/5/10, Precision@1/3/5/10, MRR via existing evaluation/metrics.py; per-stage latency aggregation from RetrievalDebug) in src/evaluation/retrieval_matrix.py (depends: T017, T040)
- [X] T042 [US7] Add ablation runner for configurations A–G (vector; bm25; vector+bm25; +fusion; +rerank; +rewrite; +rewrite+rerank, `--rewrite` opt-in) emitting Markdown to docs/levels/level-03-advanced-retrieval/experiments.md in scripts/run_retrieval_experiments.py (depends: T041)
- [X] T043 [US7] Run the matrix + ablation and record measured results into docs/levels/level-03-advanced-retrieval/experiments.md; write `TBD` for genuinely unmeasured cells, never estimates (FR-024)
- [X] T044 [US7] Run `uv run pytest tests/test_retrieval_matrix.py -q` then full `uv run pytest -q` (depends: T039–T043)

**Checkpoint**: SC-001/SC-002/SC-003/SC-006/SC-007 measurable from recorded output

---

## Phase 10: User Story 8 - Failure Analysis, Regression Suite, and Documentation (Priority: P3)

**Goal**: attribution procedure classifies every significant failure to its first losing stage; named regression tests; level docs completed (FR-025, FR-028, FR-029)

**Independent Test**: pick a failed matrix question → walk the decision tree in lessons-learned.md → failure log entry names first failing stage + fix + regression test; `uv run pytest -q` shows that named test passing and all Level 0/1/2 tests unchanged (SC-008, SC-009).

### Implementation for User Story 8

- [X] T045 [US8] Document the failure-attribution decision tree (corpus → semantic → lexical → hybrid fusion → reranking → rewriting) as a runnable procedure in docs/levels/level-03-advanced-retrieval/lessons-learned.md
- [X] T046 [US8] Walk every significant matrix failure through the procedure; fill the failure log (§7 of docs/levels/level-03-advanced-retrieval/experiments.md) with question, per-stage outcomes, first failing stage, fix, regression test name (FailureLogEntry schema, data-model.md)
- [X] T047 [US8] Add one named regression test per logged failure in tests/test_regressions_level3.py (depends: T046)
- [X] T048 [US8] Fill docs/levels/level-03-advanced-retrieval/experiments.md narrative: why each technique, measured results + latency, winning strategy per category from measurements (SC-010), remaining limitations (FR-029)
- [X] T049 [US8] Fill docs/levels/level-03-advanced-retrieval/lessons-learned.md body (why each technique introduced, failure cases, what to reconsider at Level 4)
- [X] T050 [US8] Verify FR-027/SC-008: run full `uv run pytest -q` and confirm 100% of Level 0/1/2 tests pass unchanged, including tests/test_regressions_level2.py and tests/test_rag_pipeline.py

**Checkpoint**: level knowledge durable — procedure, log, regressions, docs all in place

---

## Phase 11: Polish & Cross-Cutting Concerns

- [X] T051 [P] Static gates clean: `uv run ruff check . && uv run ruff format --check . && uv run mypy`
- [X] T052 Run quickstart.md scenarios V1–V17 end-to-end and record any deviations in docs/levels/level-03-advanced-retrieval/lessons-learned.md
- [X] T053 [P] Final full regression `uv run pytest -q` with coverage check on new modules (src/retrieval/*, src/evaluation/retrieval_matrix.py)
- [X] T054 Constitution re-check: verify all v1.3.0 Level 3 gates still PASS (esp. XXIV–XXIX) and update the Level 3 definition-of-done in docs/levels/level-03-advanced-retrieval/plan.md if any step changed during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately
- **Foundational (Phase 2)**: Depends on Setup (T001–T003) — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational **and US1** (controller orchestrates the BM25 retriever)
- **US3 (Phase 5)**: Depends on US2 (debug renders controller output)
- **US4 (Phase 6)**: Depends on US2 (filters applied in controller); US3 not required
- **US5 (Phase 7)**: Depends on US2 (rerank sits on hybrid pool); US3 not required
- **US6 (Phase 8)**: Depends on US2 (rewrite stage in controller); independent of US4/US5
- **US7 (Phase 9)**: Depends on US2 + US5 + US6 (matrix runs all strategies and both query modes); benefits from US3 latency instrumentation
- **US8 (Phase 10)**: Depends on US7 (failures come from the matrix) and US4
- **Polish (Phase 11)**: Depends on all delivered stories

### User Story Dependencies

- **US1 (P1)**: Foundational only → independently testable via tests/test_bm25.py
- **US2 (P1)**: Foundational + US1 → independently testable via `retrieve` CLI + tests/test_rrf.py etc.
- **US3 (P2)**: US2 → independently testable via `--debug`
- **US4 (P2)**: US2 → independently testable via `--filter`
- **US5 (P2)**: US2 → independently testable via `hybrid_reranked` + disable toggle
- **US6 (P2)**: US2 → independently testable via config toggle + mocked gateway
- **US7 (P3)**: US2+US5+US6 → independently testable via experiments script
- **US8 (P3)**: US7 → independently testable via failure log + named regressions

### Within Each User Story

- Tests FIRST (must fail) → implementation → story test run → full regression
- Models/entities before services; services before CLI wiring

### Parallel Opportunities

- Setup: T001 ∥ T002 (different files); T003 after T002
- Foundational: T005 ∥ T006 (after T004)
- US2 tests: T012 ∥ T013 ∥ T014 (three different test files)
- US4 tests: T024 ∥ T025
- Story branches after US2 completes: US3, US4, US5, US6 are mutually independent (all touch controller only in their own phase; parallelize across different files: src/cli.py edits are sequential within each story)
- Polish: T051 ∥ T053

---

## Parallel Example: User Story 2

```bash
# Launch all three test files together first (TDD):
Task: "Write failing RRF fusion tests ... in tests/test_rrf.py"        (T012)
Task: "Write failing controller tests ... in tests/test_retrieval_controller.py" (T013)
Task: "Write failing hybrid tests ... in tests/test_hybrid.py"         (T014)

# Then implementation sequence (file dependencies):
Task: "Implement rrf_fuse() in src/retrieval/fusion.py"                (T015)
Task: "Implement HybridRetriever in src/retrieval/hybrid.py"           (T016)
Task: "Implement RetrievalController in src/retrieval/controller.py"   (T017)
Task: "Add retrieve command in src/cli.py"                             (T018)
```

---

## Implementation Strategy

### MVP First (US1 + US2 — both P1)

1. Phase 1: Setup (dependency + provenance fields)
2. Phase 2: Foundational config (CRITICAL — blocks all stories)
3. Phase 3: US1 lexical retriever → tests/test_bm25.py green
4. Phase 4: US2 controller + fusion + `retrieve` CLI → determinism diff passes
5. **STOP and VALIDATE**: four strategies runnable from CLI, Level 2 suite green
6. MVP delivered: strategy comparison possible

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → test independently (BM25 quality for exact identifiers)
3. US2 → test independently (**MVP**: selectable strategies + fusion)
4. US3 + US4 + US5 + US6 (P2, mutually independent) → each testable alone
5. US7 → matrix + ablation measured → US8 → failures attributed, docs filled
6. Polish: static gates, quickstart V1–V17, constitution re-check

### Constraints While Executing

- Level 0/1/2 tests must stay green after every story checkpoint (FR-027)
- Never average raw scores across retrievers (Principle XXV)
- Rewriting stays default-off; original query never mutated (Principle XXIX)
- Unmeasured experiment cells → `TBD`, never estimated (FR-024)
- Commit after each task or logical group; stop at any checkpoint to validate independently
