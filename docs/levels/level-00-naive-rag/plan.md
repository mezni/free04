# Telco Enterprise RAG

## Level 0 Implementation Plan — Naive RAG

**Version:** 1.0
**Level:** 0 — Naive RAG
**Status:** Planned

---

# 1. Objective

Build the first working version of the Telco RAG system.

The system will answer questions against a small local Telco knowledge base using:

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Vector Store
    ↓
Similarity Retrieval
    ↓
Prompt
    ↓
LLM
    ↓
Answer
```

The implementation is intentionally naive.

The objective is to establish a baseline that future levels can improve.

---

# 2. Level 0 Scope

## In Scope

* Python project
* Local Markdown documents
* Document loader
* Basic chunker
* Embedding generation
* Local vector store
* Similarity search
* Top-K retrieval
* Prompt construction
* LLM generation
* CLI
* Configuration
* Basic tests
* Basic documentation

## Out of Scope

* RBAC
* authentication
* authorization
* multi-tenancy
* document ACL
* document lifecycle
* document approval
* hybrid retrieval
* BM25
* reranking
* advanced evaluation
* distributed tracing
* production monitoring
* CI/CD
* Kubernetes
* HA
* disaster recovery
* FinOps
* agentic workflows

---

# 3. Target Architecture

```text
                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │      CLI      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Question   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Retriever   │
                    └───────┬───────┘
                            │
                     Top-K chunks
                            │
                            ▼
                    ┌───────────────┐
                    │ Prompt Builder│
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │      LLM      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Answer     │
                    └───────────────┘


Ingestion:

Documents
    │
    ▼
Document Loader
    │
    ▼
Chunker
    │
    ▼
Embedder
    │
    ▼
Vector Store
```

---

# 4. Initial Telco Knowledge Base

Create a small synthetic corpus.

```text
data/
└── documents/
    ├── 5g_packet_loss.md
    ├── 5g_latency.md
    ├── lte_troubleshooting.md
    ├── broadband_connectivity.md
    ├── sim_activation.md
    ├── enterprise_sla.md
    ├── noc_incident_procedure.md
    └── network_escalation.md
```

Each document should contain realistic but fictional technical information.

No real customer information should be used.

---

# 5. Suggested Project Structure

```text
telco-rag/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile
│
├── data/
│   └── documents/
│       ├── 5g_packet_loss.md
│       ├── 5g_latency.md
│       ├── lte_troubleshooting.md
│       ├── broadband_connectivity.md
│       ├── sim_activation.md
│       ├── enterprise_sla.md
│       ├── noc_incident_procedure.md
│       └── network_escalation.md
│
├── src/
│   └── telco_rag/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── chunker.py
│       │
│       ├── embeddings/
│       │   ├── __init__.py
│       │   └── embedder.py
│       │
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── vector_store.py
│       │   └── retriever.py
│       │
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── prompt.py
│       │   └── llm.py
│       │
│       └── rag/
│           ├── __init__.py
│           └── pipeline.py
│
├── tests/
│   ├── test_loader.py
│   ├── test_chunker.py
│   ├── test_retriever.py
│   ├── test_prompt.py
│   └── test_rag_pipeline.py
│
└── docs/
    └── level-0/
        ├── constitution.md
        ├── plan.md
        └── baseline.md
```

---

# 6. Step 1 — Initialize the Python Project

Create:

```text
pyproject.toml
```

Define:

* Python version
* dependencies
* project metadata
* development dependencies
* test configuration

The project should support a reproducible local setup.

---

# 7. Step 2 — Configuration

Create:

```text
src/telco_rag/config.py
```

Configuration should contain:

```text
LLM configuration
Embedding configuration
Vector store configuration
Chunk size
Chunk overlap
Top K
Document directory
```

Secrets must come from environment variables.

Provide:

```text
.env.example
```

but never commit `.env`.

---

# 8. Step 3 — Create Telco Documents

Create the initial synthetic corpus.

Each document should contain:

* title
* technical content
* sections
* realistic terminology
* enough content to create multiple chunks

Example topics:

```text
5G packet loss
5G latency
LTE troubleshooting
Broadband outage
SIM activation
Enterprise SLA
NOC incident handling
Network escalation
```

---

# 9. Step 4 — Document Loader

Implement:

```text
ingestion/loader.py
```

Responsibilities:

1. discover Markdown files
2. read their contents
3. assign document identifiers
4. preserve document name/source
5. return normalized document objects

Example conceptual object:

```text
Document
├── document_id
├── source
└── content
```

---

# 10. Step 5 — Chunking

Implement:

```text
ingestion/chunker.py
```

Start with simple fixed-size chunking.

Parameters:

```text
chunk_size
chunk_overlap
```

Each chunk should retain:

```text
document_id
source
chunk_id
content
```

Do not implement sophisticated semantic chunking yet.

That is deliberately deferred to later levels.

---

# 11. Step 6 — Embeddings

Implement:

```text
embeddings/embedder.py
```

Responsibilities:

1. receive chunks
2. generate embeddings
3. return vectors

The embedding provider should be configurable.

The implementation should avoid hardcoding a provider into the RAG pipeline.

---

# 12. Step 7 — Vector Store

Implement:

```text
retrieval/vector_store.py
```

The vector store must support:

```text
add(chunks)
search(query_embedding, top_k)
```

Initially use a simple local vector database/store.

The goal is to understand:

```text
embedding
+
vector similarity
+
top-k retrieval
```

rather than infrastructure.

---

# 13. Step 8 — Retriever

Implement:

```text
retrieval/retriever.py
```

Responsibilities:

```text
Question
   ↓
Query embedding
   ↓
