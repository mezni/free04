# telco-rag — Architecture

## 1. Document Information

| Field              | Value                                      |
| ------------------ | ------------------------------------------ |
| Project            | `telco-rag`                                |
| Document           | Architecture                               |
| Version            | 1.0                                        |
| Status             | Draft                                      |
| Architecture Style | Layered, Domain-Oriented, Modular Monolith |
| Primary Language   | Python 3.12+                               |
| Package Manager    | uv                                         |
| API                | FastAPI                                    |
| Database           | PostgreSQL + pgvector                      |
| ORM                | SQLAlchemy 2                               |
| Migrations         | Alembic                                    |
| LLM Provider       | OpenRouter                                 |
| Containerization   | Docker Compose                             |

---

# 2. Architectural Goals

The architecture must support five goals:

1. Build a reliable RAG system first.
2. Keep domain logic independent from infrastructure.
3. Make retrieval independently testable and replaceable.
4. Enforce security before generation.
5. Allow evolution into agentic RAG without rewriting the foundation.

The architecture therefore favors:

* clear boundaries
* dependency inversion
* explicit interfaces
* small components
* measurable pipelines
* provider abstraction
* framework isolation
* incremental complexity

---

# 3. Architectural Principles

## 3.1 Domain Independence

Domain concepts must not depend on:

* FastAPI
* SQLAlchemy
* OpenRouter
* LangChain
* LangGraph
* PostgreSQL

The domain layer represents business concepts and rules.

---

## 3.2 Infrastructure at the Boundary

Infrastructure dependencies live behind adapters.

Example:

```text
Application
     ↓
LLM Interface
     ↓
OpenRouter Adapter
```

The application should not directly depend on OpenRouter-specific implementation details.

---

## 3.3 Retrieval as a Subsystem

Retrieval is not a helper function.

It is a first-class subsystem with its own:

* interfaces
* configuration
* tests
* metrics
* evaluation
* experiments

---

## 3.4 Security Before Context

Security filtering must occur before context is assembled for the LLM.

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
Security Filtering
 ↓
Retrieval
 ↓
Authorized Evidence
 ↓
LLM
```

---

## 3.5 Evidence Before Generation

Generation receives evidence produced by retrieval.

The LLM should not independently search enterprise knowledge.

---

# 4. High-Level Architecture

```text
                           ┌───────────────────┐
                           │       User        │
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │      FastAPI      │
                           │       API         │
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │   Application     │
                           │      Layer        │
                           └─────────┬─────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │    Query    │       │  Security   │       │ Generation  │
       │   Service   │       │   Service   │       │   Service   │
       └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
                           ┌───────────────────┐
                           │    Retrieval      │
                           │     System        │
                           └─────────┬─────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      ▼              ▼              ▼
                Vector Search   Keyword Search   Reranker
                      │              │              │
                      └──────────────┼──────────────┘
                                     ▼
                           ┌───────────────────┐
                           │   PostgreSQL +    │
                           │     pgvector      │
                           └───────────────────┘

                           ┌───────────────────┐
                           │    OpenRouter     │
                           │       LLM         │
                           └───────────────────┘
```

---

# 5. Architectural Style

The initial system will be a **modular monolith**.

This is intentional.

We will not begin with microservices.

The application will have clear internal boundaries that can later be extracted into services if scale requires it.

Conceptually:

```text
                    telco-rag
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
    Domain       Application      Infrastructure
       │               │                │
       └───────────────┼────────────────┘
                       │
                       ▼
                      API
```

This provides architectural discipline without premature distributed-system complexity.

---

# 6. Layered Architecture

The system has five primary layers.

```text
┌────────────────────────────────────────────┐
│                 API Layer                  │
├────────────────────────────────────────────┤
│             Application Layer              │
├────────────────────────────────────────────┤
│                Domain Layer                │
├────────────────────────────────────────────┤
│         Infrastructure / Adapters          │
├────────────────────────────────────────────┤
│        External Systems / Providers        │
└────────────────────────────────────────────┘
```

---

# 7. API Layer

Location:

```text
src/telco_rag/api/
```

Responsibilities:

* HTTP endpoints
* request validation
* response serialization
* dependency injection
* authentication integration
* HTTP error mapping

The API layer must not contain:

* retrieval algorithms
* chunking logic
* prompt construction
* database queries
* LLM-specific business logic

---

# 8. Application Layer

The application layer coordinates use cases.

Examples:

```text
QueryKnowledge
IngestDocument
SearchDocuments
InvestigateIncident
EvaluateRetrieval
```

Application services coordinate domain and infrastructure components.

Example:

```text
QueryKnowledge
      │
      ├── authorize user
      ├── understand query
      ├── retrieve evidence
      ├── rerank evidence
      ├── generate answer
      └── construct response
