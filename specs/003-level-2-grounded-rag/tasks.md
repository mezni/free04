---
description: "Task list template for feature implementation"
---

# Tasks: Level 2 Grounded RAG

**Input**: Design documents from `/specs/003-level-2-grounded-rag/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — explicitly requested by the feature specification
(FR-020/FR-021 mandate test coverage; spec §Testing). Write tests FIRST
and confirm they FAIL before implementing each task.

**Organization**: Tasks are grouped by user story so each story can be
implemented, tested, and delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Include exact file paths in every description

## Path Conventions

Single project: `src/`, `tests/`, `data/`, `docs/` at repository root
(matches plan.md structure; flat modules under `src/` with `sys.path`
imports per existing convention).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a clean baseline before any Level 2 work

- [X] T001 Run baseline verification from repo root: `uv run pytest -q && uv run ruff check . && uv run mypy` and record the starting state in specs/003-level-2-grounded-rag/plan.md (all must be green)
- [X] T002 [P] Verify no new runtime dependencies are needed for Level 2 (pyproject.toml dependencies and uv.lock must remain unchanged — constitution Technology Constitution)
- [X] T003 [P] Create the grounding package skeleton src/grounding/__init__.py (empty package; no code yet)

**Checkpoint**: Baseline green, zero dependency drift, package slot exists.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared domain models and configuration that EVERY user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add Evidence, Citation, and CitationVerdict models to src/domain.py per data-model.md (fields, validators, status Literal mapping; evidence_id format EVIDENCE-nnn)
- [X] T005 Add GroundedAnswer, ConflictNote, EvidenceSufficiencyDecision, GroundednessVerdict, and StructuredOutputError to src/domain.py per data-model.md (GroundedAnswer invariants: abstained→citations empty, conflicts positions ≥2, extra="forbid")
- [X] T006 [P] Add grounding configuration keys (sufficiency_threshold, min_evidence, structured_output toggle) to src/config.py and config/settings.yaml with Level 2 defaults, preserving all existing keys (Principle X)

**Checkpoint**: All shared entities exist; US1–US6 can start in parallel against them.

---

## Phase 3: User Story 1 - Grounded Answer With Evidence and Citations (Priority: P1)

**Goal**: Answers generated from explicit evidence objects, returned as a
structured answer with citations, displayed with a Sources block.

**Independent Test**: Ask a known Telco question and verify the response
contains an answer, citations naming actually-retrieved document/chunk
pairs, and a Sources block (spec US1 acceptance scenarios 1–4).

### Tests for User Story 1 (write FIRST, expect FAIL) ⚠️

- [X] T007 [P] [US1] Evidence builder tests in tests/test_evidence.py (stable EVIDENCE-nnn IDs, preserved document_id/chunk_id/title/source/text/score/rank/metadata, empty-input → empty list, missing-field error)
- [X] T008 [P] [US1] GroundedAnswer schema tests in tests/test_answer_schema.py (valid parse, missing required field → error, extra field rejected, abstained+citations inconsistency flagged, malformed provider JSON → StructuredOutputError)

### Implementation for User Story 1

- [X] T009 [US1] Implement evidence builder `build_evidence(results) -> list[Evidence]` in src/grounding/evidence_builder.py (depends: T004, T007)
- [X] T010 [P] [US1] Implement evidence-aware grounded prompt (QUESTION / EVIDENCE / INSTRUCTIONS sections per contracts/grounded-answer-schema.md) in src/generation/prompt.py, keeping the existing build_prompt untouched for Level 1
- [X] T011 [P] [US1] Add structured JSON generation to src/generation/llm.py: `response_format={"type":"json_object"}` attempt, prompt-enforced JSON fallback, raw-text return for parsing (research R1)
- [X] T012 [US1] Implement generator `generate_grounded(prompt) -> GroundedAnswer` in src/generation/generator.py: LLM → JSON → Pydantic; parse/schema failure raises StructuredOutputError (depends: T005, T010, T011)
- [X] T013 [US1] Wire grounded path in src/rag/pipeline.py: new `run_grounded()` = retrieve → build_evidence → grounded prompt → generate_grounded, returning evidence + GroundedAnswer; refactor `run()` to delegate while preserving ALL legacy dict keys (research R7, FR-022) (depends: T009, T012)
- [X] T014 [US1] Add Sources block to normal `query` output in src/cli.py per contracts/cli-grounded-output.md §1 (answer + `[document_id:chunk_id]` lines; validation FAIL banner deferred to US2) (depends: T013)
- [X] T015 [US1] Extend tests/test_rag_pipeline.py with deterministic grounded-path tests using a FakeLLM fixture: evidence built, structured answer parsed, legacy run() keys unchanged, no live LLM calls (depends: T013)

**Checkpoint**: US1 fully functional — grounded answers with sources, independently testable.

---

## Phase 4: User Story 2 - Citation Validation Against Retrieval Results (Priority: P1)

**Goal**: Every citation validated against the actual retrieval result;
invented identifiers rejected before display.

**Independent Test**: Feed citations for a nonexistent document, an
invalid chunk, and an unretrieved chunk; verify each is rejected with a
distinct verdict (spec US2 acceptance scenarios 1–5; SC-002).

### Tests for User Story 2 (write FIRST, expect FAIL) ⚠️

- [X] T016 [P] [US2] Citation validation tests in tests/test_citations.py covering VALID, UNKNOWN_DOCUMENT, UNKNOWN_CHUNK, NOT_RETRIEVED (valid chunk, not retrieved for this question), MALFORMED, duplicate dedup, empty citation list

### Implementation for User Story 2

- [X] T017 [US2] Implement pure-function citation validator `validate_citations(evidence, citations) -> list[CitationVerdict]` in src/grounding/citation_validator.py per research R2 (no I/O, no retrieval; deterministic dedup) (depends: T004, T005, T016)
- [X] T018 [US2] Attach `citation_validation` to the run_grounded() result in src/rag/pipeline.py and update src/cli.py normal-mode output per contracts/cli-grounded-output.md §1: Sources lists only VALID citations, FAIL banner with per-citation verdicts (depends: T017, T013, T014)

**Checkpoint**: US1+US2 — fabricated citations can no longer reach the user unflagged.

---

## Phase 5: User Story 3 - Abstention When Evidence Is Insufficient (Priority: P2)

**Goal**: System abstains with an explicit sufficiency decision instead of
fabricating answers from general knowledge.

**Independent Test**: Ask "What is the average 5G speed in Japan?" and
verify the abstention message with no Sources block; verify a sufficient
question still answers with citations (spec US3 acceptance scenarios 1–4).

### Tests for User Story 3 (write FIRST, expect FAIL) ⚠️

- [X] T019 [P] [US3] Abstention tests in tests/test_abstention.py: NO_EVIDENCE fast path (no LLM call), BELOW_MIN_COUNT, BELOW_THRESHOLD, MODEL_REPORTS_INSUFFICIENT, SUFFICIENT, reason ordering per research R3, abstained flag set

### Implementation for User Story 3

- [X] T020 [US3] Implement evidence-sufficiency decision `decide(evidence, model_answer=None) -> EvidenceSufficiencyDecision` in src/grounding/abstention.py (layered reasons per data-model.md; uses config keys from T006) (depends: T004, T005, T006, T019)
- [X] T021 [US3] Wire abstention into src/rag/pipeline.py: zero-evidence → abstain without generation; pass model's sufficient_evidence into decide(); expose `abstained`, `sufficient_evidence`, `evidence_sufficiency` on the result (depends: T020, T013)
- [X] T022 [US3] Abstention display in src/cli.py per contracts/cli-grounded-output.md: abstention message, no Sources block, abstention takes precedence over citations (depends: T021, T018)

**Checkpoint**: US1–US3 — grounded, validated, honest answers end to end.

---

## Phase 6: User Story 4 - Observable Grounded Pipeline in the CLI (Priority: P2)

**Goal**: Full grounding path (evidence → answer → citations →
validation → conflicts) observable in one debug run.

**Independent Test**: Run `query "..." --debug-grounding` and verify every
block in contracts/cli-grounded-output.md §3 appears; verify
`--debug-retrieval` output is byte-level unchanged (spec US4 scenarios
1–4).

### Tests for User Story 4 (write FIRST, expect FAIL) ⚠️

- [X] T023 [P] [US4] CLI grounding tests in tests/test_cli_grounding.py: --debug-grounding prints evidence IDs, sufficiency, citations, validation PASS/FAIL; generation failure after retrieval still prints evidence then exits 2; --debug-retrieval never invokes the LLM

### Implementation for User Story 4

- [X] T024 [US4] Add `--debug-grounding` flag to `query` in src/cli.py printing the full path per contracts/cli-grounded-output.md §3 (Retrieved Evidence, Evidence sufficiency, Generated Answer, Citations, Citation Validation, Conflicts, Groundedness, Final Response) (depends: T021, T018, T023)
- [X] T025 [US4] Conflict surfacing: ensure ConflictNote[] flows through run_grounded() in src/rag/pipeline.py and render a Conflicts block (debug) plus conflict line in normal mode in src/cli.py, never merged (FR-019, Principle XXIII) (depends: T005, T024)

**Checkpoint**: US1–US4 — every grounding stage is inspectable.

---

## Phase 7: User Story 5 - Answer and Groundedness Evaluation (Priority: P3)

**Goal**: Extended dataset + five answer-level metrics reported as a
separate layer beside preserved retrieval metrics.

**Independent Test**: Run `evaluate` (retrieval block unchanged) and
`evaluate --answers` (five answer metrics over every case, no
unmeasured cases) (spec US5 scenarios 1–4; SC-004, SC-005).

### Tests for User Story 5 (write FIRST, expect FAIL) ⚠️

- [X] T026 [P] [US5] Answer-metric tests in tests/test_answer_evaluation.py: correctness, abstention correctness (answerable vs unanswerable), citation validity fraction, citation completeness (INCOMPLETE_CITATIONS), per-case matrix completeness
- [X] T027 [P] [US5] Groundedness classification tests in tests/test_grounding.py: SUPPORTED / UNSUPPORTED / PARTIALLY_SUPPORTED verdicts over fixture claims+evidence, judge interface mocked

### Implementation for User Story 5

- [X] T028 [P] [US5] Inspect data/documents/*.md and add conflict/partial source documents under data/documents/ only where the existing corpus cannot produce a genuine conflict or partial-evidence case (synthetic, Telco, no real data)
- [X] T029 [US5] Create data/evaluation/grounded_answers.jsonl with answerable, unanswerable, partial, and conflict cases (fields per data-model.md; includes the "average 5G speed in Japan" unanswerable case)
- [X] T030 [US5] Add GroundedEvaluationCase to src/domain.py and loader `load_grounded_cases()` in src/evaluation/dataset.py with Level 1 loader behavior unchanged (depends: T029)
- [X] T031 [US5] Implement answer metrics in src/evaluation/answer_metrics.py (correctness, abstention accuracy, citation validity, citation completeness, groundedness aggregation — transparent Python, no framework; Principle XVI) (depends: T005, T026)
- [X] T032 [P] [US5] Implement groundedness evaluation in src/evaluation/groundedness.py: deterministic claim/evidence lexical-support baseline + `GroundednessJudge` interface for structured LLM judging (live judge mocked in tests; research R4) (depends: T005, T027)
- [X] T033 [US5] Extend `evaluate` in src/cli.py with the answer layer per contracts/cli-grounded-output.md §4 (`--answers` or `--dataset data/evaluation/grounded_answers.jsonl`), printing retrieval block and answer block as separate labeled layers (depends: T030, T031, T032)

**Checkpoint**: Two-layer evaluation operational; retrieval metrics preserved and reported separately.

---

## Phase 8: User Story 6 - Hallucination Tests, Experiments, and Regression Suite (Priority: P3)

**Goal**: All six hallucination scenarios tested, prompt experiments
recorded, every failure becomes a regression test, docs completed.

**Independent Test**: Full suite runs green with the new scenario and
regression files; experiments.md and lessons-learned.md contain recorded
results (spec US6 scenarios 1–5; SC-006, SC-008, SC-009).

### Tests for User Story 6 (write FIRST) ⚠️

- [X] T034 [P] [US6] Six hallucination scenario tests in tests/test_rag_pipeline.py using FakeLLM fixtures (correct evidence → correct answer; correct evidence → unsupported extra claim detected; insufficient → abstain; no evidence → abstain; conflicting → conflict reported; valid answer → missing citation flagged) per research R8
- [X] T035 [P] [US6] Named regression tests in tests/test_regressions_level2.py per FR-021: test_answer_does_not_use_external_knowledge, test_unknown_question_abstains, test_invalid_citation_rejected, test_unretrieved_citation_rejected, test_supported_answer_has_citation, test_conflicting_evidence_is_reported

### Implementation for User Story 6

- [X] T036 [P] [US6] Run prompt-strategy experiments A (simple RAG), B (evidence-only), C (+citations), D (+citations+abstention) over data/evaluation/grounded_answers.jsonl and record strategy, per-measure results, hallucination-test outcomes, conflict-test outcomes, and winning strategy in docs/levels/level-02-grounded-rag/experiments.md (FR-023, FR-025, SC-008, SC-009)
- [X] T037 [US6] Answer the lessons-learned questions and document the failure-attribution procedure (retrieval problem vs generation/grounding problem) in docs/levels/level-02-grounded-rag/lessons-learned.md (FR-018, FR-024; depends: T036)

**Checkpoint**: All six stories complete; knowledge of failure modes recorded.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Verification and cleanup that affect the whole feature

- [X] T038 [P] Run `uv run ruff format . && uv run ruff check . && uv run mypy` and fix all findings in src/grounding/, src/generation/, src/evaluation/, src/rag/, src/cli.py, src/domain.py and tests/
- [X] T039 Execute every scenario V1–V10 in specs/003-level-2-grounded-rag/quickstart.md end-to-end and confirm each expected outcome (uses live LLM where noted)
- [X] T040 [P] Update README.md and CHANGELOG.md to describe Level 2 grounded capabilities (evidence, citations, abstention, two-layer evaluation) without altering Level 1 instructions
- [X] T041 Verify every Level 2 Definition of Done and Exit Criteria item in .specify/memory/constitution.md (sections "Level 2 Quality Gates") and record pass/fail per item in specs/003-level-2-grounded-rag/checklists/requirements.md notes or a short completion note
- [X] T042 Final full regression from repo root: `uv run pytest -q && uv run ruff check . && uv run mypy` against tests/ and src/ — all Level 0/1/2 tests green (SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — no dependencies on other stories
- **US2 (Phase 4)**: Depends on Phase 2 + US1's run_grounded()/pipeline (T013, T014) — validation needs evidence and answers to validate
- **US3 (Phase 5)**: Depends on Phase 2 + US1 (T013) — abstention plugs into the grounded pipeline; display task T022 needs US2's validation display (T018)
- **US4 (Phase 6)**: Depends on US1+US2+US3 outputs (debug mode renders evidence, validation, abstention, conflicts)
- **US5 (Phase 7)**: Depends on Phase 2; answer evaluation needs generated answers (US1) and abstention labels (US3); can start dataset/loader/groundedness work (T027, T028, T029) as soon as Phase 2 completes
- **US6 (Phase 8)**: Depends on US1–US5 behaviors existing; experiment run (T036) needs the full pipeline + dataset
- **Polish (Phase 9)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — fully independent
- **US2 (P1)**: After Foundational + US1 (validates US1's citations)
- **US3 (P2)**: After Foundational + US1 (abstention inside grounded pipeline)
- **US4 (P2)**: After US1 + US2 + US3 (renders their outputs)
- **US5 (P3)**: After Foundational; evaluation consumers need US1/US3 outputs for scoring runs; T027–T030 can proceed in parallel with US4
- **US6 (P3)**: After US1–US5 (scenarios assert on all behaviors)

### Within Each User Story

1. Tests first — write, run, confirm FAIL
2. Models/entities → builders/services → pipeline/CLI wiring
3. Story checkpoint before moving on

### Parallel Opportunities

- Phase 1: T002, T003 parallel (different files)
- Phase 3 tests: T007 ∥ T008; implementation: T010 ∥ T011 (different files)
- Phase 5: T019 alone; Phase 7 tests: T026 ∥ T027; T028 ∥ T029 (data vs docs)
- Phase 8: T034 ∥ T035 ∥ T036 (three different files)
- Phase 9: T038 ∥ T040
- After Foundational: US1 ∥ US5-dataset-work (T027–T029) can proceed concurrently; US2 ∥ US3 both plug into T013 independently (separate files: citation_validator.py vs abstention.py)

---

## Parallel Example: User Story 1

```bash
# Tests first, in parallel (different files):
Task T007: "Evidence builder tests in tests/test_evidence.py"
Task T008: "GroundedAnswer schema tests in tests/test_answer_schema.py"

