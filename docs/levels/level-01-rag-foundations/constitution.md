# Telco Enterprise RAG

## Level 1 Constitution — RAG Foundations

**Version:** 1.0
**Level:** 1
**Status:** Active
**Previous Level:** Level 0 — Naive RAG
**Next Level:** Level 2 — Grounded RAG

---

## 1. Purpose

Level 1 transforms the Level 0 prototype from a purely simulated RAG system into a real, measurable, inspectable retrieval system.

Level 0 demonstrated the basic RAG pipeline using Python implementations and a fake vector database.

Level 1 introduces:

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

The goal is not to build an enterprise-scale platform yet.

The goal is to understand exactly how a real retrieval system works.

---

## 2. Core Principle

Every retrieval decision must be observable, explainable, configurable, and measurable.

At the end of Level 1, we should be able to answer:

- What document was indexed?
- How was it chunked?
- What embedding model created the vector?
- What metadata belongs to the chunk?
- What query embedding was generated?
- Which chunks were retrieved?
- What similarity score did each chunk receive?
- Why were those chunks selected?
- Was the expected document retrieved?
- How does retrieval quality change when configuration changes?

---

## 3. Level 1 Architecture

The system shall follow this conceptual pipeline:

```
Documents
    ↓
Document Loader
    ↓
Document Model
    ↓
Chunker
    ↓
Chunk Model
    ↓
Embedding Model
    ↓
Vector Store
    ↓
Retriever
    ↓
Retrieval Results
    ↓
Prompt Builder
    ↓
LLM
    ↓
Answer
```

Evaluation is a separate path:

```
Evaluation Dataset
       ↓
     Query
       ↓
   Retriever
       ↓
Retrieved Documents
       ↓
Expected Documents
       ↓
Retrieval Metrics
```

---

## 4. Technology Constitution

Level 1 shall use the following technologies.

### 4.1 Programming Language

Python shall remain the primary implementation language.

The core RAG logic shall continue to be implemented directly in Python.

### 4.2 Dependency Management

Use:

- **uv**

for Python dependency management and environment management.

### 4.3 Data Models

Use:

- **Pydantic v2**

for explicit domain models.

At minimum:

- Document
- Chunk
- RetrievalResult
- RetrievalQuery

### 4.4 Embeddings

Level 1 shall use a real local embedding model.

Recommended model:

- **BAAI/bge-small-en-v1.5**

using:

- **sentence-transformers**

The embedding implementation shall be isolated behind an application interface so that the embedding model can later be replaced.

### 4.5 Vector Database

Level 1 shall replace the Level 0 fake vector database with:

- **ChromaDB**

ChromaDB shall provide:

- persistent vector storage
- vector similarity search
- metadata storage
- top-K retrieval
- similarity/distance information

The application shall not expose ChromaDB throughout the entire codebase.

Vector database access shall remain behind a small repository/interface layer.

### 4.6 LLM

The generation model shall continue to use:

- **OpenRouter**

The OpenAI-compatible Python SDK may be used as the client.

The LLM provider shall remain separate from the embedding provider.

### 4.7 CLI

Use:

- **Typer**

for the command-line interface.

The CLI shall support normal querying and retrieval diagnostics.

Example:

```bash
python -m telco_rag.cli "Why is my 5G connection experiencing packet loss?"
```

Debug retrieval:

```bash
python -m telco_rag.cli \
    "Why is my 5G connection experiencing packet loss?" \
    --debug-retrieval
```

---

## 5. Structured Knowledge Objects

Documents and chunks shall be explicit application objects.

A document should conceptually contain:

- document_id
- title
- source
- content
- metadata

A chunk should contain:

- chunk_id
- document_id
- text
- chunk_index
- metadata

Retrieval results should contain:

- chunk_id
- document_id
- text
- score
- metadata

The exact implementation may evolve, but retrieval must never return anonymous strings.

---

## 6. Metadata Principle

Metadata shall survive the complete ingestion → retrieval pipeline.

At minimum:

- document_id
- title
- source
- chunk_id
- chunk_index

The design shall leave room for future enterprise metadata such as:

- tenant_id
- owner
- department
- classification
- version
- status
- effective_from
- effective_until
- access_policy

These fields do not need to be implemented as access-control mechanisms in Level 1.

They are identified now because metadata architecture becomes increasingly important at later enterprise levels.

---

## 7. Chunking Constitution

Chunking shall be treated as a retrieval design decision.

The system shall not permanently hard-code one chunk size.

At minimum, the following shall be configurable:

- chunk_size
- chunk_overlap

Different configurations shall be experimentally evaluated.

The project shall document how chunk size affects:

- retrieval quality
- context size
- semantic coherence
- duplicate information
- retrieval precision

---

## 8. Retrieval Constitution

Retrieval configuration shall not be hard-coded.

At minimum:

- top_k
- similarity_threshold

shall be configurable.

The retriever shall return enough information to diagnose its behavior.

A retrieval result shall expose:

- document_id
- chunk_id
- score
- text
- metadata

---

## 9. Retrieval Diagnostics

The system shall provide a way to inspect retrieval independently from answer generation.

Example:

