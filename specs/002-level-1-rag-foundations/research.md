# Research: Level 1 RAG Foundations

**Date**: 2026-10-06 | **Feature**: 002-level-1-rag-foundations

This document records the technology and design decisions for replacing the
Level 0 simulated RAG infrastructure with real components. Each entry follows
Decision / Rationale / Alternatives considered.

## Embedding Model

**Decision**: Use `sentence-transformers` with `BAAI/bge-small-en-v1.5`
(default; 384 dimensions, 512 max tokens, MIT license), isolatable behind the
existing `Embedder` interface (`embed` / `embed_batch` / `dimension`).

**Rationale**: User-required stack. Small (≈127 MB fp32), local, free, and
fast enough for a learning corpus. BGE v1.5 models remove the v1.0 query
instruction requirement, so the same `SentenceTransformer.encode()` call can
embed both documents and queries. Actual retrieval is bound by the LLM, not
the embedding pass, and SC-009 (<3s query-to-retrieval) is achievable with
the 384-dim model on CPU.

**Alternatives considered**:
- `all-MiniLM-L6-v2` (current Level 0 test model) — retained only for fast,
  deterministic unit tests (spec Assumptions); too generic for the production
  default.
- BGE base/large (768/1024-dim) — higher MTEB scores but slower and larger for
  no Level 1 need.
- `text-embeddings-inference` server — requires Docker/server, excluded by
  constitution (no containerization).
- OpenAI/API embeddings — rejected by constitution (real local, no API dep).

## Vector Database

**Decision**: Use `chromadb` in **local persistent mode**
(`PersistentClient(path=...)`, default `./data/chroma`) behind the existing
`VectorStore` repository interface. The application passes explicit
embeddings (from our `Embedder`) rather than ChromaDB's default embedding
function.

