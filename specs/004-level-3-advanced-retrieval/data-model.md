# Phase 1 Data Model: Level 3 Advanced Retrieval

**Feature**: specs/004-level-3-advanced-retrieval
**Date**: 2026-10-08

Existing entities (`Document`, `Chunk`, `RetrievalQuery`, `RetrievalResult`,
`Answer`, `EvaluationQuestion`) live in `src/domain.py` and are **extended,
not replaced** (FR-027 — Level 2 compatibility).

---

## Modified Entities

### RetrievalResult *(extended with provenance)*

One ranked result from any strategy (FR-009). The Level 2 fields keep
their exact meaning; new fields are optional and `None` means *the stage
did not run* — never a fabricated value.

| Field | Type | Rules |
|-------|------|-------|
| `chunk` | `Chunk` | unchanged; required |
| `score` | `float` | unchanged slot, strategy-dependent meaning: cosine similarity (vector), BM25 score (bm25), RRF score (hybrid), cross-encoder score (hybrid_reranked) |
| `rank` | `int` | final 1-based rank within the returned list; ≥ 1 |
| `retrieval_method` | `str \| None` | **new**; one of `vector`, `bm25`, `hybrid`, `hybrid_reranked`; set by the controller on every returned result |
| `vector_rank` | `int \| None` | **new**; 1-based rank from vector search when it ran; `None` otherwise |
| `bm25_rank` | `int \| None` | **new**; 1-based rank from BM25 when it ran; `None` otherwise |
| `rrf_score` | `float \| None` | **new**; RRF contribution total when fusion ran; `None` otherwise |
| `reranker_score` | `float \| None` | **new**; cross-encoder score when reranking ran; `None` otherwise |

**Compatibility contract**: `grounding/evidence_builder.py` reads only
`chunk`, `score`, `rank` — all unchanged. Level 2 tests must pass without
modification (FR-027).

**Provenance matrix** (which fields each strategy populates):

| Strategy | vector_rank | bm25_rank | rrf_score | reranker_score |
|----------|-------------|-----------|-----------|----------------|
| `vector` | ✓ | — | — | — |
| `bm25` | — | ✓ | — | — |
| `hybrid` | ✓ | ✓ | ✓ | — |
| `hybrid_reranked` (on) | ✓ | ✓ | ✓ | ✓ |
| `hybrid_reranked` (disabled) | ✓ | ✓ | ✓ | — |

---

### EvaluationQuestion *(extended)*

Dataset entry for the retrieval matrix (FR-020).

| Field | Type | Rules |
|-------|------|-------|
| `id` | `str` | unchanged; required, unique |
| `question` | `str` | unchanged; non-empty |
| `relevant_documents` | `list[str]` | unchanged; empty ⇒ unanswerable (true negative) |
| `category` | `str` | **constrained**: one of `semantic`, `exact_terminology`, `error_code`, `acronym`, `multi_concept`, `ambiguous`, `metadata_filtered`, `unanswerable`, (legacy values `general` + topic names remain readable) |
| `relevant_chunks` | `list[str]` | **new**, optional, default `[]`; chunk-level labels used for Recall@K at chunk granularity; when empty, document-level labels are the ground truth |
| `filters` | `dict[str, Any]` | **new**, optional, default `{}`; metadata restriction the matrix applies for that question (mechanism for the `metadata_filtered` category); empty = unrestricted |

---

## New Entities

### BM25Index *(derived artifact, not persisted truth)*

In-process lexical index built at ingestion from the same chunks as the
vector store (FR-001/FR-002, Principle XXVIII).

| Component | Type | Rules |
|-----------|------|-------|
| entries | `list[BM25Entry]` | parallel corpus order; index position defines corpus rank input |
| `chunk_id` | `str` | per entry; required, unique within index |
| `document_id` | `str` | per entry; required |
| `text` | `str` | per entry; chunk content, non-empty |
| `metadata` | `dict[str, Any]` | per entry; copy of chunk metadata (filter evaluation) |
| tokens | `list[list[str]]` | lowercase `[a-z0-9]+` tokenization of `text` |
| `k1`, `b` | `float` | BM25 parameters; defaults of the library unless configured |

**Lifecycle**: built by `ingest` → held by the retrieval layer → rebuild
reproduces it byte-identically from documents. Never edited in place,
never treated as authoritative.

---

### RetrievalStrategy *(value object / validated enum)*

| Value | Pipeline executed |
|-------|-------------------|
| `vector` | (rewrite?) → filter → vector search |
| `bm25` | (rewrite?) → filter → BM25 search |
| `hybrid` | (rewrite?) → vector + BM25 → filter → RRF fusion |
| `hybrid_reranked` | (rewrite?) → vector + BM25 → filter → RRF → cross-encoder rerank (if enabled) |