Vector search
   ↓
Top K chunks
```

Return:

```text
chunk
document_id
source
score
```

The retrieval results must be inspectable.

---

# 14. Step 9 — Prompt Builder

Implement:

```text
generation/prompt.py
```

The prompt should contain:

```text
System instructions
+
Retrieved context
+
User question
```

The system instruction should tell the LLM:

* use the supplied context
* do not invent facts
* state when the context is insufficient
* answer clearly

---

# 15. Step 10 — LLM Client

Implement:

```text
generation/llm.py
```

Responsibilities:

```text
prompt
  ↓
LLM provider
  ↓
response
```

The provider/model should be configurable.

The RAG pipeline should not depend directly on a specific vendor.

---

# 16. Step 11 — RAG Pipeline

Implement:

```text
rag/pipeline.py
```

The pipeline should coordinate:

```text
question
   ↓
retriever
   ↓
context
   ↓
prompt builder
   ↓
LLM
   ↓
answer
```

It should return enough information to debug the request:

```text
answer
retrieved_chunks
scores
```

---

# 17. Step 12 — CLI

Implement:

```text
cli.py
```

Example:

```bash
python -m telco_rag.cli \
  "How do I troubleshoot 5G packet loss?"
```

Expected output:

```text
Question:
How do I troubleshoot 5G packet loss?

Retrieved Documents:
- 5g_packet_loss.md
- noc_incident_procedure.md

Answer:
...
```

The CLI should make experiments easy.

---

# 18. Step 13 — Tests

Create tests for deterministic components.

### Loader

Verify:

```text
documents discovered
content loaded
IDs assigned
```

### Chunker

Verify:

```text
chunks generated
chunk sizes respected
metadata preserved
```

### Retriever

Verify:

```text
query returns results
top-k is respected
metadata is preserved
```

### Prompt

Verify:

```text
question included
context included
instructions included
```

### Pipeline

Use mocked embedding/LLM components where possible.

Verify:

```text
question
→ retrieval
→ prompt
→ generation
```

---

# 19. Step 14 — Baseline Experiments

Create:

```text
docs/level-0/baseline.md
```

Run a small question set.

Example:

```text
Q1:
How do I troubleshoot 5G packet loss?

Q2:
What are the common causes of high latency?

Q3:
How do I activate a SIM?

Q4:
What is the enterprise SLA for broadband?

Q5:
How do I escalate a network incident?

Q6:
What is the procedure for something that does not exist
in the knowledge base?
```

Record:

```text
question
retrieved documents
retrieval scores
answer
observations
```

---

# 20. Step 15 — Deliberately Test Failure

Level 0 must not only demonstrate successful queries.

Test questions where:

* the answer does not exist
* terminology is ambiguous
* the query uses synonyms
* the query contains irrelevant information
* multiple documents appear relevant

Example:

```text
"What is the procedure for satellite network
handover?"
```

when no satellite document exists.

Observe whether the system invents an answer.

---

# 21. Step 16 — Document Known Limitations

At the end of Level 0, document the problems discovered.

Expected limitations include:

```text
1. Fixed-size chunking may split important context.

2. Vector similarity may retrieve irrelevant documents.

3. Exact technical terms may not retrieve correctly.

4. There is no reranking.

5. There is no metadata filtering.

6. There is no document versioning.

7. There is no document approval workflow.

8. There is no access control.

9. There is no evaluation framework.

10. There is no production observability.

11. There is no CI/CD.

12. There is no reliability architecture.

13. There is no tenant isolation.
```

These limitations become the input to Level 1 and subsequent levels.

---

# 22. Level 0 Deliverables

At completion, the repository should contain:

```text
Application
├── working ingestion
├── working chunking
├── working embeddings
├── working vector store
├── working retrieval
├── working LLM generation
└── working CLI

Tests
├── unit tests
└── basic integration test

Knowledge
└── synthetic Telco corpus

Documentation
├── constitution.md
├── plan.md
└── baseline.md
```

---

# 23. Definition of Done

Level 0 is complete when this works:

```bash
python -m telco_rag.cli \
  "How do I troubleshoot 5G packet loss?"
```

and the system successfully:

```text
1. Loads the question
2. Generates a query embedding
3. Searches the vector store
4. Retrieves relevant chunks
5. Displays/records retrieved sources
6. Builds a context-aware prompt
7. Calls the LLM
8. Produces an answer
9. Handles an unknown question without silently fabricating knowledge
```

Tests must pass.

The system must be reproducible from the repository documentation.

---

# 24. Exit Criteria

Before moving to Level 1, answer these questions:

### RAG fundamentals

* What is an embedding?
* Why do we chunk documents?
* What is cosine similarity?
* What does top-K mean?
* What is the difference between retrieval and generation?

### Retrieval

* Which documents are retrieved for each test question?
* Are the relevant documents consistently in the top K?
* What happens when the answer does not exist?

### Generation

* Does the LLM stay within retrieved context?
* When does it hallucinate?
* What happens when context is insufficient?

### Engineering

* Can the application be reproduced?
* Can components be tested independently?
* Can we inspect the retrieved context?

### Enterprise readiness

Finally:

> **What is missing from this naive implementation that a real Telco enterprise would require?**

The answer to that question drives Level 1 and the subsequent maturity roadmap.

---

# 25. Next Level

Level 1 will address the weaknesses discovered here:

```text
Naive RAG
    ↓
Better RAG foundations
    ↓
Metadata
    ↓
Retrieval diagnostics
    ↓
Configuration
    ↓
Improved chunking
```

We will continue to add enterprise capabilities incrementally rather than introducing the complete enterprise architecture at Level 0.