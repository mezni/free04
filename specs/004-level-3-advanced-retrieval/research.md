# Phase 0 Research: Level 3 Advanced Retrieval

**Feature**: specs/004-level-3-advanced-retrieval
**Date**: 2026-10-08
**Status**: All decisions resolved — no open NEEDS CLARIFICATION items.

The feature spec required no clarifications; this document resolves the
technical unknowns in the plan's Technical Context. Constitution:
`.specify/memory/constitution.md` v1.3.0.

---

## R1. BM25 library, tokenization, and index lifecycle

**Decision**: Use `rank-bm25` (`BM25Okapi`) as the only new runtime
dependency, wrapped by `retrieval/bm25.py::BM25Index` (build/search) and
`BM25Retriever` (returns `RetrievalResult[]`). The index is built in-process
during ingestion from the *same* chunk objects handed to the vector store:
each entry stores `chunk_id`, `document_id`, chunk text, and a metadata
copy. Tokenization: lowercase + regex word tokenization
(`[a-z0-9]+`), which keeps error codes (`504`, `x2`), acronyms (`noc`,
`sla`) and hyphenated terms splittable into matching tokens. The index is
held by the retrieval layer (rebuildable by `telco-rag ingest`), never
persisted as an authoritative artifact.

**Rationale**: Principle XXVIII — documents/chunks are truth, index is
derived; rebuilding at ingest makes it reproducible by construction.
Regex tokenization is dependency-free, transparent (Principle XVI spirit:
explainable behavior), and adequate for a synthetic English corpus where
the exact-identifier tokens are alphanumeric.

**Alternatives considered**:
- *Persist BM25 pickle alongside ChromaDB* — rejected: creates a second
  store to keep in sync; a desynced index silently violates
  reproducibility. Rebuild cost is trivial at 20 chunks.
- *Whoosh / Jieba / spaCy tokenizers* — rejected: extra dependencies for
  no measured need (Principle XXIV: complexity must justify itself).
- *Treat ChromaDB full-text/HNSW as "BM25"* — rejected: it is not BM25;
  the spec requires a genuine lexical peer for the ablation B experiment.
- *Stemming / stopword removal* — rejected for now: changes recall
  behavior (e.g. dropping "not"), adds knobs; revisit only if measured
  failures attribute to tokenization (Principle XXVII).

---

## R2. Reciprocal Rank Fusion: determinism, ties, duplicates

**Decision**: `retrieval/fusion.py::rrf_fuse(result_lists, k=60)` as a
pure function. Input: named lists of results (each internally ranked
1-based). Score: `RRF(d) = Σ 1/(k + rank_i(d))` over the lists in which
`d` appears, keyed by `chunk_id` (duplicates across lists merged once,
keeping the first-seen rich metadata and recording each contributing
rank). Ordering: descending RRF score, ties broken by `(first_seen_list
order, first_seen position)` — a stable, documented rule, so output is
byte-identical across runs. `k` comes from configuration
(`retrieval.fusion.k`, default 60). Empty input → empty output; one
non-empty list → that list's order fused (ranks still 1-based).

**Rationale**: Principle XXV (NON-NEGOTIABLE) demands rank-based, never
score-averaged, combination; Principle XXV (determinism clause) and
SC-004 demand identical output for identical input; keying on `chunk_id`
implements FR-006's "appear once". A pure function makes every RRF test
case (both/one system, equal/differing ranks, duplicates, missing,
determinism) directly testable with no I/O.

**Alternatives considered**:
- *Weighted score averaging (vector + BM25)* — rejected: prohibited
  NON-NEGOTIABLE (XXV); incomparable score distributions.
- *Normalize scores (min-max/z-score) then blend* — rejected: calibration
  is corpus- and query-dependent; adds failure modes the level would have
  to teach; RRF sidesteps it entirely.
- *Tie-break by chunk_id alphabetically* — rejected: hides first-seen
  provenance; stable insertion order is simpler to explain and preserves
  retriever intent.

---

## R3. Extending RetrievalResult without breaking Level 2

**Decision**: Add **optional** fields with `None` defaults to the existing
`domain.RetrievalResult`: `retrieval_method: str | None`,
`vector_rank: int | None`, `bm25_rank: int | None`,
`rrf_score: float | None`, `reranker_score: float | None`. The existing
`chunk`, `score`, `rank` fields keep their exact meaning (`score` = the
strategy's headline score: cosine for vector/bm25 score for BM25, RRF for
hybrid, cross-encoder logit for reranked; `rank` = final 1-based rank).
`model_config` already allows assignment. Evidence builder
(`grounding/evidence_builder.py`) reads only `chunk`/`score`/`rank`-based
data, so it is untouched.

**Rationale**: Principle XXVI mandates provenance; absence must be
*meaningful* (`None` = stage did not run), which is why there are no
fabricated zeros. Extending the model rather than introducing a parallel
"AdvancedResult" type keeps the Evidence Builder contract unchanged
(FR-027) — Level 2 tests pass without modification.

