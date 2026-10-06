# Feature Specification: Level 1 RAG Foundations

**Feature Branch**: `002-level-1-rag-foundations`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "From docs/levels/level-01-rag-foundations/plan.md, upgrade Level 0 naive RAG to Level 1 using the recommended stack: Python 3.12+, uv, Pydantic v2, Markdown documents, own Python chunking, Sentence Transformers (BAAI/bge-small-en-v1.5), ChromaDB for vector storage/similarity/metadata, OpenRouter LLM via OpenAI SDK, YAML + Pydantic Settings configuration, Typer CLI, pytest, own Recall@K/Precision@K/MRR metrics, Ruff formatting, mypy type checking, no Docker."

## Clarifications

### Session 2026-10-06

- Q: When the chunking configuration changes (e.g., chunk_size 500 → 1000), should re-ingestion clear the existing vector database or keep the previously stored chunks? → A: Reset/recreate the collection on each ingestion run so stored vectors reflect only the current configuration.
- Q: Should the retrieval evaluation dataset include questions that are intentionally unanswerable from the corpus, and how should they be scored? → A: Include a few unanswerable questions (empty expected documents) to verify abstention; exclude them from the Recall@K/Precision@K/MRR aggregate and report them as a separate true-negative count.
- Q: Should metadata filtering be a user-facing capability exposed through the CLI, or an internal capability of the retrieval layer only? → A: Internal retrieval-layer capability only (optional query argument); NOT exposed through the CLI in Level 1.
- Q: When the generation backend (LLM) is unreachable or returns an error during a normal query, what should the user experience be? → A: Print a clear error (e.g., "generation backend unavailable") with a non-zero exit code; if --debug-retrieval was requested, still print retrieval results before the error.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real Embedding and Vector Retrieval (Priority: P1)

As a developer learning RAG, I want the system to use a real local embedding
model and a real persistent vector database so that retrieval results reflect
genuine semantic similarity rather than simulated behavior.

**Why this priority**: This is the core upgrade from Level 0. Without real
embeddings and a real vector store, every downstream capability (diagnostics,
evaluation, configuration experiments) measures simulated noise rather than
actual retrieval quality.

**Independent Test**: Ingest the Telco markdown documents, ask a query about
5G packet loss, and verify that the returned chunks come from the correct
documents with meaningful similarity scores — all using a real embedding model
and persistent vector storage.

**Acceptance Scenarios**:

1. **Given** 8 Telco markdown documents are loaded, **When** the system
   ingests them, **Then** each document is chunked, embedded with a real
   384-dimensional embedding model, and stored in a persistent vector database
   with its metadata intact.
2. **Given** documents are ingested, **When** a user queries "What causes 5G
   packet loss?", **Then** the system returns ranked chunks from relevant
   documents with similarity scores.
3. **Given** the vector database has been populated, **When** the application
   restarts, **Then** previously ingested chunks are still retrievable
   (persistence across restarts).
4. **Given** two semantically similar sentences, **When** both are embedded,
   **Then** their vectors have higher cosine similarity than two unrelated
   sentences.

---

### User Story 2 - Retrieval Diagnostics (Priority: P2)

As a developer, I want to inspect retrieval results independently from answer
generation so that I can debug whether the right knowledge was retrieved
before evaluating the LLM's response.

**Why this priority**: Retrieval debugging is the primary learning tool of
Level 1. Without it, the developer cannot distinguish retrieval failures from
generation failures.

**Independent Test**: Run a query with a debug flag and verify that the output
shows retrieved document IDs, chunk IDs, and similarity scores without
calling the LLM.

**Acceptance Scenarios**:

1. **Given** documents are ingested, **When** the user runs a query with
   `--debug-retrieval`, **Then** the output displays each retrieved chunk's
   document ID, chunk ID, and similarity score.
2. **Given** `--debug-retrieval` is active, **When** retrieval completes,
   **Then** the LLM is not invoked (retrieval inspection is independent of
   generation).
3. **Given** a query, **When** no chunks pass the similarity threshold,
   **Then** the debug output clearly indicates zero results.

---

### User Story 3 - Configurable Retrieval and Chunking (Priority: P2)

As a developer running experiments, I want chunk size, chunk overlap, top-K,
and similarity threshold to be configurable so that I can measure how each
parameter affects retrieval quality.

**Why this priority**: Configuration enables the experimental evaluation
required by the Level 1 constitution. Without it, the developer cannot answer
"How does chunk size affect retrieval?"

**Independent Test**: Change chunk_size from 500 to 1000 in configuration,
re-ingest, and verify that the number and boundaries of chunks change
accordingly.

