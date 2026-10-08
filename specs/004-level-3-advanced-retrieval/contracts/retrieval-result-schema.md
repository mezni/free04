# Contract: RetrievalResult Schema (Level 3)

**Feature**: specs/004-level-3-advanced-retrieval
**Interface**: `src/domain.py::RetrievalResult` — the object returned by
every retrieval strategy and consumed by the Level 2 evidence builder.
This contract is additive: fields may be added, existing fields may not
change name, type, or meaning (FR-027).

## 1. Schema (Pydantic v2)

```json
{
  "chunk": {
    "chunk_id": "string (non-empty)",
    "document_id": "string (non-empty)",
    "source": "string",
    "text": "string",
    "metadata": { "document_name": "string", "...": "any corpus key" }
  },
  "score": "number (strategy-dependent, see §3)",
  "rank": "integer >= 1 (final 1-based rank)",
  "retrieval_method": "string | null  — vector | bm25 | hybrid | hybrid_reranked",
  "vector_rank":  "integer >= 1 | null",
  "bm25_rank":    "integer >= 1 | null",
  "rrf_score":    "number | null",
  "reranker_score": "number | null"
}
```

## 2. Provenance semantics (Principle XXVI)

- A field is **non-null only if that stage ran** for this result.
- `null` means *not executed*, never *zero* / *unknown*.
- Consumers must treat missing provenance as "stage skipped", and debug
  output must mirror this (see `cli-retrieve.md`).

## 3. `score` meaning per strategy

| Strategy | `score` |
|----------|---------|
| `vector` | cosine similarity (existing Level 1 behavior) |
| `bm25` | BM25 Okapi score (≥ 0) |
| `hybrid` | RRF score = `Σ 1/(k + rank_i)` over contributing lists |
| `hybrid_reranked` | cross-encoder score (only when reranking ran; otherwise the RRF score) |

Raw vector and BM25 scores are **never** averaged or blended — rank
fusion only (Principle XXV, NON-NEGOTIABLE).

## 4. Ordering rules

- `results` are always sorted by `rank` ascending; `rank` is dense
  (1, 2, 3, …) with no gaps.
- Ties after fusion/rerank are broken deterministically by first-seen
  order (documented in `research.md` R2), so identical input ⇒
  byte-identical output.

## 5. Level 2 compatibility (guaranteed)

`grounding/evidence_builder.py` continues to read only:

- `result.chunk` → `Evidence.{document_id, chunk_id, text, metadata}`
- `result.score` → `Evidence.retrieval_score`
- `result.rank` → `Evidence.rank`

No Level 2 code path reads the new fields; adding them cannot change
evidence or citation behavior. Existing tests
(`tests/test_evidence_builder.py`, `tests/test_citations.py`,
`tests/test_rag_pipeline.py`) must pass unmodified.

## 6. Failure modes

| Condition | Behavior |
|-----------|----------|
| strategy returns 0 candidates | `results: []` (empty list, exit 0) — never an error; downstream abstention is a valid result (Principle XIX) |
| fusion input has one non-empty list | fused order = that list's order, provenance from contributing retriever preserved |
| all strategies fail at runtime | CLI exits `2` with the underlying error message (unchanged exit protocol) |
