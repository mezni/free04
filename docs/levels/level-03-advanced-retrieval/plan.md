# Telco Enterprise RAG

## Level 3 Plan — Advanced Retrieval

**Version:** 1.0
**Level:** 3
**Status:** Planned
**Previous Level:** Level 2 — Grounded RAG

> File paths reflect the actual package layout: the package root is `src/`
> (e.g. `src/retrieval/retriever.py`), tests live in `tests/`.

---

# 1. Objective

Improve retrieval quality by introducing:

```text
BM25
metadata filtering
hybrid retrieval
Reciprocal Rank Fusion
cross-encoder reranking
query rewriting
retrieval strategy comparison
retrieval failure analysis
```

The Level 2 grounding pipeline must remain unchanged from the perspective of its contract.

---

# 2. Starting Point

Level 2 currently provides:

```text
Question
    ↓
Vector Retriever
    ↓
Evidence
    ↓
Grounded Generator
    ↓
Citation Validator
    ↓
Grounding Checker
    ↓
Answer
```

Level 3 changes retrieval to:

```text
Question
    ↓
Advanced Retriever
    ↓
Better Evidence
    ↓
Existing Level 2 Grounding Pipeline
```

---

# 3. Target Architecture

```text
                         Question
                            │
                            ↓
                    Query Processing
                     │            │
                     │            └── Query Rewriter
                     │
                     ↓
              Retrieval Controller
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Vector       BM25     Metadata
       Search      Search     Filter
          │          │          │
          └──────────┼──────────┘
                     ↓
                  RRF Fusion
                     ↓
               Candidate Pool
                     ↓
              Cross Encoder
                 Reranker
                     ↓
               Final Results
                     ↓
                  Evidence
                     ↓
             Grounded Generation
                     ↓
             Citation Validation
                     ↓
                 Answer
```

Target project structure additions:

```text
src/
├── retrieval/
│   ├── retriever.py          (existing — vector retrieval)
│   ├── vector_store.py       (existing)
│   ├── bm25.py               (new — BM25Index, BM25Retriever)
│   ├── hybrid.py             (new — hybrid retrieval)
│   ├── fusion.py             (new — RRF)
│   ├── reranker.py           (new — cross-encoder reranker)
│   ├── query_rewriter.py     (new — OpenRouter query rewriting)
│   └── controller.py         (new — Retrieval Controller)
│
└── evaluation/
    └── retrieval_matrix.py   (new — strategy comparison metrics)
```

---

# 4. Implementation Steps

## Step 1 — Add BM25

Add:

```text
rank-bm25
```

Create:

```text
src/retrieval/bm25.py
```

Implement:

```text
BM25Index
BM25Retriever
```

The index should operate over the same chunks used by vector retrieval.

## Step 2 — Build BM25 Index

During ingestion:

```text
Documents
    ↓
Chunks
    ↓
BM25 Index
```

Store:

```text
chunk_id
document_id
chunk text
metadata
```

The BM25 index must be reproducible from the source documents.

Do not make the BM25 index the source of truth.

## Step 3 — Add BM25 Tests

Test:

```text
exact keyword matching
technical terminology
error codes
acronyms
no-result queries
top-K behavior
metadata preservation
```

Example:

```text
Query:
"X2 timeout 504"

Expected:
chunk containing "X2 timeout 504"
```

## Step 4 — Add Metadata Filtering

Extend retrieval configuration.

Example:

```yaml
retrieval:
  strategy: vector

  filters:
    department: network
    product: 5g
```

Support filters such as:

```text
department
product
document_type
classification
source
```

Keep the filter implementation generic so future authorization policies can build on it.

## Step 5 — Add Hybrid Retrieval

Create:

```text
src/retrieval/hybrid.py
```

The hybrid retriever should execute:

```text
Vector Search
      +
BM25 Search
      ↓
Candidate Combination
```

Avoid simply averaging raw vector and BM25 scores because their score distributions are different.

## Step 6 — Implement Reciprocal Rank Fusion

Create:

```text
src/retrieval/fusion.py
```

Implement:

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

where:

```text
d = document/chunk
rank_i = rank from retrieval system i
k = configurable constant
```

The implementation should remain small and directly testable.

## Step 7 — Test RRF

Create tests for:

```text
result appearing in both systems
result appearing in only one system
equal ranks
different ranks
duplicate chunks
missing results
deterministic ordering
```

## Step 8 — Add Cross-Encoder Reranking

Create:

```text
src/retrieval/reranker.py
```

Use:

```text
BAAI/bge-reranker-base
```

through Sentence Transformers.

Input:

```text
query
candidate chunk
```

Output:

```text
reranker score
```

Pipeline:

```text
Hybrid top 20
      ↓
Reranker
      ↓
Top 5
```

## Step 9 — Reranker Configuration

Add configuration:

```yaml
reranking:
  enabled: true
  model: BAAI/bge-reranker-base
  candidate_k: 20
  final_k: 5
```

Allow reranking to be disabled.

This is important for controlled experiments.

## Step 10 — Add Query Rewriting

Create:

```text
src/retrieval/query_rewriter.py
```

Use OpenRouter.

The rewriting prompt should require:

```text
preserve user intent
expand useful terminology
preserve technical identifiers
avoid adding unsupported assumptions
return one retrieval query
```

The original query must always be preserved.

## Step 11 — Add Query Rewrite Configuration

Example:

```yaml
query_rewriting:
  enabled: false
```

The system must support:

```text
original query
```

and:

```text
rewritten query
```

as separate experimental modes.

## Step 12 — Create Retrieval Strategy Configuration

Example:

```yaml
retrieval:
  strategy: hybrid

  top_k:
    vector: 20
    bm25: 20
    hybrid: 20
    final: 5

  fusion:
    method: rrf
    k: 60

  filters: {}
```

Supported strategies:

```text
vector
bm25
hybrid
hybrid_reranked
```

---

# 5. Retrieval Result Model

Extend the existing retrieval result.

Target concept:

```text
RetrievalResult(
    document_id=...,
    chunk_id=...,
    text=...,
    score=...,
    rank=...,
    retrieval_method=...,
    metadata=...,
    vector_rank=...,
    bm25_rank=...,
    rrf_score=...,
    reranker_score=...,
)
```

Not every field must be populated for every strategy.

---

# 6. Retrieval Controller

Create:

```text
src/retrieval/controller.py
```

Responsibilities:

```text
select strategy
apply filters
rewrite query if enabled
retrieve candidates
fuse candidates
rerank candidates
return final RetrievalResult[]
```

The controller should not generate answers.

---

# 7. CLI

Extend the CLI.

Examples:

```bash
telco-rag retrieve "Why is 5G packet loss occurring?"
telco-rag retrieve \
  "Why is 5G packet loss occurring?" \
  --strategy vector
telco-rag retrieve \
  "Why is 5G packet loss occurring?" \
  --strategy bm25
telco-rag retrieve \
  "Why is 5G packet loss occurring?" \
  --strategy hybrid
telco-rag retrieve \
  "Why is 5G packet loss occurring?" \
  --strategy hybrid_reranked \
  --debug
```

Debug output should expose:

```text
Query
Rewritten Query
Strategy
Chunk
Vector Rank
BM25 Rank
RRF Score
Reranker Score
Final Rank
```

---

# 8. Evaluation Dataset

Expand:

```text
data/evaluation/retrieval_questions.jsonl
```

Include categories:

```text
semantic
exact terminology
error code
acronym
multi-concept
ambiguous
metadata-filtered
unanswerable
```

Example:

```json
{
  "question": "What causes 5G packet loss?",
  "relevant_documents": ["5g_packet_loss"],
  "relevant_chunks": ["5g_packet_loss_02"]
}
```

---

# 9. Evaluation Matrix

Every retrieval question should be evaluated with:

```text
Vector
BM25
Hybrid
Hybrid + Reranker
```

Then separately:

```text
Original Query
Rewritten Query
```

Measure:

```text
Recall@1
Recall@3
Recall@5
Recall@10

Precision@1
Precision@3
Precision@5
Precision@10

MRR
```

---

# 10. Retrieval Ablation Study

Run:

```text
Experiment A   Vector only
Experiment B   BM25 only
Experiment C   Vector + BM25
Experiment D   Vector + BM25 + RRF
Experiment E   Hybrid + Reranker
Experiment F   Hybrid + Query Rewriting
Experiment G   Hybrid + Query Rewriting + Reranker
```

Record:

```text
Recall
Precision
MRR
Latency
```

---

# 11. Failure Analysis

For every significant failure determine:

```text
Was the correct chunk in the corpus?
        ↓
Did vector retrieve it?
        ↓
Did BM25 retrieve it?
        ↓
Did hybrid retrieve it?
        ↓
Did reranking preserve it?
        ↓
Did query rewriting help?
```

This creates a retrieval-debugging methodology rather than blind tuning.

---

# 12. Grounding Integration

Do not rewrite the Level 2 grounding layer.

The new flow becomes:

```text
Question
   ↓
Retrieval Controller
   ↓
Advanced Retrieval
   ↓
RetrievalResult[]
   ↓
Evidence Builder
   ↓
Evidence[]
   ↓
Grounded Generator
   ↓
Answer
   ↓
Citation Validator
   ↓
Grounding Checker
```

---

