# Phase 1 Data Model: Level 2 Grounded RAG

**Feature**: specs/003-level-2-grounded-rag
**Date**: 2026-10-07

Existing Level 1 entities (`Document`, `Chunk`, `RetrievalQuery`,
`RetrievalResult`, `Answer`, `EvaluationQuestion`) live in `src/domain.py`
and are extended — not replaced — per FR-022.

---

## New Entities

### Evidence

Explicit representation of one retrieved chunk used to ground an answer
(FR-001). The boundary between retrieval and generation (Principle XVII).

| Field | Type | Rules |
|-------|------|-------|
| `evidence_id` | `str` | stable, ordered: `EVIDENCE-001`, `EVIDENCE-002`, … assigned by the evidence builder; non-empty |
| `document_id` | `str` | preserved from `RetrievalResult.chunk.document_id`; required |
| `chunk_id` | `str` | preserved from `RetrievalResult.chunk.chunk_id`; required |
| `title` | `str` | from chunk/document metadata (`document_name`); required |
| `source` | `str` | preserved from chunk; required |
| `text` | `str` | chunk content; non-empty |
| `retrieval_score` | `float` | preserved from `RetrievalResult.score`; in [-1, 1] |
| `rank` | `int` | preserved from `RetrievalResult.rank`; ≥ 1 |
| `metadata` | `dict[str, Any]` | preserved chunk metadata; default `{}` |

**Relationships**: 1 `RetrievalResult` → 1 `Evidence` (builder is a
lossless projection except for added `evidence_id`); referenced by
`Citation` via `(document_id, chunk_id)`.

**Validation**: builder raises if any source field is missing; evidence
IDs are unique within one run.

---

### Citation

Reference from a claim in an answer to a specific document/chunk (FR-006).

| Field | Type | Rules |
|-------|------|-------|
| `document_id` | `str` | required, non-empty |
| `chunk_id` | `str` | required, non-empty |
| `evidence_id` | `str \| None` | optional; when present must match an `Evidence.evidence_id` of the current question |

**Validation**: format-level validation only at parse time (non-empty
strings). Existence is decided by the validator, not the model.

---

### CitationVerdict *(value object, output of validation)*

| Field | Type | Rules |
|-------|------|-------|
| `citation` | `Citation` | the input citation |
| `status` | `Literal["VALID", "UNKNOWN_DOCUMENT", "UNKNOWN_CHUNK", "NOT_RETRIEVED", "MALFORMED"]` | see mapping below |
| `detail` | `str` | human-readable reason; empty for VALID |

**Status mapping** (FR-007): the validator builds the set
`{(document_id, chunk_id)}` from the current question's `Evidence[]`:

- empty/whitespace ids → `MALFORMED`
- document absent from the evidence set's document ids → `UNKNOWN_DOCUMENT`
- document present but `(document_id, chunk_id)` pair absent because that
  chunk id exists nowhere → `UNKNOWN_CHUNK`
- pair absent but document has other retrieved chunks → `NOT_RETRIEVED`
  (the "valid chunk, not retrieved for this question" case)
- pair present → `VALID`

Duplicates: identical `(document_id, chunk_id)` pairs are collapsed before
reporting; deduplication is deterministic and never inflates counts.

---

### GroundedAnswer *(structured answer; FR-004)*

| Field | Type | Rules |
|-------|------|-------|
| `answer` | `str` | answer text; required; may be the abstention message |
| `citations` | `list[Citation]` | default `[]`; may be empty only if `abstained` |
| `abstained` | `bool` | default `false` |
| `sufficient_evidence` | `bool` | model's evidence-sufficiency assessment (FR-011) |
| `conflicts` | `list[ConflictNote]` | default `[]`; required non-empty when the model detects conflicting evidence (FR-019) |

**State / invariants** (checked by a model-level validator, tested in
`test_answer_schema.py`):

- `abstained == true` → `answer` non-empty; `citations` SHOULD be empty
  (non-empty is flagged as inconsistent — edge case in spec).
- `abstained == false` and answer makes factual claims → `citations`
  non-empty, else flagged `INCOMPLETE_CITATIONS` by evaluation (not a
  parse error).
