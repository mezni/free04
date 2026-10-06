<!--
Sync Impact Report
==================
Template source: constitution-template (resolved via resolve-template.sh)
Version change: 1.0.0 -> 1.1.0
Bump type: MINOR (material expansion: new Level 1 sections added; no
           existing principle removed or redefined)

Modified principles:
  - "I. Learn From the Baseline" -> "I. Learn From the Level" (title
    generalized from Level 0 to any active level)
  - "II. Simple Before Sophisticated" -> unchanged
  - "III. Telco Domain From Day One" -> unchanged
  - "IV. Reproducibility" -> expanded to require uv, locked deps
  - "V. Explicit RAG Pipeline" -> expanded to include evaluation path
  - "VI. Retrieval Before Generation" -> unchanged
  - "VII. No Knowledge Outside the Corpus" -> unchanged
  - "VIII. Make Retrieval Inspectable" -> expanded: independent
    retrieval diagnostics (Level 1 Section 9)
  - "IX. Minimal Metadata" -> expanded: metadata must survive full
    ingestion->retrieval pipeline (Level 1 Section 6)
  - "X. Configuration Over Hardcoding" -> expanded: chunk_size,
    chunk_overlap, top_k, similarity_threshold explicitly configurable
  - "XI. Tests From the Beginning" -> expanded: Level 0 regression
    tests must continue to pass (Level 1 Section 11)
  - "XII. CLI First" -> expanded: --debug-retrieval flag required
  - "XIII. No Premature Enterprise Architecture" -> unchanged
  - "XIV. Every Level Must Expose the Next Problem" -> unchanged
  - "XV. Real Before Sophisticated (NON-NEGOTIABLE)" -> NEW: replace
    simulation with real infrastructure before adding sophistication
  - "XVI. Metrics Written, Not Hidden (NON-NEGOTIABLE)" -> NEW: recall/
    precision/MRR implemented directly in Python, not behind a framework

Added sections:
  - Level 1 Technology Constitution (source Section 4: uv, Pydantic v2,
    sentence-transformers, BAAI/bge-small-en-v1.5, ChromaDB, OpenRouter,
    Typer)
  - Level 1 Structured Knowledge Objects (source Section 5)
  - Level 1 Chunking Constitution (source Section 7)
  - Level 1 Retrieval Constitution (source Section 8)
  - Level 1 Retrieval Evaluation (source Section 10)
  - Level 1 Reproducibility Addendum (source Section 13)
  - Level 1 Out of Scope (source Section 15)
  - Level 1 Backward Compatibility (source Section 16)
  - Level 1 Enterprise Preparation (source Section 17)
  - Level 1 Quality Gates (source Section 18: Definition of Done)
  - Level 1 Exit Criteria (source Section 19)

Removed sections:
  - none. Level 0 content preserved as historical baseline.

Placeholders left undefined: none.
Follow-up TODOs: none.

Date notes:
  - RATIFICATION_DATE kept at 2026-10-06 (original constitution adoption).
  - LAST_AMENDED_DATE set to 2026-10-06 (Level 1 content incorporated).
-->

# Telco Enterprise RAG Constitution

**Level:** 1 — RAG Foundations | **Status:** Active
**Previous Level:** Level 0 — Naive RAG | **Next Level:** Level 2 — Grounded RAG

## Core Principles

### I. Learn From the Level (NON-NEGOTIABLE)

The active level's implementation MUST remain simple enough that the
developer can understand every component. No abstraction MAY be introduced
merely because it is common in enterprise RAG systems. Every component MUST
answer the question "What active-level problem does this component solve?";
any component that cannot answer it MUST be deferred to a later level.

Rationale: each level is a learning milestone; opaque abstractions defeat
its purpose.

### II. Simple Before Sophisticated (NON-NEGOTIABLE)

The active level MUST prefer a simple implementation over framework
complexity. The implementation MUST NOT introduce agent frameworks,
orchestration frameworks, microservices, distributed systems, message
queues, Kubernetes, or complex databases unless no level requirement can be
met without them.

Rationale: RAG fundamentals must be understood before enterprise
infrastructure is introduced.

### III. Telco Domain From Day One

