# Telco Enterprise RAG

## Level 0 Constitution — Naive RAG

**Version:** 1.0
**Level:** 0 — Naive RAG
**Status:** Active

---

## 1. Purpose

This constitution defines the engineering principles and boundaries for Level 0 of the Telco Enterprise RAG project.

The objective of Level 0 is deliberately narrow:

> Build the simplest working Retrieval-Augmented Generation system for a Telco knowledge base.

The system must demonstrate the complete RAG lifecycle:

```text
Documents
    ↓
Load
    ↓
Chunk
    ↓
Embed
    ↓
Store
    ↓
Retrieve
    ↓
Build prompt
    ↓
LLM
    ↓
Answer
```

Level 0 is a learning and architectural baseline. It is **not a production-ready enterprise system**.

---

# 2. Scope

Level 0 includes only the capabilities required to demonstrate basic RAG.

### Included

* Python application
* Local Telco knowledge documents
* Document loading
* Basic text chunking
* Embedding generation
* Vector storage
* Similarity search
* Top-K retrieval
* Prompt construction
* LLM answer generation
* Basic CLI interface
* Basic configuration
* Basic error handling
* Basic tests
* Basic project documentation

### Explicitly excluded

The following capabilities belong to later maturity levels:

* RBAC
* ABAC
* authentication
* authorization
* multi-tenancy
* document ACLs
* document approval workflows
* document version lifecycle
* document expiration
* knowledge governance
* hybrid retrieval
* BM25
* reranking
* query rewriting
* advanced evaluation
* distributed tracing
* production observability
* CI/CD
* DevSecOps
* high availability
* disaster recovery
* autoscaling
* FinOps
* enterprise API gateway
* agentic workflows
* autonomous actions
* production compliance controls

These exclusions are intentional.

---

# 3. Core Principle — Learn From the Baseline

The Level 0 implementation must remain simple enough that the developer can understand every component.

We will not introduce an abstraction merely because it is common in enterprise RAG systems.

Every component should answer:

> What problem does this component solve?

If a component does not solve a Level 0 problem, it should be deferred.

---

# 4. Principle — Simple Before Sophisticated

Level 0 must prefer:

```text
simple implementation
        over
framework complexity
```

The implementation should avoid unnecessary:

* agent frameworks
* orchestration frameworks
* microservices
* distributed systems
* message queues
* Kubernetes
* complex databases
* unnecessary abstractions

The goal is to understand RAG fundamentals before introducing enterprise infrastructure.

---

# 5. Principle — Telco Domain From Day One

Although the implementation is naive, the knowledge domain must be realistic enough to expose RAG-specific problems.

The initial knowledge base should contain Telco-oriented documents such as:

```text
5G troubleshooting
LTE troubleshooting
Network incidents
NOC procedures
SIM activation
Broadband troubleshooting
Enterprise SLA
Network operations
```

Documents should be synthetic and safe for learning.

No real customer data or confidential telecom information should be used.

---

# 6. Principle — Reproducibility

A developer should be able to clone the repository and reproduce the Level 0 system with documented steps.

The project must define:

* Python version
* dependency management
* environment configuration
* required environment variables
* installation instructions
* execution instructions
* test instructions

The same input documents and configuration should produce reproducible retrieval behavior within reasonable embedding/model variability.

---

# 7. Principle — Explicit RAG Pipeline

The implementation must make the RAG stages visible.

The code should conceptually expose:

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

These responsibilities should not be hidden inside one opaque function.

The purpose is educational as well as architectural.

---

# 8. Principle — Retrieval Before Generation

The LLM must not be treated as the knowledge source.

The application must:

1. receive a question
2. retrieve relevant context
3. construct a prompt containing the retrieved context
4. ask the LLM to answer using that context

Conceptually:

```text
Question
   ↓
Retriever
   ↓
Context
   ↓
Prompt
   ↓
LLM
   ↓
Answer
```

---

# 9. Principle — No Knowledge Outside the Corpus

The Level 0 RAG prompt should instruct the model to answer using the supplied retrieved context.

When the retrieved context does not contain enough information, the system should prefer an explicit inability to answer rather than inventing unsupported facts.

For example:

```text
I don't have enough information in the knowledge base
to answer this question.
```

