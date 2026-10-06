# Data Model: Level 0 — Naive RAG Baseline

**Date**: 2026-10-06
**Source**: `specs/001-naive-rag-baseline/spec.md` (Key Entities, FR-001..FR-016)
**Constitution**: v1.0.0 (P IX Minimal Metadata)

This document describes the domain entities the Level 0 system manipulates
and the validation rules that apply to them. It is deliberately small: Level
0 holds documents, chunks, retrieval results, prompts, answers, and baseline
records in memory. Entities are shown with logical fields (no
implementation types) except where a format is a contract (see
`contracts/`).

## Entities

### Document

A source knowledge file in the corpus.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `document_id` | identifier | yes | Stable identity assigned at load time (FR-002/FR-009 provenance) |
| `document_name` | text | yes | File name / display name (e.g. `5g_packet_loss.md`) |
| `source` | path | yes | Where the document came from (`data/documents/*.md`) |
| `content` | text | yes | Full document text |

**Validation**:
- Corpus is a configured directory (`DOCUMENT_DIR`); at least one Markdown
  file must be discoverable, otherwise ingestion fails with a clear error
  (spec edge case "empty knowledge base").
- `document_id` is unique across the corpus.
- Content must be non-empty after read.
- P II / P III constraint: documents are synthetic; no real customer data
  is ever ingested.

### Chunk

A fragment of a document; the unit of embedding and retrieval.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `chunk_id` | identifier | yes | Unique per chunk (e.g. `docId#0003`) |
| `content` | text | yes | The fragment text (~500 chars) |
| `document_id` | identifier | yes | Back-reference to owning Document |
| `document_name` | text | yes | Denormalized for display (FR-010) |
| `source` | path | yes | Denormalized for provenance (P IX) |

**Validation**:
- `chunk_size` (default 500) and `chunk_overlap` (default 50) are positive
  integers; overlap < chunk_size.
- Chunking is fixed-size, not semantic (FR-002; improved chunking deferred
  to Level 1).
- A document smaller than one chunk produces exactly one chunk (edge case).
- Required metadata (`document_id`, `document_name`, `chunk_id`, `source`)
  is always preserved (P IX).

### Query (Question)

The user's free-text request from the CLI.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | text | yes | Non-empty; stripped of surrounding whitespace |

**Validation**: Non-empty single positional argument; the CLI rejects an
empty question with a usage error (exit code 1).

### Retrieval Result

The outcome of searching a query embedding against the store.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `chunk` | Chunk | yes | Retrieved chunk |
| `score` | float | yes | Cosine similarity to the query (0..1 after normalization) |
| `rank` | int | yes | Position in result list (1..K) |

**Validation**:
- Exactly `top_k` (default 4) results returned when that many exist; fewer
  when the store holds fewer chunks.
- Ordered by descending score.
- Scores are inspectable and displayed to the user (P VIII, FR-010).

### Prompt

The composed request sent to the answer provider.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `system_instruction` | text | yes | Grounding rules (P VII): use supplied context only, do not invent facts, state when context is insufficient, answer clearly |
| `context` | text | yes | Concatenated retrieved chunk content |
| `question` | text | yes | The user question |

### Answer

The provider's response, or the system's abstention.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `text` | text | yes | Model output |
| `used_context` | boolean | yes | Whether retrieval produced ≥1 chunk used to build the prompt |
| `citations` | list[text] | no | Source document names included in the inspection output |

**Validation**:
- When `used_context` is false, the pipeline produces an explicit
  "not enough information" response instead of calling the LLM with empty
  context (P VII, FR-015).
- Answer text is never passed to the user without the supporting retrieval
  record (P VIII, FR-010).

## Relationships

```text
Document 1 ──── * Chunk
Chunk * ──────── 1 RetrievalResult  (via VectorStore.search)
Query 1 ──────── * RetrievalResult   (top-K)
RetrievalResult * ── 1 Prompt        (context section)
Query 1 ─────────── 1 Prompt
Prompt 1 ────────── 1 Answer
```

## State Transitions

Level 0 entities are mostly immutable values; the only meaningful lifecycle
is the query flow:

```text
Query (asked)
   → retrieved (RetrievalResult list built, used_context = true/false)
   → answered (Answer produced: grounded answer OR abstention)
   → recorded (BaselineRecord appended in baseline experiment mode)
```

Documents and chunks follow a single ingest transition:
```text
Document (loaded) → Chunk (chunked) → embedded → indexed in VectorStore
```
No document versioning, approval, or lifecycle states exist in Level 0
(P XIII; explicitly out of scope).

## Baseline Record

Persisted experiment row (FR-014, spec SC-006).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | text | yes | The asked question |
| `retrieved_documents` | list[text] | yes | Source names returned |
| `retrieval_scores` | list[float] | yes | Scores for those sources |
| `answer` | text | yes | Model response |
| `observations` | text | yes | Analyst notes (hallucination? wrong doc? abstained?) |

**Validation**: `docs/levels/level-00-naive-rag/baseline.md` records one
Baseline Record per question in the fixed baseline set (spec SC-006); the
trailing section lists known limitations that feed Level 1 (FR-016).