```

---

# 9. Domain Layer

Location:

```text
src/telco_rag/domain/
```

The domain layer represents telecom concepts.

Examples:

```text
Document
DocumentVersion
Chunk
Incident
SupportTicket
Product
Service
SLA
Technology
Region
User
Role
AccessPolicy
```

The domain layer should contain:

* entities
* value objects
* domain rules
* domain interfaces where appropriate

It should not contain infrastructure implementations.

---

# 10. Infrastructure Layer

Location:

```text
src/telco_rag/infrastructure/
```

Responsibilities include:

* PostgreSQL
* SQLAlchemy
* OpenRouter
* embedding providers
* vector search implementation
* external systems
* persistence

Examples:

```text
infrastructure/
├── database.py
├── repositories/
├── llm/
├── embeddings/
└── search/
```

---

# 11. Ingestion Architecture

The ingestion pipeline is:

```text
                  Source Document
                        │
                        ▼
                  Document Loader
                        │
                        ▼
                    Parser
                        │
                        ▼
                    Cleaner
                        │
                        ▼
                Metadata Extractor
                        │
                        ▼
                    Chunker
                        │
                        ▼
                  Embedder
                        │
                        ▼
                  Persistence
                        │
                        ▼
                 Search Index
```

Each stage should have a defined responsibility.

---

# 12. Document Loader

Loaders convert external document formats into a common representation.

Initial loaders:

```text
PDF
DOCX
Markdown
TXT
```

Conceptual interface:

```python
class DocumentLoader(Protocol):
    def load(self, source: str) -> ParsedDocument:
        ...
```

The rest of the pipeline should not care which file format was used.

---

# 13. Parsed Document

The parser should produce a normalized internal representation.

Conceptually:

```python
@dataclass
class ParsedDocument:
    title: str
    text: str
    source: str
    metadata: dict
```

The exact domain representation will be defined during implementation.

---

# 14. Cleaning

Cleaning transforms extracted text into normalized content.

Responsibilities:

* whitespace normalization
* extraction artifact removal
* preserving headings
* preserving important technical identifiers
* removing irrelevant noise

Cleaning must be deterministic where possible.

---

# 15. Metadata Extraction

Metadata extraction identifies structured properties.

Examples:

```text
technology = 5G
region = Ontario
document_type = incident
classification = INTERNAL
severity = HIGH
```

Metadata is persisted with the document and inherited by chunks where appropriate.

---

# 16. Chunking Architecture

Chunking is an independent subsystem.

```text
Parsed Document
      ↓
Structure Detection
      ↓
Chunking Strategy
      ↓
Chunks
```

Initial implementation should use custom Python logic.

Possible strategies:

* fixed-size chunking
* recursive chunking
* section-aware chunking
* semantic chunking

The project should evaluate these experimentally.

---

# 17. Embedding Architecture

Embedding generation must be abstracted.

```text
Chunk
  ↓
Embedding Interface
  ↓
Provider Adapter
  ↓
Embedding Vector
```

Example conceptual interface:

```python
class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        ...
```

The provider can later be changed without modifying ingestion or retrieval logic.

---

# 18. Storage Architecture

PostgreSQL stores the core system state.

Conceptually:

```text
PostgreSQL
│
├── documents
├── document_versions
├── chunks
├── embeddings
├── products
├── services
├── incidents
├── support_tickets
├── runbooks
├── slas
├── users
├── roles
├── access_policies
└── evaluation_cases
```

pgvector stores chunk embeddings.

---

# 19. Database Boundary

Application code should use repository interfaces.

Example:

```text
Application
     ↓
DocumentRepository
     ↓
SQLAlchemy Repository
     ↓