**Acceptance Scenarios**:

1. **Given** configuration specifies chunk_size=500, **When** documents are
   chunked, **Then** no chunk exceeds 500 characters.
2. **Given** configuration specifies chunk_overlap=50, **When** consecutive
   chunks are created, **Then** they share approximately 50 characters of
   overlap.
3. **Given** configuration specifies top_k=3, **When** a query is executed,
   **Then** at most 3 results are returned.
4. **Given** configuration specifies a similarity_threshold, **When** results
   below that threshold are found, **Then** they are excluded from the
   results.

---

### User Story 4 - Retrieval Evaluation (Priority: P3)

As a developer, I want a retrieval evaluation dataset and metrics
(Recall@K, Precision@K, MRR) so that I can quantitatively measure retrieval
quality and compare configurations.

**Why this priority**: Evaluation is what transforms subjective "this seems
right" into measurable evidence. It is required by the Level 1 definition of
done but depends on real retrieval (P1) and configuration (P2) being in place.

**Independent Test**: Run the evaluation against a known dataset of 20–30
questions with expected documents and verify that Recall@K, Precision@K, and
MRR are calculated and reported.

**Acceptance Scenarios**:

1. **Given** an evaluation dataset of questions with expected documents,
   **When** the evaluation runs, **Then** Recall@K, Precision@K, and MRR are
   computed and reported.
2. **Given** a question whose expected document is retrieved in the top 3,
   **When** MRR is calculated, **Then** the reciprocal rank reflects position
   3 (1/3).
3. **Given** a question whose expected document is not retrieved, **When**
   Recall@K is calculated for that question, **Then** recall is 0 for that
   question.

---

### User Story 5 - Level 0 Regression (Priority: P1)

As a developer, I want all Level 0 functionality to continue working after
the Level 1 upgrade so that the replacement of simulated infrastructure does
not break the existing pipeline.

**Why this priority**: The Level 1 constitution mandates backward
compatibility. If Level 0 behavior regresses, the upgrade has failed regardless
of new capabilities.

**Independent Test**: Run the existing Level 0 test suite and CLI scenarios
(5G packet loss, unknown question abstention) and verify they pass unchanged.

**Acceptance Scenarios**:

1. **Given** the Level 1 upgrade is applied, **When** the Level 0 test suite
   runs, **Then** all existing tests pass.
2. **Given** the upgraded system, **When** an unknown question is asked with
   no matching chunks, **Then** the system returns the abstention message.
3. **Given** the upgraded system, **When** a known question is asked, **Then**
   the four-block CLI output protocol is preserved.

---

### Edge Cases

- What happens when a document is empty or whitespace-only? → System produces
  a single empty chunk without crashing (preserves Level 0 behavior).
- How does the system handle an embedding model that fails to download or load?
  → Clear error message with actionable remediation (check network, model
  name).
- What happens when the vector database directory does not exist? → System
  creates it on first ingestion.
- How does the system handle a query that returns zero chunks above the
  similarity threshold? → Abstention response; debug output shows zero
  results.
- What happens when chunk_overlap >= chunk_size? → Configuration validation
  rejects the value with a clear error before ingestion begins.
- How does the system handle a document whose content is shorter than
  chunk_size? → Produces exactly one chunk.
- What happens when a chunk config parameter (chunk_size / chunk_overlap) is
  changed and the user re-ingests? → The collection is reset and rebuilt from
  scratch; no stale chunks from the previous configuration remain.
- What happens when the LLM backend is unreachable at query time? → Clear
  error + non-zero exit; retrieval diagnostics are still shown if requested.
- What happens when the evaluation dataset references a document not in the
  corpus? → Evaluation reports the miss; it does not crash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use a real local embedding model to generate
  vector representations of text (recommended: BAAI/bge-small-en-v1.5, 384
  dimensions).
- **FR-002**: System MUST store embeddings in a persistent local vector
  database that survives application restarts.
- **FR-003**: System MUST preserve document and chunk metadata (document_id,
  document_name, chunk_id, source, chunk_index) through the complete
  ingestion → retrieval pipeline.
- **FR-004**: System MUST represent documents, chunks, and retrieval results
  as structured, typed objects — retrieval MUST NOT return anonymous strings.
- **FR-005**: System MUST make chunk_size and chunk_overlap configurable
  without code changes.
- **FR-006**: System MUST make top_k and similarity_threshold configurable
  without code changes.
- **FR-007**: System MUST provide a retrieval diagnostics mode that displays
  retrieved chunks with similarity scores independently from answer
  generation.
