# Level 3 Advanced Retrieval — Lessons Learned

**Status: MEASURED — 2026-10-08** (source: `experiments.md` runs of the
same date; unmeasured cells are marked *to be measured*, never asserted).

This file answers the eight Exit-Criteria questions in the constitution
(“Level 3 Quality Gates — Exit Criteria”) and the `Document:` block in
`docs/levels/level-03-advanced-retrieval/plan.md`. Each section is filled
only from measured results.

---

## 1. Why was BM25 introduced?

Measured answer (ablation A vs B, experiments §2/§4):

- BM25 was introduced as the **exactness guarantee**: for queries with
  literal tokens (exact terminology, error codes, acronyms) it matches by
  construction and puts the anchor chunk at rank 1 — verified in the
  failure log (F-001, F-003: anchor `#0001` at BM25 rank 1) and pinned by
  `test_f001`/`test_f003`.
- On aggregates it does **not** beat vector (R@5 0.8200 vs 0.9000,
  MRR 0.8113 vs 0.8733) and the corpus produced **no category BM25 wins
  outright** — exact/error/acronym are four-way ties at the ceiling
  (experiments §6). The hypothesis “exact term → BM25” is therefore
  *consistent with* the data, not *proved* by it.
- Its measured unique contribution is coverage, not ranking: the only
  question hybrid fixes against vector (eval-019, +0.02 R@5, experiments
  §2) and the metadata-filtered category tie come from the BM25 side, and
  BM25 costs 1.6 ms p50 — effectively free (§5).

Net: introduced for lexical recall and exact-term anchors; kept because it
is cheap and never breaks exact queries — not because it wins aggregates.

---

## 2. Why was hybrid retrieval introduced?

Measured answer (C/D vs A/B, experiments §2/§4) — **complementarity was
the hypothesis; this corpus refutes it**:

- Hybrid does **not** cover failures of both singles: all three
  significant misses (F-001…F-003, §7) are also vector misses, and the
  BM25 pools never contained those chunks at any depth (F-001 tail absent
  entirely, F-002 deep-only, F-003 tail absent) — fusion cannot rescue a
  chunk neither branch retrieved.
