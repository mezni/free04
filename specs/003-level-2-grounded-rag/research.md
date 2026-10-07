# Phase 0 Research: Level 2 Grounded RAG

**Feature**: specs/003-level-2-grounded-rag
**Date**: 2026-10-07
**Status**: All decisions resolved — no open NEEDS CLARIFICATION items.

The feature spec required no clarifications; this document resolves the
technical unknowns in the plan's Technical Context.

---

## R1. Structured answer output from the OpenRouter-compatible endpoint

**Decision**: Request JSON output with `response_format={"type": "json_object"}`
on the existing httpx chat-completions client, and treat Pydantic
validation as the source of truth. If the endpoint ignores or rejects
`response_format`, fall back to prompt-enforced JSON ("Respond with a JSON
object matching this schema: ..."). In both cases the raw text is parsed
strictly: parse failure or schema failure raises a `StructuredOutputError`
— never silently accepted as an answer (spec FR-004).

**Rationale**: OpenRouter's support for `response_format` varies by
upstream model. A two-layer approach (transport hint + prompt mandate +
strict Pydantic parse) guarantees the contract holds regardless of
provider behavior, and malformed output becomes a visible error rather
than a plausible-looking free-text answer.

**Alternatives considered**:
- *Tool/function calling for schema* — rejected: OpenRouter tool-call
  support is also model-dependent, and it adds a protocol the level does
  not need to teach.
- *Prompt-enforced JSON only* — rejected as sole mechanism: too weak alone;
  would violate Principle XX if validation were not also deterministic.
- *Free text + regex citation extraction* — rejected: fragile, hides
  schema violations, cannot express abstention reliably.

---

## R2. Citation validation design

**Decision**: A pure function in `grounding/citation_validator.py`:
input = `list[Evidence]` (the current question's retrieval result) +
`list[Citation]` from the structured answer; build a set of
`(document_id, chunk_id)` pairs from the evidence and check each citation.
Verdicts: `VALID`, `UNKNOWN_DOCUMENT`, `UNKNOWN_CHUNK`,
`NOT_RETRIEVED`, `MALFORMED`, plus deterministic de-duplication of
identical citations. No I/O, no retrieval, no LLM (spec FR-007/FR-008).

**Rationale**: Deterministic validation is the only thing that makes
citations trustworthy (Principle XVIII); keeping it a pure function makes
every rejection case directly testable without mocks.

**Alternatives considered**:
- *Ask the model to self-check citations* — rejected: the model is the
  suspect, not the auditor (Principle XX).
- *Validate inside the retriever* — rejected: violates separation
  (Principle XXI, validator must not retrieve).
- *Validate against the whole vector DB* — rejected: a chunk that exists
  but was not retrieved for THIS question must still be rejected
  (spec US2 scenario 3).

---

## R3. Evidence-sufficiency decision

**Decision**: Layered, in this order (first hit wins):

1. **Deterministic pre-check**: zero evidence above
   `similarity_threshold` → abstain without invoking generation for the
   answer (existing Level 1 behavior preserved).
2. **Config signals**: evidence count < `min_evidence` or mean score <
   `sufficiency_threshold` (new config keys, defaulting to existing
   retrieval threshold) → candidate abstention.
3. **Model assessment**: the structured answer includes
   `sufficient_evidence: bool`; if the model reports insufficient,
   abstain.

No semantic-entailment model (plan Section 11 explicitly defers it).

**Rationale**: gives an explainable abstention path that works offline
(layer 1–2 are testable with zero LLM calls) while letting the model
override with judgment (layer 3), satisfying FR-010/FR-011 without
over-engineering.

**Alternatives considered**:
- *Threshold only* — rejected: cannot catch "retrieved similar but
  irrelevant" chunks; spec requires a structured model assessment signal.
- *LLM-only sufficiency* — rejected: non-deterministic, untestable
  offline, and unreachable when retrieval already returned nothing.

---

## R4. Groundedness and answer-correctness evaluation strategy

**Decision**: Split metrics by determinism:

- **Deterministic, in-repo, always run in CI-style tests**: citation
  validity, citation completeness (factual answers must carry ≥1 valid
  citation), abstention correctness, conflict presence, and a
  claim-support *lexical* baseline (claim token overlap against cited
  evidence text) in `evaluation/groundedness.py`.
- **Model-based judge, isolated**: full claim-level verdicts
  (SUPPORTED / UNSUPPORTED / PARTIALLY_SUPPORTED) via a structured LLM
  call in `evaluation/groundedness.py`, behind a `GroundednessJudge`
  interface. Unit tests use fixture judges; live runs are recorded only
  in `docs/levels/level-02-grounded-rag/experiments.md`.
- **Answer correctness**: expected-answer keyword/coverage scoring for
  deterministic regression use; LLM-judge comparison recorded in
  experiments only.

**Rationale**: Principle XVI requires metrics written and explainable;
the spec requires judge results but the constitution forbids hiding
evaluation behind frameworks. Isolation keeps `pytest` hermetic (FR-022:
no live-LLM assertions in the deterministic suite).

**Alternatives considered**:
- *External RAG evaluation framework (RAGAS, DeepEval)* — rejected:
  explicitly prohibited by constitution (Framework Constitution).
- *Fully deterministic only* — rejected: cannot produce real
  SUPPORTED/UNSUPPORTED verdicts required by FR-016/SC-004.
- *Fully LLM-judge* — rejected: non-hermetic tests, unexplainable scores.

---

## R5. Conflict handling at Level 2

**Decision**: No automatic semantic conflict detector. Instead: (a) the
grounded prompt instructs the model that contradictory evidence must be
reported as a conflict naming both sources; (b) the structured answer
schema carries an optional `conflicts` list
(`document_id`/`chunk_id` pairs + short description); (c) a dedicated
conflict case exists in `grounded_answers.jsonl` with expected behavior;
(d) a deterministic test asserts that when fixture evidence contains
contradictions, a fixture-model conflict response is surfaced unmerged in
CLI output.

**Rationale**: Level 2's requirement is "do not silently merge" — prompt +
schema slot + test achieves that; authority ranking / governance is
explicitly deferred (constitution Level 2 scope).

**Alternatives considered**:
- *Automated claim-contradiction detection* — rejected: needs an
  entailment model, deferred in plan Section 12/18.
- *Ignoring conflicts* — rejected: violates FR-019 and Principle XXIII.

---

## R6. CLI debug surface for the grounding path

**Decision**: Keep `--debug-retrieval` exactly as-is (Level 1 behavior and
tests unchanged: diagnostics-only, LLM not invoked). Add
`--debug-grounding`, which runs the full grounded pipeline and prints the
path: Retrieved Evidence → Generated Answer → Citations → Citation
Validation (PASS/FAIL + per-citation verdict) → Groundedness summary.
Normal mode additionally prints a `Sources:` block (FR-013).

**Rationale**: preserves Level 1's "inspect retrieval independently"
contract (Principle VIII, SC-005) while adding Level 2 observability;
two flags with disjoint meanings avoid overloading one.

**Alternatives considered**:
- *Overloading `--debug-retrieval` with generation* — rejected: breaks the
  Level 1 guarantee that this flag never invokes the LLM.
- *A single `--debug` level flag* — rejected: conflates two different
  diagnostics and would break existing flag semantics/tests.

---

## R7. Backward compatibility of `RAGPipeline.run()`

**Decision**: Keep the existing `run()` return keys (`question`, `answer`,
`retrieved_documents`, `retrieval_scores`, `used_context`, `abstention`)
and add new keys (`grounded_answer`, `evidence`, `citation_validation`,
`sufficient_evidence`, `abstained`, `conflicts`). Add a new
`run_grounded()` method as the canonical Level 2 entry point; `run()`
delegates to it and shapes the legacy dict, so Level 0/1 tests and CLI
fallback behavior remain valid (FR-022).

**Rationale**: Level 1 regression tests construct and assert this shape
directly; preserving it is cheaper and safer than rewriting history.

**Alternatives considered**:
- *Replace `run()` with a GroundedAnswer return type* — rejected: breaks
  Level 1 tests, violating FR-022 and the backward-compatibility gate.
- *Parallel Level 2 pipeline class* — rejected: duplicated orchestration
  violates "one clear responsibility per component" and Principle I.

---

## R8. Hallucination and prompt-experiment test strategy

**Decision**: All six hallucination scenarios (correct / incorrect /
incomplete / conflicting / no evidence / unknown question) are expressed
as **deterministic fixture tests**: a scripted `FakeLLM` returns
canned structured answers (valid, invalid-citation, no-citation,
abstain-when-it-should-not, conflict) against fixed evidence fixtures;
assertions cover validator and abstention behavior, never live output.
Citation-hallucination tests (nonexistent doc, invalid chunk, unretrieved
chunk) are pure validator tests (SC-002). The four prompt strategies
(A simple RAG, B evidence-only, C +citations, D +citations+abstention) are
compared in a documented experiment run recorded in `experiments.md`,
measuring the five answer-level measures (SC-009).

**Rationale**: FR-020/FR-021/FR-025 demand durable regression coverage;
live-model prompt comparisons are experiments (recorded evidence), not
assertions (spec Assumptions).

**Alternatives considered**:
- *Live-LLM integration tests in the suite* — rejected: flaky, non-hermetic,
  and contradicts the existing Level 1 test convention.
- *Skipping prompt experiments* — rejected: SC-009/FR-023 require them.

---

## R9. Dataset extension format

**Decision**: New file `data/evaluation/grounded_answers.jsonl` (keep
Level 1 `retrieval_questions.jsonl` untouched) with entries:
`id, question, answerable, expected_answer, relevant_documents,
relevant_chunks, case_type` where `case_type ∈ {answerable, unanswerable,
partial, conflict}`. Loaded by an extended loader in
`evaluation/dataset.py`; `EvaluationQuestion` gains optional
`answerable` / `expected_answer` / `relevant_chunks` / `case_type` fields
with Level 1 defaults so old entries still load unchanged.

**Rationale**: separation of datasets mirrors the two-layer evaluation
principle (XXII); additive optional fields preserve Level 1 loaders.

**Alternatives considered**:
- *Extend `retrieval_questions.jsonl` in place* — rejected: mixing layers
  makes it harder to keep retrieval metrics meaning unchanged (SC-005).
- *Separate per-case-type files* — rejected: one grounded-answer file with
  a `case_type` column is simpler to iterate and report on.
