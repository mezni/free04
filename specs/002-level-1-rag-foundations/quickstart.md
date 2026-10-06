# Quickstart: Level 1 RAG Foundations

**Date**: 2026-10-06 | **Feature**: 002-level-1-rag-foundations

Runnable validation path for implementation (maps to Success Criteria SC-001…
SC-009 and the spec acceptance scenarios). Run top-to-bottom after
implementation; each step names the SC it proves.

## 1. Environment (uv only — constitution 4.2)

```bash
uv sync                     # install deps + telco-rag script from pyproject
uv run pytest               # SC-005: all Level 0 tests still pass
```

Env contract: `LLM_BASE_URL`, `LLM_MODEL` must be set (Level 0 behavior).

## 2. Configure (SC-004 / FR-005 / FR-006)

`config/settings.yaml` defaults: `chunk_size: 500`, `chunk_overlap: 50`,
`top_k: 4`, `similarity_threshold: 0.0`, `embedding.model:
BAAI/bge-small-en-v1.5`, `retrieval.vector_db_path: data/chroma`.

## 3. Ingest (SC-001 / SC-008 / FR-001 / FR-002 / FR-003 / FR-016 / FR-011)

```bash
uv run telco-rag ingest
# expect: 8 documents, N chunks, elapsed < 60s, collection telco_documents
#         recreated in data/chroma/
```

Verify:
- `data/chroma/` exists after run; metadata `document_id`, `document_name`,
  `source`, `chunk_id`, `chunk_index` present per vector (FR-003).
- Re-run `ingest` after editing `chunk_size: 1000` → chunk count changes and
  **no stale 500-char chunks remain** (FR-016).

## 4. Persistence (US-1/3, FR-002)

```bash
uv run telco-rag query "What causes 5G packet loss?"
# restart/re-run: same stored chunks retrievable (persistence across restarts)
```

## 5. Query & Diagnostics (SC-002 / SC-007 / FR-007 / FR-008 / US-2)

```bash
uv run telco-rag query "What causes 5G packet loss?" --debug-retrieval
# expect block 2 expanded: document_id :: chunk_id :: filename (score)
#   e.g. "5g_packet_loss :: 5g_packet_loss#0008 :: 5g_packet_loss.md (score: 0.84)"
# expect NO LLM call — verify by LLM base_url pointing at a dead port + exit 0
#   (debug retrieves without generation)
```

Zero-context query (unknown topic) ⇒ `(none)` + Level 0 abstention message,
exit 0 (US-5 regression). With `similarity_threshold` raised (e.g. `0.65`) an
unknown topic retrieves 0 results → abstention. Recorded SC-009: warm
query-to-retrieval 0.08–0.13s per question (< 3s required); the 3s figure
quoted in measurements includes one-time embedder model load.

## 6. Config Experiments (SC-004)

```bash
# top_k via flag and via config
uv run telco-rag query "What causes 5G packet loss?" --top-k 8
# similarity_threshold: set 0.95 in settings.yaml → fewer/no results; restore 0.0
```

## 7. Evaluate (SC-006 / FR-009 / FR-009a / FR-010 / US-4)

```bash
uv run telco-rag evaluate                 # K=5, threshold from settings (0.0)
# expect:
#   Evaluation: N answerable, M unanswerable
#   Recall@5 / Precision@5 / MRR numeric
#   Unanswerable: true-negatives T / false-positives F
#   per-question line for each answerable question
uv run telco-rag evaluate --k 3          # same dataset, depth 3
uv run telco-rag evaluate --threshold 0.65  # raise abstention boundary (FR-006)
```

Assert at least one answerable question whose expected doc is retrieved in
top-3 contributing MRR `1/3`-or-better (US-4/2), and ≥1 unanswerable question
recorded as a true negative (abstention) once `--threshold` is above the
unanswerable questions' top scores (measured 0.41–0.58 vs. answerable
0.70–0.88 on the Level 1 corpus; `--threshold 0.65` yields 3/3 true-negatives).

## 8. Cleanup & Code Quality

```bash
uv run ruff check src tests            # layout/format gates
uv run mypy src                        # typing gates (dev-time, non-blocking)
```

## Pipeline Checklist (maps plan.md phases)

- [ ] Phase 0 research.md delivered — done.
- [ ] Phase 1 data-model.md, contracts/, quickstart.md — done.
- [ ] Phase 2 tasks.md + implementation (chunking → embedder → chroma store →
      retriever → config → cli → evaluation → tests).
- [ ] Post-impl: rerun §1–§7; SC-009 query-to-retrieval < 3s; commit + PR.