**Alternatives considered**:
- *Separate `Provenance` sub-model* — rejected: nested optional object
  adds indirection for five scalar fields; flat optionals are directly
  assertable in tests.
- *Subclasses per strategy (VectorResult, HybridResult...)* — rejected:
  `list[RetrievalResult]` is the contract with Level 2; subclasses would
  leak strategy typing into evidence building.
- *Overload `metadata` dict with provenance keys* — rejected: metadata is
  corpus-derived; mixing diagnostics into it would pollute filtering
  (FR-011) and violate the "missing = not run" semantics.

---

## R4. Metadata filtering: mechanism and placement

**Decision**: A single generic helper `matches_filters(metadata, filters)`
evaluating `all(metadata.get(k) == v for k, v in filters.items())` —
applied in the controller to every strategy's results *after* retrieval
and *before* fusion/reranking. Filters come from
`retrieval.filters` (dict in `settings.yaml`, empty = no restriction).
Vector-store-side filtering (Chroma `where`) MAY additionally be used for
the vector strategy as an optimization, but the controller-side generic
filter is the correctness authority so all four strategies behave
identically (FR-010/FR-011).

**Rationale**: Principle/spec demand genericity (new keys work with zero
code changes) and uniform application across strategies. Applying one
helper centrally is the smallest implementation that guarantees identical
filter semantics everywhere; post-retrieval filtering is correct because
filtered-out chunks simply reduce the candidate pool (restriction, never
ranking). At 20 chunks the precision loss from filtering after top-K is
negligible; if measured failures attribute to it (e.g. a filter excluding
the correct chunk from the top-K window), the fallback is to raise the
per-strategy `top_k` under filters — recorded as a config knob, not a
code fork.

**Alternatives considered**:
- *Filter only inside ChromaDB `where` clauses* — rejected: BM25/reranked
  paths bypass Chroma; would need a second filter implementation per
  retriever (violates uniformity of FR-010).
- *Pre-filter at chunk-loading time* — rejected: one query = one filter
  set; mutating the corpus view per query breaks the shared-index model.
- *Metadata store / authorization service* — rejected: RBAC is Out of
  Scope at Level 3; filters are the foundation only (constitution).

---

## R5. Cross-encoder reranker integration

**Decision**: `retrieval/reranker.py` wraps a lazy-loaded
`sentence_transformers.CrossEncoder` with model
`reranking.model` (default `BAAI/bge-reranker-base`). API:
`rerank(query, candidates, final_k) -> list[RetrievalResult]` scoring
`len(candidates) ≤ candidate_k` pairs in one batch, sorting descending,
slicing `final_k`, recording `reranker_score` and re-assigning `score` +
`rank`. Config `reranking.enabled=false` short-circuits in the
controller: the `hybrid_reranked` strategy returns fusion order, sets no
`reranker_score` (matches the hybrid baseline exactly — SC-005), and debug
output marks reranking as skipped. Unit tests inject a fake scorer
(callable) so no model download occurs in CI; the real model is exercised
only in quickstart/manual runs.

**Rationale**: Principle XXIV — the stage must be toggleable to be
measurable (ablation D→E); bounded candidate_k=20 keeps latency
explained (constitution Latency section); constructor injection keeps
deterministic tests hermetic (Level 2 testing rule carried forward).

**Alternatives considered**:
- *Embedding-based "reranking" (re-embed + cosine)* — rejected: that is
  the bi-encoder already used for retrieval; the spec requires a
  cross-encoder's joint scoring.
- *Cohere/Jina hosted rerank API* — rejected: external dependency,
  contradicts local-first stack; model is configurable so it can be
  swapped later without code change.
- *Rerank inside fusion* — rejected: violates stage separation (V/XXI)
  and would make ablation D vs E impossible.

---

## R6. Query rewriting: prompt, failure semantics, experiment modes

**Decision**: `retrieval/query_rewriter.py` reuses the existing OpenRouter
httpx chat client (`generation/llm.py`) with temperature 0.0 and a
system prompt mandating: preserve intent, expand terminology, preserve
technical identifiers (error codes/acronyms/protocol names), no
unsupported assumptions, return exactly one query (no quotes, no
preamble). The controller holds both `original_query` and
`rewritten_query: str | None`; retrieval uses the rewritten string only
when `query_rewriting.enabled=true` AND the rewrite succeeded (non-empty
after validation). Any exception, empty output, or obviously broken reply
(non-string/too long) → warn, fall back to original (FR-017). Debug shows
both. Default `enabled: false`.

**Rationale**: Principle XXIX (NON-NEGOTIABLE) — original always
preserved, off by default, fallback on failure; temperature 0 +
"one query" mandate keeps rewrites as reproducible as an LLM call allows;
reusing the existing client adds no dependency (Assumptions). Separate
modes are achieved by a config flag, which is exactly how the evaluation
matrix toggles original vs rewritten (FR-021).

