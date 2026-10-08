# Level 3 Retrieval Experiments — Strategy Comparison & Ablation Study

<!-- BEGIN:run-meta -->
**Status: MEASURED — 2026-10-08**

Command: `LLM_MODEL=<model> uv run python scripts/run_retrieval_experiments.py`

- Corpus: data/documents (10 documents, 20 chunks) | questions: 28 across 8 categories
- Query modes measured: original (rewritten: TBD — no gateway run)
- Fusion: RRF k=60 | rerank candidate_k=20, final_k=5 | evaluation top_k=10
- Per-question metadata filters applied where the dataset defines them (metadata_filtered category)
- TBD = not measured; never replaced with an estimate (FR-024)
<!-- END:run-meta -->

All tables below are templates. Every cell must be filled from a recorded
run; empty cells are not results. No number in this file may be asserted
without a corresponding run — record results, never assume them.

---

## 1. Method

Two independent axes, evaluated over
`data/evaluation/retrieval_questions.jsonl` (all eight categories):

```text
Axis 1 — strategy:   Vector | BM25 | Hybrid | Hybrid + Reranker
Axis 2 — query mode: Original Query | Rewritten Query
```

Metrics per cell:

```text
Recall@1 / @3 / @5 / @10
Precision@1 / @3 / @5 / @10
MRR
```

Plus per-stage latency (§5).

Relevance ground truth comes from `relevant_documents` / `relevant_chunks`
in the dataset. Unanswerable questions score correct only when retrieval
returns nothing relevant — they are reported separately, never averaged
into answerable Recall silently.

---

## 2. Evaluation Matrix — Strategy × Metrics

Original query, no rewriting. One row per strategy.

| Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Prec@1 | Prec@3 | Prec@5 | Prec@10 | MRR |
|----------|----------|----------|----------|-----------|--------|--------|--------|---------|-----|
<!-- BEGIN:matrix-rows -->
| Vector | 0.6000 | 0.8600 | 0.9000 | 0.9800 | 0.8000 | 0.4000 | 0.2560 | 0.1440 | 0.8733 |
| BM25 | 0.5800 | 0.7000 | 0.8200 | 0.8600 | 0.7600 | 0.3200 | 0.2320 | 0.1240 | 0.8113 |
| Hybrid (RRF) | 0.6000 | 0.8600 | 0.8800 | 0.9400 | 0.8000 | 0.4000 | 0.2480 | 0.1360 | 0.8707 |
| Hybrid + Reranker | 0.6600 | 0.7800 | 0.8400 | 0.9200 | 0.8800 | 0.3733 | 0.2480 | 0.1360 | 0.8967 |
<!-- END:matrix-rows -->

**Measured outcome (2026-10-08, 28 questions / 25 answerable):**

- Every question scored under all four strategies — SC-001 satisfied for
  the original-query axis (no unmeasured cell above).
- Best Recall@1/5/10: **Vector** at @5 (0.9000) and @10 (0.9800);
  best Recall@1 and MRR: **Hybrid + Reranker** (0.6600 / 0.8967).
  BM25 is the weakest aggregate (0.8200 @5) but guarantees the exact-
  terminology categories (see §6).
- **SC-003 is REFUTED on this corpus**: hybrid Recall@10 (0.9400) is
  *below* the better single retriever (vector 0.9800). Per-question
  attribution: RRF lost vector-found chunks on eval-003 (#0002 fell
  from vector rank 6 to hybrid rank 12) and eval-005 (noc#0002 fell
  from 9 to 13), while gaining nothing at @10; at @5 it lost eval-003
  and eval-006 and rescued eval-019 (net −0.02). Recorded as a measured
  refutation, not an implementation bug: on a 20-chunk corpus RRF's
  interleaving has little headroom to recover and chunks to lose.
  Re-evaluate at Level 4 with a larger corpus.
- All figures above are reproduced by `uv run python
  scripts/run_retrieval_experiments.py` (byte-deterministic strategies;
  reranker latencies vary with machine load).

---

## 3. Query Rewriting — Original vs Rewritten

Held strategy constant (hybrid), toggle `query_rewriting.enabled`.

