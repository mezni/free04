# Feature Specification: Level 3 Advanced Retrieval

**Feature Branch**: `004-level-3-advanced-retrieval`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "docs/levels/level-03-advanced-retrieval/plan.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lexical Retrieval Finds Exact Technical Identifiers (Priority: P1)

As a developer learning RAG, I want a lexical (keyword) retrieval
capability that operates over the same knowledge chunks as semantic
retrieval, so that queries built around exact technical identifiers —
error codes, acronyms, protocol names — find the right chunk even when
the embedding-based retriever misses it.

**Why this priority**: Vector retrieval blurs exact identifiers; this is
the specific retrieval failure Level 2 exposed and the foundation every
later strategy (hybrid, fusion, reranking) builds on. Without a working
lexical retriever there is nothing to fuse or compare.

**Independent Test**: Query the lexical strategy with "X2 timeout 504"
and verify the chunk containing that exact string is returned in the
top results with its document ID, chunk ID, and metadata intact.

**Acceptance Scenarios**:

1. **Given** ingested documents, **When** a query contains an exact error
   code or protocol term present in a chunk, **Then** that chunk is
   returned within the top-K lexical results.
2. **Given** a query containing an acronym defined in the corpus,
   **When** the lexical strategy runs, **Then** chunks containing that
   acronym are ranked above chunks that do not.
3. **Given** a query with terms that appear nowhere in the corpus,
   **When** the lexical strategy runs, **Then** an empty result set is
   returned without error.
4. **Given** the knowledge corpus, **When** the lexical index is rebuilt
   from the source documents, **Then** the rebuilt index is identical in
   content to the previous one — the documents, not the index, are the
   source of truth.
5. **Given** a top-K parameter, **When** retrieval runs, **Then** at most
   K results are returned, ordered by descending relevance, and each
   result preserves its document and chunk metadata.

---

### User Story 2 - Configurable Retrieval Strategies With Hybrid Rank Fusion (Priority: P1)

As a developer, I want a retrieval controller that selects between
semantic-only, lexical-only, and hybrid strategies from configuration and
from the command line, combining both retrievers through deterministic
rank-based fusion, so that I can choose and compare how evidence is
gathered for a question.

**Why this priority**: The strategy layer is the spine of the level —
reranking, filtering, diagnostics, and the evaluation matrix all hang off
it. A hybrid that cannot be selected and compared to its parts delivers
no learning value.

**Independent Test**: Run the same question under each strategy
(semantic, lexical, hybrid) and verify each returns ranked results with
the strategy recorded, and that repeated hybrid runs produce identical
ordering.

**Acceptance Scenarios**:

1. **Given** a configuration selecting a strategy, **When** a query runs,
   **Then** only that strategy's retrieval path executes and the results
   record which strategy produced them.
2. **Given** semantic and lexical result lists, **When** hybrid fusion
   runs, **Then** candidates are combined by rank-based fusion
   (Reciprocal Rank Fusion with configurable k), never by averaging raw
   scores from the two retrievers.
3. **Given** identical inputs, **When** fusion runs repeatedly, **Then**
   the output ordering is identical every time, with ties broken by a
   stable rule.
4. **Given** a document found by only one retriever, **When** fusion runs,
   **Then** it still appears in the fused pool with a fusion score derived
   from its rank in that retriever.
5. **Given** a document found by both retrievers, **When** fusion runs,
   **Then** it receives contributions from both ranks and appears once in
   the output.
6. **Given** an unknown or invalid strategy value, **When** configuration
   is loaded or the command runs, **Then** the system fails with a clear
   error instead of silently falling back to another strategy.
7. **Given** a hybrid query where one retriever returns no results,
   **When** fusion runs, **Then** the fused output contains the other
   retriever's candidates in their rank order.

---

### User Story 3 - Per-Stage Retrieval Diagnostics (Priority: P2)

As a developer, I want retrieval diagnostics that show, per result, how it
was found — semantic rank, lexical rank, fusion score, reranker score,
and final rank, alongside the original and any rewritten query — so that
I can attribute a retrieval failure to the exact stage that lost the
chunk.

**Why this priority**: Diagnostics are the learning vehicle of the level
and the raw material for failure analysis, but they can be layered on
once strategies exist.

