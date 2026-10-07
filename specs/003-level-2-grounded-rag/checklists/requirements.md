# Specification Quality Checklist: Level 2 Grounded RAG

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Validation iteration 1: all items pass. Two draft-time leaks were fixed
  before sign-off — a vector-store product name and a list of excluded
  framework names in the Assumptions section were rewritten as behavior and
  scope statements.
- FR-017 retains the metric names Recall@K / Precision@K / MRR; these are
  domain evaluation concepts preserved from Level 1, not implementation
  details.

## Level 2 Completion Verification (recorded 2026-10-07, T041)

Pass/fail per Level 2 Quality Gates item (source: `.specify/memory/constitution.md`
Sections 22–23). All 23 Definition-of-Done items PASS; 12/12 Exit Criteria
explanations below.

### Definition of Done — pass/fail

| # | DoD item | Status | Evidence |
|---|----------|--------|----------|
| 1 | answers generated from explicit evidence | PASS | `run_grounded` → `build_grounded_prompt` (QUESTION/EVIDENCE/INSTRUCTIONS); `test_run_grounded_builds_evidence_and_parses_answer` |
| 2 | evidence as structured objects | PASS | `domain.Evidence` (evidence_id/document_id/chunk_id/title/source/text/retrieval_score/rank) |
| 3 | evidence builder transforms results | PASS | `grounding.evidence_builder.build_evidence`; `tests/test_evidence.py` |
| 4 | answers contain citations | PASS | `GroundedAnswer.citations`; `tests/test_answer_schema.py` |
| 5 | citations reference retrieved chunks | PASS | validator: VALID only when `(doc, chunk)` ∈ evidence pairs; SC-002 |
| 6 | invalid citations detected | PASS | `tests/test_citations.py` (11 tests: unknown doc, invalid chunk, unretrieved, duplicates, missing) |
| 7 | the LLM can abstain | PASS | `GroundedAnswer.abstained` + `abstention.decide()`; `tests/test_abstention.py` |
| 8 | unknown questions tested | PASS | `test_unknown_question_abstains` (regression) + `test_run_grounded_zero_results_abstains_without_generation` |
| 9 | structured answer output validated | PASS | `parse_grounded_answer` → `StructuredOutputError` (contract rule 1); `test_run_grounded_malformed_output_raises_structured_output_error` |
| 10 | evidence sufficiency decided explicitly | PASS | `EvidenceSufficiencyDecision` + layers in `decide()`; exposed on result |
| 11 | groundedness evaluated | PASS | `evaluation.groundedness` (lexical baseline + judge); `tests/test_grounding.py` (12 tests) |
| 12 | citation correctness evaluated | PASS | claim↔evidence support assessed per claim (SUPPORTED/PARTIAL/UNSUPPORTED); correctness metric in §4 report |
| 13 | citation validity evaluated | PASS | `CitationVerdict` per citation; `citation_validity` metric (§4) |
| 14 | citation completeness evaluated | PASS | `INCOMPLETE_CITATIONS` rule; `citation_completeness` metric |
| 15 | answer correctness evaluated | PASS | `answer_correctness` (expected-token coverage; abstention-exact for unanswerable) |
| 16 | retrieval metrics remain available | PASS | `evaluate` unchanged (Recall@5 1.00/Precision@5 0.20/MRR 1.00 on rebuilt index) |
| 17 | hallucination/unsupported-answer tests | PASS | six scenarios in `test_rag_pipeline.py` (R8) |
| 18 | conflicting evidence handled explicitly | PASS | `ConflictNote` + CLI `Conflicts:` block; scenario/regression tests |
| 19 | retrieval vs generation failures separated | PASS | two-layer eval (Principle XXII) + FR-018 procedure (lessons-learned §7) |
| 20 | regression tests for every failure | PASS | `tests/test_regressions_level2.py` (6 named, FR-021) |
| 21 | experiments documented | PASS | `docs/levels/level-02-grounded-rag/experiments.md` |
| 22 | lessons learned documented | PASS | `docs/levels/level-02-grounded-rag/lessons-learned.md` |
| 23 | all behavior covered by tests | PASS | 155 tests green; live-model behavior recorded, not asserted (R8 insertion/FR-022) |

### Exit Criteria — verification of explanation

1. **Retrieval ≠ answer correctness:** correctness is token/claim-overlap vs
   `expected_answer`; retrieval delivers evidence. A short retrieval + a
   correct answer can still be a grounding violation, and a full retrieval
   can still produce an unsupported answer (lessons-learned §1–§2).
2. **What grounding means:** claims of the answer must be supported by the
   retrieved evidence and every citation must point at a retrieved chunk
   (FR-003/FR-008).
3. **What evidence means:** the structured projection of each retrieved
   result (id, document/chunk identity, metadata, score) that forms the
   *only* sanctioned input to generation (FR-001, Principle XVII).
4. **Why citations must be validated:** the model invents identifiers;
   `UNKNOWN_DOCUMENT`/`UNKNOWN_CHUNK`/`NOT_RETRIEVED` are rejected before
   display (SC-002).
5. **Why the LLM can't invent ids:** it has no authority over the index; a
   fabricated id is indistinguishable from a real one except by validator
   membership checks against retrieved evidence.
6. **What abstention means:** refusing to answer when evidence is absent,
   below `min_evidence`/`sufficiency_threshold`, or the model reports
   insufficiency — bounded output, no fabrication.
7. **Citation validity vs correctness:** validity = the citation references
   a retrieved chunk (mechanical check); correctness = the cited evidence
   actually supports the claim (groundedness). Both are evaluated
   separately (§4).
8. **Citation completeness:** every factual answer must carry ≥1 VALID
   citation; without it, the answer is flagged `INCOMPLETE_CITATIONS` even
   if its claims are otherwise supported.
9. **Identifying unsupported claims:** per-claim lexical support ratio and
   the `GroundednessJudge`; example pinned by
   `test_hallucination_scenario_unsupported_extra_claim_detected`.
10. **Why retrieval and answer evaluation are separate:** a retrieval miss
    and a generation/hallucination are different owners with different
    fixes (FR-018); merged numbers hide which layer regressed (Principle
    XXII).
11. **How conflicting evidence should be handled:** surfaced as a named
    `Conflicts:` block with both source positions — never merged into a
    single fact (FR-019).
12. **Why prompt instructions alone are insufficient:** the deterministic
    experiment shows A–D prompt deltas produce 0.00 effect (experiments.md);
    guarantees come from enforced schema + validator + abstention logic,
    not appeals (lessons-learned §4).

### Level 2 Completion Test (Section 24) — determination

All five query classes were exercised deterministically (hermetic scenarios +
the recorded experiment run); live confirmation of the LLM-bearing steps is
blocked in this environment (no credentials) and recorded as such in
quickstart.md (T039). Chain
`retrieved evidence → generated answer → citations → citation validation →
groundedness evaluation → final response` is executable via
`--debug-grounding` and implemented end-to-end in `_run_answer_outcome` +
`score_case`.
- Scope boundary: advanced retrieval techniques (hybrid search, reranking,
  query rewriting), new frameworks, and new infrastructure are explicitly
  excluded per the constitution's Level 2 out-of-scope rules.
- No [NEEDS CLARIFICATION] markers were required; the Level 2 plan and
  constitution supplied defaults for all open decisions.
