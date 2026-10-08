# Telco Enterprise RAG

## Level 3 Constitution — Advanced Retrieval

**Version:** 1.0
**Level:** 3
**Status:** Planned
**Previous Level:** Level 2 — Grounded RAG
**Next Level:** Level 4 — (future maturity capabilities)

---

# 1. Purpose

Level 3 transforms the Level 2 grounded RAG system into an **advanced
retrieval system**.

Level 2 established:

```text
Question
    ↓
Vector Retriever
    ↓
Evidence
    ↓
Grounded Generation
    ↓
Citation-validated Answer
```

Level 2 proved that answers can be grounded in retrieved evidence. Level 3
addresses the next fundamental problem:

> **What happens when the system cannot retrieve the right evidence in the
> first place?**

Level 2's own failure analysis showed that many "bad answers" are actually
retrieval misses. Grounding validates what was retrieved; it cannot recover
what was never found. Level 3 therefore attacks the retrieval layer itself:

```text
Level 2 question:  Is this answer supported by the evidence we retrieved?
Level 3 question:  Did we retrieve the right evidence at all — reliably,
                   for every class of Telco question?
```

---

# 2. Core Principle

> **Retrieve broadly, rank intelligently, measure objectively, and only add
> complexity when the evidence justifies it.**

Every retrieval component added in Level 3 must earn its place through
measured results. No component ships because it is fashionable; it ships
because an experiment shows it improves retrieval for a class of questions.

---

# 3. Technology Constitution

Level 3 shall continue using the Level 1/2 stack.

## Application

```text
Python 3.12+
uv
Pydantic v2
PyYAML
Typer
```

## Retrieval

```text
sentence-transformers
BAAI/bge-small-en-v1.5          (embeddings — unchanged)
ChromaDB                        (vector store — unchanged)
rank-bm25                       (new — lexical retrieval)
BAAI/bge-reranker-base          (new — cross-encoder reranking)
```

## Generation

```text
OpenRouter
OpenAI Python SDK               (also used for query rewriting)
```

## Testing

```text
pytest
pytest-cov
Ruff
mypy
```

No RAG framework shall be introduced (see §21).

---

# 4. What Is New in Level 3

```text
BM25 lexical retrieval
        ↓
Metadata filtering
        ↓
Hybrid retrieval (vector + BM25)
        ↓
Reciprocal Rank Fusion
        ↓
Cross-encoder reranking
        ↓
Query rewriting
        ↓
Retrieval Controller (strategy selection)
        ↓
Strategy comparison + ablation study
        ↓
Retrieval failure analysis
```

---

# 5. Target Architecture

```text
                         INGESTION
                            │
                            ↓
                      Documents
                            ↓
                          Chunks
                ┌───────────┴───────────┐
                ↓                       ↓
          Embeddings                 BM25 Index
                ↓                       │
            ChromaDB                    │
                │                       │
                └───────────┬───────────┘
                            │
                            ↓
                         RETRIEVAL
                            │
Question ──→ Query Processing (optional Query Rewriter)
                            │
                            ↓
                  Retrieval Controller
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          Vector          BM25        Metadata Filter
          Search         Search
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                     RRF Fusion (rank-based)
                            ↓
                     Candidate Pool
                            ↓
                 Cross-Encoder Reranker (optional)
                            ↓
                    Final RetrievalResult[]
                            │
                            ↓
              ┌─────────────┴─────────────┐
              ↓                           ↓
     Level 2 Evidence Builder      Evaluation / Debug
              ↓                     (diagnostics CLI)
     Grounded Generation
              ↓
     Citation Validation + Grounding Check
              ↓
           Answer
```

---

# 6. BM25 Constitution

BM25 shall be introduced as a **lexical retrieval peer** to vector search —
not a replacement.

Requirements:

```text
BM25Index operates over the same chunks as vector retrieval
index stores: chunk_id, document_id, chunk text, metadata
index is reproducible from source documents
index is NOT the source of truth (documents/chunks are)
index is rebuilt from ingestion, never hand-edited
```

Why BM25 exists: vector embeddings blur exact identifiers. Error codes,
acronyms, protocol names and exact technical terms ("X2 timeout 504") are
precisely where cosine similarity over small embedding models loses to
term-frequency matching. BM25 recovers them.

---

# 7. Metadata Filtering Constitution

Filters shall be generic key/value restrictions over document metadata:

```text
department
product
document_type
classification
source
```

Rules:

```text
filters are configuration-driven (retrieval.filters)
filters apply to every retrieval strategy uniformly
filter logic is generic — it must not hardcode the keys above
filters are the foundation for future authorization policies
an unknown metadata key filters nothing dangerous: it must be explicit
```

Filtering is a **restriction** mechanism, never a ranking mechanism. Its
purpose is "which chunks is the system allowed to see", which is why it must
stay generic: future RBAC/ABAC layers will build on the same interface.

---

# 8. Hybrid Retrieval Constitution

Hybrid retrieval shall combine vector search and BM25 search through **rank
fusion**, never through naive score averaging.