**Alternatives considered**:
- *Multi-query expansion (3 rewrites + fusion)* — rejected: query
  decomposition is Out of Scope; spec demands exactly one query.
- *Local small rewriter model* — rejected: a second model to ship and
  teach; gateway already exists and is configurable.
- *Rewriting on by default* — rejected: violates XXIX default-off and
  would contaminate baseline measurements.

---

## R7. Retrieval controller and strategy configuration

**Decision**: `retrieval/controller.py::RetrievalController` with
`retrieve(question, strategy=None, filters=None, top_k=None) ->
RetrievalDebug` (results + stage metadata for CLI/debug). Strategy
resolution order: explicit call argument → `retrieval.strategy` config →
error. Valid values: `vector | bm25 | hybrid | hybrid_reranked`; anything
else raises `ValueError` at construction/validation time (Pydantic
validator on the Settings field too) — never silent fallback (FR-008).
Config additions validated in `config.py` with Pydantic (defaults: top_k
vector/bm25/hybrid 20, final 5; fusion method `rrf`, k 60; filters {}).
The controller owns: rewrite (if enabled) → per-strategy retrieval →
filter → fuse → rerank (if enabled) → final ranking. It does not touch
generation.

**Rationale**: One entry point implements FR-007/FR-019 and keeps strategy
behavior observable in a single object; validating the strategy enum in
Settings means invalid configuration fails at startup (quick, loud),
while runtime validation covers CLI `--strategy` overrides.

**Alternatives considered**:
- *Registry/plugin strategy objects* — rejected: four hardcoded branches
  with a validated enum are clearer at this scale (Principle I); a
  registry is framework thinking.
- *Strategy flags instead of enum* (`--hybrid --rerank`) — rejected:
  combinatorial states (e.g. bm25+rerank) are not spec-supported; enum
  keeps the supported set closed.
- *Controller living inside `rag/pipeline.py`* — rejected: pipeline is
  the Level 2 generation path; mixing retrieval selection into it risks
  the grounding contract (FR-027).

---

## R8. Evaluation matrix, ablation harness, and latency capture

**Decision**: `evaluation/retrieval_matrix.py` — pure Python over
`load_questions()` (existing `evaluation/dataset.py`; dataset extended
with `category` values and optional `relevant_chunks`). For each question
× strategy (× query mode when rewriting is enabled) it runs the
controller and reuses the existing Recall/Precision/MRR functions in
`evaluation/metrics.py` (no reimplementation — Principle XVI).
`scripts/run_retrieval_experiments.py` executes ablation A–G by
constructing controllers with fixed configs (rewriting toggles hit the
LLM gateway; flagged `--rewrite` so the default run stays offline and
deterministic) and emits a Markdown report into
`docs/levels/level-03-advanced-retrieval/experiments.md`. Latency: the
controller records `time.perf_counter()` deltas per stage
(rewrite, embed, vector, bm25, filter, fuse, rerank, total) on the debug
object; the harness aggregates them. Unmeasured cells are written as
`TBD`, never estimated (FR-024).

**Rationale**: Two-layer evaluation (XXII) — matrix stays in the
retrieval layer; metrics reuse keeps formulas in one place; a script +
Markdown output matches the Level 2 experiment workflow the project
already follows; per-stage timers on the debug object serve both SC-007
and failure analysis (the same debug trail answers "where did it drop?").

**Alternatives considered**:
- *RAGAS / evaluation framework* — rejected: NON-NEGOTIABLE (XVI,
  Framework Constitution).
- *Writing matrix logic inside the CLI* — rejected: untestable as a
  unit; CLI should render results, not compute metrics.
- *Async/parallel experiment runner* — rejected: 40–50 questions × 4
  strategies is seconds of work offline; concurrency adds nondeterminism
  to latency numbers.

---

## R9. Dependency and reproducibility impact

**Decision**: Add `rank-bm25` to `[project].dependencies` and refresh
`uv.lock` in the same change. Reranker model weights are a
sentence-transformers download (already a dependency), cached locally and
pinned by model name in config; no new service, no API key. Test suite
never requires the model download (fake scorer injection, R5) or the LLM
gateway (mocked rewrite, R6).

**Rationale**: Reproducibility (IV) requires locked deps; keeping
network-bound artifacts out of the test path keeps CI hermetic — the
Level 2 rule for LLM tests extends to reranker/rewrite tests.

**Alternatives considered**:
- *Vendor a hand-written BM25* — rejected: re-implementing a standard
  algorithm duplicates `rank-bm25` poorly; the constitution admits the
  library explicitly.
- *Optional/extra dependency group for reranker* — rejected: reranking
  is a core strategy in the matrix; an extra would make the default
  install unable to run experiment E.
