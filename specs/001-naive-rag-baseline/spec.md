# Feature Specification: Level 0 — Naive RAG Baseline

**Feature Branch**: `001-naive-rag-baseline`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "read all docs/levels/level-00-naive-rag/plan.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a question and get a grounded answer (Priority: P1)

A developer asks the system a question about Telco operations (for example,
"How do I troubleshoot 5G packet loss?"). The system searches a small local
knowledge base of synthetic Telco documents, finds the most relevant passages,
and produces an answer that is based on those passages. The answer names the
documents it used.

**Why this priority**: This is the entire point of Level 0 — proving that a
complete retrieval-augmented question/answer loop works end to end. Without
it there is no product.

**Independent Test**: Ask a covered question through the command line and
verify an answer is returned together with the source documents used.

**Acceptance Scenarios**:

1. **Given** the knowledge base contains a document about 5G packet loss,
   **When** the user asks "How do I troubleshoot 5G packet loss?", **Then**
   the system returns an answer derived from that document and lists it as a
   retrieved source.
2. **Given** the knowledge base is populated, **When** the user asks any
   question covered by the corpus, **Then** the answer is produced without
   the user needing to provide context manually.
3. **Given** a question about a covered topic, **When** the answer is
   produced, **Then** the answer content is consistent with the retrieved
   document text (no facts that contradict the corpus).

---

### User Story 2 - Inspect what was retrieved (Priority: P2)

A developer debugging the system can see, for every question, which document
passages were retrieved and how strongly each one matched the question, in
addition to the final answer.

**Why this priority**: Level 0 exists to teach the debugging question "did we
retrieve the right information?". An opaque answer makes the system
impossible to evaluate or improve; retrieval visibility is the core
educational value of this level.

**Independent Test**: Ask any question and confirm the output includes the
question, the retrieved passages with their source documents, match scores,
and the answer.

**Acceptance Scenarios**:

1. **Given** a question has been answered, **When** the user reviews the
   output, **Then** the retrieved passages, their source document names, and
   their similarity scores are displayed.
2. **Given** two questions are asked, **When** the results are compared,
   **Then** differences in retrieved sources and scores are visible between
   the two runs.

---

### User Story 3 - Reproduce the system from a fresh checkout (Priority: P3)

A developer clones the repository, follows the documented setup steps, and
has a working system — including passing tests — without needing undocumented
knowledge.

**Why this priority**: Reproducibility is a constitutional requirement and
guarantees the baseline can be evaluated by anyone; however it does not
deliver user value until the question/answer loop (Story 1) exists.

**Independent Test**: On a clean environment, follow only the README to
install, run the test suite, and ask a sample question successfully.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository, **When** the documented setup
   steps are followed, **Then** the system is ready to answer questions.
2. **Given** the setup is complete, **When** the test suite is run, **Then**
   all tests pass.
3. **Given** required secrets are absent from the repository, **When** the
   repository is inspected, **Then** no real secret values are present and a
   template of required settings is provided.

---

### User Story 4 - Run baseline experiments and record limitations (Priority: P4)

A developer runs a fixed set of baseline questions — including questions the
knowledge base cannot answer — records retrieved documents, scores, answers,
and observations, and documents the weaknesses discovered during Level 0.

**Why this priority**: The recorded baseline is what justifies every later
level of the roadmap, so it matters; but it can only happen once the system
works (Stories 1–3).

**Independent Test**: Execute the documented baseline question set and verify
a baseline record exists containing, per question: retrieved documents,
scores, answer, and observations, plus a list of known limitations.

**Acceptance Scenarios**:

1. **Given** the system is working, **When** the baseline question set is
   run, **Then** each question's retrieved documents, scores, answer, and
   observations are recorded in a baseline document.
2. **Given** a question whose answer does not exist in the corpus (e.g.
   satellite network handover), **When** it is asked, **Then** the response
   and any observed hallucination behavior are recorded.
3. **Given** baseline experiments are complete, **When** the limitations list
   is reviewed, **Then** it documents the discovered weaknesses (e.g. chunking
   splits context, irrelevant retrieval, no reranking, no access control,
   no evaluation framework) as input for Level 1.

---

### Edge Cases

- The knowledge base does not contain the answer: the system must explicitly
  state it lacks enough information instead of inventing an answer.
- The question uses synonyms or different terminology than the documents:
  retrieval may return weakly related passages; behavior must still be
  observable via scores.
- The question contains irrelevant or misleading extra information: the
  system must still return only corpus-grounded content.
- Multiple documents are plausibly relevant: all top-ranked passages are
  shown so the user can judge.
- The knowledge base is empty or a configured document directory is missing:
  the system reports a clear error rather than silently returning nothing.
- A required setting (model/endpoint/credential) is missing: the system
  reports which setting is missing instead of failing opaquely.
- A document is too small to produce multiple chunks: ingestion still
  succeeds with a single chunk.
