# Research: Level 0 — Naive RAG Baseline

**Date**: 2026-10-06
**Scope**: Resolve technical unknowns from the plan's Technical Context for a
single-user, discoverable, naive RAG baseline. Source inputs: the Level 0
plan (`docs/levels/level-00-naive-rag/plan.md`), the feature spec
(`specs/001-naive-rag-baseline/spec.md`), and the project constitution
v1.0.0.

## Open Questions

The following decisions resolve every `NEEDS CLARIFICATION` item raised in
Technical Context. Each is recorded as Decision / Rationale / Alternatives.

### 1. Embedding provider

**Decision**: `sentence-transformers` with the default model
(`all-MiniLM-L6-v2`, 384-dim), exposed behind a minimal embedder contract
(`embed_documents(list[str]) -> vectors`, `embed_query(str) -> vector`,
plus `dimension`).

**Rationale**: One small (~91 MB) one-time download, then fully offline and
CPU-feasible — deterministic enough for a reproducible baseline and fitting
Constitution Principle II (simple before sophisticated). The protocol keeps
the pipeline provider-agnostic (Principle V / FR-003), so Level 1+ can swap
in an API-backed provider without touching retrieval code.

**Alternatives considered**:
- OpenAI-compatible embeddings API: network + key + latency, non-reproducible
  without cached embeddings — better deferred to Level 1.
- Ollama `/api/embed`: requires a running daemon — extra machine dependency.
- TF-IDF/hash baselines: deterministic but not true vector RAG.

### 2. Vector store

**Decision**: In-memory numpy store. Embeddings are L2-normalized once and
stored in a single `(N, dim)` float32 matrix; cosine similarity is the dot
product; search is `np.argsort(-scores)[:k]`.

**Rationale**: ~30 readable lines, exact search (recall 1.0), zero deps
beyond numpy, trivially testable with hand-crafted vectors. It is a
legitimate baseline that later levels genuinely replace (Chroma/FAISS/
pgvector) through the same `add(chunks)` / `search(query, top_k)` contract
(FR-004, FR-005). This is an intentional no-infrastructure choice per
Constitution Principles I and II.

**Alternatives considered**:
- ChromaDB: easy but brings index + persistence machinery to explain.
- FAISS: fast but low-level/opaque and unnecessary at this corpus size.

### 3. Top-K default

**Decision**: `k = 4`.

**Rationale**: An 8-document corpus chunked at ~500 characters yields roughly
20–40 chunks; k=4 surfaces the target document plus neighbours from chunk
overlap while keeping the prompt small and noise low (FR-005). Consistent
with observed optima (k≈3–5) for fact-style QA on small corpora.

**Alternatives considered**: k=3 (may miss connected facts); k=5–8
(over-retrieval with overlapping chunks muddies grounding).

### 4. LLM answer provider

**Decision**: Plain HTTP call to an OpenAI-compatible chat-completions
endpoint (`POST {LLM_BASE_URL}/chat/completions`), non-streaming, configured
via environment (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`,
`LLM_MAX_TOKENS`=512, `LLM_TEMPERATURE`=0.0).

**Rationale**: Non-streaming keeps the Level 0 client small and readable; the
compatibility contract works with most local and hosted servers, satisfying
FR-008 (configurable provider, not bound to one vendor) and Principle X.

**Pitfalls to handle**:
- Servers that ignore `stream:false` and return SSE — respond with
  `Accept: application/json` and parse defensively.
- `max_tokens` vs `max_completion_tokens` differences — send `max_tokens`
  and tolerate rejection with a clear error.
- Timeouts, connection refused, HTTP 4xx/5xx, empty/`choices`, and
  `finish_reason == "length"` MUST surface as readable CLI errors, never
  crash the process opaquely (FR-011 spirit, spec edge cases).
- `temperature=0` is not perfectly deterministic across providers, so tests
  MUST mock the model/embedding clients rather than the network (FR-012).

**Alternatives considered**:
- Official `openai` SDK: less code but hides the HTTP contract (educational
  value lost).
- Ollama-only: deterministic but single-provider (violates FR-008).
- Responses API: not yet universally compatible.

## Other Defaults Confirmed

- **Language/version**: Python 3.12+ (matches existing `pyproject.toml`:
  `requires-python = ">=3.12"`, project name `telco-rag`).
- **Chunking**: fixed-size by character length with overlap
  (`CHUNK_SIZE`=500, `CHUNK_OVERLAP`=50); deliberately naive (FR-002).
- **Config**: single settings object loaded from environment with validated
  defaults; a `.env.example` committed, `.env` git-ignored (Principle X).
- **Corpus**: 8 synthetic Telco Markdown files under `data/documents/`
  (5G/LTE troubleshooting, broadband, SIM activation, SLA, NOC, escalation).
- **Testing**: pytest; deterministic logic (loader, chunker, retriever,
  prompt) tested directly; embedding/LLM clients mocked for the
  end-to-end test; abstracted behind small client classes.
- **Similarity metric**: cosine (post-normalization dot product).
- **Search exactness**: brute-force exact search is acceptable and desired at
  this scale (no ANN index in Level 0).