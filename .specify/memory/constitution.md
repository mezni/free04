<!--
Sync Impact Report
==================
Template source: constitution-template (resolved via resolve-template.sh)
Version change: (unpopulated template placeholders) -> 1.0.0
Bump type: MAJOR (initial ratification of the project constitution)

Modified principles:
  - none. The template shipped only placeholder slots
    ([PRINCIPLE_1..5_NAME] / [PRINCIPLE_1..5_DESCRIPTION]); no prior ratified
    principles existed to rename or redefine.

Added sections:
  - Core Principles (XIV principles, sourced from
    docs/levels/level-00-naive-rag/constitution.md sections 3-16)
  - Purpose and Scope (source sections 1-2; central principle quote from
    source section 20 folded in here)
  - Level 0 Quality Gates (source sections 17-18: Success Criteria +
    Definition of Done)
  - Future Evolution (source section 19)
  - Governance (new; the source Level 0 document had no governance section)

Removed sections:
  - [SECTION_2_NAME] placeholder block and example comment
  - [SECTION_3_NAME] placeholder block and example comment
  - [GOVERNANCE_RULES] placeholder block and example comment
  - Remaining template example comments

Placeholders left undefined: none.
Follow-up TODOs: none.

Date notes:
  - RATIFICATION_DATE set to 2026-10-06: this is the first population of
    .specify/memory/constitution.md. The source Level 0 constitution declared
    "Version: 1.0, Status: Active" but recorded no adoption date, and
    docs/levels/ is untracked so no git adoption date exists.
  - LAST_AMENDED_DATE set to 2026-10-06 (initial content adoption).
-->

# Telco Enterprise RAG Constitution

**Level:** 0 — Naive RAG | **Status:** Active

## Core Principles

### I. Learn From the Baseline (NON-NEGOTIABLE)

The Level 0 implementation MUST remain simple enough that the developer can
understand every component. No abstraction MAY be introduced merely because it
is common in enterprise RAG systems. Every component MUST answer the question
"What Level 0 problem does this component solve?"; any component that cannot
answer it MUST be deferred to a later level.

Rationale: Level 0 is a learning baseline; opaque abstractions defeat its
purpose.

### II. Simple Before Sophisticated (NON-NEGOTIABLE)

Level 0 MUST prefer a simple implementation over framework complexity. The
implementation MUST NOT introduce agent frameworks, orchestration frameworks,
microservices, distributed systems, message queues, Kubernetes, or complex
databases unless no Level 0 requirement can be met without them.

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

A developer MUST be able to clone the repository and reproduce the Level 0
system using documented steps alone. The project MUST define: Python version,
dependency management, environment configuration, required environment
variables, installation instructions, execution instructions, and test
instructions.

Given the same input documents and configuration, retrieval behavior MUST be
reproducible within reasonable embedding/model variability.

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

The Level 0 prompt MUST instruct the model to answer using only the supplied
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

Rationale: Level 0 exists to teach the fundamental RAG debugging question —
did the system retrieve the right information before asking whether the LLM
generated the right answer? An opaque answer is a failed debug session.

### IX. Minimal Metadata

Every document and chunk MUST carry metadata identifying its origin. At
minimum:

```text
document_id
document_name
chunk_id
source
```

This metadata exists for traceability and debugging only. It MUST NOT be
treated as an authorization mechanism in Level 0.

### X. Configuration Over Hardcoding

Model names, API endpoints, embedding configuration, retrieval parameters,
and other environment-specific settings MUST be centralized in configuration
and MUST NOT be scattered through the source code.

Secrets MUST NEVER be committed to Git. The `.env` file MUST be excluded
from source control, and a `.env.example` template listing all required
variables (without values) MUST be provided.

### XI. Tests From the Beginning

Code MUST be testable from the first commit. Tests MUST cover, at minimum:

- document loading
- chunking
- retrieval
- prompt construction
- basic end-to-end RAG behavior

Tests MUST distinguish deterministic application logic from external LLM
behavior; assertions against live LLM output MUST be isolated from
deterministic unit tests.

### XII. CLI First

Level 0 MUST expose a simple command-line interface, for example:

```bash
python -m app "How do I troubleshoot 5G packet loss?"
```

The CLI MUST make experimentation fast. A web UI MUST NOT be built at this
level.

### XIII. No Premature Enterprise Architecture

Level 0 MUST NOT claim or simulate production readiness. The architecture
documentation MUST explicitly list known limitations, including at minimum:

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