This is a baseline behavior that will later evolve into more sophisticated grounding and evaluation mechanisms.

---

# 10. Principle — Make Retrieval Inspectable

The developer must be able to inspect what was retrieved.

A query should expose at minimum:

```text
Question
Retrieved chunks
Similarity scores
Final answer
```

This is important because Level 0 is intended to teach the fundamental RAG debugging question:

> Did the system retrieve the right information before asking whether the LLM generated the right answer?

---

# 11. Principle — Minimal Metadata

Each document/chunk should have enough metadata to identify its origin.

At minimum:

```text
document_id
document_name
chunk_id
source
```

This metadata is not yet an authorization mechanism.

It exists primarily for traceability and debugging.

---

# 12. Principle — Configuration Over Hardcoding

Model names, API endpoints, embedding configuration, retrieval parameters and other environment-specific settings should not be scattered throughout the source code.

Configuration should be centralized.

Secrets must never be committed to Git.

Example:

```text
.env
```

must be excluded from source control.

A safe template should be provided:

```text
.env.example
```

---

# 13. Principle — Tests From the Beginning

Even though this is a learning baseline, code must be testable.

At minimum, tests should cover:

* document loading
* chunking
* retrieval
* prompt construction
* basic end-to-end RAG behavior

Tests should distinguish deterministic application logic from external LLM behavior.

---

# 14. Principle — CLI First

Level 0 should expose a simple command-line interface.

Example:

```bash
python -m app "How do I troubleshoot 5G packet loss?"
```

The CLI should make experimentation fast.

A web UI is not required at this level.

---

# 15. Principle — No Premature Enterprise Architecture

Level 0 must not pretend to be production-ready.

The architecture should explicitly document known limitations.

Examples:

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

These limitations are not failures.

They are the starting point for the next levels.

---

# 16. Principle — Every Level Must Expose the Next Problem

The project is designed as a maturity progression.

At the end of Level 0, we should be able to identify problems such as:

* poor chunking
* irrelevant retrieval
* lack of metadata
* weak source traceability
* inability to measure retrieval quality
* inability to manage document versions
* inability to enforce access control

These problems become the motivation for subsequent levels.

---

# 17. Level 0 Success Criteria

Level 0 is complete when:

### Functional

* Documents can be loaded.
* Documents can be chunked.
* Chunks can be embedded.
* Embeddings can be stored.
* A question can retrieve relevant chunks.
* The LLM can generate an answer from retrieved context.
* The application can be executed from the CLI.

### Technical

* Configuration is externalized.
* Secrets are not committed.
* Basic tests exist.
* The project can be reproduced locally.
* Retrieval results can be inspected.

### Educational

The developer can explain:

1. What embeddings are.
2. What a vector store does.
3. What chunking does.
4. What similarity search does.
5. Why retrieval quality affects generation quality.
6. Why RAG is different from simply asking an LLM a question.

---

# 18. Definition of Done

Level 0 is considered complete when the following flow works:

```text
Telco documents
      ↓
Load
      ↓
Chunk
      ↓
Embed
      ↓
Vector store
      ↓
User question
      ↓
Similarity retrieval
      ↓
Retrieved context
      ↓
LLM
      ↓
Grounded answer
```

The implementation must be understandable, executable, testable and documented.

---

# 19. Future Evolution

Level 0 establishes the baseline for the subsequent maturity levels.

The expected evolution is:

```text
Level 0
Naive RAG
   ↓
Level 1
RAG Foundations
   ↓
Level 2
Grounded RAG
   ↓
Level 3
Advanced Retrieval
   ↓
Level 4
Knowledge Lifecycle
   ↓
Level 5
Knowledge Governance
   ↓
Level 6
Authentication + RBAC
   ↓
Level 7
ABAC + Multi-tenancy
   ↓
Level 8
Evaluation
   ↓
Level 9
Testing
   ↓
Level 10
CI/CD + DevSecOps
   ↓
...
   ↓
Level 24
Enterprise RAG Platform
```

The architecture should evolve incrementally rather than implementing the final architecture prematurely.

---

# 20. Constitution Principle

The central principle of Level 0 is:

> **Build the smallest understandable RAG system that works, measure its limitations, and use those limitations to justify every subsequent enterprise capability.**