**Independent Test**: Run a hybrid query in debug mode and verify every
returned result displays its per-stage scores/ranks and the strategy
used.

**Acceptance Scenarios**:

1. **Given** a query in debug mode, **When** results are displayed,
   **Then** each result shows: strategy used, semantic rank, lexical
   rank, fusion score, reranker score (when reranking applied), and final
   rank.
2. **Given** a query, **When** debug output is produced, **Then** the
   original query is always shown, and a rewritten query is shown
   separately whenever a rewrite occurred.
3. **Given** a result produced by a single-retriever strategy, **When**
   diagnostics are shown, **Then** fields belonging to stages that did
   not run are visibly absent rather than filled with fabricated values.
4. **Given** a retrieval failure, **When** debug output is inspected,
   **Then** the first stage at which the correct chunk disappears can be
   identified without reading source code.

---

### User Story 4 - Metadata Filtering (Priority: P2)

As a developer, I want generic metadata filters (department, product,
document type, classification, source) applied uniformly to every
strategy, so that retrieval can be restricted to the slice of the corpus
a question is allowed to see — and so that future access policies have a
foundation to build on.

**Why this priority**: Filtering is a restriction layer that any strategy
can apply; it is independently testable but does not block the core
retrieval upgrades.

**Independent Test**: Configure a filter (e.g. department=network) and
verify that results under every strategy contain only matching chunks,
while an empty filter set returns unfiltered results.

**Acceptance Scenarios**:

1. **Given** configured metadata filters, **When** any strategy retrieves,
   **Then** only chunks whose metadata matches all filter keys are
   returned.
2. **Given** a filter key that exists on no chunk, **When** retrieval
   runs, **Then** an empty result set is returned without error.
3. **Given** no filters configured, **When** retrieval runs, **Then**
   behavior is identical to the unfiltered baseline.
4. **Given** filters, **When** results are ranked, **Then** filtering only
   restricts the candidate set and never reorders or scores results.
5. **Given** a new metadata key not present in today's key list, **When**
   it is configured as a filter, **Then** it works without code changes.

---

### User Story 5 - Cross-Encoder Reranking of the Candidate Pool (Priority: P2)

As a developer, I want an optional reranking stage that re-scores the top
hybrid candidates with a cross-encoder and returns a smaller final set,
so that a stronger relevance signal can be measured against the cheaper
fusion ordering — and toggled off for controlled experiments.

**Why this priority**: Reranking builds on the hybrid candidate pool (P1)
and is the last quality lever before evaluation; its value is only
provable through measurement, so it must exist but must also be
disable-able.

**Independent Test**: Run the reranked strategy and verify final results
are ordered by reranker score over the candidate pool, with reranker
scores recorded; then disable reranking and verify the unreranked fusion
ordering is returned instead.

**Acceptance Scenarios**:

1. **Given** a hybrid candidate pool of size candidate_k, **When**
   reranking runs, **Then** candidates are re-scored and the top final_k
   results are returned in reranker-score order.
2. **Given** reranking disabled in configuration, **When** the reranked
   strategy is requested, **Then** results fall back to fusion ordering
   and no reranker scores are recorded.
3. **Given** a candidate pool, **When** reranking runs, **Then** no result
   outside the candidate pool can appear in the output.
4. **Given** a candidate pool of fewer than final_k items, **When**
   reranking runs, **Then** all candidates are returned without error.
5. **Given** reranker scores, **When** diagnostics display results, **Then**
   the per-result reranker score is visible.

---

### User Story 6 - Optional Query Rewriting With the Original Preserved (Priority: P2)

As a developer, I want an optional query-rewriting stage that expands a
poorly phrased question into a better retrieval query through the LLM
gateway while always preserving the original question, so that I can
measure whether rewriting helps — without ever losing what the user
actually asked.

**Why this priority**: Rewriting mutates user input and adds a network
dependency; it must be off by default and evaluated as a separate
experimental mode, so it comes after the retrieval core is stable.

**Independent Test**: With rewriting enabled, run a poorly phrased query
and verify both the original and rewritten queries are displayed, the
retrieval uses the rewritten form, and the original is unchanged; with
the gateway unavailable, verify retrieval falls back to the original
query.

