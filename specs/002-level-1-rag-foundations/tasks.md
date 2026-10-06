---

description: "Task list for Level 1 RAG Foundations feature implementation"
---

# Tasks: Level 1 — RAG Foundations

**Input**: Design documents from `/specs/002-level-1-rag-foundations/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests ARE included. The feature specification mandates them — US5/FR-013 ("all existing tests continue to pass") and constitution principle XI ("Tests From the Beginning", NON-NEGOTIABLE test coverage list incl. models, embeddings, vector-store, retrieval thresholds, evaluation).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths below assume single project (flat `src/` package per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: uv packaging, YAML config, tooling. All Level 0 tests still pass at the end of this phase (only `pyproject.toml`, new config files, no source changes).

- [x] T001 Update `pyproject.toml`: add `[build-system]` (setuptools), runtime deps (`pydantic>=2`, `pydantic-settings`, `chromadb`, `openai`, `pyyaml`, `typer`), run `uv lock` + `uv sync`
- [x] T002 [P] Add dev deps (`ruff`, `mypy`, `pytest-cov`) and `[tool.ruff]` / `[tool.mypy]` sections to `pyproject.toml`
- [x] T003 [P] Create `config/settings.yaml` with the full schema from `specs/002-level-1-rag-foundations/contracts/config-contract.md` (corpus, chunking, retrieval incl. `vector_db_path`/`collection`, embedding default `BAAI/bge-small-en-v1.5`, evaluation, llm)
- [x] T004 [P] Create `.env.example` documenting all required vars (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY) and ensure `.env` is in `.gitignore`
- [x] T005 [P] Create `data/evaluation/` directory with `.gitkeep` (evaluation dataset lands in US4)

**Checkpoint**: `uv run pytest` → 29 Level 0 tests pass; `uv run telco-rag "question"` still works (env vars from `.env`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic v2 domain models, pydantic-settings config, real embedder API — all three blocks EVERY user story. No user story work before this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Migrate `src/domain.py` from dataclasses to Pydantic v2 `BaseModel`: `Document`, `Chunk` (add `chunk_index`), `RetrievalResult` (drop fake `used_context` score>0 property), `Answer`, and new `RetrievalQuery` (question, top_k, similarity_threshold, optional metadata_filter) per `data-model.md` — keep existing field names so Level 0 tests still construct them
- [x] T007 [P] Refactor `src/config.py` → `pydantic-settings`: load `config/settings.yaml` as base, env vars as overrides (keep exact env names DOCUMENT_DIR/CHUNK_SIZE/CHUNK_OVERLAP/TOP_K/EMBEDDING_*/LLM_*), fail-fast validation per `contracts/config-contract.md`
- [x] T008 [P] Refactor `src/embeddings/embedder.py` → real `sentence-transformers` API: `embed()`, `embed_batch()`, `dimension()`; default model `BAAI/bge-small-en-v1.5` (384-dim); remove hash-based fallback from the production path
- [x] T009 [P] Create `tests/test_models.py` covering Pydantic validation: Document/Chunk required fields, `chunk_index`, RetrievalQuery defaults + metadata_filter, RetrievalResult score/rank (constitution XI)

**Checkpoint**: Foundation ready — `uv run pytest` green (32 tests); user story implementation can begin in parallel.

---

## Phase 3: User Story 1 — Real Embedding and Vector Retrieval (Priority: P1) 🎯 MVP

**Goal**: Replace the fake hash-embedding + numpy store with sentence-transformers (bge-small-en-v1.5) embeddings stored in persistent ChromaDB, with typed metadata preserved and an ingest→query flow (FR-001/002/003/004/016).

**Independent Test**: Ingest the 8 Telco docs, query "What causes 5G packet loss?", and verify ranked chunks come from the correct documents (`5g_packet_loss`) with meaningful similarity scores, and that chunks survive an application restart.

### Tests for User Story 1 (write first, expect FAIL before implementation) ⚠️

- [x] T010 [P] [US1] Create `tests/test_embeddings.py`: similar sentences → higher cosine similarity than unrelated ones (deterministic model `all-MiniLM-L6-v2`, US1/acceptance 4)
- [x] T011 [P] [US1] Rewrite `tests/test_vector_store.py` for a ChromaDB-backed store (temp dir): add/count, `reset()` recreates collection (FR-016), `query` top_k clamp, persistence across store reopen, distance→score conversion, metadata_filter
- [x] T012 [P] [US1] Rewrite `tests/test_retriever.py` for `RetrievalQuery`: descending score order, rank assignment, similarity_threshold filtering, metadata_filter restrict

### Implementation for User Story 1

- [x] T013 [P] [US1] Add `chunk_index` passthrough in `src/ingestion/chunker.py` Chunk construction (`f"{doc_id}#{index:04d}"` + index field)
- [x] T014 [P] [US1] Implement `src/retrieval/vector_store.py` backed by `chromadb.PersistentClient(path=vector_db_path)`: `add(chunks, embeddings)` with explicit embeddings + metadata (document_id, document_name, source, chunk_id, chunk_index), `reset()`, `count()`, `query(query_embedding, top_k, metadata_filter)` converting Chroma distances to scores (`1 - distance`), clamp top_k to collection size (per `contracts/store-and-retriever.md`)
- [x] T015 [US1] Implement `src/retrieval/retriever.py` using `RetrievalQuery` (depends T014): embed query → store.query → sort by score desc → drop below similarity_threshold → assign ranks
- [x] T016 [US1] Wire `src/rag/pipeline.py`: build `RetrievalQuery` from config (top_k/threshold), call `retriever.retrieve`, keep Level 0 abstention behavior (depends T015)
- [x] T017 [US1] Add `ingest` command to `src/cli.py`: reset collection (FR-016) → `discover_documents` → `chunk_document` → `embed_batch` → `store.add`; report doc count, chunk count, elapsed time
- [x] T018 [US1] Make `query` command in `src/cli.py` run over the real store through pipeline.run (retains existing four-block output protocol)
- [x] T019 [US1] Update `tests/test_chunker.py` to assert `chunk_index` values

**Checkpoint**: US1 functional — `uv run telco-rag ingest` then `uv run telco-rag query "What causes 5G packet loss?"` returns 5g_packet_loss chunks with scores; restart + re-query still returns them.

---

## Phase 4: User Story 2 — Retrieval Diagnostics (Priority: P2)

**Goal**: `--debug-retrieval` shows `document_id :: chunk_id :: filename :: score` per chunk WITHOUT invoking the LLM (FR-007, US2), plus FR-017 clear-error + non-zero exit when LLM unreachable.

**Independent Test**: Run a query with `--debug-retrieval` pointing LLM at a dead port → diagnostics print; exit code 0 and NO LLM call.

### Tests for User Story 2 (write first, expect FAIL before implementation) ⚠️

- [x] T020 [P] [US2] Extend `tests/test_cli_output.py`: `--debug-retrieval` prints per-chunk line format `document_id :: chunk_id :: filename :: score`; LLM client mock asserts no generate() call when flag active
- [x] T021 [P] [US2] Extend `tests/test_rag_pipeline.py`: LLM `RuntimeError`/unreachable → clear error surface + non-zero exit code, and debug retrieval results still printed before the error (FR-017)

### Implementation for User Story 2

- [x] T022 [US2] Migrate `src/cli.py` to `typer`: subcommands `query`, `ingest`, `evaluate`, options `--top-k`, `--debug-retrieval`, `--config` per `contracts/CLI.md` (preserve exit codes 0/1/2)
- [x] T023 [US2] Implement `--debug-retrieval` diagnostics block in `src/cli.py`: per-chunk line `document_id :: chunk_id :: filename (score: 0.XX)` + first-120-chars text preview, printed BEFORE any generation (FR-007, SC-003/SC-007)
- [x] T024 [US2] Implement FR-017 in `src/cli.py`: catch generation errors → stderr `Error: generation backend unavailable (...)`, exit 2; debug block still prints first

**Checkpoint**: `uv run telco-rag query "..." --debug-retrieval` shows per-chunk diagnostics and works with LLM_BASE_URL pointing at a dead port.

---

## Phase 5: User Story 3 — Configurable Retrieval and Chunking (Priority: P2)

**Goal**: chunk_size/chunk_overlap/top_k/similarity_threshold all change behavior from `config/settings.yaml` or env/CLI without code edits (FR-005/006/011, SC-004); `--top-k` override honored.

**Independent Test**: Change `chunk_size` 500→1000 in `config/settings.yaml`, re-ingest, verify chunk count and boundaries change and NO stale chunks remain (FR-016); change `top_k` 4→8, verify up to 8 results.

### Tests for User Story 3 (write first, expect FAIL before implementation) ⚠️

- [x] T025 [P] [US3] Create `tests/test_config.py`: env var overrides YAML value; validated settings reject chunk_overlap>=chunk_size, top_k<1, similarity_threshold outside [-1,1] (config-contract.md)
- [x] T026 [P] [US3] Extend `tests/test_retriever.py`: top_k override respected; similarity_threshold excludes low-score results; `--top-k` reaches retriever via CLI

### Implementation for User Story 3

- [x] T027 [US3] Wire `--top-k` CLI override + `similarity_threshold` from config into the `RetrievalQuery` built in `src/rag/pipeline.py` and `src/cli.py` (depends T022)
- [x] T028 [US3] Drive `chunk_size`/`chunk_overlap` from settings in the `ingest` command in `src/cli.py` (no code edits to change chunking)
- [x] T029 [US3] Verify/complete re-ingest reset semantics in `src/cli.py` `ingest` so a chunk-config change leaves zero stale vectors (FR-016; add assertion to `tests/test_vector_store.py`)

**Checkpoint**: Config-only experiment loop works end-to-end — edit YAML, re-ingest, observe different chunk boundaries/results.

---

## Phase 6: User Story 4 — Retrieval Evaluation (Priority: P3)

**Goal**: `data/evaluation/retrieval_questions.jsonl` (20–30 questions incl. unanswerable), in-house Recall@K/Precision@K/MRR + true-negative count (FR-009/009a/010, constitution XVI), and `telco-rag evaluate`.

**Independent Test**: Run `evaluate --k 5`; verify Recall@5, Precision@5, MRR aggregate over answerable questions and a separate true-negative count for unanswerable ones.

### Tests for User Story 4 (write first, expect FAIL before implementation) ⚠️

- [x] T030 [P] [US4] Create `tests/test_evaluation.py` covering the formulas (constitution XVI): Recall@K with expected doc in top-3 → 1; expected doc not retrieved → 0; MRR with expected doc at rank 3 → 1/3; unanswerable questions excluded from aggregate and counted as true-negative/false-positive (FR-009a, `contracts/evaluation-contract.md`)

### Implementation for User Story 4

- [x] T031 [US4] Create `data/evaluation/retrieval_questions.jsonl`: 20–30 `EvaluationQuestion` entries (`id` eval-001.., `question`, `relevant_documents`, `category`), 2–4 unanswerable (empty `relevant_documents`), doc ids from the 8 real corpus files
- [x] T032 [P] [US4] Implement `src/evaluation/dataset.py`: load/validate jsonl into `EvaluationQuestion` list, report doc-not-in-corpus as a miss, never crash
- [x] T033 [P] [US4] Implement `src/evaluation/metrics.py`: `recall_at_k`, `precision_at_k`, `mrr`, true-negative/false-positive counts per `contracts/evaluation-contract.md`
- [x] T034 [US4] Add `evaluate` command (option `--k`, `--dataset`, `--config`) to `src/cli.py` + report format per evaluation contract (depends T031, T032, T033)

**Checkpoint**: `uv run telco-rag evaluate` prints Recall/Precision/MRR + unanswerable true-negative count.

---

## Phase 7: User Story 5 — Level 0 Regression (Priority: P1) + Polish

**Goal**: All Level 0 behavior preserved through the real-infrastructure upgrade (FR-013, US5): existing tests pass, unknown-question abstention works, four-block CLI protocol intact. Plus cross-cutting polish.

**Independent Test**: Run the full Level 0 suite; ask the abstention question; verify the four-block output protocol; run quickstart validation.

- [x] T035 [US5] Run full Level 0 suite (`uv run pytest`): fix any regression in `tests/test_loader.py`, `tests/test_prompt.py`, `tests/test_rag_pipeline.py`, `tests/test_cli_output.py` caused by the Level 1 upgrade; verify abstention ("I don't have enough information...") on an out-of-corpus query and the four-block output protocol
- [x] T036 [P] Run `specs/002-level-1-rag-foundations/quickstart.md` scenarios (§1–§7) and record results as SC-001…SC-009 evidence (SC-008 ingest <60s, SC-009 query-to-retrieval <3s)
- [x] T037 [P] Run `uv run ruff check src tests` and `uv run mypy src`; fix findings (dev-time gates, non-blocking for CI)
- [x] T038 [P] Update `CHANGELOG.md` (feature entry) and `README.md` (uv setup: `uv sync`, `uv run telco-rag ...`, config/settings.yaml docs)

**Checkpoint**: `uv run pytest` fully green; quickstart validation passes; Level 1 Definition of Done complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US2 (diagnostics) depends on US1 (real store/pipeline)
  - US3 (configurability) depends on US1 (real retrieval) and US2 (Typer CLI)
  - US4 (evaluation) depends on US1 (real retrieval + retriever) only
  - US5 (regression gate) runs continuously from Phase 1 onward and is finalized last
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 — MVP)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1's real pipeline; independently testable once US1 done
- **User Story 3 (P2)**: Depends on US1 + US2 CLI; independently testable
- **User Story 4 (P3)**: Depends on US1 retriever only; CAN run in parallel with US2 and US3
- **User Story 5 (P1)**: Continuous gate; final verification depends on all others

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services; services before commands
- Core implementation before integration

### Parallel Opportunities

- Phase 1: T001 vs T002–T005 all disjoint files
- Phase 2: T006 vs T007 vs T008 vs T009 disjoint
- Phase 3: T010/T011/T012 (tests) parallel; T013/T014 parallel; T015/T016/T017/T018 sequential after
- Phase 4: T020/T021 parallel; T022 then T023/T024
- Phase 5: T025/T026 parallel; T027/T028/T029 concern disjoint CLI/pipeline pieces
- Phase 6: T030 parallel with T031/T032/T033; T034 sequential after dataset+metrics
- Phase 7: T035 sequential (fix regressions first); T036/T037/T038 parallel after green

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD — expect FAIL first):
Task: "Create tests/test_embeddings.py (US1)"
Task: "Rewrite tests/test_vector_store.py for ChromaDB (US1)"
Task: "Rewrite tests/test_retriever.py for RetrievalQuery (US1)"

# Launch all independent implementations together:
Task: "Add chunk_index passthrough in src/ingestion/chunker.py (US1)"
Task: "Implement ChromaDB vector_store.py + metadata (US1)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (uv packaging, settings.yaml)
2. Complete Phase 2: Foundational (models, config, embedder) — BLOCKS all stories
3. Complete Phase 3: User Story 1 → real embeddings + ChromaDB + ingest/query
4. **STOP and VALIDATE**: quickstart §3–§5; verify persistence across restart
5. MVP demo: real retrieval with diagnostics-free query protocol

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 (MVP) → test independently → validate
3. US2 diagnostics → FR-017 hardening → validate
4. US3 config experiments → validate SC-004
5. US4 evaluation → metrics + dataset → validate SC-006
6. US5 regression + polish → full `pytest` green + quickstart SC-001..SC-009

### Parallel Team Strategy

With multiple developers after Foundational:
- Developer A: User Story 1 (blocking)
- Developer B: pull US4 dataset/metrics in parallel (needs retriever only)
- Developer C: US2 diagnostics once US1 lands
- All rejoin for US5 regression gate + polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story independently completable and testable (TDD: tests FAIL first)
- Constitution gates: XV/FR-001 real embeddings; XV/FR-002 ChromaDB; XVI/FR-010 in-house metrics; FR-016 reset-on-ingest; FR-008 metadata_filter internal-only (never CLI-exposed); FR-017 clear-error+exit2
- Commit after each task or logical group
- Existing Level 0 test env vars (LLM_BASE_URL/LLM_MODEL) remain required via conftest.py — preserved by config refactor (contracts/config-contract.md backward compat)