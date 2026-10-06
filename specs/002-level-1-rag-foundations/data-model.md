# Data Model: Level 1 RAG Foundations

**Date**: 2026-10-06 | **Feature**: 002-level-1-rag-foundations | **Also see**: [contracts/](contracts/), [research.md](research.md)

Defines the Pydantic v2 entities shared across ingestion → embedding → retrieval →
generation → evaluation. FR-004 requires structured, typed objects — retrieval
MUST NOT return anonymous strings.

## Design Principles

- **Pydantic v2** models (required stack) replace the current
  `dataclasses` in `src/domain.py`.
- **Deterministic ids**: derived from content/position so re-ingestion with
  identical config produces identical ids (aids SC-004 comparisons).
- **Score before rank**: `RetrievalResult` always carries a meaningful numeric
  score; `rank` is derived (constitution VIII).
- **Metadata survives end-to-end** (FR-003, constitution IX): every stored
  chunk carries `document_id`, `document_name`, `source`, `chunk_id`,
  `chunk_index`.

## Entity: Document

Corresponds to one Telco Markdown file under `data/documents/`.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `document_id` | `str` | yes | Deterministic, derived from filename (text before `.md`). Uniquely identifies the document across experiments. |
| `document_name` | `str` | yes | Original filename, e.g. `5g-networking.md`. |
| `source` | `str` | yes | Absolute source path at ingestion time. |
| `content` | `str` | yes | Full file text. |
| `metadata` | `dict[str, Any]` | no | Reserved; empty by default at Level 1. |

**Validation**: `content` must not be empty/whitespace-only (raises
`ValidationError`) — preserves current Level 0 behavior.

**Produced by**: `src/ingestion/loader.py:discover_documents()`.

## Entity: Chunk

Unit of embedding and retrieval. One chunk maps to exactly one vector.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `chunk_id` | `str` | yes | `f"{document_id}#{index:04d}"` — e.g. `5g-networking#0003`. |
| `document_id` | `str` | yes | Parent reference. |
| `document_name` | `str` | yes | Inherited from parent (FR-003). |
| `source` | `str` | yes | Inherited from parent (FR-003). |
| `chunk_index` | `int` | yes | 1-based position in parent. Added to satisfy constitution IX minimum metadata. |
| `content` | `str` | yes | Chunk text. |
| `metadata` | `dict[str, Any]` | no | Reserved; holds document metadata copy if ever needed. |

**Validation**: `content` must be non-empty — except the documented edge case:
an empty document produces exactly one empty chunk (preserves Level 0
behavior; allowed by spec Edge Cases) — chunk_index `0`.

**Produced by**: `src/ingestion/chunker.py:chunk_document()`.

## Entity: RetrievalQuery

The typed input to the retrieval layer (replaces raw-`str` retrieval).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | `str` | yes | Non-empty after strip. |
| `top_k` | `int` | yes | Clamped to collection size by the store. |
| `similarity_threshold` | `float` | yes | Applied to scores (cosine similarity in `[-1, 1]`); results below are dropped. Default from config (0.0 → no filtering). |
| `metadata_filter` | `dict[str, Any]` | no | **Internal only** (FR-008): optional `where` clause for the vector store, e.g. `{"document_id": "5g-networking"}`. NOT exposed via CLI. |

## Entity: RetrievalResult

One ranked retrieval match. FR-004 star entity — score MUST be present and
meaningful.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `chunk` | `Chunk` | yes | Full typed chunk, never a bare string. |
| `score` | `float` | yes | Similarity to query where **higher = more similar** (cosine similarity). ChromaDB returns distances → converted `score = 1 - distance` in the store layer. |
| `rank` | `int` | yes | 1-based position after sorting descending by score. Level 0 `used_context` property (score > 0) is **removed** — the real threshold lives in `RetrievalQuery.similarity_threshold` (constitution VIII; SC-007 explainability). |

**Produced by**: `src/retrieval/retriever.py:retrieve()` via the vector store.

## Entity: EvaluationQuestion

One line of `data/evaluation/retrieval_questions.jsonl`.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `str` | yes | `eval-001` … `eval-030`. |
| `question` | `str` | yes | Non-empty question text. |
| `relevant_documents` | `list[str]` | yes | Expected `document_id`s. **Empty for unanswerable questions** (FR-009 / clarification). |
| `category` | `str` | no | Free-form tag (e.g. `factual`, `unanswerable`) for reporting. |

**Validation**: question non-empty; `relevant_documents` may be empty but a
document id must be non-empty if present; referenced ids that are not in the
corpus are reported as a miss at evaluation time — they do **not** crash
(spec Edge Cases).

**Loaded by**: `src/evaluation/dataset.py`.

## Relationship Summary

```text
Document (1) ──chunks──▶ (N) Chunk ──embedding──▶ vector (384-dim)
                                                      │
RetrievalQuery ──▶ embed_query ──▶ vector store search ──▶ [RetrievalResult] (ranked)
                                                      │
EvaluationQuestion ──▶ RepeatRetrieval ──▶ Recall@K / Precision@K / MRR + true-negatives
```

## What Stays the Same vs. Changes

- `Document` and `Chunk` keep their field names from Level 0 (regression-safe
  for tests); they migrate `dataclass` → `BaseModel` and add `chunk_index`.
- `RetrievalResult` drops the fake `used_context` property and adds typed
  `chunk`/`score`/`rank` semantics **unchanged in shape** except the property.
- `Answer` remains the typed generation result (text, `used_context`,
  `citations`) — Level 0 regression preserved.