**Acceptance Scenarios**:

1. **Given** rewriting disabled (default), **When** a query runs, **Then**
   the original query is used for retrieval and no rewrite is attempted.
2. **Given** rewriting enabled, **When** a query is rewritten, **Then**
   the output is exactly one retrieval query that preserves intent and
   technical identifiers and adds no unsupported assumptions.
3. **Given** a rewritten query, **When** debug output is shown, **Then**
   both the original and the rewritten query appear.
4. **Given** a rewrite failure or gateway error, **When** retrieval
   continues, **Then** the original query is used and the request
   succeeds.
5. **Given** evaluation runs, **When** rewriting is measured, **Then**
   original-query and rewritten-query results are reported as separate
   experimental modes.

---

### User Story 7 - Strategy Comparison, Ablation, and Latency Baseline (Priority: P3)

As a developer, I want every evaluation question scored under all four
strategies (semantic, lexical, hybrid, hybrid + reranker) and both query
modes, with an ablation study and per-stage latency measurements, so
that I can answer "which strategy works for which type of Telco
question?" from numbers instead of assumptions.

**Why this priority**: This is the level's proof, but it depends on all
strategies and diagnostics (P1/P2) existing first.

**Independent Test**: Run the evaluation matrix and verify every question
× strategy cell reports Recall@K, Precision@K, and MRR, with no gaps, and
that the ablation table reports latency per stage.

**Acceptance Scenarios**:

1. **Given** the evaluation dataset, **When** the matrix runs, **Then**
   every question is scored under all four strategies for Recall@1/3/5/10,
   Precision@1/3/5/10, and MRR.
2. **Given** query rewriting, **When** the matrix runs, **Then**
   original-query and rewritten-query results are reported separately for
   the same strategies.
3. **Given** the ablation configurations (semantic only; lexical only;
   both; both + fusion; + reranker; + rewriting; + rewriting + reranker),
   **When** each runs, **Then** Recall, Precision, MRR, and latency are
   recorded per experiment.
4. **Given** a retrieval run, **When** timing is collected, **Then**
   embedding, semantic retrieval, lexical retrieval, fusion, reranking,
   rewriting, and total latency are each recorded.
5. **Given** recorded results, **When** the documentation is consulted,
   **Then** every strategy claim traces to a measured number, and
   unmeasured cells are visibly marked as unmeasured rather than
   estimated.

---

### User Story 8 - Failure Analysis, Regression Suite, and Documentation (Priority: P3)

As a developer, I want a documented failure-analysis procedure that
attributes every significant retrieval failure to the first stage that
lost the chunk, a regression test for every discovered failure, and
level documentation (experiments and lessons learned), so that the test
suite and docs become a durable record of retrieval failure modes.

**Why this priority**: This hardens everything above into repeatable
knowledge; it is required for the level to be declared complete but
depends on strategies and evaluation existing.

**Independent Test**: Take a failed evaluation question, walk the
attribution procedure, and verify the failure is classified to a specific
stage with a named regression test covering it; then confirm the full
pre-existing suite still passes.

**Acceptance Scenarios**:

1. **Given** a retrieval failure, **When** the attribution procedure runs,
   **Then** it is classified by the first stage that lost the correct
   chunk (corpus → semantic → lexical → hybrid → reranking → rewriting).
2. **Given** every fixed failure, **When** the suite grows, **Then** a
   named regression test exists for it.
3. **Given** the failure log, **When** it is inspected, **Then** each entry
   records the question, the stage-by-stage outcomes, the first failing
   stage, the fix applied, and the regression test name.
4. **Given** all Level 3 changes, **When** the full pre-existing test
   suite runs, **Then** every Level 0/1/2 test still passes unchanged —
   including the complete Level 2 grounding suite.
5. **Given** the level's experiments and lessons, **When** the work is
   reviewed, **Then** they are documented in the level's documentation
   directory, covering why each technique was introduced, measured
   results, latency impact, failure cases, the winning configuration per
   question category, and remaining limitations.

---

### Edge Cases

- One retriever returns zero results while the other returns results →
  fusion returns the non-empty retriever's candidates; no error.
- A chunk appears in both retrievers' lists → counted once, fused from
  both ranks.