# Implementation pieces in parallel (different files):
Task T010: "Evidence-aware grounded prompt in src/generation/prompt.py"
Task T011: "Structured JSON mode in src/generation/llm.py"

# Then sequential integration:
Task T009 → T012 → T013 → T014 → T015
```

## Parallel Example: User Story 5

```bash
Task T026: "Answer-metric tests in tests/test_answer_evaluation.py"
Task T027: "Groundedness tests in tests/test_grounding.py"
Task T028: "Conflict/partial corpus docs under data/documents/"

# After tests exist:
Task T029 → T030 → T031 ∥ T032 → T033
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup + Phase 2: Foundational
2. Complete Phase 3: User Story 1
3. **STOP and VALIDATE**: `uv run telco-rag query "What can cause packet loss on a 5G network?"` shows Answer + Sources; `uv run pytest tests/test_evidence.py tests/test_answer_schema.py tests/test_rag_pipeline.py -q` green
4. MVP delivered: answers are evidence-grounded and cited (not yet validated)

### Incremental Delivery

1. Setup + Foundational → shared models ready
2. + US1 → grounded answers with Sources (MVP checkpoint)
3. + US2 → invalid citations rejected (trust checkpoint)
4. + US3 → honest abstention (honesty checkpoint)
5. + US4 → full grounding observability
6. + US5 → measurable grounding (two-layer evaluation)
7. + US6 → durable failure knowledge + documented experiments
8. Polish → full regression + quickstart V1–V10 + constitution DoD

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Then: Dev A → US1; Dev B → US5 dataset/groundedness (T027–T030); Dev C → US2 validator (T016–T017) against Foundational models
3. US2/US3 integrate into US1's pipeline as their tasks land; US4 serializes on US1–US3; US6 last

---

## Notes

- [P] tasks touch different files with no dependency on incomplete tasks
- [Story] labels map each task to a spec user story for traceability
- Tests are mandatory for this feature (FR-020/FR-021) — always write them first and confirm they fail
- Deterministic tests MUST use FakeLLM/fixture judges — no live LLM in pytest (spec Assumptions; FR-022)
- Commit after each task or logical group; stop at each story checkpoint to validate independently
- 42 tasks total: Setup 3, Foundational 3, US1 9, US2 3, US3 4, US4 3, US5 8, US6 4, Polish 5
