# Telco RAG — Implementation Plan

## 1. Purpose

This document defines the implementation sequence for the `telco-rag` platform.

The project will be built incrementally from a framework-light RAG core toward a production-oriented enterprise RAG and eventually agentic RAG platform.

The implementation order is intentional.

We will first make the fundamentals reliable:

```text
Domain
→ Data
→ Database
→ Ingestion
→ Embeddings
→ Retrieval
→ Generation
→ Grounding
→ Evaluation
→ API
→ Security
→ Observability
→ Framework Integration
→ Agents
→ Memory
→ Production
```

We will not begin with LangChain or LangGraph.

---

# 2. Implementation Principles

The implementation must follow these principles:

1. Build one working vertical slice at a time.
2. Keep the domain independent of infrastructure.
3. Use Pydantic for application boundaries and structured data.
4. Use SQLAlchemy for persistence.
5. Use Alembic for migrations.
6. Use PostgreSQL and pgvector for persistence and vector search.
7. Use OpenRouter behind a provider abstraction.
8. Start with custom Python RAG mechanics.
9. Add frameworks only after understanding the underlying mechanics.
10. Write tests alongside implementation.
11. Create evaluation data before optimizing retrieval.
12. Enforce authorization before generation.
13. Never allow unauthorized content into the LLM context.
14. Make observability part of implementation rather than a final addition.
15. Introduce agentic behavior only after baseline RAG is reliable.

---

# 3. Implementation Stages

The project will be implemented through the following stages:

```text
Stage 0   Repository Foundation
Stage 1   Domain Model
Stage 2   Configuration
Stage 3   Database
Stage 4   Synthetic Telecom Data
Stage 5   Document Loaders
Stage 6   Cleaning and Metadata
Stage 7   Chunking
Stage 8   Embeddings
Stage 9   Vector Retrieval
Stage 10  Keyword Retrieval
Stage 11  Hybrid Retrieval
Stage 12  Baseline RAG
Stage 13  Query Understanding
Stage 14  Grounding and Citations
Stage 15  Evaluation
Stage 16  Security and Authorization
Stage 17  FastAPI
Stage 18  Observability
Stage 19  Reranking
Stage 20  LangChain Integration
Stage 21  Agentic RAG
Stage 22  Agent Memory
Stage 23  Production Hardening
Stage 24  Frontend
Stage 25  CI/CD
Stage 26  Production Architecture
```

---

# 4. Stage 0 — Repository Foundation

## Goal

Create a clean Python project using `uv`.

## Tasks

Create:

```text
telco-rag/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── config/
├── docs/
├── data/
├── scripts/
├── src/
└── tests/
```

Configure:

* Python 3.12+
* `uv`
* pytest
* Ruff
* mypy or equivalent type checking
* Pydantic
* SQLAlchemy
* Alembic

## Deliverable

A project that can execute:

```bash
uv run pytest
```

with a clean test result.

---

# 5. Stage 1 — Domain Model

## Goal

Implement the telecom domain independently from infrastructure.

Create:

```text
src/telco_rag/domain/
├── documents.py
├── chunks.py
├── users.py
├── access.py
├── incidents.py
├── tickets.py
└── products.py
```

Define:

* entities
* value objects
* enumerations
* domain invariants
* relationships

Important classifications:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Important document types:

```text
NETWORK_DOCUMENTATION
PRODUCT_DOCUMENTATION
SUPPORT_KB
INCIDENT_REPORT
POSTMORTEM
RUNBOOK
CHANGE_PROCEDURE
SLA
OTHER
```

## Deliverable

Domain tests execute without PostgreSQL or external services.

---

# 6. Stage 2 — Configuration

## Goal

Implement centralized configuration.

Create:

```text
src/telco_rag/config/
├── settings.py
└── __init__.py
```

Use Pydantic Settings.

Support:

```text
environment
database
OpenRouter
embeddings
retrieval
generation
security
evaluation
observability
```

Configuration hierarchy:

```text
Environment variables
        ↓
Profile configuration
        ↓
Application configuration
```

## Deliverable

The application can load configuration for:

```text
dev
test
prod
```

---

# 7. Stage 3 — PostgreSQL + pgvector