The knowledge base MUST contain Telco-oriented documents covering at least:
5G troubleshooting, LTE troubleshooting, network incidents, NOC procedures,
SIM activation, broadband troubleshooting, enterprise SLA, and network
operations. The domain must be realistic enough to expose RAG-specific
problems even though the implementation is naive.

All documents MUST be synthetic. No real customer data or confidential
telecom information MAY be ingested, at any level.

### IV. Reproducibility

A developer MUST be able to clone the repository and reproduce the system
using documented steps alone. The project MUST define: Python version,
dependency management (uv), environment configuration, required environment
variables, installation instructions, execution instructions, and test
instructions.

Dependencies MUST be pinned/locked through uv (`uv.lock`). Given the same
input documents and configuration, retrieval behavior MUST be reproducible
within reasonable embedding/model variability.

### V. Explicit RAG Pipeline

The implementation MUST make every RAG stage visible as a distinct,
identifiable responsibility:

```text
Document Loader
      ↓
Chunker
      ↓
Embedder
      ↓
Vector Store
      ↓
Retriever
      ↓
Prompt Builder
      ↓
LLM
      ↓
Answer
```

Evaluation is a separate path:

```text
Evaluation Dataset → Query → Retriever → Retrieved Documents
                   → Expected Documents → Retrieval Metrics
```

Stage responsibilities MUST NOT be hidden inside one opaque function.

Rationale: the pipeline is educational as well as architectural; learners
MUST be able to point at each stage in the code.

### VI. Retrieval Before Generation

The LLM MUST NOT be treated as the knowledge source. For every question the
application MUST, in order:

1. receive the question,
2. retrieve relevant context from the vector store,
3. construct a prompt containing the retrieved context,
4. ask the LLM to answer using that context.

Any code path that sends a user question directly to the LLM without
retrieval violates this principle.

### VII. No Knowledge Outside the Corpus

The prompt MUST instruct the model to answer using only the supplied
retrieved context. When the retrieved context does not contain enough
information, the system MUST produce an explicit inability-to-answer response
rather than invent unsupported facts, for example:

```text
I don't have enough information in the knowledge base
to answer this question.
```

Rationale: this baseline grounding behavior is what later levels refine into
citations, abstention, and evaluation.

### VIII. Make Retrieval Inspectable

Every query MUST expose, at minimum:

```text
Question
Retrieved chunks
Similarity scores
Final answer
```

The system MUST provide a way to inspect retrieval independently from answer
generation (e.g., a `--debug-retrieval` CLI flag). The project MUST NOT
require the user to inspect the final LLM answer to understand retrieval
behavior.

Rationale: each level exists to teach the fundamental RAG debugging
question — did the system retrieve the right information before asking
whether the LLM generated the right answer? An opaque answer is a failed
debug session.

### IX. Minimal Metadata

Every document and chunk MUST carry metadata identifying its origin. At
minimum:

```text
document_id
title
source
chunk_id
chunk_index
```

Metadata MUST survive the complete ingestion → retrieval pipeline. The
design MUST leave room for future enterprise metadata (tenant_id, owner,
department, classification, version, status, effective_from,
effective_until, access_policy) even though those fields are not
implemented as access-control mechanisms yet.

Rationale: metadata architecture becomes increasingly important at later
enterprise levels; designing for it now prevents costly rework.

### X. Configuration Over Hardcoding

Model names, API endpoints, embedding configuration, retrieval parameters,
and other environment-specific settings MUST be centralized in configuration
and MUST NOT be scattered through the source code.

At minimum, the following MUST be configurable:

```text
embedding model
chunk_size
chunk_overlap
top_k
similarity_threshold
vector database path
LLM configuration
```

Secrets MUST NEVER be committed to Git. The `.env` file MUST be excluded
from source control, and a `.env.example` template listing all required
variables (without values) MUST be provided.

### XI. Tests From the Beginning

Code MUST be testable from the first commit. Tests MUST cover, at minimum:

- document models
- chunk models
- chunking
- embeddings
- vector-store operations
- retrieval
- metadata preservation
- retrieval thresholds
- retrieval evaluation
- RAG integration

Tests MUST distinguish deterministic application logic from external LLM
behavior; assertions against live LLM output MUST be isolated from
deterministic unit tests.

Level 0 regression tests MUST continue to pass unless a deliberate
behavioral change is documented.

### XII. CLI First

The system MUST expose a simple command-line interface, for example:

```bash
python -m telco_rag.cli "Why is my 5G connection experiencing packet loss?"
```

The CLI MUST support retrieval diagnostics:

```bash
python -m telco_rag.cli "question" --debug-retrieval
```

The CLI MUST make experimentation fast. A web UI MUST NOT be built at this
level.

### XIII. No Premature Enterprise Architecture

The active level MUST NOT claim or simulate production readiness. The
architecture documentation MUST explicitly list known limitations, including
at minimum:

```text
No authentication
No RBAC
No document lifecycle
No tenant isolation
No production monitoring
No HA
No CI/CD
No enterprise evaluation framework
```

Rationale: these limitations are deliberate starting points for later levels,
not defects to be papered over with stub enterprise features.

### XIV. Every Level Must Expose the Next Problem

The project is a maturity progression. Completing a level MUST leave its
known problems documented — at minimum: poor chunking, irrelevant retrieval,
lack of metadata, weak source traceability, inability to measure retrieval
quality, inability to manage document versions, and inability to enforce
access control.

Each level MUST end by identifying the problems it cannot solve; those
problems become the justification for the subsequent level.

### XV. Real Before Sophisticated (NON-NEGOTIABLE)

The active level MUST replace simulated infrastructure with real
infrastructure before adding sophistication. At Level 1 this means: real
embeddings (sentence-transformers), a real vector database (ChromaDB), and
structured Pydantic models — not additional abstractions on top of fake
components.

Rationale: replacing simulation with reality is the core upgrade of each
early level; sophistication built on simulation teaches nothing about real
retrieval behavior.

### XVI. Metrics Written, Not Hidden (NON-NEGOTIABLE)

Retrieval metrics (Recall@K, Precision@K, MRR) MUST be implemented directly
in Python rather than delegated to an evaluation framework. The developer
MUST be able to explain the formula behind each metric.

Rationale: the purpose of Level 1 evaluation is to understand what the
metrics measure, not to run a black-box benchmark.

## Purpose and Scope

This constitution defines the engineering principles and boundaries for
Level 1 of the Telco Enterprise RAG project. The objective of Level 1 is:

> Replace simulation with reality, but do not replace understanding with
> frameworks.

Level 1 transforms the Level 0 prototype from a purely simulated RAG system
into a real, measurable, inspectable retrieval system by introducing:

- real embeddings
- a real vector database
- structured document and chunk models
- metadata
- configurable chunking
- configurable retrieval
- retrieval scores
- retrieval diagnostics
- retrieval evaluation
- retrieval regression tests

The system must demonstrate the complete RAG lifecycle with real
infrastructure:

```text
Documents → Load → Chunk → Embed → Store (ChromaDB) → Retrieve
          → Build prompt → LLM → Answer
```

Level 1 is a real-infrastructure learning level. It is **not a
production-ready enterprise system**.

### Included

Level 1 includes only the capabilities required to demonstrate real
retrieval:

- Python application with Pydantic v2 models
- uv for dependency and environment management
- Local Telco knowledge documents
- Document loading into structured Document objects
- Configurable text chunking with metadata preservation
- Real embedding generation (sentence-transformers, BAAI/bge-small-en-v1.5)
- Persistent vector storage (ChromaDB)
- Similarity search with metadata support
- Configurable top-K and similarity threshold
- Retrieval diagnostics (`--debug-retrieval`)
- Retrieval evaluation (Recall@K, Precision@K, MRR)
- Prompt construction
- LLM answer generation (OpenRouter)
- CLI interface (Typer)
- Externalized configuration (YAML + Pydantic Settings)
- Comprehensive tests including Level 0 regression
- Project documentation

### Explicitly Excluded

The following capabilities belong to later maturity levels. Their exclusion
is intentional:

- BM25, hybrid search, reranking, query rewriting, query decomposition,
  multi-query retrieval, contextual compression
- document approval, version lifecycle, superseding, archiving, retention,
  expiration
- authentication, RBAC, ABAC, document ACLs, tenant isolation
- REST API, distributed deployment, Kubernetes, high availability,
  multi-region, disaster recovery
- CI/CD, production observability, distributed tracing, FinOps, incident
  management
- LangChain, LlamaIndex, LangGraph, agent frameworks, message queues,
  microservices

## Level 1 Technology Constitution

