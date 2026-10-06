---

description: "Task list template for feature implementation"
---

# Tasks: Level 0 — Naive RAG Baseline

**Input**: Design documents from `/specs/001-naive-rag-baseline/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — the feature specification explicitly requires automated
tests (spec FR-012, SC-005) and the project constitution mandates
"Tests From the Beginning" (P XI). Test tasks are included per story and
MUST be written first (fail) before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Package is `src/telco_rag/` (src layout, see plan.md "Source Code")

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create package skeleton for `src/telco_rag/` with `__init__.py`,
      `__main__.py`, and stage packages `ingestion/`, `embeddings/`,
      `retrieval/`, `generation/`, `rag/` (empty `__init__.py` each)
- [ ] T002 Configure `pyproject.toml`: build backend for src layout,
      `requires-python = ">=3.12"`, runtime deps (`numpy`, `httpx`,
      `sentence-transformers`), dev deps (`pytest`), and pytest
      configuration (testpaths `tests`)
- [ ] T003 [P] Create the synthetic Telco corpus: `data/documents/`
      with 8 Markdown files (`5g_packet_loss.md`, `5g_latency.md`,
      `lte_troubleshooting.md`, `broadband_connectivity.md`,
      `sim_activation.md`, `enterprise_sla.md`,
      `noc_incident_procedure.md`, `network_escalation.md`) — each with
      title, sections, realistic synthetic technical content, enough text
      for multiple chunks, no real customer data
- [ ] T004 Create `.env.example` mirroring every variable in
      `contracts/config.md` (with placeholder values only) and ensure
      `.env`, `.venv/`, `__pycache__/`, model cache dirs are git-ignored in
      `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `src/telco_rag/config.py`: settings loaded from
      environment (optionally `.env` via `--config`), defaults and
      validation per `contracts/config.md` (CHUNK_SIZE/OVERLAP/TOP_K/
      EMBEDDING_*/LLM_*/DOCUMENT_DIR), fail fast with variable name on
      invalid values, required-var check (LLM_BASE_URL, LLM_MODEL)
- [ ] T006 Implement core domain types in `src/telco_rag/domain.py`:
      `Document`, `Chunk`, `RetrievalResult` with fields and validation per
      `data-model.md` (document_id/chunk_id uniqueness rules, metadata
      preserved)
- [ ] T007 Implement `src/telco_rag/ingestion/loader.py`: discover `.md`
      files under `DOCUMENT_DIR`, assign `document_id`, preserve
      `document_name` and `source`, return Document objects; clear error if
      directory missing or no files (exit 1 path)
- [ ] T008 [P] Implement `src/telco_rag/ingestion/chunker.py`: fixed-size
      character chunking with `CHUNK_SIZE`/`CHUNK_OVERLAP`, produce Chunk
      objects carrying `chunk_id`, content, and inherited metadata
      (document_id, document_name, source); single chunk for
      undersized documents
- [ ] T009 [P] Write foundational deterministic tests in
      `tests/test_loader.py` and `tests/test_chunker.py` (discovery,
      content load, ID assignment, chunk sizes/overlap respected,
      metadata preserved)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ask a question and get a grounded answer (Priority: P1) 🎯 MVP

**Goal**: A developer asks a Telco question via the CLI and receives an
answer grounded in the retrieved corpus, naming its source documents
(spec User Story 1; FR-001..FR-009).

**Independent Test**: With `LLM_BASE_URL`/`LLM_MODEL` configured,
`python -m telco_rag "How do I troubleshoot 5G packet loss?"` returns the
Question, a `Retrieved Documents` list including `5g_packet_loss.md`, and a
grounded Answer — end to end in under 10 seconds.

### Tests for User Story 1 (spec-required: FR-012, SC-005)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Deterministic vector-store test in
      `tests/test_vector_store.py` (hand-crafted vectors; add/search,
      top-K respected, descending order)
- [ ] T011 [P] [US1] Deterministic retriever test in
      `tests/test_retriever.py` (query returns top-K with metadata and
      scores preserved)
- [ ] T012 [P] [US1] Prompt test in `tests/test_prompt.py` (question
      included, context included, grounding instructions included)