- Repeated identical questions: retrieval results and scores are stable
  within normal numerical tolerance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest a local corpus of synthetic Telco Markdown
  documents (5G/LTE troubleshooting, broadband, SIM activation, enterprise
  SLA, NOC procedures, escalation) from a configured directory.
- **FR-002**: System MUST split each document into overlapping chunks while
  preserving, for every chunk, its document identity, source name, chunk
  identity, and content.
- **FR-003**: System MUST convert chunks and questions into comparable
  numerical representations using a configurable embedding provider.
- **FR-004**: System MUST store chunk representations locally and support
  adding chunks and searching nearest matches.
- **FR-005**: System MUST retrieve the top-K most similar chunks for a
  question, where K is configurable.
- **FR-006**: System MUST construct a prompt containing system instructions,
  the retrieved context, and the user's question.
- **FR-007**: The system instructions MUST direct the answer model to use
  only the supplied context, to not invent facts, to state when the context
  is insufficient, and to answer clearly.
- **FR-008**: System MUST generate an answer via a configurable answer model
  provider and MUST NOT be bound to a single vendor in the question/answer
  flow.
- **FR-009**: System MUST expose a command-line interface that accepts a
  question and prints the question, the retrieved sources, and the answer.
- **FR-010**: System MUST print, at minimum, for each query: the question,
  retrieved passages with source document names, similarity scores, and the
  final answer.
- **FR-011**: All environment-specific settings (model configuration,
  embedding configuration, chunk size, chunk overlap, top-K, document
  directory) MUST be externalized into a single configuration source; no
  secret values MAY be committed, and a settings template MUST be provided.
- **FR-012**: System MUST include automated tests covering document loading,
  chunking, retrieval, prompt construction, and end-to-end question/answer
  behavior, with deterministic logic tested independently of live model
  behavior.
- **FR-013**: The repository MUST include documentation sufficient for a
  new developer to install, run, and test the system.
- **FR-014**: System MUST record baseline experiment results (question,
  retrieved documents, scores, answer, observations) in a baseline document.
- **FR-015**: System MUST be tested against deliberately unanswerable,
  ambiguous, synonym-based, and noisy questions, and MUST NOT silently
  fabricate knowledge for questions the corpus does not cover.
- **FR-016**: On completion, the project MUST document its known limitations
  as the justification for Level 1.

### Key Entities

- **Document**: A source knowledge file with a stable identity, a name/path
  used as its source reference, and full text content.
- **Chunk**: A fragment of a document with its own identity, the content
  text, and inherited references to its document and source; the unit of
  retrieval.
- **Question**: The user's free-text query submitted through the command
  line.
- **Retrieval Result**: The outcome of searching for a question — an ordered
  list of chunks, each with a similarity score and source reference.
- **Answer**: The model's response generated from a prompt composed of
  instructions, retrieved context, and the question; produced only when
  context exists, otherwise an explicit insufficient-information response.
- **Baseline Record**: The persisted outcome of running the fixed baseline
  question set, containing per-question retrieval and answer data plus
  observations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each of at least 5 covered baseline questions, the system
  returns an answer within 10 seconds, and at least one topically relevant
  corpus document appears among the retrieved sources shown to the user.
- **SC-002**: For questions with no corpus coverage (e.g. satellite network
  handover), the system responds with an explicit "not enough information"
  style answer instead of a fabricated one in at least 9 out of 10 attempts.
- **SC-003**: 100% of queries display the retrieved sources and match scores
  alongside the answer, so retrieval can always be inspected.
- **SC-004**: A developer unfamiliar with the project completes setup and
  successfully answers a sample question in under 30 minutes using only the
  repository documentation.
- **SC-005**: 100% of the automated test suite passes on a fresh checkout,
  and all five component areas (loading, chunking, retrieval, prompt
  construction, end-to-end flow) have at least one test each.
- **SC-006**: The baseline record covers 100% of the agreed baseline question
  set, with retrieved documents, scores, answer, and observations present
  for every question.
- **SC-007**: Zero secret values are present in the repository; a new user
  can identify every required setting from the provided template.

## Assumptions

- The corpus is a small synthetic set of roughly 8 local Telco documents;
  no real customer or confidential telecom data is used (constitutional
  requirement).
- The primary (and only) interface for Level 0 is a command-line tool; web
  UI, authentication, and multi-user access are out of scope.
- An answer model and an embedding capability are reachable through
  configuration supplied by the developer (endpoint/credential); which
  provider is used is deliberately unspecified and interchangeable.
- Retrieval is single-strategy vector similarity search with a configurable
  top-K (default 4); hybrid search, BM25, reranking, query rewriting, and
  metadata filtering are out of scope.
- Fixed-size chunking with overlap is acceptable as the deliberately naive
  baseline; improved chunking is deferred to Level 1.
- English-language documents and questions.
- "Reproducible within reasonable model variability" means identical
  documents and configuration yield the same retrieved documents, not
  byte-identical model output.
- No CI/CD, containerization, deployment, monitoring, or production
  hardening at this level.