PostgreSQL
```

The application layer should not construct raw SQL for ordinary domain operations.

---

# 20. Retrieval Architecture

Retrieval is divided into independent stages.

```text
Query
  ↓
Query Processing
  ↓
Metadata Filtering
  ↓
Candidate Retrieval
  ├── Vector
  └── Keyword
  ↓
Fusion
  ↓
Reranking
  ↓
Evidence Selection
```

---

# 21. Vector Retrieval

Vector retrieval performs semantic similarity search.

Input:

```text
query embedding
```

Output:

```text
ranked candidate chunks
```

The vector implementation should be isolated from the retrieval interface.

---

# 22. Keyword Retrieval

Keyword retrieval is designed for exact terminology.

Useful examples:

```text
INC-2026-0042
5G-SA
AMF
SMF
VoLTE
ERR-4032
PRODUCT-ENTERPRISE-5G
```

Keyword search and vector search serve different purposes.

---

# 23. Hybrid Retrieval

Hybrid retrieval combines lexical and semantic results.

Possible fusion strategies:

* weighted score fusion
* Reciprocal Rank Fusion
* normalized score fusion

The first implementation should choose one simple, explainable strategy.

---

# 24. Metadata Filtering

Metadata filtering should occur before or during candidate retrieval whenever possible.

Example:

```text
technology = 5G
AND
region = Ontario
AND
classification <= user's access level
```

Security filters must never be treated as optional retrieval filters.

---

# 25. Reranking

Reranking receives candidate results.

```text
Query
+
Candidates
    ↓
Reranker
    ↓
Ordered Results
```

The reranker must be replaceable.

Possible future implementations:

* cross-encoder
* hosted reranker
* LLM-based reranker

---

# 26. Evidence Assembly

After retrieval and reranking, the system constructs an evidence set.

```text
Top Results
    ↓
Deduplicate
    ↓
Validate Authorization
    ↓
Select Context
    ↓
Evidence Set
```

The evidence set becomes the only enterprise knowledge available to generation.

---

# 27. Generation Architecture

```text
User Query
    +
Authorized Evidence
    +
System Instructions
        ↓
   Prompt Builder
        ↓
    LLM Adapter
        ↓
    LLM Provider
        ↓
Generated Answer
```

The generation layer should not perform retrieval itself.

---

# 28. Prompt Architecture

Prompts are externalized from application code.

Location:

```text
prompts/
├── query/
├── generation/
└── agents/
```

Prompt versions must be identifiable.

Example:

```text
answer_v1
answer_v2
```

This allows evaluation across prompt versions.

---

# 29. Grounding Architecture

The generation layer should receive structured evidence.

Conceptually:

```python
GenerationRequest(
    query=query,
    evidence=evidence,
    instructions=instructions,
)
```

The generator should not receive unrestricted access to the database.

---

# 30. Citation Architecture

Each retrieved chunk should have enough information to create a citation.

Example:

```text
Chunk
 ├── document_id
 ├── document_version
 ├── section
 ├── page
 └── source
```

The generation response should map claims to these sources where practical.

---

# 31. Security Architecture

Security is cross-cutting but has a dedicated subsystem.

```text
src/telco_rag/security/
```

Components:

```text
authentication.py
authorization.py
acl.py
filters.py
```

Flow:

```text
Request
  ↓
Authentication
  ↓
User Identity
  ↓
Authorization
  ↓
Retrieval Policy
  ↓
Secure Retrieval
  ↓
Authorized Evidence
```

---

# 32. Security Invariant

The following invariant must always hold:

```text
Unauthorized Data
        X
        │
        X
        ↓
LLM Context
```

No component after retrieval should be expected to remove unauthorized content.

Authorization must happen as early as possible.

---

# 33. Query Architecture

The query subsystem contains:

```text
query/
├── classifier.py
├── rewriter.py
├── router.py
└── models.py
```

The initial implementation may bypass query classification.

Later:

```text
Query
 ↓
Classification
 ↓
Entity Extraction
 ↓
Rewrite
 ↓
Routing
```

---

# 34. Query Router

The router determines which retrieval strategy is appropriate.

Example:

```text
"Why does 5G handover fail?"
        ↓
Technical Retrieval

"Which SLA applies?"
        ↓
SLA Retrieval

"Have we seen this outage before?"
        ↓