- [ ] T013 [P] [US1] End-to-end pipeline test in
      `tests/test_rag_pipeline.py` using mocked embedder and LLM clients
      (question → retrieval → prompt → generation; grounded-answer path and
      abstention path)

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/telco_rag/retrieval/vector_store.py`:
      in-memory numpy store (L2-normalized `(N,dim)` float32 matrix,
      cosine via dot product, `add(chunks)`/`search(query, top_k)` exact
      brute-force) per research.md §2
- [ ] T015 [US1] Implement `src/telco_rag/embeddings/embedder.py`:
      embedder protocol (`embed_documents`, `embed_query`, `dimension`)
      with `local-sentence-transformers` provider using
      `EMBEDDING_MODEL` per research.md §1
- [ ] T016 [US1] Implement `src/telco_rag/retrieval/retriever.py`:
      question → query embedding → vector search → top-K RetrievalResults
      (chunk, document_id, source, score) per data-model.md
- [ ] T017 [P] [US1] Implement `src/telco_rag/generation/prompt.py`:
      system instruction (context-only, no invented facts, explicit
      insufficiency, clear answers — per `contracts/config.md` grounding
      rules) + retrieved context + user question
- [ ] T018 [US1] Implement `src/telco_rag/generation/llm.py`: non-streaming
      OpenAI-compatible chat-completions client via httpx
      (`Accept: application/json`, `max_tokens`, `temperature=0.0`);
      map timeout/connect/HTTP 4xx-5xx/empty `choices`/`length` to readable
      errors per `contracts/config.md` provider contract
- [ ] T019 [US1] Implement `src/telco_rag/rag/pipeline.py`:
      orchestrate retrieve → prompt → generate → answer; return answer +
      retrieval record; abstention ("I don't have enough information in the
      knowledge base to answer this question.") when no context, without
      calling the LLM
- [ ] T020 [US1] Implement `src/telco_rag/cli.py` and wire
      `src/telco_rag/__main__.py`: positional `question`, `--top-k`,
      `--config`; stdout protocol (Question / Retrieved Documents / Answer
      with source names) and exit codes 0/1/2 per `contracts/cli.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Inspect what was retrieved (Priority: P2)

**Goal**: Every query output exposes question, retrieved chunks, similarity
scores, and final answer so retrieval is always inspectable (spec User Story
2; P VIII; FR-010; SC-003).

**Independent Test**: Ask any question; the CLI output includes ranked
retrieved sources WITH their similarity scores per `contracts/cli.md` — 100%
of queries (including abstentions).

### Tests for User Story 2 (spec-required: FR-010, SC-003)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US2] CLI output-contract test in
      `tests/test_cli_output.py` (mocked pipeline/LLM: assert exact Ordered
      stdout blocks Question/Retrieved Documents/Answer, score format
      `name  (score: 0.00)`, abstention `(none)`, exit codes 0/1/2)

### Implementation for User Story 2

- [ ] T022 [US2] Extend `src/telco_rag/cli.py` to render ranked similarity
      scores and abstention `(none)` exactly per `contracts/cli.md` stdout
      protocol
- [ ] T023 [US2] Ensure `src/telco_rag/rag/pipeline.py` surfaces the full
      retrieval record (ranked RetrievalResults with scores) to the CLI;
      no query path hides retrieval detail
- [ ] T024 [US2] Run end-to-end CLI verification against a real configured
      provider; confirm score values visible and stable across repeated
      identical questions (within tolerance)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce the system from a fresh checkout (Priority: P3)

**Goal**: A new developer clones the repo, follows documented setup, and has
a working, tested system (spec User Story 3; P IV; FR-011, FR-013; SC-004,
SC-005, SC-007).

**Independent Test**: On a clean environment, following `README.md` only:
install → `pytest` all green → `python -m telco_rag "How do I troubleshoot
5G packet loss?"` answers.

### Implementation for User Story 3

- [ ] T025 [P] [US3] Write `README.md`: project overview, prerequisites
      (Python 3.12+, model download note), setup steps (venv, editable
      install `.[dev]`, `.env.example` copy), run instructions, test
      instructions — enough to reproduce Level 0 with no undocumented steps
- [ ] T026 [US3] Fresh-checkout validation: create a clean venv, install,
      run `pytest`, and answer a sample question using only the README;
      fix any gaps discovered in README/pyproject/env wiring
- [ ] T027 [P] [US3] Verify `contracts/config.md` parity: every config
      variable implemented in `src/telco_rag/config.py` is present in
      `.env.example` (and vice versa); confirm no secret values exist
      anywhere in the repository (grep for placeholder markers)

**Checkpoint**: All user stories should now be independently functional for delivery to next phase

---

## Phase 6: User Story 4 - Run baseline experiments and record limitations (Priority: P4)

**Goal**: Run the fixed baseline question set, record per-question retrieval
and answers, and document known limitations as Level 1 input (spec User
Story 4; FR-014..FR-016; plan §19–§21).

