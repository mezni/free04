# Contract: CLI Grounded Output

**Feature**: specs/003-level-2-grounded-rag
**Interface**: `telco-rag` CLI (Typer), commands `query` (extended) and
`evaluate` (extended). Exit-code protocol unchanged: `0` success or
abstention, `1` usage/config error, `2` runtime failure.

## 1. `query` — normal mode (FR-013)

```text
Question:
<question>

Retrieved Documents:
1. <document_name>  (score: 0.87)
...

Answer:
<answer text>            ← or the abstention message

Sources:
[<document_id>:<chunk_id>]
[<document_id>:<chunk_id>]
```

Rules:
- `Sources:` lists exactly the **validated** citations (deduplicated).
  Citations that failed validation are NOT printed as sources; they are
  reported in a `Citation validation: FAIL` line before `Answer:`.
- Abstained answers print the abstention text and no `Sources:` line (or
  an empty block) — abstention takes precedence.
- Output remains plain text, deterministic ordering (rank order of
  evidence).

Example (invalid citation surfaced instead of hidden):

```text
Citation validation: FAIL (1 invalid)
  [ghost_doc:chunk-99] NOT_RETRIEVED

Answer:
<answer>
```

## 2. `query --debug-retrieval` — UNCHANGED (Level 1 contract)

Diagnostics only; **the LLM is never invoked**; prints per-chunk
`document_id :: chunk_id :: document_name (score)`; exit 0. Existing
tests and behavior are preserved verbatim (FR-022, Principle VIII).

## 3. `query --debug-grounding` — NEW (FR-014)

Runs the full grounded pipeline and prints the whole path:

```text
Question:
<question>

Retrieved Evidence:
EVIDENCE-001 | <document_id> | <chunk_id> | score 0.87
  <text, first 120 chars...>

Evidence sufficiency: SUFFICIENT (count=4, mean_score=0.81)
  …or: INSUFFICIENT (<REASON>)

Generated Answer:
<answer text>

Citations:
[<document_id>:<chunk_id>]  (evidence EVIDENCE-001)

Citation Validation:
PASS
  …or FAIL with one line per verdict:
  [<document_id>:<chunk_id>] UNKNOWN_DOCUMENT — not in retrieval result

Conflicts:
(none)  …or one block per ConflictNote

Groundedness:
SUPPORTED=2 UNSUPPORTED=0 PARTIALLY_SUPPORTED=1   (when evaluated)

Final Response:
<answer or abstention>
```

Rules:
- Evidence block shows all evidence in rank order with IDs — this is the
  observability requirement that makes attribution possible (SC-007).
- `Citation Validation:` line MUST be present even when there are zero
  citations (`PASS — no citations`).
- Generation failure after retrieval: print the Retrieved Evidence block,
  then `Error: generation backend unavailable: …`, exit 2 (parity with
  Level 1 fallback behavior).

## 4. `evaluate` — extended (two-layer reporting; FR-017)

Existing retrieval block is preserved byte-for-byte in meaning:

```text
Recall@K: …   Precision@K: …   MRR: …   (retrieval layer)
```

New answer-layer block (only when a grounded-answer dataset is selected,
e.g. `--dataset data/evaluation/grounded_answers.jsonl` or
`--answers` flag):

```text
Answer Evaluation: N cases (answerable A / unanswerable U / partial P / conflict C)
Answer correctness:   0.xx
Abstention accuracy:  0.xx
Citation validity:    0.xx
Citation completeness:0.xx
Groundedness:         supported s / unsupported u / partially p
Per-case: id (correct, abstain=ok, citations 3/3 valid, grounded 2/0/1)
```

Rules:
- Retrieval metrics and answer metrics MUST appear as separate labeled
  layers — never merged into a single score (Principle XXII).
- `retrieval_questions.jsonl` behavior unchanged; new dataset in
  `grounded_answers.jsonl` (research R9).

## 5. Error surfaces

| Condition | Behavior | Exit |
|-----------|----------|------|
| Empty question | `Error: Question cannot be empty` | 1 |
| Missing/invalid dataset file | `Error: evaluation dataset not found: …` | 1 |
| LLM unreachable / timeout | evidence block (if any) + `Error: generation backend unavailable: …` | 2 |
| Structured output invalid | `Error: structured output invalid: <detail>` (+ evidence in debug) | 2 |
| Citation validation FAIL (normal mode) | shown inline, answer still printed with FAIL banner | 0 |