Incident Retrieval
```

Initially, routing may remain simple.

---

# 35. Evaluation Architecture

Evaluation is independent from production query execution.

```text
Evaluation Dataset
       ↓
Evaluation Runner
       ↓
Retrieval System
       ↓
Generation System
       ↓
Metrics
       ↓
Report
```

This allows different versions of retrieval and generation to be compared.

---

# 36. Evaluation Isolation

Evaluation code must not modify production data.

Evaluation datasets should be versioned.

Example:

```text
data/eval/
├── questions.jsonl
├── retrieval_cases.jsonl
└── expected_answers.jsonl
```

---

# 37. Observability Architecture

Observability covers:

```text
Logging
Tracing
Metrics
```

Architecture:

```text
API
 ↓
Application
 ↓
Retrieval
 ↓
Database / LLM
```

Each layer should emit useful operational telemetry.

---

# 38. Logging

Logs should be structured.

Example conceptual event:

```json
{
  "event": "retrieval.completed",
  "request_id": "...",
  "query_id": "...",
  "candidate_count": 50,
  "selected_count": 8,
  "latency_ms": 120
}
```

Sensitive content should not be logged by default.

---

# 39. Metrics

Important metrics include:

```text
requests_total
requests_failed
retrieval_latency
reranking_latency
llm_latency
end_to_end_latency
tokens_input
tokens_output
retrieval_recall
answer_quality
```

---

# 40. Tracing

Tracing should eventually represent the complete request lifecycle.

Example:

```text
Trace
│
├── API request
│
├── authentication
│
├── authorization
│
├── query classification
│
├── vector search
│
├── keyword search
│
├── fusion
│
├── reranking
│
├── prompt construction
│
├── LLM call
│
└── response construction
```

---

# 41. Configuration Architecture

Configuration is externalized.

```text
config/
├── settings.yaml
├── ingestion.yaml
├── retrieval.yaml
├── evaluation.yaml
├── security.yaml
├── observability.yaml
└── profiles/
    ├── dev.yaml
    ├── test.yaml
    └── prod.yaml
```

Environment-specific secrets belong in environment variables or secret management systems.

---

# 42. Configuration Rules

Configuration must not contain secrets committed to Git.

Examples of configuration:

```text
chunk_size
chunk_overlap
top_k
reranker_top_k
embedding_model
llm_model
database URL
logging level
```

Secrets:

```text
OPENROUTER_API_KEY
DATABASE_PASSWORD
```

must be supplied externally.

---

# 43. API Architecture

The API exposes application use cases.

Example:

```text
POST /query
      ↓
QueryKnowledge
```

rather than:

```text
POST /query
      ↓
SQL Query
      ↓
LLM Call
```

The endpoint should remain thin.

---

# 44. Dependency Direction

The preferred dependency direction is:

```text
API
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

More explicitly:

```text
API ──────────────→ Application
                         │
                         ↓
                      Domain
                         ↑
                         │
                  Infrastructure
```

Infrastructure implements interfaces required by the application/domain.

---

# 45. Dependency Rules

The following dependencies are prohibited where practical:

```text
Domain → FastAPI
Domain → SQLAlchemy
Domain → OpenRouter
Domain → LangChain
Domain → LangGraph
```

The following are acceptable:

```text
API → Application
Application → Domain
Infrastructure → Domain
Infrastructure → Application Interfaces
```

---

# 46. Module Boundaries

Primary modules:

```text
api
domain
ingestion
retrieval
query
generation
security
evaluation
observability
infrastructure
agents
```

Each module should have one clear architectural responsibility.

---

# 47. Agent Architecture

Agents are explicitly separated from baseline RAG.

Location:

```text
src/telco_rag/agents/
```

Future structure:

```text
agents/
├── graph.py
├── state.py
├── planner.py
└── tools/
    ├── knowledge_search.py
    ├── incident_search.py
    ├── ticket_search.py
    └── product_search.py
```

---

# 48. Agent State

A future investigation agent may maintain:

```text
InvestigationState
├── original_query
├── current_plan
├── findings
├── retrieved_evidence
├── incidents
├── tickets
├── hypotheses
├── confidence
└── next_action
```

The state must respect authorization boundaries.

---

# 49. Agent Tool Architecture

Tools should be explicit capabilities.

Example:

```text
Agent
  ↓
KnowledgeSearchTool
  ↓
RetrievalService
```

The agent should not directly access:

* PostgreSQL
* OpenRouter
* internal repositories

Tools are the controlled boundary.

---

# 50. Agent Authority

The agent may initially:

* search knowledge
* search incidents
* search tickets
* search products
* summarize evidence

The agent must not initially:

* modify network configuration
* execute production commands
* disable services
* alter customer accounts
* approve operational changes

---

# 51. Memory Architecture

Memory will be introduced after agent workflows exist.

Possible architecture:

```text
Agent
 ↓
Memory Interface
 ↓
Conversation Memory
Investigation Memory
Long-Term Memory
```

Memory must be subject to the same security model as other enterprise information.

---

# 52. Human-in-the-Loop Architecture

For sensitive operations:

```text
Agent
 ↓
Decision
 ↓
Approval Required
 ↓
Human
 ↓
Approved / Rejected
```

The system must preserve the distinction between:

```text
Recommendation
```

and:

```text
Action
```

---

# 53. Data Flow — Ingestion

Complete ingestion flow:

```text
Document
   ↓
Loader
   ↓
Parser
   ↓
Cleaner
   ↓
Metadata Extraction
   ↓
Chunking
   ↓
Embedding
   ↓
PostgreSQL
   +
pgvector
```

---

# 54. Data Flow — Query

Complete query flow:

```text
User
 ↓
FastAPI
 ↓
Authentication
 ↓
Authorization
 ↓
Query Processing
 ↓
Metadata / Security Filters
 ↓
Vector Search
 +
Keyword Search
 ↓
Fusion
 ↓
Reranking
 ↓
Evidence Assembly
 ↓
Prompt Construction
 ↓
LLM
 ↓
Citation Mapping
 ↓
Response
```

---

# 55. Data Flow — Evaluation

```text
Evaluation Dataset
        ↓
Query
        ↓
RAG Pipeline
        ↓
Retrieved Evidence
        ↓
Generated Answer
        ↓
Evaluation Metrics
        ↓
Experiment Result
```

---

# 56. Failure Architecture

The system must fail safely.

## Database Failure

```text
Database unavailable
       ↓
Controlled error
       ↓
No fabricated answer
```

## LLM Failure

```text
LLM unavailable
       ↓
Controlled error
       ↓
Optional retrieval-only response
```

## Retrieval Failure

```text
Retrieval unavailable
       ↓
No unsupported generation
```

## Insufficient Evidence

```text
Weak evidence
       ↓
Uncertainty response
```

---

# 57. Testing Architecture

Tests remain outside `src`.

```text
tests/
├── unit/
├── integration/
└── evaluation/
```

Unit tests should test components independently.

Integration tests verify component interactions.

Evaluation tests measure RAG quality.

---

# 58. Testing Pyramid

```text
              ┌───────────────┐
              │  Evaluation   │
              └───────┬───────┘
                      │
              ┌───────┴───────┐
              │  Integration  │
              └───────┬───────┘
                      │
          ┌───────────┴───────────┐
          │      Unit Tests       │
          └───────────────────────┘
```

Most tests should be unit tests.

---

# 59. Deployment Architecture — Development

Development uses Docker Compose.

```text
Docker Compose
│
├── PostgreSQL
│   └── pgvector
│
└── telco-rag API
```

The application itself may run directly through `uv` during development.

---

# 60. Deployment Architecture — Future

A production deployment may eventually look like:

```text
                    Load Balancer
                          │
                          ▼
                    API Instances
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Query       Ingestion    Evaluation
          Workers      Workers      Workers
             │            │            │
             └────────────┼────────────┘
                          ▼
                     PostgreSQL
                      + pgvector
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
          LLM Provider          Embedding Provider
```

This is a future architecture, not an MVP requirement.

---

# 61. Architecture Evolution

The architecture evolves through controlled stages.

## Stage 1 — Basic RAG

```text
API
 ↓
Retriever
 ↓
LLM
```

---

## Stage 2 — Production RAG

```text
API
 ↓
Security
 ↓
Retriever
 ↓
Reranker
 ↓
LLM
```

---

## Stage 3 — Query-Aware RAG