- Parse failure of provider output → `StructuredOutputError` (never a
  silent default answer).

**JSON wire form** (contract: `contracts/grounded-answer-schema.md`):

```json
{
  "answer": "...",
  "citations": [{"document_id": "...", "chunk_id": "..."}],
  "abstained": false,
  "sufficient_evidence": true,
  "conflicts": []
}
```

---

### ConflictNote *(value object)*

| Field | Type | Rules |
|-------|------|-------|
| `description` | `str` | non-empty; states the disagreement |
| `positions` | `list[Citation]` | ≥ 2 entries — the conflicting sources |

---

### EvidenceSufficiencyDecision *(output of abstention module; FR-011)*

| Field | Type | Rules |
|-------|------|-------|
| `sufficient` | `bool` | final decision |
| `reason` | `Literal["NO_EVIDENCE", "BELOW_MIN_COUNT", "BELOW_THRESHOLD", "MODEL_REPORTS_INSUFFICIENT", "SUFFICIENT"]` | explainable cause |
| `evidence_count` | `int` | ≥ 0 |
| `mean_score` | `float \| None` | `None` when count = 0 |

**Decision order** (research R3, first match wins):
`NO_EVIDENCE` → `BELOW_MIN_COUNT` → `BELOW_THRESHOLD` →
`MODEL_REPORTS_INSUFFICIENT` → `SUFFICIENT`.

---

### GroundednessVerdict *(value object; FR-016)*

| Field | Type | Rules |
|-------|------|-------|
| `claim` | `str` | non-empty extracted claim |
| `status` | `Literal["SUPPORTED", "UNSUPPORTED", "PARTIALLY_SUPPORTED"]` | required |
| `supporting_evidence_ids` | `list[str]` | evidence IDs cited as support; `[]` for UNSUPPORTED |

---

### GroundedEvaluationCase *(dataset entry; FR-015)*

New file `data/evaluation/grounded_answers.jsonl`; additive extension of
`EvaluationQuestion` so Level 1 entries load unchanged.

| Field | Type | Rules |
|-------|------|-------|
| `id` | `str` | unique; required |
| `question` | `str` | non-empty |
| `answerable` | `bool` | required (no empty-list inference for this dataset) |
| `case_type` | `Literal["answerable", "unanswerable", "partial", "conflict"]` | required |
| `expected_answer` | `str` | required for `answerable`/`partial`; `""` for `unanswerable` |
| `relevant_documents` | `list[str]` | expected doc ids |
| `relevant_chunks` | `list[str]` | expected chunk ids |
| `notes` | `str` | optional; e.g., what "partial" means for this case |

**Scoring** (`evaluation/answer_metrics.py`): per case → correctness,
abstention_correct (bool), citation_validity (fraction of VALID
verdicts), citation_completeness (supported claims cited / total),
groundedness (mean of verdicts). Unanswerable cases score abstention
exactly (SC-003).

---

## Entity relationship summary

```text
RetrievalResult ──(evidence_builder)──▶ Evidence
                                             │
GroundedAnswer.citations ──(citation_validator over Evidence[])──▶ CitationVerdict
        │
        ├── abstained ──▶ EvidenceSufficiencyDecision
        ├── conflicts ──▶ ConflictNote ──▶ Citation (positions)
        └── answer claims ──▶ GroundednessVerdict ──▶ Evidence.evidence_id

GroundedEvaluationCase ──(run pipeline)──▶ GroundedAnswer ──▶ answer_metrics report
```

## State transitions

`GroundedAnswer` is immutable after parsing. The pipeline's observable
states in one run:

```text
RETRIEVED → EVIDENCE_BUILT → GENERATED (or STRUCTURED_OUTPUT_ERROR)
          → VALIDATED (citations all VALID / any INVALID)
          → SUFFICIENT → FINAL_ANSWER
          → INSUFFICIENT → ABSTAINED
```

An INVALID citation never reaches normal-mode display unflagged: the
answer is returned with validation FAIL and flagged citations listed
(FR-007), or degraded to an abstention-style notice in strict mode.