**Validation**: closed set; any other value fails configuration load or
CLI parsing with a clear error — no silent fallback (FR-008).

---

### RetrievalSettings *(configuration entity, `config/settings.yaml`)*

| Field | Type | Default | Rules |
|-------|------|---------|-------|
| `strategy` | `RetrievalStrategy` | `vector` | must be a valid strategy |
| `top_k.vector` | `int` | `20` | ≥ 1 |
| `top_k.bm25` | `int` | `20` | ≥ 1 |
| `top_k.hybrid` | `int` | `20` | ≥ 1 |
| `top_k.final` | `int` | `5` | ≥ 1 |
| `fusion.method` | `str` | `rrf` | only `rrf` supported at Level 3 |
| `fusion.k` | `int` | `60` | ≥ 1 |
| `filters` | `dict[str, Any]` | `{}` | generic keys; empty = unrestricted |

**Reranking block**

| Field | Type | Default | Rules |
|-------|------|---------|-------|
| `enabled` | `bool` | `true` | disable ⇒ hybrid_reranked falls back to fusion order |
| `model` | `str` | `BAAI/bge-reranker-base` | non-empty model id |
| `candidate_k` | `int` | `20` | ≥ 1; pool size entering rerank |
| `final_k` | `int` | `5` | ≥ 1; ≤ candidate_k warned, not errored |

**Query rewriting block**

| Field | Type | Default | Rules |
|-------|------|---------|-------|
| `enabled` | `bool` | `false` | **default off** (Principle XXIX); on ⇒ uses LLM gateway |

Validation happens at Settings load (Pydantic); invalid values fail at
startup (FR-008, research R7).

---

### RetrievalDebug *(controller output for CLI/debug/evaluation)*

What `RetrievalController.retrieve()` returns: results plus the trail
needed for diagnostics and failure analysis (FR-019, research R7).

| Field | Type | Rules |
|-------|------|-------|
| `query` | `str` | original user question; always present, unmodified |
| `rewritten_query` | `str \| None` | set only when a rewrite ran AND succeeded; `None` otherwise |
| `strategy` | `RetrievalStrategy` | the strategy actually executed |
| `filters` | `dict[str, Any]` | filters applied (possibly `{}`) |
| `results` | `list[RetrievalResult]` | final ranked output with provenance |
| `latency_ms` | `dict[str, float]` | stage → milliseconds; keys among `rewrite`, `embed`, `vector`, `bm25`, `filter`, `fuse`, `rerank`, `total` — only stages that ran are present (same absent-means-not-run semantics) |
| `stages_skipped` | `list[str]` | e.g. `["rewrite", "rerank"]` when disabled — makes "off" explicit in debug output |

---

### FailureLogEntry *(documentation entity, experiments.md §7)*

One row per significant evaluation failure (FR-025/FR-028, Principle XXVII).

| Field | Type | Rules |
|-------|------|-------|
| `id` | `str` | `F-001`, `F-002`, … |
| `question` | `str` | the failing evaluation question |
| `in_corpus` | `bool` | was the correct chunk present? |
| `vector_found` | `bool \| None` | `None` if not tested |
| `bm25_found` | `bool \| None` | |
| `hybrid_found` | `bool \| None` | |
| `rerank_preserved` | `bool \| None` | |
| `rewrite_helped` | `helped \| neutral \| hurt \| None` | |
| `first_failing_stage` | `str` | the first `NO` in the decision tree |
| `fix` | `str` | what changed |
| `regression_test` | `str` | name of the test in `tests/` |

---

## Relationships

```text
EvaluationQuestion 1 ── * RetrievalDebug (one per strategy × query mode)
RetrievalDebug     1 ── * RetrievalResult
RetrievalResult    1 ── 1 Chunk          (unchanged)
BM25Index         1 ── * BM25Entry       (1:1 with Chunks at build time)
FailureLogEntry   * ── 1 EvaluationQuestion
```

## State Transitions

A candidate's journey through `hybrid_reranked` (failure analysis maps to
these states):

```text
(not retrieved)            → lost at vector/BM25 stage (before pool)
vector/bm25 result         → filtered out            (metadata stage)
fused candidate (in pool)  → demoted below final_k   (rerank stage)
final result               → returned (scores/provenance attached)
```

Nothing in the pipeline mutates a result after its final rank is assigned;
`score`/`rank` are rewritten only at the stage that owns them (vector
search, fusion, rerank).