```text
Vector Search
      +
BM25 Search
      ↓
Candidate Combination
```

Raw vector scores (cosine similarity) and raw BM25 scores have different
distributions and different ranges. Averaging them is meaningless. The
constitution therefore mandates rank-based combination (RRF, §9) unless an
experiment demonstrates a calibrated alternative.

---

# 9. Reciprocal Rank Fusion Constitution

RRF shall be implemented as a small, pure, directly testable function:

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

where:

```text
d        = document/chunk
rank_i   = rank from retrieval system i (1-based)
k        = configurable constant (default 60)
```

Rules:

```text
fusion is deterministic — identical inputs give identical output
ties are broken deterministically (stable, documented order)
duplicates across systems are handled, not double-counted silently
the k constant is configuration, not a magic number in code
RRF input is ranks; it never sees raw scores
```

Why RRF: it is scale-free. It sidesteps the score-calibration problem
entirely by using only ordinal ranks, which both retrievers produce
natively. It is also trivially testable.

---

# 10. Reranking Constitution

The cross-encoder reranker shall re-score the fused candidate pool.

```text
Hybrid top 20 (candidate_k)
      ↓
Cross-Encoder (BAAI/bge-reranker-base)
      ↓
Top 5 (final_k)
```

Rules:

```text
reranking is optional and must be disable-able (reranking.enabled)
candidate_k and final_k are configuration
reranker scores are recorded, not discarded (reranker_score field)
reranking must never introduce chunks that were not in the candidate pool
reranking must never be silently applied to a non-hybrid strategy
```

Why rerank: bi-encoder (vector) scoring is cheap but approximate — it
scores query and document independently. A cross-encoder reads them
*jointly*, which is a strictly stronger relevance signal at higher cost.
The cost is bounded by reranking only the top candidate_k, not the corpus.

---

# 11. Query Rewriting Constitution

Query rewriting shall use OpenRouter and must obey:

```text
preserve user intent
expand useful terminology
preserve technical identifiers
avoid adding unsupported assumptions
return exactly one retrieval query
```

Non-negotiable rules:

```text
the original query is ALWAYS preserved
original and rewritten query are separate experimental modes
rewriting is OFF by default (query_rewriting.enabled: false)
rewriting never silently replaces the user's query in debug output
a rewrite failure falls back to the original query
```

Why off by default: rewriting adds a network call, latency and a failure
mode. It must prove itself against the original query in the evaluation
matrix before being enabled.

---

# 12. Retrieval Controller Constitution

The controller is the single entry point for retrieval:

```text
select strategy
apply filters
rewrite query if enabled
retrieve candidates
fuse candidates
rerank candidates
return final RetrievalResult[]
```

Rules:

```text
the controller does NOT generate answers
the controller does NOT modify the Level 2 grounding pipeline
the controller is deterministic for a fixed configuration
unknown strategy → explicit configuration error, not silent fallback
```

Supported strategies:

```text
vector
bm25
hybrid
hybrid_reranked
```

---

# 13. Result Model Constitution

Retrieval results shall carry provenance — *how* each result was found:

```text
RetrievalResult(
    document_id, chunk_id, text,
    score, rank,
    retrieval_method, metadata,
    vector_rank, bm25_rank,
    rrf_score, reranker_score,
)
```

Rules:

```text
not every field is populated for every strategy — absence is meaningful
retrieval_method records which strategy produced the final result
per-system ranks (vector_rank, bm25_rank) are preserved for diagnostics
the model stays backward compatible with Level 2 (Evidence Builder contract
  must keep working unchanged)
```

Provenance is what makes failure analysis (§16) possible: to ask "did BM25
find it?" the result must remember who found what.

---

# 14. Configuration Constitution

All Level 3 behavior shall be configuration-driven:

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

reranking:
  enabled: true
  model: BAAI/bge-reranker-base
  candidate_k: 20
  final_k: 5

query_rewriting:
  enabled: false
```

Rules:

```text
every experimental knob has a default
invalid configuration fails loudly at load time
every strategy is selectable without code changes
feature flags (enabled: false) are first-class — controlled experiments
  require turning things OFF as much as ON
```

---

# 15. CLI and Diagnostics Constitution

The CLI shall expose retrieval directly:

```bash
telco-rag retrieve "Why is 5G packet loss occurring?" --strategy hybrid
```

`--debug` output shall expose the full diagnostic trail:

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

Rules:

```text
retrieval diagnostics never require reading source code
debug output is per-chunk and per-stage
the retrieve command stops at RetrievalResult[] — it never generates
```

If a retrieval decision cannot be explained from `--debug` output, the
diagnostics are incomplete.

---

# 16. Evaluation Constitution

Level 3 shall extend the Level 1/2 retrieval evaluation, not replace it.

## Evaluation matrix

Every retrieval question shall be evaluated with:

```text
Vector | BM25 | Hybrid | Hybrid + Reranker
```

and separately:

```text
Original Query | Rewritten Query
```

## Metrics

```text
Recall@1 / @3 / @5 / @10
Precision@1 / @3 / @5 / @10
MRR
Latency
```

## Ablation study

```text
A: Vector only
B: BM25 only
C: Vector + BM25
D: Vector + BM25 + RRF
E: Hybrid + Reranker
F: Hybrid + Query Rewriting
G: Hybrid + Query Rewriting + Reranker
```

## Evaluation dataset

`data/evaluation/retrieval_questions.jsonl` shall cover:

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

Rules:

```text
results are RECORDED in experiments.md, never asserted
every strategy claim ("BM25 wins for error codes") traces to a measured
  number in the evaluation matrix