```
Query:
Why is 5G packet loss occurring?

Retrieved:

1. document=5g_packet_loss
   chunk=5g_packet_loss-03
   score=0.87

2. document=network_troubleshooting
   chunk=network_troubleshooting-07
   score=0.79

3. document=5g_latency
   chunk=5g_latency-02
   score=0.72
```

This capability is mandatory.

The project must not require the user to inspect the final LLM answer to understand retrieval behavior.

---

## 10. Retrieval Evaluation

Level 1 shall introduce a small retrieval evaluation dataset.

The dataset shall contain approximately:

- 20–30 questions

Each question should identify one or more expected/relevant documents.

Example:

```json
{
  "question": "What can cause packet loss on a 5G network?",
  "relevant_documents": [
    "5g_packet_loss"
  ]
}
```

The system shall calculate at least:

- Recall@K
- Precision@K
- MRR

The implementation of these metrics should initially be written in Python rather than hidden behind an evaluation framework.

---

## 11. Testing Constitution

Testing begins in Level 1.

Tests shall cover:

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

The Level 0 tests must continue to pass unless a deliberate behavioral change is documented.

---

## 12. Configuration Constitution

Configuration shall be externalized.

At minimum:

- embedding model
- chunk size
- chunk overlap
- top K
- similarity threshold
- vector database path
- LLM configuration

Configuration must not be scattered throughout application code.

---

## 13. Reproducibility

A developer must be able to recreate the Level 1 environment from the repository.

The project shall provide:

- pyproject.toml
- .env.example
- README.md

Dependencies shall be pinned/locked through the selected Python dependency-management workflow.

---

## 14. Simplicity Principle

Level 1 shall intentionally avoid unnecessary frameworks.

The project shall not introduce:

- LangChain
- LlamaIndex
- LangGraph
- agent frameworks
- Kubernetes
- distributed vector databases
- message queues
- microservices

The purpose is to understand the underlying RAG mechanics before introducing abstractions.

---

## 15. Explicitly Out of Scope

Level 1 shall not implement:

**Retrieval**
- BM25
- hybrid search
- reranking
- query rewriting
- query decomposition
- multi-query retrieval
- contextual compression

**Knowledge lifecycle**
- document approval
- version lifecycle
- superseding
- archiving
- retention
- expiration

**Security**
- authentication
- RBAC
- ABAC
- document ACLs
- tenant isolation

**Platform**
- REST API
- distributed deployment
- Kubernetes
- high availability
- multi-region
- disaster recovery

**Operations**
- CI/CD
- production observability
- distributed tracing
- FinOps
- incident management

These capabilities belong to later maturity levels.

---

## 16. Backward Compatibility

Level 1 must preserve the conceptual behavior of Level 0.

Level 0:

```
Question
    ↓
Retrieve
    ↓
Generate
```

Level 1:

```
Question
    ↓
Real embedding
    ↓
Real vector retrieval
    ↓
Generate
```

The major change is the replacement of simulated infrastructure with real infrastructure, not a complete redesign of the application.

---

## 17. Enterprise Preparation

Level 1 shall make architectural decisions that allow later enterprise capabilities without implementing them prematurely.

The metadata model shall be capable of eventually supporting:

```
Document
 ├── ownership
 ├── classification
 ├── version
 ├── lifecycle status
 ├── effective dates
 └── access policy
```

This prepares the system for later:

- Level 4 → Document Lifecycle
- Level 5 → Knowledge Governance
- Level 6 → RBAC
- Level 7 → ABAC / Multi-tenancy

---

## 18. Definition of Done

Level 1 is complete when:

- [ ] real documents can be loaded
- [ ] documents are represented by structured models
- [ ] documents are chunked using configurable parameters
- [ ] real embeddings are generated
- [ ] embeddings are stored in ChromaDB
- [ ] metadata is persisted
- [ ] queries generate real embeddings
- [ ] real vector similarity retrieval works
- [ ] top-K is configurable
- [ ] similarity threshold is configurable
- [ ] retrieval scores are inspectable
- [ ] retrieval can be run without generation
- [ ] retrieval evaluation data exists
- [ ] Recall@K is implemented
- [ ] Precision@K is implemented
- [ ] MRR is implemented
- [ ] retrieval tests exist
- [ ] Level 0 functionality still works
- [ ] retrieval failures have been documented

---

## 19. Exit Criteria

Before moving to Level 2, the developer must be able to explain:

- What an embedding represents.
- How the embedding model transforms text into vectors.
- How vectors are stored.
- How similarity search works.
- What top-K means.
- What a similarity threshold means.
- Why chunk size affects retrieval.
- Why chunk overlap affects retrieval.
- What metadata is attached to a chunk.
- How to inspect retrieved chunks.
- How Recall@K is calculated.
- How Precision@K is calculated.
- How MRR is calculated.
- Why a high retrieval score does not necessarily mean the answer is correct.
- Where Level 1 retrieval still fails.

---

## 20. Level 1 Guiding Principle

**Replace simulation with reality, but do not replace understanding with frameworks.**

Level 1 exists to make retrieval real, measurable, and inspectable while keeping the implementation simple enough that every major operation can still be understood.