| Strategy | Query mode | Recall@5 | MRR | Latency (ms) |
|----------|------------|----------|-----|--------------|
<!-- BEGIN:rewrite-rows -->
| Hybrid (RRF) | original | 0.8800 | 0.8707 | 135.6105 |
| Hybrid (RRF) | rewritten | TBD | TBD | TBD |
| Hybrid + Reranker | original | 0.8400 | 0.8967 | 20877.4075 |
| Hybrid + Reranker | rewritten | TBD | TBD | TBD |
<!-- END:rewrite-rows -->

Rewriting counts as a win only if it improves the aggregate **and** does
not systematically break the exact-terminology / error-code categories
(rewrites must preserve technical identifiers).

---

## 4. Ablation Study

| Experiment | Configuration | Recall@5 | Precision@5 | MRR | Latency (ms) |
|------------|---------------|----------|-------------|-----|--------------|
<!-- BEGIN:ablation-rows -->
| A | Vector only | 0.9000 | 0.2560 | 0.8733 | 137.4395 |
| B | BM25 only | 0.8200 | 0.2320 | 0.8113 | 1.6565 |
| C | Vector + BM25 (round-robin, no fusion) | 0.8800 | 0.2480 | 0.8673 | 137.5460 |
| D | Vector + BM25 + RRF | 0.8800 | 0.2480 | 0.8707 | 135.6105 |
| E | Hybrid + Reranker | 0.8400 | 0.2480 | 0.8967 | 20877.4075 |
| F | Hybrid + Query Rewriting | TBD | TBD | TBD | TBD |
| G | Hybrid + Query Rewriting + Reranker | TBD | TBD | TBD | TBD |
<!-- END:ablation-rows -->

Isolate deltas: C→D measures fusion alone, D→E measures the reranker
alone, D→F measures rewriting alone, F→G measures the reranker on top of
rewriting. A component is kept only if its delta justifies its latency
(constitution §18).

**Measured deltas (original-query axis):**

- **C→D (fusion alone)**: identical Recall@5/P@5 (0.8800/0.2480), MRR
  +0.0034 (0.8673 → 0.8707), latency −1.9 ms. RRF and round-robin are
  statistically indistinguishable on this corpus; RRF is kept for its
  scale-free, score-calibration-free formulation (Principle XXV), not
  because this run proves it better.
- **D→E (reranker alone)**: Recall@1 +0.06 (0.60 → 0.66), MRR +0.026
  (0.8707 → 0.8967) — the cross-encoder genuinely reorders the top of
  the list — **but** Recall@5 −0.04 (0.88 → 0.84), Recall@10 −0.02
  (0.94 → 0.92) and latency 135.6 ms → 20 877.4 ms (**×154**).
  Verdict per constitution §XXIV: **latency not justified** by the
  quality delta on CPU at candidate_k=20; F-001 additionally records a
  reranker demotion (lost a chunk the hybrid stage had at rank 9).
  Recommendation: keep the stage implementable and measured, but do not
  enable it as the default path until it runs on GPU (candidate for
  Level 4/5) — the current default `strategy: vector` is unaffected.
- **D→F, F→G (rewriting)**: TBD — no gateway run (§3, §9).

---

## 5. Latency Baseline

Per-stage timings, recorded with the ablation runs:

| Stage | p50 (ms) | p95 (ms) | Notes |
|-------|----------|----------|-------|
<!-- BEGIN:latency-rows -->
| Embedding | 119.5 | 182.6 | bge-small-en-v1.5 |
| Vector retrieval | 13.6 | 26.3 |  |
| BM25 retrieval | 1.6 | 4.4 |  |
| Metadata filter | 0.0 | 0.1 |  |
| Fusion (RRF) | 0.2 | 2.3 |  |
| Reranking | 20740.2 | 25821.1 | candidate_k = 20 |
| Query rewriting | TBD | TBD | not measured in this run |
| **Total** | 135.6 | 22164.0 | across strategies; per-config totals in §4 |
<!-- END:latency-rows -->

Reading: reranking is **99 %** of hybrid_reranked latency
(20 740 ms of 22 164 ms p95-equivalent total); embedding is the main
cost of vector/hybrid (119.5 ms p50 = 88 % of the 135.6 ms hybrid
total); BM25 (1.6 ms), metadata filtering (0.0 ms) and RRF fusion
(0.2 ms) are effectively free — they cannot move the p50 at all.