failure analysis uses the decision tree in §17 — no blind tuning
```

---

# 17. Failure Analysis Constitution

Every significant retrieval failure shall be diagnosed with this procedure:

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

Rules:

```text
each stage is a yes/no question answered from debug output or eval data
a failure is attributed to the FIRST stage that lost the chunk
fixes target the attributed stage only — no shotgun tuning
each discovered failure becomes a regression test
```

This creates a retrieval-debugging methodology rather than blind tuning.

---

# 18. Latency Constitution

Level 3 shall establish the first retrieval performance baseline by
recording:

```text
embedding latency
vector retrieval latency
BM25 latency
fusion latency
reranking latency
query rewriting latency
total retrieval latency
```

Rules:

```text
every added component carries a measured cost
latency is reported alongside quality metrics in the ablation study
a component whose quality gain does not justify its latency is a
  candidate for removal — complexity must pay rent
```

---

# 19. Grounding Integration Constitution

**Do not rewrite the Level 2 grounding layer.**

```text
Question
   ↓
Retrieval Controller
   ↓
Advanced Retrieval
   ↓
RetrievalResult[]
   ↓
Evidence Builder            ← Level 2, unchanged contract
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

Rules:

```text
the Evidence Builder keeps consuming RetrievalResult[]
Level 2 grounding tests must still pass, unchanged
Level 3 improves WHAT is retrieved, never HOW it is validated
retrieval provenance (reranker_score etc.) must not leak into grounding
  behavior unless deliberately designed and tested
```

---

# 20. Separation of Responsibilities

```text
Retrieval Controller   → decides what to retrieve
Retrievers (vector/BM25) → retrieve
Fusion                 → combines ranks
Reranker               → reorders candidates
Evidence Builder       → packages evidence          (Level 2)
Generator              → answers from evidence      (Level 2)
Validator/Checker      → verifies the answer        (Level 2)
```

The controller must not generate answers. The generator must not perform
retrieval. The reranker must not invent candidates.

---

# 21. Framework Constitution

Do not introduce:

```text
LangChain
LlamaIndex
LangGraph
RAG evaluation frameworks
agent frameworks
```

unless an experiment demonstrates a specific need.

BM25 (`rank-bm25`), Sentence Transformers and the OpenAI-compatible client
are libraries, not frameworks: they implement one mechanism each and leave
the architecture visible.

---

# 22. Explicitly Out of Scope

Level 3 shall not introduce:

```text
query decomposition
multi-hop retrieval
document lifecycle / approval
RBAC / ABAC (metadata filtering only lays the foundation)
multi-tenancy
agents / memory / tool calling
production observability / distributed tracing
CI/CD, Kubernetes, multi-region, FinOps
```

---

# 23. Definition of Done

Level 3 is complete when:

* BM25 works and vector retrieval still works
* metadata filtering works generically
* hybrid retrieval works via rank fusion
* RRF works and is deterministic
* cross-encoder reranking works and can be disabled
* query rewriting works and can be disabled
* all four strategies are configurable without code changes
* retrieval diagnostics are available via `--debug`
* the evaluation dataset covers all eight question categories
* vector/BM25/hybrid/reranked are compared in the evaluation matrix
* query rewriting is experimentally evaluated against the original query
* latency is measured per stage
* retrieval failures are documented with the §17 decision tree
* unit tests pass
* **Level 2 grounding tests still pass, unchanged**
* documentation and lessons learned are updated

---

# 24. Exit Criteria

Before moving on, the project must answer — from measured results, not
assumptions:

> **Which retrieval strategy works best for which type of Telco question?**

Expected hypothesis (to be confirmed or refuted by the evaluation matrix):

```text
Semantic question                    → Vector
Exact technical term                 → BM25
Mixed semantic + exact terminology   → Hybrid
Large candidate set                  → Hybrid + Reranker
Poorly phrased question              → Query Rewriting + Hybrid
```

The developer must additionally be able to explain:

1. Why raw vector and BM25 scores must not be averaged.
2. What RRF buys and what it costs.
3. Why the reranker scores candidates it did not retrieve.
4. Why query rewriting is off by default.
5. Where the BM25 index sits in the truth hierarchy (documents > chunks >
   indexes).
6. How to attribute a retrieval failure to a specific stage.
7. Which strategy wins per question category — with numbers.

---

# 25. Level 3 Guiding Principle

> **Retrieve broadly, rank intelligently, measure objectively, and only add
> complexity when the evidence justifies it.**