## Goal

Create the persistence foundation.

Use Docker Compose.

Services:

```text
PostgreSQL
```

with pgvector enabled.

Create SQLAlchemy models for:

```text
documents
document_versions
chunks
embeddings
technologies
regions
products
services
incidents
support_tickets
runbooks
users
roles
access_policies
```

Create Alembic migrations.

## Deliverable

This must work:

```bash
docker compose up -d
uv run alembic upgrade head
```

---

# 8. Stage 4 — Synthetic Telecom Data

## Goal

Create realistic synthetic telecom knowledge.

Generate:

```text
network documentation
product documentation
support articles
incident reports
postmortems
runbooks
change procedures
SLA documents
```

Include realistic entities:

```text
5G
4G/LTE
VoLTE
IMS
RAN
Core Network
EPC
5GC
AMF
SMF
UPF
gNodeB
eNodeB
```

Generate relationships between:

```text
products
services
regions
technologies
incidents
documents
```

Include different classifications.

## Deliverable

The repository contains a reproducible synthetic telecom dataset.

---

# 9. Stage 5 — Document Loaders

## Goal

Implement document ingestion.

Create:

```text
ingestion/loaders/
├── pdf.py
├── docx.py
├── markdown.py
└── text.py
```

Support:

```text
PDF
DOCX
Markdown
TXT
```

Define:

```python
class DocumentLoader(Protocol):
    def load(self, source: Path) -> LoadedDocument:
        ...
```

## Deliverable

Every supported format can be converted into a common document representation.

---

# 10. Stage 6 — Cleaning and Metadata

## Goal

Normalize documents and extract metadata.

Implement:

```text
cleaning.py
metadata.py
```

Metadata should include:

```text
classification
document_type
technology
region
product
service
department
incident_severity
source
version
created_at
```

Classification must never default unknown content to `PUBLIC`.

## Deliverable

A raw document becomes a normalized document with validated metadata.

---

# 11. Stage 7 — Chunking

## Goal

Build the first custom chunking implementation.

Implement:

```text
src/telco_rag/ingestion/chunking.py
```

Start with structure-aware chunking.

Preserve:

```text
document_id
version_id
chunk_id
section
page
position
text
```

Important principle:

> Chunking must preserve enough source information to support later citations.

## Deliverable

A document can be transformed into reproducible chunks.

---

# 12. Stage 8 — Embeddings

## Goal

Create an embedding abstraction.

Define:

```python
class EmbeddingProvider(Protocol):
    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        ...
```

Implement an OpenRouter-compatible adapter or selected embedding provider behind the abstraction.

Store:

```text
embedding model
embedding dimension
embedding version
```

## Deliverable

Chunks can be embedded and persisted.

---

# 13. Stage 9 — Vector Retrieval

## Goal

Implement semantic retrieval using pgvector.

Flow:

```text
Query
 ↓
Embedding
 ↓
pgvector
 ↓
Top K chunks
```

Implement:

```text
retrieval/vector.py
```

Start with:

```text
cosine similarity
```

Benchmark indexing strategies later.

## Deliverable

A natural-language query retrieves semantically relevant telecom chunks.

---

# 14. Stage 10 — Keyword Retrieval

## Goal

Implement lexical retrieval.

Use PostgreSQL full-text search plus exact identifier matching.

Important identifiers include:

```text
incident IDs
ticket IDs
network elements
product codes
technology names
protocol names
```

Implement:

```text
retrieval/keyword.py
```

## Deliverable

Exact technical identifiers can be retrieved reliably.

---

# 15. Stage 11 — Hybrid Retrieval

## Goal

Combine semantic and lexical retrieval.

Implement:

```text
retrieval/hybrid.py
```

Initial approach:

```text
Vector Search
+
Keyword Search
↓
RRF
↓
Candidate Set
```

Configuration:

```yaml
retrieval:
  hybrid:
    enabled: true
    method: rrf
```

## Deliverable

Hybrid retrieval outperforms either retrieval method on the evaluation dataset.

---

# 16. Stage 12 — Baseline RAG

## Goal

Build the first complete RAG pipeline.

Flow:

```text
Question
 ↓
Retrieval
 ↓
Evidence
 ↓
Prompt
 ↓
OpenRouter
 ↓
Answer
```

Implement:

```text
generation/generator.py
generation/prompts.py
```

The model must be instructed to answer from supplied evidence.

## Deliverable

The system can answer telecom questions using retrieved documentation.

---

# 17. Stage 13 — Query Understanding

## Goal

Transform raw questions into structured retrieval requests.

Implement:

```text
query/
├── classifier.py
├── rewriter.py
├── router.py
└── models.py
```

Classify:

```text
KNOWLEDGE
INCIDENT
TROUBLESHOOTING
PRODUCT
SUPPORT
SLA
POLICY
COMPARISON
TEMPORAL
UNKNOWN
```

Extract:

```text
technology
region
product
service
incident_id
ticket_id
severity
protocol
vendor
```

## Deliverable

Queries become structured retrieval requests.

---

# 18. Stage 14 — Grounding and Citations

## Goal

Prevent unsupported answers.

Pipeline:

```text
Retrieved Evidence
 ↓
Evidence Validation
 ↓
Generation
 ↓
Claim Validation
 ↓
Citation Validation
 ↓
Final Answer
```

Implement:

```text
generation/citations.py
generation/grounding.py
```

Support:

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
CONTRADICTED
```

Support answer states:

```text
grounded
abstained
partial
conflicting
```

## Deliverable

Answers contain traceable citations and abstain when evidence is insufficient.

---

# 19. Stage 15 — Evaluation

## Goal

Make retrieval and generation measurable.

Create:

```text
data/eval/
├── questions.jsonl
├── retrieval_cases.jsonl
└── expected_answers.jsonl
```

Measure:

### Retrieval

```text
Recall@K
Precision@K
MRR
NDCG@K
Hit Rate@K
```

### Generation

```text
correctness
relevance
groundedness
completeness
citation correctness
citation completeness
```

### System

```text
latency
tokens
cost
failure rate
```

## Deliverable

Every major RAG change can be compared against a baseline.

---

# 20. Stage 16 — Security and Authorization

## Goal

Introduce enterprise access control before exposing the platform.

Implement:

```text
security/
├── authentication.py
├── authorization.py
├── acl.py
└── filters.py
```

Security pipeline:

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
Security Filters
 ↓
Retrieval
 ↓
Evidence
 ↓
Generation
```

Critical invariant:

> Unauthorized content must never enter the LLM context.

Test:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

with different user roles.

---

# 21. Stage 17 — FastAPI

## Goal

Expose the application through an API.

Create:

```text
api/
├── app.py
├── dependencies.py
└── routes/
    ├── health.py
    ├── query.py
    ├── documents.py
    ├── ingestion.py
    └── incidents.py
```

Implement:

```text
GET  /health
GET  /ready
GET  /api/v1/version

POST /api/v1/query

GET  /api/v1/documents
GET  /api/v1/documents/{id}

POST /api/v1/ingestion
GET  /api/v1/ingestion/{id}

GET /api/v1/incidents
GET /api/v1/incidents/{id}
```

Routes should delegate to application services.

---

# 22. Stage 18 — Observability

## Goal

Make the platform observable.

Implement:

```text
logging
tracing
metrics
```

Use:

```text
OpenTelemetry
Prometheus-compatible metrics
structured JSON logging
```

Trace:

```text
API
 ↓
Application
 ↓
Query Processing
 ↓
Security
 ↓
Retrieval
 ↓
Generation
 ↓
LLM
 ↓
Grounding
```

Track:

```text
latency
tokens
cost
retrieval scores
candidate counts
errors
model
prompt version
embedding version
```

---

# 23. Stage 19 — Reranking

## Goal

Improve evidence quality after hybrid retrieval.

Flow:

```text
Vector Search
+
Keyword Search
 ↓
Candidate Fusion
 ↓
Reranker
 ↓
Top Evidence
```

Implement:

```text
retrieval/reranker.py
```

Evaluate against the baseline.

Do not enable reranking simply because it exists.

Enable it only if evaluation demonstrates improvement relative to its latency/cost.

---

# 24. Stage 20 — LangChain Integration

## Goal