---

## 6. Per-Category Breakdown

Strategy wins are per question category, not global:

| Category | Best strategy | Evidence (Recall@5) |
|----------|---------------|---------------------|
<!-- BEGIN:category-rows -->
| semantic | Vector | Recall@5 = 0.7500 (MRR = 0.6667, n=6) |
| exact terminology | Vector | Recall@5 = 1.0000 (MRR = 1.0000, n=3) (tie with BM25, Hybrid (RRF), Hybrid + Reranker) |
| error code | Vector | Recall@5 = 1.0000 (MRR = 1.0000, n=3) (tie with BM25, Hybrid (RRF), Hybrid + Reranker) |
| acronym | Vector | Recall@5 = 0.8750 (MRR = 1.0000, n=4) (tie with BM25, Hybrid (RRF), Hybrid + Reranker) |
| multi-concept | Hybrid (RRF) | Recall@5 = 1.0000 (MRR = 1.0000, n=3) (tie with Hybrid + Reranker) |
| ambiguous | Vector | Recall@5 = 1.0000 (MRR = 0.7778, n=3) (tie with Hybrid (RRF)) |
| metadata-filtered | BM25 | Recall@5 = 1.0000 (MRR = 1.0000, n=3) (tie with Hybrid + Reranker) |
| unanswerable | n/a (unanswerable excluded from Recall) | false positives: vector 3, bm25 3, hybrid 3, hybrid_reranked 3 |
<!-- END:category-rows -->

This table is the source for the exit criterion
"which strategy works for which type of Telco question"
(constitution §24). The hypothesis there stays a hypothesis until this
table is filled.

**SC-010 verdict — winners determined from these measurements, ties are
ties (no assumptions):**

- *Confirmed*: semantic → **Vector** (0.7500, clear winner); mixed →
  **Hybrid** (multi-concept is the only category hybrid wins outright,
  tied with reranked).
- *Confirmed only as a tie*: exact terminology / error code / acronym —
  **all four strategies reach the ceiling** (1.0000 / 1.0000 / 0.8750).
  BM25's exactness guarantee is real (§7 shows it never *loses* an
  anchor) but the corpus offers no question on which it alone wins; the
  "exact term → BM25" hypothesis is therefore *consistent with* the data,
  not *proved* by it.
- *Partial*: metadata-filtered → **BM25** (1.0000, tied with reranked);
  vector also reaches 1.0000 when the generic filter is applied, so the
  measured value of the filter is coverage, not exclusivity.
- *Refuted on this corpus*: large-result-set → reranker (the reranker
  pays ×154 latency for −0.04 Recall@5, §4).
- *Unmeasured*: poorly-phrased → rewriting (§3 TBD).

---

## 7. Failure Analysis Log

For every significant failure, one row, filled with the decision tree
(Principle XXVII / constitution “Level 3 Failure Analysis”, procedure in
`lessons-learned.md` §10):