**Independent Test**: `docs/levels/level-00-naive-rag/baseline.md` contains
a record for every question Q1–Q7 (question, retrieved documents, scores,
answer, observations) plus the limitations list (SC-006).

### Implementation for User Story 4

- [ ] T028 [P] [US4] Run baseline questions Q1–Q6 from `quickstart.md`
      through the CLI (covered-set: 5G packet loss, latency, SIM, SLA,
      escalation, nonexistent topic) and capture per-question output
- [ ] T029 [US4] Run the deliberate-failure set Q7 (satellite network
      handover) at least 3× plus the synonyms/ambiguous/noisy probe queries
      from spec edge cases; record abstention vs fabricated-answer behavior
- [ ] T030 [US4] Author `docs/levels/level-00-naive-rag/baseline.md`:
      one Baseline Record per question (retrieved documents, retrieval
      scores, answer, observations) following `data-model.md`, plus a
      known-limitations section (chunking splits context, irrelevant
      retrieval, no reranking, no metadata filtering, no versioning/
      approval/access control, no evaluation framework, no observability)
      as the Level 1 justification (FR-016)

**Checkpoint**: All user stories complete; baseline evidence recorded

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Run `specs/001-naive-rag-baseline/quickstart.md` validation
      end to end (setup, pytest, covered question <10s, abstention 9/10,
      edge-case call matrix) and fix failures
- [ ] T032 [P] Verify stdout protocol consistency between `cli.py` and
      `contracts/cli.md` (labels, score formatting, exit codes)
- [ ] T033 Constitution compliance pass: spot-check all 14 principles
      (esp. no secrets in repo, no stubbed enterprise features, retrieval
      always before generation, pipeline stages explicit and nameable)
- [ ] T034 [P] Code cleanup: remove dead code, consistent error messages,
      ensure `pytest` runs green from a clean environment with no warnings
      from our code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 pipeline/CLI
  internals (extends `pipeline.py` visibility + `cli.py` rendering) but is
  independently testable via mocked pipeline output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — depends on US1 being
  functional to prove the reproducibility story; docs/environment tasks are parallel-safe
- **User Story 4 (P4)**: Depends on US1 + US2 (needs a working, inspectable CLI); runs after
  scores/inspection output exists

### Within Each User Story

- Tests (included per spec FR-012) MUST be written and FAIL before implementation
- Domain/foundational components before pipeline
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T003 (corpus) parallel with T002/T004
- Phase 2: T008 (chunker) and T009 (tests) can proceed once domain types exist
- Phase 3: T010–T013 tests parallel; T014 vector_store parallel with T017 prompt;
  embedder (T015) before retriever (T016)
- Phases 4–6: US2, US3 doc tasks, and US4 aren't file-conflicting — can be staffed in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (they must fail first):
Task: "Deterministic vector-store test in tests/test_vector_store.py"
Task: "Deterministic retriever test in tests/test_retriever.py"
Task: "Prompt test in tests/test_prompt.py"
Task: "E2E pipeline test in tests/test_rag_pipeline.py (mocked embedder + LLM)"

# Launch independent implementation pieces together:
Task: "Vector store in src/telco_rag/retrieval/vector_store.py"
Task: "Prompt builder in src/telco_rag/generation/prompt.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `python -m telco_rag "How do I troubleshoot 5G packet loss?"`
   answers with grounded context and sources; pytest green (mocked e2e)
5. This is the MVP — the smallest understandable RAG system that works

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP** (grounded Q&A via CLI)
3. Add User Story 2 → retrieval inspectability (scores) → test → demo
4. Add User Story 3 → reproducibility/docs verified from fresh checkout
5. Add User Story 4 → baseline experiments + limitations recorded
6. Polish: quickstart validation, constitution compliance, cleanup

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (pipeline + core CLI)
   - Developer B: User Story 3 docs/environment tasks (README, .env parity)
   - Developer C: User Story 2 tests + score rendering spec (after US1 core lands)
3. Stories complete and integrate independently
4. User Story 4 runs last (needs working CLI + scores)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests in Phases 3–4 MUST be written and verified failing before implementation
- Commit after each logical group; stop at any checkpoint to validate the story
- Configuration surface, stdout protocol, exit codes, and prompt grounding rules are
  fixed by `contracts/config.md` and `contracts/cli.md` — deviation requires a plan update
- Corollary: real provider access is required to exercise US1/US4 end to end; mocked
  clients cover the automated suite (FR-012)