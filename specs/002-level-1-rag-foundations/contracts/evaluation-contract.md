# Contract: Retrieval Evaluation (FR-009 / FR-009a / FR-010 / XVI)

**Silent goal**: metrics computed from first principles in
`src/evaluation/metrics.py` (constitution XVI, NON-NEGOTIABLE), driven by a
versioned dataset, with unanswerable questions isolated as true negatives.

## Dataset — `data/evaluation/retrieval_questions.jsonl`

One `EvaluationQuestion` per line (see data-model): `id`, `question`,
`relevant_documents` (empty ⇒ unanswerable), `category`. 20–30 entries: the
majority answerable (1 expected `document_id`), plus 2–4 unanswerable
(empty list). Loaded by `src/evaluation/dataset.py` with an
`EvaluationQuestion` Pydantic list|model_validate per line; invalid line ⇒
clear error (exit 1), never silent skip.

Known doc ids (from `data/documents/`, filename minus `.md`): `5g_latency`,
`5g_packet_loss`, `broadband_connectivity`, `enterprise_sla`,
`lte_troubleshooting`, `network_escalation`, `noc_incident_procedure`,
`sim_activation`.

## Metrics (in-house formulas)

Let `Y` = question's relevant doc id(s), `R` = the top-K retrieved results
(by `RetrievalResult.document`), `|.|` = cardinality.

- **Recall@K** = `|Y ∩ R| / |Y|`  (per question; `1` if the expected doc is in
  the top-K hits, else `0/partial`). Aggregate = mean over answerable
  questions.
- **Precision@K** = `|Y ∩ R| / K`  (per question, denominator always K; a
  miss yields `0`).
- **MRR** = mean of `1 / rank_first_relevant` over answerable questions,
  where `rank_first_relevant` = the rank of the first retrieved result whose
  `document_id ∈ Y` (or `0` contribution when none retrieved — spec US-4: "a
  question whose expected document is not retrieved ⇒ recall 0").

**FR-009a / clarification**: unanswerable questions (`|Y| == 0`) are EXCLUDED
from Recall/Precision/MRR aggregates and reported separately:
- **true-negative** = unanswerable question where retrieval returned 0 results
  (correct abstention).
- **false-positive** = unanswerable question where retrieval returned ≥1
  result (system wrongly answers).

## Report Format (`telco-rag evaluate`)

```text
Evaluation: N answerable, M unanswerable (dataset: <path>)
Recall@5:   0.XX
Precision@5: 0.XX
MRR:         0.XX
Unanswerable: M questions · true-negatives T · false-positives F
Per-question: eval-001 … eval-0NN (recall / precision / reciprocal-rank)
```

## Integration

`evaluate` runs `Retriever` per question (no LLM), reuses `RetrievalQuery`
with `evaluation.default_k`. Dataset references a doc missing from the corpus
⇒ reported as a miss for that question, never a crash (spec Edge Case).