The project is a maturity progression. Completing Level 0 MUST leave its
known problems documented — at minimum: poor chunking, irrelevant retrieval,
lack of metadata, weak source traceability, inability to measure retrieval
quality, inability to manage document versions, and inability to enforce
access control.

Each level MUST end by identifying the problems it cannot solve; those
problems become the justification for the subsequent level.

## Purpose and Scope

This constitution defines the engineering principles and boundaries for
Level 0 of the Telco Enterprise RAG project. The objective of Level 0 is
deliberately narrow:

> Build the smallest understandable RAG system that works, measure its
> limitations, and use those limitations to justify every subsequent
> enterprise capability.

The system must demonstrate the complete RAG lifecycle:

```text
Documents → Load → Chunk → Embed → Store → Retrieve
          → Build prompt → LLM → Answer
```

Level 0 is a learning and architectural baseline. It is **not a
production-ready enterprise system**.

### Included

Level 0 includes only the capabilities required to demonstrate basic RAG:

- Python application
- Local Telco knowledge documents
- Document loading
- Basic text chunking
- Embedding generation
- Vector storage
- Similarity search
- Top-K retrieval
- Prompt construction
- LLM answer generation
- Basic CLI interface
- Basic configuration
- Basic error handling
- Basic tests
- Basic project documentation

### Explicitly Excluded

The following capabilities belong to later maturity levels. Their exclusion
is intentional:

- RBAC, ABAC, authentication, authorization, multi-tenancy
- document ACLs, approval workflows, version lifecycle, expiration
- knowledge governance
- hybrid retrieval, BM25, reranking, query rewriting
- advanced evaluation
- distributed tracing, production observability
- CI/CD, DevSecOps
- high availability, disaster recovery, autoscaling, FinOps
- enterprise API gateway
- agentic workflows, autonomous actions
- production compliance controls

## Level 0 Quality Gates

### Success Criteria

**Functional** — Level 0 is complete when:

- documents can be loaded, chunked, embedded, and stored,
- a question can retrieve relevant chunks,
- the LLM can generate an answer from retrieved context,
- the application can be executed from the CLI.

**Technical** — additionally:

- configuration is externalized,
- secrets are not committed,
- basic tests exist,
- the project can be reproduced locally,
- retrieval results can be inspected.

**Educational** — additionally, the developer can explain:

1. what embeddings are,
2. what a vector store does,
3. what chunking does,
4. what similarity search does,
5. why retrieval quality affects generation quality,
6. why RAG is different from simply asking an LLM a question.

### Definition of Done

Level 0 is considered complete when the following flow works end to end:

```text
Telco documents → Load → Chunk → Embed → Vector store
User question → Similarity retrieval → Retrieved context
→ LLM → Grounded answer
```

The implementation MUST be understandable, executable, testable, and
documented. A level is not "done" until every Success Criterion above is
demonstrably met.

## Future Evolution

Level 0 establishes the baseline for the subsequent maturity levels. The
expected evolution is incremental — each level MUST grow out of documented
limitations of the previous one rather than reimplementing the final
architecture prematurely:

```text
Level 0   Naive RAG
   ↓
Level 1   RAG Foundations
   ↓
Level 2   Grounded RAG
   ↓
Level 3   Advanced Retrieval
   ↓
Level 4   Knowledge Lifecycle
   ↓
Level 5   Knowledge Governance
   ↓
Level 6   Authentication + RBAC
   ↓
Level 7   ABAC + Multi-tenancy
   ↓
Level 8   Evaluation
   ↓
Level 9   Testing
   ↓
Level 10  CI/CD + DevSecOps
   ↓
  ...
   ↓
Level 24  Enterprise RAG Platform
```

## Governance

- **Supremacy.** This constitution supersedes all other engineering
  practices for Level 0 work. Where a plan, task, or code convention
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
  compliance with the Core Principles and the Level 0 Quality Gates.
  Deviations MUST be justified explicitly in the PR description; unjustified
  complexity or scope creep MUST be rejected. Complexity that cannot be
  tied to a Level 0 problem MUST be deferred per Principle I.
- **Level completion gate.** A maturity level MAY be declared complete only
  when all of its Success Criteria and Definition of Done items are met.
- **Runtime guidance.** Day-to-day development guidance for Level 0 lives in
  `docs/levels/level-00-naive-rag/plan.md`; it MUST remain consistent with
  this constitution and MUST NOT weaken any NON-NEGOTIABLE principle.

**Version**: 1.0.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-06