# 13. Testing

Add:

```text
tests/test_bm25.py
tests/test_hybrid.py
tests/test_rrf.py
tests/test_reranker.py
tests/test_query_rewriter.py
tests/test_metadata_filtering.py
tests/test_retrieval_controller.py
```

Test:

```text
BM25
vector/BM25 combination
RRF
reranking
query rewriting
metadata filtering
strategy selection
deterministic behavior
empty results
invalid configuration
Level 2 grounding compatibility
```

---

# 14. Performance Measurements

Record:

```text
embedding latency
vector retrieval latency
BM25 latency
fusion latency
reranking latency
query rewriting latency
total retrieval latency
```

This will establish the first meaningful retrieval performance baseline.

---

# 15. Documentation

Create:

```text
docs/levels/level-03-advanced-retrieval/
├── constitution.md
├── plan.md
├── experiments.md
└── lessons-learned.md
```

Document:

```text
why BM25 was introduced
why hybrid retrieval was introduced
why RRF was selected
reranker results
query rewriting results
latency impact
failure cases
winning configuration
remaining limitations
```

---

# 16. Definition of Done

Level 3 is complete when (status 2026-10-08, evidence in
`experiments.md` / `lessons-learned.md`):

```text
[x] BM25 works.                              (V2; 98% test coverage)
[x] Vector retrieval still works.            (V1; Level 1/2 suites unchanged)
[x] Metadata filtering works.                (V7, all 4 strategies)
[x] Hybrid retrieval works.                  (V3; FR-006 dedup verified)
[x] RRF works.                               (V5 determinism; unit tests)
[x] Cross-encoder reranking works.           (V4, V6 disable path)
[x] Query rewriting works.                   (V9 off-by-default, V10 fallback,
                                              11 unit tests)
[x] All strategies are configurable.         (config + CLI --strategy)
[x] Retrieval diagnostics are available.     (--debug, V3/V4/V11)
[x] Evaluation dataset contains diverse
    retrieval problems.                      (28 questions, 8 categories)
[x] Vector/BM25/hybrid/reranked strategies
    are compared.                            (matrix, experiments §2/§4)
[!] Query rewriting is experimentally
    evaluated.                               PARTIAL: original-only axis
                                              measured; rewritten cells TBD
                                              (no gateway in this env) —
                                              deviations in lessons §12
[x] Latency is measured.                     (per-stage p50/p95, §5)
[x] Retrieval failures are documented.       (F-001…F-003 + named tests)
[x] Unit tests pass.                         (270 passed)
[x] Level 2 grounding tests still pass.      (22 passed, files unchanged)
[x] Documentation is updated.                (experiments, lessons, quickstart)
[x] Lessons learned are recorded.            (lessons-learned §1–§12)
```

Implementation-driven updates (no step changed structurally; these are
measured outcomes recorded into the DoD record):

1. **SC-003 refuted on this corpus** (hybrid R@10 0.94 < vector 0.98) —
   hybrid stays available, not default; re-test at Level 4 with a larger
   corpus (experiments §2).
2. **Reranker does not pay on CPU** (×154 ms for −0.04 R@5, +0.026 MRR)
   — default path remains `strategy: vector`; revisit with GPU at
   Level 4/5 (lessons §4/§6).
3. **Ablation C** implemented as vector+bm25 round-robin interleave (the
   first vector-priority concatenation degenerated to vector-only at
   k≤10 and was replaced).
4. **Latent Level 2 CLI bug fixed** en route to V13: bare
   `evaluate --answers` resolved its dataset from the Level 3 retrieval
   setting; now defaults to `grounded_dataset_path`, pinned by
   `test_evaluate_answers_flag_defaults_to_grounded_dataset`.

---

# 17. Exit Criteria

The project should be able to answer:

> **Which retrieval strategy works best for which type of Telco question?**

Measured answer (experiments §6, 2026-10-08 — ties are ties, no
assumptions):

```text
Semantic question                    → Vector             (0.7500, clear win)
Exact technical term                 → all four tie (1.0000)
Error code                           → all four tie (1.0000)
Acronym                              → all four tie (0.8750)
Mixed / multi-concept                → Hybrid (RRF)       (1.0000, tie reranked)
Ambiguous                            → Vector             (1.0000, tie hybrid)
Metadata-filtered                    → BM25               (1.0000, tie reranked)
Large candidate set                  → REFUTED: reranker −0.04 R@5, ×154 ms
Poorly phrased question              → TBD (rewriting axis unmeasured)
```

These conclusions come from evaluation results rather than assumptions
(lessons-learned §8).

---

# 18. Guiding Principle

> **Retrieve broadly, rank intelligently, measure objectively, and only add complexity when the evidence justifies it.**