### Programming Language

Python 3.12+ SHALL remain the primary implementation language. The core RAG
logic SHALL continue to be implemented directly in Python.

### Dependency Management

**uv** SHALL be the single tool for all Python packaging, dependency
management, and environment management: creating/managing the virtual
environment, installing dependencies, locking dependencies (`uv.lock`), and
running scripts/entry points.

pip, pipenv, poetry, and conda SHALL NOT be used.

### Data Models

**Pydantic v2** SHALL be used for explicit domain models. At minimum:
Document, Chunk, RetrievalResult, RetrievalQuery.

### Embeddings

Level 1 SHALL use a real local embedding model via **sentence-transformers**.
Recommended model: **BAAI/bge-small-en-v1.5** (384 dimensions).

The embedding implementation SHALL be isolated behind an application
interface so that the embedding model can later be replaced.

### Vector Database

Level 1 SHALL replace the Level 0 fake vector database with **ChromaDB**,
providing: persistent vector storage, vector similarity search, metadata
storage, top-K retrieval, and similarity/distance information.

ChromaDB-specific code SHALL NOT be exposed outside a small
repository/interface layer.

### LLM

The generation model SHALL continue to use **OpenRouter**. The
OpenAI-compatible Python SDK MAY be used as the client.

The LLM provider SHALL remain separate from the embedding provider.

### CLI

**Typer** SHALL be used for the command-line interface. The CLI SHALL
support normal querying and retrieval diagnostics.

## Level 1 Structured Knowledge Objects

Documents and chunks SHALL be explicit application objects.

A document SHALL contain at minimum: document_id, title, source, content,
metadata.

A chunk SHALL contain at minimum: chunk_id, document_id, text, chunk_index,
metadata.

Retrieval results SHALL contain at minimum: chunk_id, document_id, text,
score, metadata.

Retrieval MUST NEVER return anonymous strings. The exact implementation MAY
evolve, but document and chunk identity MUST be preserved end to end.

## Level 1 Chunking Constitution

Chunking SHALL be treated as a retrieval design decision. The system SHALL
NOT permanently hard-code one chunk size.

At minimum, `chunk_size` and `chunk_overlap` SHALL be configurable.
Different configurations SHALL be experimentally evaluated.

The project SHALL document how chunk size affects: retrieval quality,
context size, semantic coherence, duplicate information, and retrieval
precision.

## Level 1 Retrieval Constitution

Retrieval configuration SHALL NOT be hard-coded. At minimum, `top_k` and
`similarity_threshold` SHALL be configurable.

The retriever SHALL return enough information to diagnose its behavior. A
retrieval result SHALL expose: document_id, chunk_id, score, text, metadata.

## Level 1 Retrieval Evaluation

Level 1 SHALL introduce a retrieval evaluation dataset of approximately
20–30 questions. Each question SHALL identify one or more expected/relevant
documents.

Example entry:

```json
{
  "question": "What can cause packet loss on a 5G network?",
  "relevant_documents": ["5g_packet_loss"]
}
```

The system SHALL calculate at least: Recall@K, Precision@K, MRR. These
metrics SHALL be implemented in Python, not hidden behind an evaluation
framework (see Principle XVI).

## Level 1 Reproducibility Addendum

A developer MUST be able to recreate the Level 1 environment from the
repository. The project SHALL provide: `pyproject.toml`, `.env.example`,
`README.md`. Dependencies SHALL be pinned/locked through uv.

## Level 1 Out of Scope

The following capabilities SHALL NOT be implemented at Level 1:

**Retrieval:** BM25, hybrid search, reranking, query rewriting, query
decomposition, multi-query retrieval, contextual compression.

**Knowledge lifecycle:** document approval, version lifecycle, superseding,
archiving, retention, expiration.

**Security:** authentication, RBAC, ABAC, document ACLs, tenant isolation.

**Platform:** REST API, distributed deployment, Kubernetes, high
availability, multi-region, disaster recovery.

**Operations:** CI/CD, production observability, distributed tracing,
FinOps, incident management.

These capabilities belong to later maturity levels.

## Level 1 Backward Compatibility

Level 1 MUST preserve the conceptual behavior of Level 0. The major change
is the replacement of simulated infrastructure with real infrastructure, not
a complete redesign of the application.

