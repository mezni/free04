# Contract: Retrieval Configuration

**Feature**: specs/004-level-3-advanced-retrieval
**Interface**: `config/settings.yaml` → `src/config.py` (pydantic-settings).
All keys are validated at startup; invalid configuration fails fast with
a clear message — never a silent fallback (FR-008, research R7).

## 1. Schema

```yaml
retrieval:
  top_k: 4                     # legacy Level 1 query depth (unchanged; contract note §5)
  strategy: vector             # vector | bm25 | hybrid | hybrid_reranked  (closed set)
  stage_top_k:
    vector: 20                # int >= 1
    bm25: 20                  # int >= 1
    hybrid: 20                # int >= 1
    final: 5                  # int >= 1; results returned to caller
  fusion:
    method: rrf               # only "rrf" accepted at Level 3
    k: 60                     # int >= 1; RRF constant
  filters: {}                 # dict[str, Any]; generic metadata filters, {} = unrestricted

reranking:
  enabled: true               # bool; false => hybrid_reranked = fusion order (skipped, not error)
  model: BAAI/bge-reranker-base
  candidate_k: 20             # int >= 1; pool entering rerank
  final_k: 5                  # int >= 1

query_rewriting:
  enabled: false              # bool; DEFAULT OFF (Principle XXIX, NON-NEGOTIABLE)
```

**Implementation note (amended during implementation)**: `retrieval.top_k` (scalar)
is the legacy Level 1 depth used by `telco-rag query` and MUST stay unchanged;
the Level 3 per-stage depths therefore live under `retrieval.stage_top_k`.
`src/config.py` flattens these into `retrieval_strategy`, `stage_top_k_*`,
`fusion_*`, `retrieval_filters`, `rerank_*`, `query_rewrite_enabled`.

## 2. Validation rules

| Rule | Violation result |
|------|------------------|
| `strategy` ∈ closed set | startup error listing valid values |
| all `top_k`, `fusion.k`, `candidate_k`, `final_k` ≥ 1 | startup error |
| `fusion.method` == `rrf` | startup error ("level 3 supports rrf only") |
| `reranking.final_k` > `candidate_k` | warning + clamp to `candidate_k` (rerank pool smaller than requested output) |
| unknown key inside `retrieval.filters` | accepted (filters are generic by design, FR-011) |
| `query_rewriting.enabled: true` but no LLM credentials | rewrite falls back to original query with a warning at runtime; retrieval still succeeds (FR-017) |

## 3. CLI overrides

`telco-rag retrieve --strategy <s>` overrides `retrieval.strategy` for
that invocation only; validation is identical (closed set, else exit 1).
`--top-k <n>` overrides the result count (default `stage_top_k.final`). Config file is never
written by the CLI.

## 4. Defaults rationale

- `strategy: vector` — Level 1 behavior is the safe default; advanced
  strategies are opt-in.
- `k: 60` — standard RRF constant (level constitution, constitution §RRF).
- `final: 5` / `final_k: 5` — matches Level 1 top-k output size so the
  grounding pipeline sees comparable evidence volume.
- `query_rewriting.enabled: false` — Principle XXIX: original query
  preserved, off unless deliberately measured.
- Secrets: none added; rewriting reuses existing `LLM_*` env vars only.