Learn how LangChain maps onto the RAG architecture.

Only now introduce LangChain.

Compare:

```text
Custom RAG
```

against:

```text
LangChain RAG
```

Study:

* document abstractions
* retrievers
* prompt templates
* model wrappers
* chains
* structured output

Keep LangChain behind application/infrastructure boundaries.

## Deliverable

You understand both:

```text
how RAG works
```

and:

```text
how LangChain implements RAG
```

---

# 25. Stage 21 — Agentic RAG

## Goal

Introduce controlled agentic investigation.

First agent:

```text
Telecom Investigation Agent
```

Possible tools:

```text
knowledge_search
incident_search
ticket_search
product_search
```

Flow:

```text
User
 ↓
Agent
 ↓
Plan
 ↓
Tool
 ↓
Evidence
 ↓
Reason
 ↓
Next Tool
 ↓
Evidence
 ↓
Final Answer
```

The agent does not bypass:

```text
authorization
retrieval
grounding
observability
evaluation
```

---

# 26. Stage 22 — Agent Memory

## Goal

Introduce controlled memory.

Separate:

```text
Conversation State
Working Memory
Long-Term Memory
Enterprise Knowledge
```

Do not confuse memory with RAG.

Memory is:

```text
information about interaction/state
```

Knowledge is:

```text
authoritative enterprise information
```

Implement memory only after agentic RAG is stable.

---

# 27. Stage 23 — Production Hardening

## Goal

Make the system resilient.

Implement:

```text
timeouts
retries
circuit breakers
rate limiting
connection pooling
caching
backpressure
health checks
readiness checks
graceful degradation
```

Also implement:

```text
secret management
security headers
request limits
audit logging
data retention
PII controls
```

---

# 28. Stage 24 — Frontend

## Goal

Build the enterprise RAG user interface.

Technology:

```text
React
TypeScript
Tailwind
```

Initial screens:

```text
Login
Chat
Sources
Document Browser
Incident Browser
Evaluation Dashboard
System Status
```

The chat interface should show:

```text
Answer
Citations
Sources
Grounding status
```

---

# 29. Stage 25 — CI/CD

## Goal

Automate quality gates.

GitHub Actions pipeline:

```text
Commit
 ↓
Lint
 ↓
Type Check
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Security Tests
 ↓
Evaluation Tests
 ↓
Build
 ↓
Container Scan
 ↓
Deploy
```

Evaluation should eventually become a CI quality gate.

---

# 30. Stage 26 — Production Architecture

## Goal

Evaluate whether the modular monolith should evolve.

Initial architecture:

```text
                    ┌──────────────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Application  │
                    └──────┬───────┘
                           │
        ┌──────────────────┼─────────────────┐
        ▼                  ▼                 ▼
   Retrieval          Generation         Security
        │                  │                 │
        └──────────────────┼─────────────────┘
                           ▼
                    ┌──────────────┐
                    │ PostgreSQL   │
                    │ + pgvector   │
                    └──────────────┘
```

Only split services when there is a demonstrated need.

Possible future services:

```text
Ingestion Worker
Retrieval Service
Evaluation Worker
Agent Runtime
Frontend
```

Do not introduce microservices prematurely.

---

# 31. Implementation Order by Learning Objective

The project is also a learning curriculum.

## Phase A — Software Architecture

```text
Foundation
Domain
Application
Infrastructure
Database
```

## Phase B — RAG Fundamentals

```text
Documents
Cleaning
Chunking
Embeddings
Vector Search
Keyword Search
Hybrid Search
```

## Phase C — LLM Application Engineering

```text
Prompting
Structured Output
Query Understanding
Grounding
Citations
Abstention
```

## Phase D — Enterprise RAG

```text
Authentication
Authorization
ACL
Metadata Filtering
Evaluation
Observability
```

## Phase E — Frameworks

```text
LangChain
LangGraph
```

## Phase F — Agent Engineering

```text
Tools
Planning
State
Memory
Multi-step Investigation
Human Oversight
```

## Phase G — Production Engineering

```text
Reliability
Performance
Security
CI/CD
Cost
Deployment
```

---

# 32. Vertical Slice Strategy