- Two candidates receive identical fusion scores → tie broken by a
  stable, documented rule so ordering is deterministic.
- Candidate pool smaller than the reranker's final size → all candidates
  returned, no error.
- Reranking or rewriting disabled → the pipeline runs without that stage
  and records that it was skipped; output matches the corresponding
  unreranked/unrewritten baseline exactly.
- Query rewriting gateway unavailable or returns garbage → falls back to
  the original query; retrieval still succeeds.
- Unknown strategy name in configuration → clear configuration error, no
  silent fallback.
- Filter matches no chunks → empty result set, no error; downstream
  grounding abstains per Level 2 behavior.
- Unanswerable question under any strategy → no relevant chunks returned
  (true negative preserved), not a spurious near-miss ranked as relevant.
- BM25 index out of sync with source documents → index is rebuilt from
  the documents, never patched by hand.

## Requirements *(mandatory)*

### Functional Requirements

**Lexical retrieval and index**

- **FR-001**: The system MUST provide lexical (keyword) retrieval over
  the same chunks used by semantic retrieval, returning results with
  document ID, chunk ID, text, and metadata, ordered by relevance, with
  top-K behavior and an empty result set for queries matching nothing.
- **FR-002**: The lexical index MUST store chunk ID, document ID, chunk
  text, and metadata, and MUST be reproducible by re-running ingestion
  over the source documents; source documents and chunks remain the
  source of truth and the index MUST NOT be hand-edited or treated as
  authoritative.
- **FR-003**: Semantic (embedding-based) vector retrieval MUST continue
  to work unchanged and remain selectable as its own strategy.

**Strategy selection and fusion**

- **FR-004**: The system MUST support exactly these retrieval strategies,
  selectable from configuration and per command invocation: semantic-only,
  lexical-only, hybrid, and hybrid-with-reranking.
- **FR-005**: Hybrid retrieval MUST combine semantic and lexical results
  using rank-based fusion — Reciprocal Rank Fusion, RRF(d) = Σ 1/(k +
  rank_i(d)), with configurable k — and MUST NOT average or otherwise mix
  raw scores from the two retrievers.
- **FR-006**: Fusion MUST be deterministic: identical inputs produce
  identical output ordering, ties are broken by a stable documented rule,
  duplicates across retrievers appear once, and results from a single
  retriever are still fused when the other retriever returns nothing.
- **FR-007**: A retrieval controller MUST orchestrate strategy selection,
  filtering, optional rewriting, retrieval, fusion, and reranking, and
  MUST return ranked retrieval results only — it MUST NOT generate
  answers.
- **FR-008**: An unknown or invalid strategy value MUST fail loudly at
  configuration or invocation time; silent fallback to another strategy
  is prohibited.
- **FR-009**: Every retrieval result MUST carry provenance: which
  strategy produced it, and — as applicable — semantic rank, lexical
  rank, fusion score, reranker score, final rank, and metadata. Fields
  for stages that did not run MUST be absent rather than fabricated.

**Metadata filtering**

- **FR-010**: The system MUST support generic key/value metadata filters
  configured alongside retrieval, applying them uniformly to every
  strategy, supporting at least: department, product, document type,
  classification, and source.
- **FR-011**: Filter implementations MUST be generic over metadata keys
  (new keys work without code changes); filtering MUST only restrict the
  candidate set and MUST NOT rank or score results; empty filters MUST
  produce unfiltered behavior identical to the baseline.

**Reranking**

- **FR-012**: The system MUST provide an optional reranking stage that
  re-scores the fused candidate pool (size: configurable candidate_k)
  with a cross-encoder relevance model and returns the top configurable
  final_k results ordered by reranker score.
- **FR-013**: Reranking MUST be disable-able through configuration; when
  disabled, the reranked strategy MUST return fusion ordering with no
  reranker scores recorded, matching the unreranked baseline exactly.
- **FR-014**: The reranker MUST only reorder candidates that fusion
  produced; it MUST NOT introduce results from outside the candidate
  pool, and reranker scores MUST be recorded on returned results.

**Query rewriting**

- **FR-015**: The system MUST support optional query rewriting through
  the LLM gateway, whose rewriting instruction requires: preserving user
  intent, expanding useful terminology, preserving technical identifiers,
  avoiding unsupported assumptions, and returning exactly one retrieval
  query.
