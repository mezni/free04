# Contract: CLI `retrieve` Command

**Feature**: specs/004-level-3-advanced-retrieval
**Interface**: `telco-rag` CLI (Typer), new command `retrieve`. Exit-code
protocol unchanged: `0` success (including empty results), `1` usage /
config error, `2` runtime failure.

## 1. Synopsis

```text
telco-rag retrieve "QUESTION"
  [--strategy vector|bm25|hybrid|hybrid_reranked]
  [--top-k N]
  [--filter key=value ...]
  [--debug]
```

| Option | Default | Behavior |
|--------|---------|----------|
| `--strategy` | `retrieval.strategy` from config | validated closed set; invalid ⇒ exit 1 with valid values listed |
| `--top-k` | `retrieval.stage_top_k.final` | final result count, ≥ 1 |
| `--filter k=v` (repeatable) | `retrieval.filters` from config | merges over config filters; value parsed as YAML scalar (int/bool/string) |
| `--debug` | off | prints the diagnostic block of §3 |

`retrieve` performs **no LLM generation** — retrieval stops at
`RetrievalResult[]` (Principle VI / XXI). Rewriting and reranking follow
config (`query_rewriting.enabled`, `reranking.enabled`).

## 2. Normal output (plain text, deterministic)

```text
Strategy: hybrid (query mode: original)
Results: 5

1. (score: 0.0321)  5g-nokia-5g-deployment.pdf:chunk-003
   ...first line of chunk text...
2. ...
```

- Results in final rank order; `score` is the strategy's headline score
  (see `retrieval-result-schema.md` §3).
- `query mode: rewritten` appears only when a rewrite actually ran
  (original remains query of record).
- Zero results → `Results: 0`, exit 0 (abstention downstream is valid).

## 3. `--debug` output

```text
Query: <original user question>                 ← always present, unmodified
Rewritten query: <text> | (not run)
Strategy: hybrid_reranked
Filters: {"category": "5g"} | (none)
Stages skipped: rewrite, rerank                 ← explicit "off" accounting

1. (score: 0.0412, rrf_score: 0.0311, vector_rank: 2, bm25_rank: 1, reranker_score: 7.83)
   [chunk-id]
   ...
2. ...

Latency (ms): embed 4.1 | vector 1.8 | bm25 0.3 | filter 0.1 | fuse 0.0 | rerank 96.4 | total 102.9
```

Rules (Principle XXVI, FR-019):

- Each result line shows **only the provenance that ran**; absent stages
  are omitted (not printed as 0).
- `Query:` is printed even when rewriting is enabled and succeeded — the
  original is always visible (Principle XXIX).
- Latency keys only for stages that ran; `total` always present.
- Output ordering and formatting are deterministic for identical input.

## 4. Error behavior

| Condition | Exit | Message |
|-----------|------|---------|
| unknown `--strategy` value | 1 | lists `vector, bm25, hybrid, hybrid_reranked` |
| invalid config (startup) | 1 | Pydantic validation error naming the key |
| rewrite gateway failure | 0 | warning on stderr, falls back to original query (FR-017) |
| reranker model load failure | 2 | error naming model id (config problem surfaces loudly) |
| empty index (nothing ingested) | 0 | `Results: 0` |

## 5. Compatibility

Existing commands (`ingest`, `query`, `evaluate`) keep their current
signatures and outputs; `retrieve` is purely additive. `query
--debug-retrieval` output format is unchanged (Level 1 contract).