```text
API
 ↓
Query Understanding
 ↓
Routing
 ↓
Hybrid Retrieval
 ↓
Reranking
 ↓
LLM
```

---

## Stage 4 — Agentic RAG

```text
API
 ↓
Agent
 ├── Knowledge Search
 ├── Incident Search
 ├── Ticket Search
 └── Product Search
 ↓
Evidence
 ↓
LLM
```

---

## Stage 5 — Telecom Investigation Platform

```text
User
 ↓
Investigation Agent
 ↓
Planner
 ↓
Multiple Tools
 ↓
Evidence Graph
 ↓
Reasoning
 ↓
Human Approval
 ↓
Grounded Result
```

---

# 62. Architectural Tradeoffs

## Modular Monolith vs Microservices

### Decision

Use a modular monolith initially.

### Reason

The project is primarily a learning and architecture-building project.

A modular monolith provides:

* simpler development
* easier debugging
* easier local deployment
* lower operational complexity
* clear module boundaries

Microservices can be introduced later if actual scaling requirements justify them.

---

# 63. PostgreSQL + pgvector vs Dedicated Vector Database

### Decision

Use PostgreSQL + pgvector initially.

### Reason

The system requires both:

* structured enterprise data
* vector search

Using PostgreSQL reduces infrastructure complexity.

A dedicated vector database may be evaluated later if scale or workload characteristics require it.

---

# 64. Custom RAG vs LangChain

### Decision

Build the first RAG pipeline without LangChain.

### Reason

This exposes the underlying mechanics:

* embeddings
* retrieval
* ranking
* context construction
* prompting
* generation

LangChain can later be introduced to compare abstractions against the custom implementation.

---

# 65. LangGraph

LangGraph is deferred until agentic workflows are introduced.

It should not be used to implement the initial deterministic RAG pipeline.

---

# 66. OpenRouter

OpenRouter is the initial model gateway.

The architecture must isolate it behind:

```text
LLMProvider
```

This allows future providers to be introduced.

---

# 67. Architecture Decision Records

Important architectural decisions must be recorded in:

```text
docs/decisions/
```

Initial ADRs:

```text
ADR-001-database.md
ADR-002-vector-search.md
ADR-003-llm-provider.md
ADR-004-embedding-provider.md
ADR-005-framework-strategy.md
```

---

# 68. Repository Mapping

The architecture maps to the repository as follows:

```text
src/telco_rag/
│
├── api/
├── domain/
├── ingestion/
├── retrieval/
├── query/
├── generation/
├── security/
├── agents/
├── evaluation/
├── observability/
├── infrastructure/
└── config/
```

---

# 69. Architectural Constraints

The following constraints are mandatory:

1. Domain logic must remain framework-independent.
2. Security filtering must occur before LLM context construction.
3. Retrieval must be independently testable.
4. LLM providers must be replaceable.
5. Embedding providers must be replaceable.
6. Core RAG must not depend on LangChain.
7. Agentic functionality must not bypass security.
8. Evaluation must be versioned.
9. Synthetic data must be used initially.
10. Production network actions require explicit human authorization.
11. Secrets must never be committed to source control.
12. Architecture decisions must be documented.

---

# 70. Definition of Done

An architectural component is considered complete when:

* its responsibility is documented
* its boundary is clear
* its dependencies are understood
* its interface is defined
* unit tests exist
* integration behavior is defined where applicable
* observability requirements are identified
* security implications are addressed
* configuration requirements are documented

---

# 71. Final Architecture

The target architecture can be summarized as:

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Application       │
                         │      Services       │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
        Query Layer           Security Layer        Generation Layer
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Retrieval        │
                         │      Engine         │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
             Vector Search    Keyword Search     Reranker
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     PostgreSQL      │
                         │      + pgvector     │
                         └─────────────────────┘

                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    LLM Interface    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              OpenRouter

Future:

                         ┌─────────────────────┐
                         │   Agentic Layer     │
                         ├─────────────────────┤
                         │ Planner             │
                         │ State               │
                         │ Tools               │
                         │ Memory              │
                         │ Human Escalation    │
                         └─────────────────────┘
```

The architecture is intentionally designed so that the future agentic layer sits **above a mature RAG foundation**, rather than replacing it.

The central architectural rule remains:

> **Retrieve authorized evidence first, then generate.**