- **FR-016**: The original query MUST always be preserved unmodified;
  original-query and rewritten-query operation MUST be separate
  experimental modes; rewriting MUST be disabled by default; debug output
  MUST show both queries whenever a rewrite occurs.
- **FR-017**: A rewrite failure or gateway error MUST fall back to the
  original query without failing the request.

**CLI and diagnostics**

- **FR-018**: The CLI MUST expose a retrieval-only command accepting a
  question and a strategy selection, returning results without generating
  answers.
- **FR-019**: A debug mode MUST expose, per result: query, rewritten
  query (when applicable), strategy, chunk, semantic rank, lexical rank,
  fusion score, reranker score, and final rank — sufficient to identify
  the first stage that lost a correct chunk without reading source code.

**Evaluation and measurement**

- **FR-020**: The retrieval evaluation dataset MUST be extended to cover
  eight categories: semantic, exact terminology, error code, acronym,
  multi-concept, ambiguous, metadata-filtered, and unanswerable; each
  case MUST record the question, relevant documents, and relevant
  chunks.
- **FR-021**: Every evaluation question MUST be scored under all four
  strategies and, separately, under original vs rewritten query modes,
  reporting Recall@1/3/5/10, Precision@1/3/5/10, and MRR.
- **FR-022**: An ablation study MUST run configurations: semantic only;
  lexical only; semantic + lexical; semantic + lexical + fusion; hybrid +
  reranking; hybrid + rewriting; hybrid + rewriting + reranking —
  recording Recall, Precision, MRR, and latency for each.
- **FR-023**: Per-stage latency MUST be recorded for embedding, semantic
  retrieval, lexical retrieval, fusion, reranking, rewriting, and total
  retrieval time.
- **FR-024**: Experiment results MUST be recorded in the level's
  experiments documentation; unmeasured values MUST be marked unmeasured,
  never estimated, and every strategy claim MUST trace to a recorded
  number.
- **FR-025**: The system MUST provide a failure-attribution procedure
  that classifies each significant failure by the first stage that lost
  the correct chunk: corpus → semantic → lexical → hybrid fusion →
  reranking → query rewriting.

**Testing, compatibility, and documentation**

- **FR-026**: The test suite MUST cover: lexical retrieval (exact terms,
  error codes, acronyms, no-result queries, top-K, metadata
  preservation), hybrid combination, rank fusion (both/single/one-system
  results, equal and differing ranks, duplicates, missing results,
  deterministic ordering), reranker scoring and pool bounds, query
  rewriting (original preserved, fallback), generic metadata filtering,
  strategy selection, deterministic behavior, empty results, and invalid
  configuration.
- **FR-027**: The Level 2 grounding pipeline MUST remain unchanged in
  contract: the evidence builder continues to consume retrieval results,
  and 100% of existing Level 0/1/2 tests — including the full Level 2
  grounding suite — MUST pass after all Level 3 changes.
- **FR-028**: Every discovered retrieval failure MUST become a named
  regression test.
- **FR-029**: Level documentation MUST be created/updated with
  constitution, plan, experiments, and lessons-learned documents covering
  why each technique was introduced, measured results, latency impact,
  failure cases, the winning configuration per question category, and
  remaining limitations.

### Key Entities

- **Retrieval Result**: One ranked chunk returned by a strategy; carries
  document ID, chunk ID, text, score, rank, strategy that produced it,
  metadata, and stage provenance (semantic rank, lexical rank, fusion
  score, reranker score) as applicable to the stages that ran.
- **Retrieval Strategy**: A selectable retrieval mode — semantic-only,
  lexical-only, hybrid, or hybrid-with-reranking — chosen by
  configuration or per invocation; defines which stages execute.
- **Lexical Index**: A derived, rebuildable artifact built from the
  source chunks holding chunk ID, document ID, text, and metadata;
  reproducible from documents, never the source of truth.
- **Candidate Pool**: The fused set of candidates entering reranking;
  bounded by candidate_k and the only source the reranker may draw from.
- **Fusion Score**: The rank-based combination (RRF) of a chunk's ranks
  across retrievers; scale-free, deterministic, and configurable via k.