- **FR-008**: System MUST support metadata filtering as an internal
  retrieval-layer capability (an optional query argument restricting results
  to matching document metadata). Metadata filtering MUST NOT be exposed
  through the CLI in Level 1.
- **FR-009**: System MUST provide a retrieval evaluation dataset of
  approximately 20–30 questions. The dataset MUST include a small number of
  questions with no expected documents (unanswerable from the corpus) so that
  abstention behavior is verified.
- **FR-009a**: System MUST exclude unanswerable questions from the
  Recall@K/Precision@K/MRR aggregate and report them separately as a
  true-negative count (questions where the system correctly abstained vs.
  incorrectly returned results).
- **FR-010**: System MUST calculate Recall@K, Precision@K, and MRR directly
  in application code (not delegated to an external evaluation framework).
- **FR-011**: System MUST externalize all configuration (embedding model,
  chunk parameters, retrieval parameters, vector database path, LLM settings)
  into a configuration file — configuration MUST NOT be scattered through
  source code.
- **FR-012**: System MUST maintain a CLI interface supporting both normal
  querying and retrieval diagnostics.
- **FR-013**: System MUST preserve all Level 0 test coverage; existing tests
  MUST continue to pass after the Level 1 upgrade.
- **FR-014**: System MUST keep the LLM provider separate from the embedding
  provider (different services, independent configuration).
- **FR-015**: System MUST NOT expose vector database-specific APIs outside a
  dedicated repository/interface layer.
- **FR-016**: System MUST recreate/reset the vector store collection on each
  ingestion run so that stored vectors exclusively reflect the current
  configuration (no stale chunks from prior chunking or retrieval settings).
- **FR-017**: When the generation backend is unreachable or returns an error
  during a normal query, the system MUST report a clear error describing the
  failure and exit with a non-zero code. If `--debug-retrieval` was requested,
  the system MUST still print retrieval results before reporting the error.

### Key Entities

- **Document**: A loaded Telco markdown file. Key attributes: document_id
  (deterministic, derived from filename), title, source path, full content,
  metadata. One document produces zero or more chunks.
- **Chunk**: A contiguous segment of a document. Key attributes: chunk_id
  (deterministic, derived from document_id + index), document_id (parent
  reference), text content, chunk_index, metadata inherited from parent.
  One chunk maps to exactly one vector embedding.
- **RetrievalResult**: A single result from similarity search. Key
  attributes: chunk_id, document_id, text, similarity score, metadata. The
  score MUST be present and meaningful (higher = more similar).
- **Evaluation Question**: An entry in the evaluation dataset. Key
  attributes: question text, list of expected/relevant document_ids (MUST be
  empty for unanswerable questions). Used to compute Recall@K, Precision@K,
  MRR, and the true-negative count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can ingest all 8 Telco documents and retrieve
  relevant chunks for a known query in a single session with zero manual
  intervention.
- **SC-002**: Retrieval results include similarity scores that rank
  semantically relevant documents above irrelevant ones for at least 80% of
  evaluation questions.
- **SC-003**: The retrieval diagnostics output shows document ID, chunk ID,
  and score for every retrieved chunk without invoking the LLM.
- **SC-004**: Changing a configuration value (chunk_size, top_k, or
  similarity_threshold) and re-running retrieval produces observably
  different results without any code changes.
- **SC-005**: All Level 0 tests pass after the upgrade with zero regressions.
- **SC-006**: The evaluation suite reports Recall@5, Precision@5, MRR for
  the answerable evaluation questions and a separate true-negative count
  (correct abstentions) for the unanswerable ones.
- **SC-007**: A developer can explain, using the diagnostics output alone,
  why a specific chunk was retrieved for a given query.
- **SC-008**: Ingestion of the full document corpus completes in under 60
  seconds on a developer laptop.
- **SC-009**: Query-to-retrieval latency is under 3 seconds for a local
  embedding model on a developer laptop.

## Assumptions

- The 8 existing Telco markdown documents in `data/documents/` serve as the
  ingestion corpus; no additional documents are required for Level 1.
- The LLM remains accessible via OpenRouter with existing credentials; no
  LLM changes are required for this feature (generation is already working
  from Level 0).
- The existing `all-MiniLM-L6-v2` embedding model used in Level 0 tests may
  be retained for test speed, while `BAAI/bge-small-en-v1.5` is the
  recommended production embedding model.
- ChromaDB operates in local persistent mode (no server deployment).
- Docker and containerization are explicitly out of scope for Level 1.
- Type checking (mypy) and linting (Ruff) are development-time tools; they
  do not affect runtime behavior and are not part of acceptance criteria.
- Git is used for version control of experiments; no branching workflow
  changes are implied.