- Worse, RRF **lost** vector-found chunks: eval-003 (#0002: vector 6 →
  hybrid 12), eval-005 (noc#0002: 9 → 13), eval-006 (@5) — net −0.02
  R@5 and −0.04 R@10 vs vector (SC-003 refuted, experiments §2).
- The one gain: eval-019 rescued via the BM25 contribution (+0.02 @5).

Conclusion recorded from data: at 20 chunks, hybrid's expected
complementarity has no headroom; the correct Level 3 stance is *keep
hybrid measurable and available, do not default to it*. Re-run the matrix
at Level 4 with a larger corpus before revisiting this conclusion.

---

## 3. Why was RRF selected?

Measured answer (C vs D, experiments §4) + constitutional rationale:

- **Data**: round-robin and RRF are indistinguishable at Recall@5/P@5
  (0.8800/0.2480 both); RRF is +0.0034 MRR and −1.9 ms. The fusion
  *method* barely matters at this scale — the measured cost of choosing
  RRF is zero.
- **Why RRF anyway**: vector cosine (bounded, query-dependent) and BM25
  scores (unbounded, corpus-dependent) cannot be averaged without
  calibration — RRF combines ranks only, is scale-free, and deterministic
  (constitution Principle XXV; RRF determinism pinned by unit tests). The
  run confirms the selection is harmless rather than superior: RRF's
  guarantee (no score calibration, no tunable weights to overfit on 20
  chunks) is bought at 0.2 ms.

---

## 4. Reranker results

Measured D vs E per category (Recall@5 / MRR, 2026-10-08 run):

| Category | Hybrid R@5 → Reranked R@5 | Hybrid MRR → Reranked MRR |
|----------|---------------------------|---------------------------|
| semantic | 0.5833 → 0.5833 (tie) | 0.6556 → 0.7361 (**+0.0805**) |
| exact terminology | 1.0000 → 1.0000 (tie) | 1.0000 → 1.0000 |
| error code | 1.0000 → 1.0000 (tie) | 1.0000 → 1.0000 |
| acronym | 0.8750 → 0.8750 (tie) | 1.0000 → 1.0000 |
| multi-concept | 1.0000 → 1.0000 (tie) | 1.0000 → 1.0000 |
| ambiguous | 1.0000 → 0.6667 (**−0.3333**) | 0.7778 → 0.6667 (−0.1111) |
| metadata-filtered | 1.0000 → 1.0000 (tie) | 0.8333 → 1.0000 (**+0.1667**) |

What the data says:

- The reranker **never raises Recall@5** on this corpus (7 categories:
  6 ties + 1 loss); the aggregate −0.04 comes entirely from *ambiguous*,
  where the cross-encoder over-trusted a topically-similar wrong chunk.
- Its real effect is **ordering within the top 5**: MRR gains on semantic
  (+0.08) and metadata-filtered (+0.17) explain the aggregate MRR +0.026
  and Recall@1 +0.06.
- It **demotes** in at least one recorded failure (F-001: dropped a
  chunk fusion had at rank 9 out of the top 10) — the decision tree
  treats this as a reranker failure case even when attribution stops
  earlier.
- Combined with the latency verdict (§6: ×154 for these deltas), the
  measured conclusion per constitution §XXIV: **reordering quality is
  real but does not pay on CPU**. Keep it measurable, not default.

---

## 5. Query rewriting results

**To be measured** (experiments §3/§4 rows F/G are TBD): no LLM gateway
was available in this environment, so original vs rewritten was never
run. Measured facts that *are* recorded:

- the stage exists, is wired, unit-tested (11 tests) and **off by
  default** (config `query_rewriting.enabled: false`, Principle XXIX);
- `--rewrite` and the matrix `--rewrite` flag are the exact commands to
  collect the missing rows (experiments §8);
- because nothing ran, “did it help poorly-phrased questions” and “did it
  ever corrupt identifiers” are both unmeasured — recorded as such, never
  assumed (FR-024); SC-006 is satisfied only on its documentation half.

Level 4 must re-run with a real `LLM_MODEL` and fill §3/§4 F/G before
any claim about rewriting's value.

---

## 6. Latency impact

Measured (experiments §4/§5):

| Component | p50 cost | Quality delta (measured) | Verdict |
|-----------|----------|--------------------------|---------|
| Embedding (bge-small) | 119.5 ms (88 % of hybrid's 135.6 ms) | required for any vector stage | unavoidable |
| BM25 | 1.6 ms | +coverage, ties exact categories | keep — free |
| Metadata filter | 0.0 ms | +coverage on filtered category | keep — free |
| RRF fusion | 0.2 ms | ±0.0034 MRR vs round-robin | keep — free |
| **Cross-encoder rerank** | **20 740 ms (99 % of reranked total)** | MRR +0.026, R@1 +0.06, **R@5 −0.04** | **latency NOT justified on CPU (§XXIV)** — ×154 for a net @5 loss |
| Query rewriting | TBD | TBD | unmeasured |

The component that costs the most is the one whose quality delta does not
pay for it: on CPU the reranker buys top-of-list ordering (MRR/R@1) with a
Recall@5 loss and a 154× latency multiplier. It stays implemented and
measurable, default path stays `strategy: vector` (135.6 ms p50).

---

## 7. Failure cases

Three significant failures, all attributed by the decision tree
(experiments §7, procedure §10 above):

```text
F-001 eval-004 (5g speed KPI tail)  → first failing stage: VECTOR (rank 9)
F-002 eval-005 (NOC operations)     → first failing stage: VECTOR (ranks 6/9)
F-003 eval-016 (NOC anomaly tail)   → first failing stage: VECTOR (rank 12)
```

Lessons the log taught:

1. **All first-stage vector semantic misses** — on this corpus the
   limiting factor is embedding rank, not lexical/fusion/reranking. The
   diagnosis prevented the tempting cross-stage “fixes” (shrink RRF k,
   grow the rerank pool) that would violate the attribution rule and
   touch stages that measured fine.
2. The reranker is a **second-order failure source**: in F-001 it demoted
   a chunk fusion had at rank 9 out of the top 10 — recorded as a
   secondary finding even though attribution stops at vector.
3. Two of three tails are **heading-less continuation chunks** whose
   labels span chunk boundaries — the corpus step is YES (chunks exist),
   but the *shape* of those chunks explains the low ranks; recorded as a
   documented limitation, not a code fix.
4. Each failure is pinned by a named hermetic test
   (`tests/test_regressions_level3.py`, FR-028) — BM25/loader facts only,
   no models (research R9).

---

## 8. Winning configuration

Measured winners (experiments §6, ties are ties — no assumptions):

```text
Semantic question                    → Vector             (0.7500, clear win)
Exact technical term                 → ALL TIE at ceiling (1.0000 ×4)
Error code                           → ALL TIE at ceiling (1.0000 ×4)
Acronym                              → ALL TIE at ceiling (0.8750 ×4)
Mixed/multi-concept                  → Hybrid (RRF)       (1.0000, tie reranked)
Ambiguous                            → Vector             (1.0000, tie hybrid)
Metadata-filtered                    → BM25               (1.0000, tie reranked)
Large candidate set                  → REFUTED (reranker −0.04 R@5, ×154 ms)
Poorly phrased question              → TBD (rewriting unmeasured)
Unanswerable                         → n/a — 3 FP each at threshold 0
```

Exit-criteria question 1 answered from data: **vector is the measured
default** (best aggregate R@5/R@10), hybrid wins exactly one category
(multi-concept), BM25 guarantees anchors and filtered coverage for
1.6 ms, reranking does not pay on CPU, rewriting is unmeasured. The
config default `strategy: vector` is therefore the measured optimum, not
a placeholder.

---

## 9. Remaining limitations

The measured limitations live in `experiments.md` §9 (FR-029, eight
items). Level 4 inherits, in priority order:

```text
1. corpus size ceiling (20 chunks) — every number, incl. the SC-003
   refutation, must be re-measured on a larger corpus
2. rewritten-query axis entirely TBD — needs a real LLM gateway run
3. reranker unusable interactively on CPU (20.7 s/query)
4. chunk-boundary labels span mid-word splits (F-001/F-003)
5. unanswerable questions: retrieval never abstains at threshold 0
   (3 FP per strategy — Level 1 threshold owns abstention)
6. error_code category has no formal codes in-corpus (ceiling may be
   artificial)
7. one machine, one run: reranker latency and ×154 are machine-bound
8. rewriting determinism unmeasured (temp 0.0 configured, never run)
```

---

## 10. Failure-analysis procedure (runnable — run it on any matrix miss)

Every significant failure is attributed with the decision tree below
(constitution “Level 3 Failure Analysis”, Principle XXVII). The tree is
operational: the definitions and steps below can be executed on any
question without interpretation.

### Definitions

```text
found at depth k (per stage)
    every relevant chunk of the question (dataset `relevant_chunks`;
    if that is empty: at least one chunk of every `relevant_documents`
    entry) has rank <= k in that stage's OUTPUT list.

stage outputs (one retrieve() call, read from --debug / the matrix harness)
    vector   = vector branch list (stage pool = stage_top_k.vector = 20)
    bm25     = BM25 branch list (stage pool = stage_top_k.bm25 = 20)
    hybrid   = post-RRF list (fused pool = stage_top_k.hybrid = 20)
    rerank   = post-reranker list (candidates = rerank_candidate_k = 20)
    rewrite  = the query string actually sent downstream

evaluation depth k = 5   (the matrix primary depth, Recall@5)
significant failure
    an answerable question where some relevant chunk is not found at
    k = 5 under ANY strategy — i.e. the best-strategy Recall@5 < 1.0.
corpus check (step 1)
    the relevant chunk ids exist in the loader+chunker output
    (labels are derived from the same chunker, so this guards ingestion,
    not the labels).
```

### The tree (first NO names the failing stage — stop there)

```text
Was the correct chunk in the corpus?     NO → corpus/chunking problem
        ↓ YES                            fix ingestion; test guards presence
Did vector retrieve it (found@5)?        NO → vector miss
        ↓                                record the actual rank; sub-causes:
                                         embedder similarity / rank below
                                         depth / threshold / top-K
Did BM25 retrieve it (found@5)?          NO → BM25 miss (tokenization or
        ↓                                lexical gap; note whether the chunk
                                         exists deeper in the BM25 pool)
Did hybrid retrieve it (found@5)?        NO → fusion miss (RRF k / pool)
        ↓
Did reranking preserve it?               NO → reranker demotion
        ↓                                (a chunk fusion had at <=5 was
                                         pushed below 5, or a top-10 member
                                         was dropped from the top 10)
Did query rewriting help?                helped / neutral / hurt / not run
                                         (never run ⇒ None, not "neutral")
```

### Execution steps

```text
1. Confirm significance: best-strategy Recall@5 < 1.0 (matrix, §6/§2).
2. For each stage in tree order, retrieve the question at top_k = 10
   (vector/bm25/hybrid/hybrid_reranked) and check found@5; record the
   actual rank of every missing chunk, including deeper pool positions.
3. Walk the tree; the FIRST "NO" is the first failing stage.
4. Fix targets ONLY that stage (constitution: no cross-stage tuning).
5. Write one row into experiments.md §7 (FailureLogEntry schema,
   data-model.md): question, per-stage booleans (None = not tested),
   first failing stage, fix, regression test name.
6. Add a named hermetic test in tests/test_regressions_level3.py that
   pins the recorded stage outcome (FR-028). Tests must stay model-free
   (research R9): BM25/loader facts for lexical/corpus claims, fakes for
   fusion mechanics — never a live embedder or reranker.
```

Worked example (the three misses of the 2026-10-08 run) are recorded in
`experiments.md` §7 as F-001…F-003, with their tests in
`tests/test_regressions_level3.py`.

---

## 11. Grounding integration note

**Confirmed (T050, 2026-10-08):** the advanced retriever wires into the
existing grounding path with **zero Level 2 changes**:

- `tests/test_rag_pipeline.py` + `tests/test_regressions_level2.py`:
  **22 passed, files unchanged** (`git diff` empty) — the Level 2
  grounding contract (evidence → generate → validate → citations) is
  untouched (constitution “Level 3 Backward Compatibility”).
- Full suite **269 passed** (Level 0/1/2 + Level 3), was 266 before US8
  added the three failure regressions.
- The only pre-existing test files touched anywhere were
  `tests/test_loader.py` and `tests/test_chunker.py` — **pure additions**
  (+48 lines, 0 deletions) covering US4 YAML front matter. No existing
  Level 0/1 assertion was modified or removed.

Lesson recorded: adding index-time metadata required *new* ingestion
tests, not *changed* ones — the front-matter parser is strictly additive
(documents without front matter keep `metadata == {}`), which is why the
Level 0 suite stayed green untouched.

---

## 12. Quickstart validation (V1–V17, 2026-10-08)

All scenarios from `specs/004-level-3-advanced-retrieval/quickstart.md`
were executed. Results and deviations:

| # | Result | Notes |
|---|--------|-------|
| V1 | PASS | vector baseline ranked, top = 5g_packet_loss#0001 (Level 1 parity) |
| V2 | PASS | BM25 scores, exact-terminology hits surfaced |
| V3 | PASS | `vector_rank` + `bm25_rank` + `rrf_score` per result; duplicates once |
| V4 | PASS | `reranker_score` present, order differs from V3; latency block includes `rerank` (60.9 s cold incl. model load on the 1-CPU box) |
| V5 | PASS* | results/scores byte-identical across runs; *deviation: the measured `Latency (ms)` line is wall-clock and differs by design — determinism applies to content, not timings |
| V6 | PASS | `reranking.enabled: false` → identical to V3, `Stages skipped: rewrite, rerank`, no `reranker_score`; config restored after |
| V7 | PASS | `--filter category=5g` identical semantics under all 4 strategies; only 5g chunks returned |
| V8 | PASS | exit 1 + “valid: vector, bm25, hybrid, hybrid_reranked” |
| V9 | PASS | default config: `Rewritten query: (not run)` |
| V10 | PASS | rewriting on, no credentials → `warning: query rewrite failed (LLM API error 401 …); using original query: …`, exit 0, both Query lines shown |
| V11 | PASS | provenance lines show only stages that ran; skipped stages absent from latency block, listed under `Stages skipped:` |
| V12 | DEVIATION | no gateway credentials → clean `Error: generation backend unavailable: LLM API error 401` + retrieved docs; the grounded-answer + `Citation validation: PASS` output requires a valid `LLM_API_KEY` (gateway scenario, out of this environment) |
| V13 | DEVIATION + FIX | bare `evaluate --answers` was **broken** (pre-existing latent CLI bug: the default path resolved to `settings.eval_dataset_path` — the Level 3 retrieval dataset — and crashed `GroundedEvaluationCase` validation). Fixed in `src/cli.py` (default now `settings.grounded_dataset_path`), pinned by `test_evaluate_answers_flag_defaults_to_grounded_dataset`. With no credentials the answer layer then fails on the 401 (pre-existing Level 2 error propagation) — full §4 report needs the gateway |
| V14 | PASS | matrix + ablation recorded in experiments.md (rewritten cells TBD — no gateway) |
| V15 | PASS | experiments.md §7 has F-001…F-003 with first failing stage + test names |
| V16 | PASS | full suite green (see §11; final count after the V13 fix: 270) |
| V17 | PASS | `ruff check` + `ruff format --check` + `mypy` all clean |

Environment notes (not code deviations): every cold CLI start pays
~70 s wall-clock on unauthenticated HF Hub model loading on this 1-CPU
box; reranker latencies quoted here are cold-start numbers, the warm
matrix p50 is 20.7 s (experiments §5).