Do not implement every layer completely before running the system.

The first vertical slice should be:

```text
Synthetic Document
       ↓
Loader
       ↓
Chunk
       ↓
Embedding
       ↓
PostgreSQL
       ↓
Vector Search
       ↓
OpenRouter
       ↓
Answer
```

This establishes the first working RAG system.

Then progressively add:

```text
Keyword Search
       ↓
Hybrid Search
       ↓
Query Understanding
       ↓
Grounding
       ↓
Evaluation
       ↓
Security
       ↓
API
       ↓
Observability
```

---

# 33. Milestones

## Milestone 1 — Foundation

Complete:

```text
Stage 0
Stage 1
Stage 2
Stage 3
```

Result:

> Clean DDD-oriented Python application with working PostgreSQL.

---

## Milestone 2 — Ingestion

Complete:

```text
Stage 4
Stage 5
Stage 6
Stage 7
Stage 8
```

Result:

> Telecom documents can be transformed into searchable vectorized chunks.

---

## Milestone 3 — RAG MVP

Complete:

```text
Stage 9
Stage 10
Stage 11
Stage 12
```

Result:

> Working hybrid telecom RAG system.

---

## Milestone 4 — Reliable RAG

Complete:

```text
Stage 13
Stage 14
Stage 15
```

Result:

> Query-aware, grounded, cited, evaluated RAG.

---

## Milestone 5 — Enterprise RAG

Complete:

```text
Stage 16
Stage 17
Stage 18
Stage 19
```

Result:

> Secure, observable enterprise RAG API.

---

## Milestone 6 — Framework and Agents

Complete:

```text
Stage 20
Stage 21
Stage 22
```

Result:

> Agentic RAG with controlled tools and memory.

---

## Milestone 7 — Production

Complete:

```text
Stage 23
Stage 24
Stage 25
Stage 26
```

Result:

> Production-oriented telecom AI platform.

---

# 34. What We Should NOT Build Early

Do not start with:

```text
Multi-agent architecture
Complex LangGraph workflows
Microservices
Kubernetes
Graph databases
Large-scale distributed queues
Sophisticated memory
Autonomous network operations
```

These add complexity before the RAG fundamentals are proven.

---

# 35. First Implementation Sequence

The immediate implementation sequence is:

```text
1. Repository foundation
2. Domain models
3. Pydantic configuration
4. Docker PostgreSQL + pgvector
5. SQLAlchemy models
6. Alembic migrations
7. Synthetic telecom documents
8. Document loaders
9. Cleaning
10. Metadata extraction
11. Chunking
12. Embeddings
13. Vector search
14. Keyword search
15. Hybrid retrieval
16. Baseline generation
17. Query understanding
18. Grounding
19. Evaluation
20. Security
21. Application services
22. FastAPI
23. Observability
24. Reranking
25. LangChain
26. LangGraph / Agentic RAG
27. Memory
28. Production hardening
29. Frontend
30. CI/CD
```

---

# 36. Definition of Project Completion

The project is considered complete when a user can:

```text
Authenticate
     ↓
Ask a telecom question
     ↓
Query is understood
     ↓
Authorization is evaluated
     ↓
Hybrid retrieval executes
     ↓
Relevant evidence is selected
     ↓
Answer is generated
     ↓
Claims are grounded
     ↓
Citations are validated
     ↓
Answer is returned
     ↓
Trace/metrics are recorded
     ↓
Quality can be evaluated
```

And an authorized administrator can:

```text
Ingest documents
View ingestion status
Inspect documents
Inspect incidents
Run evaluations
Review retrieval quality
Review grounding quality
Inspect system telemetry
```

The final system should evolve toward:

```text
                    TELCO AI PLATFORM
                           │
          ┌────────────────┼────────────────┐
          │                │                │
        RAG             Agents           Data
          │                │                │
    Retrieval         Planning          Documents
    Grounding         Tools             Incidents
    Citations         Memory            Tickets
    Evaluation        State             Products
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Security Layer
                           │
                    Observability
                           │
                    PostgreSQL
                     + pgvector
```

The guiding implementation rule is:

> **Build the simplest reliable version first, measure it, then add complexity only when the evidence justifies it.**