| # | Question | Correct chunk in corpus? | Vector found it? | BM25 found it? | Hybrid found it? | Rerank preserved it? | Rewrite helped? | First failing stage | Fix applied | Regression test |
|---|----------|--------------------------|------------------|-----------------|------------------|----------------------|-----------------|--------------------|-------------|-----------------|
| F-001 | eval-004 “What real-world download rates do people actually see on 5G?” (5g_speed_reporting#0001+#0002) | YES | NO — #0002 at rank 9 | NO — only 5 lexical matches; #0002 absent entirely | NO — #0002 at rank 9 | NO — reranker dropped #0002 from the top 10 (#0001 promoted to 1) | None (not run) | vector (semantic rank): paraphrase “real-world download rates” ranks the KPI-tail chunk #0002 at 9; its label spans the chunk boundary of one sentence (“median and P95 throughput figures”) | none — documented embedding-rank limitation; reranker demotion recorded as secondary finding | tests/test_regressions_level3.py::test_f001_lexical_gap_cannot_rescue_speed_reporting_tail |
| F-002 | eval-005 “Who gets paged and what do they do when monitors light up at the operations center?” (noc_incident_procedure#0001+#0002) | YES | NO — #0001@6, #0002@9 | NO — 0 of 2 in top 10 (present only at pool ranks 16/14) | NO — #0001@10, #0002@13 | YES — reranker promoted #0001 to rank 4, lost nothing | None (not run) | vector (semantic paraphrase gap): “paged”/“operations center” vs corpus “Acknowledge alert”/“NOC” | none — documented paraphrase limitation | tests/test_regressions_level3.py::test_f002_bm25_miss_on_operations_center_paraphrase |
| F-003 | eval-016 “What does a NOC do when a network anomaly is detected?” (noc_incident_procedure#0001+#0002) | YES | NO — #0002 at rank 12 (pool 20) | NO — #0002 absent from all 15 matches | NO — #0002 at rank 17 | YES — #0001 kept at rank 1; #0002 never entered the top 10 | None (not run) | vector (semantic rank): heading-less continuation chunk (starts mid-word “verity and impact scope”) ranks 12; no strategy ever surfaced it | none — documented continuation-chunk limitation; corpus step YES so chunking is not the attributed stage | tests/test_regressions_level3.py::test_f003_exact_anchor_ranks_first_and_tail_chunk_in_corpus |

Unanswerable questions (eval-026…028) return results under all four
strategies at `similarity_threshold = 0` — 3 false positives per strategy
(§6). Not a retrieval-stage failure: abstention is the downstream
threshold (FR-009a, Level 1 tests), so no tree row applies.

Rules:

* attribute the failure to the **first** stage that lost the chunk
* fix only the attributed stage
* each fixed failure becomes a named regression test in `tests/`

---

## 8. How to Run and Record

```bash
# after implementation exists
uv run telco-rag ingest                          # rebuild vector + BM25 indexes
uv run telco-rag retrieve "<q>" --strategy hybrid --debug
# evaluation matrix + ablation (rewritten mode only with --rewrite)
LLM_MODEL=<model> uv run python scripts/run_retrieval_experiments.py
```

Recording rules:

1. This file is overwritten only by a real run — note date + command used.
2. Keep previous runs: move them here before overwriting.
3. A live-model-dependent experiment (query rewriting via OpenRouter) must
   note the model used; hermetic strategies (vector/BM25/hybrid/reranker)
   must be byte-reproducible offline.
4. TBD means "not measured". Never replace TBD with an estimate.

---

## 9. Measured Limitations (FR-029)

Recorded from this run; each item is a measured fact or an explicitly
unmeasured cell — not a forecast.

1. **Corpus size ceiling**: 10 documents / 20 chunks. Every aggregate
   above (including the SC-003 refutation in §2) is valid only at this
   scale; none of these numbers generalises to a production Telco
   corpus.
2. **SC-003 refuted** (§2): hybrid Recall@10 0.9400 < vector 0.9800 —
   fusion loses chunks on this corpus. Re-test at Level 4 with a larger
   corpus before enabling hybrid by default.
3. **Rewriting axis unmeasured**: no LLM gateway in this environment →
   §3/§4 rewritten cells are TBD; SC-006 is satisfied only for the
   original-only documentation half. Level 4 must re-run with a real
   `LLM_MODEL`.
4. **Reranker is CPU-bound**: 20 740 ms p50 for 20 candidates; quality
   deltas are mixed (§4). Not usable interactively on CPU.
5. **Chunk-boundary splits**: labels span mid-word boundaries (chunk
   overlap 50 chars) — a relevant chunk can be *lexically empty* for its
   own query (F-001) and a heading-less continuation chunk can rank
   below every threshold (F-003). Ingestion is the corpus step, not the
   attributed stage.
6. **Unanswerable questions return results** under all four strategies
   at `similarity_threshold = 0` (3 FP each, §6). Abstention is owned by
   the Level 1 threshold (FR-009a), so this is out of scope here — but
   the raw retrieval layer does not abstain.
7. **error_code category semantics** are limited by the corpus (numeric
   thresholds / literal messages rather than formal error codes) — the
   1.0000 ceiling in §6 may not survive real error-code questions.
8. **One run, one machine**: strategy rows are byte-deterministic;
   reranker latency and the ×154 figure are machine-dependent (rerank
   p50 20 740 ms here; first in-process model load ≈68 s excluded).