**Rationale**: User-required stack. ChromaDB provides real persistent vector
storage, metadata filtering, top-K, and distance information with a simple
mental model — appropriate for a learning level. Passing explicit embeddings
keeps the embedding pipeline fully in our control (constitution XV) and lets
tests use a fast model. ChromaDB's `collection.add(ids, embeddings,
documents, metadatas)` and `collection.query(query_embeddings, n_results,
where)` map directly to our `VectorStore` API.

**Score semantics**: ChromaDB returns *distances*. With the default cosine
metric, similarity = `1 - distance`. The retriever MUST convert distances to
scores before applying `similarity_threshold` (constitution VIII/FR-006).
Note ChromaDB raises if `n_results` exceeds collection size — the store MUST
clamp `n_results` to current collection count.

**Alternatives considered**:
- Keep the numpy in-memory store — rejected (constitution XV: real
  infrastructure).
- Qdrant/Milvus/Weaviate — real but heavier; deferred per constitution
  (distributed infra out of scope).
- ChromaDB default embedding function — hides the embedding model behind the
  store, violating "explain the embedding" exit criteria.
- Pinecone — SaaS, requires network + API key, not local.

## Re-ingestion / Reset (FR-016, clarified)

**Decision**: Each ingestion run **drops and recreates** the collection so
stored vectors exclusively reflect the current configuration.

**Rationale**: Clarified with the user. Guarantees experiment results are not
polluted by stale chunks from prior chunk_size/overlap settings and keeps the
store explanation simple.

**Alternatives considered**: upsert-by-id (stale chunks remain when
boundaries shift), additive append (accumulates duplicates).

## Packaging & Environment (uv)

**Decision**: Use **uv** for all environment/dependency/lock management
(`uv sync`, `uv lock`, `uv run`). Add an explicit `[build-system]` so the
`telco-rag` console script works; keep the existing flat `src/` package
layout per the earlier repo cleanup (modules importable as
`from cli import ...` after `src/` is on `sys.path`).

**Rationale**: User-required (uv) AND constitution 4.2 (uv must be the single
tool; no pip/poetry/conda). The current `pyproject.toml` has no build system;
uv treats such projects as virtual, so a console script is not guaranteed.
A declared backend (`uv_build` or `setuptools`) with
`telco-rag = "src.cli:main"` makes `uv run telco-rag "question"` work.

**Backend note**: uv's default `uv_build` assumes `src/<module>/` layout. Our
flat `src/` (package root is `src`) is non-standard; if `uv_build` misbehaves,
fall back to `hatchling`/`setuptools` with explicit package config
(`packages = ["src", ...]`). Either way, tests import modules after inserting
`src/` on `sys.path` (existing pattern), so this choice does not affect tests.

**Alternatives considered**:
- pip + requirements.txt — rejected by constitution (uv required).
- Poetry/pipenv/conda — rejected by constitution.
- Restore `src/telco_rag/` nesting — rejected: the user explicitly flattened
  the code base to `src/`.

## Configuration (YAML + env)

**Decision**: Centralize configuration in `config/settings.yaml` + environment
overrides via `pydantic-settings`. Model picks: embedding model/path, chunk
size/overlap, top-k, similarity threshold, vector store path/collection, LLM
base-url/model/key/max tokens/temperature, document dir, eval dataset path.

**Rationale**: Constitution X (externalized config) and user-required YAML +
Pydantic Settings. YAML is the editable, version-controlled default; env vars
overlay secrets/live values (e.g., OpenRouter key) without committing them.

**Alternatives considered**:
- Env-only (current Level 0) — hard to run experiments (SC-004 requires
  config-only changes).
- TOML — user specified YAML.

## LLM (OpenRouter)

**Decision**: Keep the existing `generation/llm.py` over HTTP
(`httpx`/OpenAI-compatible) pointed at OpenRouter; optionally swap the client
to the `openai` SDK as user-required. LLM config (base URL, model, key) is
independent from the embedding provider (FR-014).

**Rationale**: Unchanged from Level 0 behavior; generation is not the focus of
Level 1. A clear runtime error path (spec FR-017 / clarified) is added so
generation failures don't masquerade as retrieval failures.

**Alternatives considered**: keep `httpx` only (current) — acceptable; `openai`
SDK chosen to match the user's stack table.

## Retrieval Evaluation (FR-009/009a/010, clarified)

**Decision**: `data/evaluation/retrieval_questions.jsonl` with 20–30 entries
(`question` + `relevant_documents[]`). A few entries use an empty
`relevant_documents` list (unanswerable) to verify abstention. Metrics
(Recall@K, Precision@K, MRR) implemented in `src/evaluation/metrics.py` from
first principles; unanswerable questions are EXCLUDED from the metric
aggregate and reported as a separate true-negative count.

**Rationale**: Clarified with the user. In-house implementation is a
NON-NEGOTIABLE constitution principle (XVI) and a learner exit criterion
("explain how Recall@K is calculated").

**Alternatives considered**:
- `ragas`/`rag-evaluation` frameworks — rejected (constitution XVI).
- Include unanswerable questions in the aggregate (score 0) — rejected; distorts
  the primary metric and misrepresents retrieval quality.

## Chunking

**Decision**: Keep the hand-written character chunker
(`ingestion/chunker.py`) with configurable `chunk_size` / `chunk_overlap`,
validating `chunk_overlap < chunk_size`. Chunk IDs stay deterministic
(`{document_id}#{index:04d}`).

**Rationale**: User-required ("your own Python implementation" — learn
chunking instead of hiding it behind a framework); integration with BGE
embedding (512-token context) is compatible with 250–1000 char chunks from
experiments. No semantic/text-split library introduced (constitution II/XV).

**Alternatives considered**: `text-splitter`/langchain splitters — rejected
(no frameworks, learning objective).

## Retrieval Flow & Threshold

**Decision**: Retriever OS pipeline: question → `Embedder.embed_query()`
→ `VectorStore.query()` (top_k clamped, cosine distance → score, optional
metadata `where` filter) → apply `similarity_threshold` → build
`RetrievalResult[]` sorted by descending score.

**Rationale**: Direct expression of constitution VIII (inspectable scores),
retrieval constitution (top_k + threshold configurable), and FR-008
(internal-only metadata filter). Because BGE v1.5 similarity concentrates in
~[0.6, 1.0] for related text, the default threshold must be permissive (plan:
0.0, i.e., no filtering) and surfaced in experiments rather than guessed.

**Alternatives considered**: L2/ip distance metrics — cosine is the standard
for these embeddings and matches Level 0 semantics.

## Metadata

**Decision**: `metadatas` carry `document_id`, `document_name`, `source`,
`chunk_id`, `chunk_index` (constitution IX minimum set) and survive
ingestion → retrieval. Reserved-but-unused enterprise keys documented in
constituition Section 6 are NOT added to stored metadata yet (out of scope for
Level 1).

**Rationale**: Traceability + groundwork for later
lifecycle/governance/RBAC without implementing access control now.