- **Metadata Filter**: A generic key/value restriction applied to all
  strategies before ranking; restricts visibility, never scores.
- **Evaluation Case**: A dataset entry with question, category (one of
  eight), relevant documents, and relevant chunks; unanswerable cases
  expect no relevant results.
- **Failure Log Entry**: A record of one significant failure: the
  question, per-stage outcomes, the first failing stage, the fix
  applied, and its regression test.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of evaluation questions are scored under all four
  strategies for Recall@1/3/5/10, Precision@1/3/5/10, and MRR — a
  complete strategy-comparison matrix with no unmeasured cells.
- **SC-002**: On the exact-terminology, error-code, and acronym
  categories, the lexical strategy retrieves the known relevant chunk
  within the top 5 for at least 90% of such questions.
- **SC-003**: Hybrid fusion Recall@10 on the evaluation dataset is at
  least as high as the better of the two single-retriever Recall@10
  values, measured on the same dataset.
- **SC-004**: Repeated fusion runs over identical inputs produce
  byte-identical result ordering in 100% of runs (determinism).
- **SC-005**: With reranking and query rewriting disabled, the system's
  results are identical to the hybrid baseline for 100% of test queries
  (features that are off change nothing).
- **SC-006**: Original-query vs rewritten-query results are measured and
  reported separately for every evaluation question, and the effect of
  rewriting per question category is documented from those measurements.
- **SC-007**: All seven latency measurements (embedding, semantic
  retrieval, lexical retrieval, fusion, reranking, rewriting, total) are
  recorded for every ablation experiment — 100% of experiments have a
  latency figure.
- **SC-008**: 100% of existing Level 0/1/2 tests pass unchanged after
  all Level 3 changes, including the complete Level 2 grounding suite.
- **SC-009**: For 100% of significant evaluation failures, the first
  stage that lost the correct chunk is identified via the attribution
  procedure, and each has a named regression test.
- **SC-010**: For each of the eight evaluation categories, the winning
  strategy is determined from recorded measurements and documented — no
  category is assigned a winner by assumption.
- **SC-011**: 100% of runs under debug mode display the original query,
  the strategy, and full per-stage provenance for every returned result.

## Assumptions

- The feature builds on the completed Level 2 system; ingestion,
  chunking, embedding, vector storage, retrieval metrics, evidence
  building, grounded generation, citation validation, and grounding
  checking are reused with their existing contracts — Level 3 changes
  what is retrieved, not how it is validated.
- The synthetic Telco markdown corpus remains the knowledge base; the
  evaluation dataset is extended with new questions (and relevant
  chunk-level labels) rather than new documents, except where a category
  (e.g., metadata-filtered, error code) requires corpus or metadata
  additions.
- The lexical index is held in-process and rebuilt during ingestion; it
  is not an independently persisted store, consistent with the
  documents-are-truth hierarchy.
- The reranking stage uses a cross-encoder relevance model (default:
  `BAAI/bge-reranker-base` via sentence-transformers) loaded locally and
  configurable by name.
- Query rewriting uses the same LLM gateway already used for generation;
  because it requires live model calls, rewriting experiments are
  recorded in documentation while deterministic tests assert rewriting
  behavior (preservation, fallback, separate modes) through controlled
  fixtures.
- Default tunables unless configured otherwise: fusion k = 60; top-K per
  stage 20 (semantic, lexical, hybrid) with final 5; reranking
  candidate_k = 20, final_k = 5; rewriting disabled.
- When reranking is disabled while the reranked strategy is requested,
  the defined behavior is a graceful fall-through to fusion ordering
  (recorded as skipped) rather than a configuration error — chosen so
  ablation experiments can toggle the stage without changing strategy
  selection.
- The command-line interface remains the only user interface; no web UI,
  REST API, agent behavior, query decomposition, or multi-hop retrieval
  is introduced.
- One new runtime dependency (a BM25 implementation) and the
  already-present embedding stack are used; no RAG, orchestration, or
  evaluation frameworks are introduced, per the constitution.
- Evaluation-matrix and ablation runs are executed on the local corpus
  without external load; latency figures are single-machine baselines
  recorded for comparison, not production SLOs.