```text
Level 0: Question → Retrieve → Generate
Level 1: Question → Real embedding → Real vector retrieval → Generate
```

## Level 1 Enterprise Preparation

Level 1 SHALL make architectural decisions that allow later enterprise
capabilities without implementing them prematurely. The metadata model SHALL
be capable of eventually supporting:

```text
Document
 ├── ownership
 ├── classification
 ├── version
 ├── lifecycle status
 ├── effective dates
 └── access policy
```

This prepares the system for: Level 4 (Document Lifecycle), Level 5
(Knowledge Governance), Level 6 (RBAC), Level 7 (ABAC / Multi-tenancy).

## Level 1 Quality Gates

### Definition of Done

Level 1 is complete when:

- [ ] real documents can be loaded
- [ ] documents are represented by structured models
- [ ] documents are chunked using configurable parameters
- [ ] real embeddings are generated
- [ ] embeddings are stored in ChromaDB
- [ ] metadata is persisted through ingestion → retrieval
- [ ] queries generate real embeddings
- [ ] real vector similarity retrieval works
- [ ] top-K is configurable
- [ ] similarity threshold is configurable
- [ ] retrieval scores are inspectable
- [ ] retrieval can be run without generation (`--debug-retrieval`)
- [ ] retrieval evaluation data exists (20–30 questions)
- [ ] Recall@K is implemented
- [ ] Precision@K is implemented
- [ ] MRR is implemented
- [ ] retrieval tests exist
- [ ] Level 0 functionality still works (regression tests pass)
- [ ] retrieval failures have been documented

### Exit Criteria

Before moving to Level 2, the developer MUST be able to explain:

- what an embedding represents,
- how the embedding model transforms text into vectors,
- how vectors are stored,
- how similarity search works,
- what top-K means,
- what a similarity threshold means,
- why chunk size affects retrieval,
- why chunk overlap affects retrieval,
- what metadata is attached to a chunk,
- how to inspect retrieved chunks,
- how Recall@K is calculated,
- how Precision@K is calculated,
- how MRR is calculated,
- why a high retrieval score does not necessarily mean the answer is
  correct,
- where Level 1 retrieval still fails.

## Future Evolution

Each level MUST grow out of documented limitations of the previous one
rather than reimplementing the final architecture prematurely:

```text
Level 0   Naive RAG — Can RAG work?
Level 1   RAG Foundations — Can we retrieve the right knowledge?
Level 2   Grounded RAG — Is the answer supported by retrieved evidence?
Level 3   Advanced Retrieval
Level 4   Knowledge Lifecycle
Level 5   Knowledge Governance
Level 6   Authentication + RBAC
Level 7   ABAC + Multi-tenancy
Level 8   Evaluation
Level 9   Testing
Level 10  CI/CD + DevSecOps
...
Level 24  Enterprise RAG Platform
```

## Governance

- **Supremacy.** This constitution supersedes all other engineering
  practices for the active level. Where a plan, task, or code convention
  conflicts with a principle here, the principle wins.
- **Amendment procedure.** Amendments MUST be made by editing this file in a
  dedicated change that states the rationale, records the impact in the
  Sync Impact Report at the top of the file, and includes a migration plan
  when the amendment invalidates existing work or documents. Amendments
  require review and explicit approval before merge.
- **Versioning policy.** The constitution uses semantic versioning:
  MAJOR for backward-incompatible principle removals or redefinitions,
  MINOR for new principles or materially expanded guidance, PATCH for
  clarifications and wording fixes. The version line at the bottom of this
  file MUST match the version stated in the Sync Impact Report.
- **Compliance review.** Every pull request and design review MUST verify
  compliance with the Core Principles and the active level's Quality Gates.
  Deviations MUST be justified explicitly in the PR description; unjustified
  complexity or scope creep MUST be rejected. Complexity that cannot be
  tied to an active-level problem MUST be deferred per Principle I.
- **Level completion gate.** A maturity level MAY be declared complete only
  when all of its Definition of Done and Exit Criteria items are met.
- **Runtime guidance.** Day-to-day development guidance for the active level
  lives in `docs/levels/level-01-rag-foundations/plan.md`; it MUST remain
  consistent with this constitution and MUST NOT weaken any NON-NEGOTIABLE
  principle.

**Version**: 1.1.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-06
