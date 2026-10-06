# Telco RAG Constitution

**Project:** `telco-rag`
**Version:** 1.0.0
**Status:** Active

---

## 1. Purpose

This constitution defines the non-negotiable engineering principles, architectural constraints, quality standards, and development practices for the `telco-rag` project.

`telco-rag` is an enterprise Retrieval-Augmented Generation platform for telecommunications organizations.

The system will provide:

* Enterprise knowledge ingestion
* Semantic and lexical retrieval
* Hybrid retrieval
* Reranking
* Grounded answer generation
* Source citations
* Enterprise authorization
* Evaluation
* Observability
* Agentic RAG capabilities

The project is both a production-oriented system and a learning project. The implementation must therefore favor explicit architecture, understandable components, measurable behavior, and incremental complexity.

---

# 2. Core Principles

## Principle I — Enterprise RAG First

The primary product is an enterprise RAG platform, not an LLM chatbot.

The architecture MUST treat:

* enterprise knowledge
* retrieval
* authorization
* grounding
* evaluation
* observability

as first-class system capabilities.

The LLM is a generation component and MUST NOT be considered the source of truth.

### Requirements

Every generated answer SHOULD be traceable to retrieved enterprise evidence.

The system MUST be capable of responding that sufficient evidence was not found rather than fabricating an answer.

---

# 3. Retrieval Is a First-Class System

Retrieval quality is fundamental to the quality of the final answer.

The system MUST treat retrieval as an independently testable subsystem.

The architecture MUST allow retrieval strategies to evolve independently of generation.

The retrieval subsystem SHALL support the evolution:

```text
Vector Search
      ↓
Keyword Search
      ↓
Hybrid Retrieval
      ↓
Metadata Filtering
      ↓
Reranking
      ↓
Query Routing
```

Retrieval components MUST expose measurable results.

At minimum, retrieval evaluation SHALL support:

* Recall@K
* Precision@K
* MRR
* NDCG

---

# 4. Security Before Generation

Security is a mandatory architectural boundary.

Authorization MUST be enforced before retrieved information is provided to the LLM.

The system MUST NOT rely solely on prompts such as:

> "Do not reveal confidential information."

The required security flow is:

```text
User
  ↓
Authentication
  ↓
Authorization
  ↓
Retrieval Policy
  ↓
Authorized Retrieval
  ↓
Context Construction
  ↓
LLM
```

Unauthorized content MUST NOT enter the LLM context.

The system SHALL support, at minimum:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Document access MAY depend on:

* user
* role
* department
* region
* document classification
* ownership
* policy

Security behavior MUST be covered by automated tests.

---

# 5. Grounded Generation

The generation layer MUST use retrieved enterprise evidence as its primary factual basis.

Generated answers SHOULD contain source citations whenever supporting evidence exists.

A citation SHOULD identify, where available:

* document
* document version
* page
* section
* chunk

The system MUST distinguish between:

```text
Supported answer
Unsupported answer
Insufficient evidence
```

The system SHOULD prefer:

```text
"I don't have sufficient information to answer this."
```

over unsupported factual claims.

---

# 6. Telecom Domain Fidelity

The system SHALL model telecom concepts explicitly rather than treating all enterprise information as generic documents.

Initial domain concepts include:

```text
Network
5G
4G/LTE
VoLTE
Fiber
Broadband
IoT

Products
Services
SLAs

Incidents
Support Tickets
Runbooks
Postmortems

Regions
Departments
Users
Roles
Access Policies
```

Telecom-specific metadata SHALL be preserved during ingestion whenever available.

Examples include:

```text
technology
region
service
product
incident severity
document type
department
classification
```

---

# 7. Incremental Complexity

The project MUST evolve incrementally.

The implementation SHALL follow approximately:

```text
Basic RAG
    ↓
Hybrid Retrieval
    ↓
Reranking
    ↓
Query Understanding
    ↓
Security
    ↓
Evaluation
    ↓
Observability
    ↓
Agentic RAG
```

Agentic capabilities MUST NOT be introduced before the core RAG pipeline is measurable and reliable.

The project SHALL NOT begin with a complex multi-agent architecture.

---

# 8. Framework Independence

The core architecture MUST NOT become tightly coupled to a single AI framework.

The initial RAG mechanics SHOULD be implemented using explicit Python components before introducing higher-level frameworks.

The project MAY later use:

* LangChain
* LangGraph
* Ragas

but these frameworks MUST remain implementation details behind appropriate application boundaries where practical.

Business/domain logic MUST NOT depend directly on framework-specific abstractions unless there is a clear architectural reason.

The system SHOULD allow LLM providers, embedding providers, and retrieval implementations to be replaced without rewriting the domain layer.

---

# 9. Provider Independence

The project SHALL avoid unnecessary vendor lock-in.

The initial LLM integration will use OpenRouter.

LLM access SHOULD be isolated behind an application/infrastructure interface.

The architecture SHOULD allow future providers to be introduced without modifying business logic.

The same principle applies to:

* embedding models
* rerankers
* vector storage
* observability providers

Provider-specific code SHALL reside in infrastructure or adapter layers.

---

# 10. Python Architecture

The project SHALL use a modern Python `src` layout.

The repository SHALL follow:

```text
src/
└── telco_rag/
```

Application code MUST NOT be placed directly in the repository root.

Tests SHALL remain outside `src`:

```text
tests/
├── unit/
├── integration/
└── evaluation/
```

The project SHALL use:

* Python 3.12+
* `uv`
* type hints
* Pydantic
* pytest

Dependencies SHALL be explicitly declared in `pyproject.toml`.

---

# 11. Domain-Driven Structure

The architecture SHOULD separate domain concepts from infrastructure concerns.

The primary boundaries are:

```text
domain/
ingestion/
retrieval/
query/
generation/
security/
evaluation/
observability/
agents/
infrastructure/
api/
```

The domain layer MUST NOT directly depend on:

* PostgreSQL
* FastAPI
* LangChain
* LangGraph
* OpenRouter
* specific vector databases

Infrastructure components MAY depend on domain/application abstractions.

---

# 12. Data Quality

Enterprise RAG quality depends heavily on ingestion quality.

The ingestion pipeline MUST be deterministic and observable.

The pipeline SHALL conceptually follow:

```text
Source
  ↓
Load
  ↓
Parse
  ↓
Clean
  ↓
Normalize
  ↓
Metadata Extraction
  ↓
Chunk
  ↓
Validate
  ↓
Embed
  ↓
Index
```

The system MUST preserve document provenance.

Every chunk SHOULD be traceable back to:

```text
source document
document version
page or section
ingestion operation
```

Documents SHOULD have content hashes or equivalent identifiers to support idempotent ingestion.

---

# 13. Chunking Discipline

Chunking SHALL be treated as an engineering decision rather than a fixed utility call.

The project MUST support experimentation with:

* chunk size
* overlap
* semantic boundaries
* document structure
* metadata preservation

Chunking strategies SHALL be evaluated using retrieval metrics.

No chunking strategy shall be considered "correct" solely because it works on a small sample.

---

# 14. Database Principles

The primary relational database SHALL be PostgreSQL.

Vector search SHALL initially use `pgvector`.

Database schema changes MUST be managed through Alembic migrations.

The application MUST NOT rely on manually modified production schemas.

Database access SHALL use SQLAlchemy.

The system SHOULD separate:

```text
domain models
database models
API schemas
```

when their responsibilities differ.

---

# 15. Configuration Management

Configuration MUST be externalized.

Environment-specific settings MUST NOT be hard-coded into application logic.

The system SHALL support:

```text
dev
test
prod
```

Configuration SHOULD be strongly typed using Pydantic.

Secrets MUST NOT be committed to source control.

`.env.example` MAY document required environment variables without containing real credentials.

---

# 16. API Design

The service API SHALL use FastAPI.

API endpoints MUST be versioned.

Initial API version:

```text
/api/v1/
```

API contracts SHALL use Pydantic models.

The API SHOULD provide consistent:

* validation
* error responses
* logging
* request identifiers
* authentication
* authorization

API design MUST NOT expose internal infrastructure details unnecessarily.

---

# 17. Evaluation-Driven Development

RAG quality MUST be measurable.

The project SHALL maintain a versioned evaluation dataset containing:

```text
question
expected intent
expected sources
expected answer
difficulty
domain
```

Evaluation MUST include both retrieval and generation.

Changes to:

* chunking
* embeddings
* retrieval
* reranking
* prompts
* LLMs

SHOULD be evaluated against a consistent benchmark before being considered improvements.

A change MUST NOT be declared an improvement solely because a few manually tested examples look better.

---

# 18. Observability

The system SHALL be observable from end to end.

At minimum, observability SHALL cover:

```text
request
query
retrieval
reranking
context
LLM invocation
generation
response
errors
latency
token usage
```

The project SHALL use structured logging.

The project SHOULD use:

* OpenTelemetry
* Prometheus
* distributed traces

Observability MUST NOT expose sensitive enterprise content unnecessarily.

Logs MUST NOT contain secrets.

---

# 19. Testing

Testing is mandatory.

The project SHALL maintain:

### Unit tests

For:

* domain logic
* chunking
* metadata extraction
* retrieval logic
* security policies
* prompt construction
* response parsing

### Integration tests

For:

* PostgreSQL
* pgvector
* ingestion
* retrieval
* API
* authentication/authorization

### Evaluation tests

For:

* retrieval quality
* answer quality
* citation quality
* grounding

Security-sensitive behavior MUST have automated regression tests.

---

# 20. Synthetic Data First

Development SHALL initially use synthetic telecom data.

The system SHOULD generate realistic:

```text
network documentation
runbooks
incidents
support tickets
products
SLAs
postmortems
```

Synthetic data MUST contain realistic metadata and relationships.

The project MUST NOT require proprietary telecom data to demonstrate its core capabilities.

This enables reproducible development and testing.

---

# 21. Agentic RAG

Agentic functionality SHALL be introduced only after the core RAG platform has:

* reliable retrieval
* security enforcement
* evaluation
* observability
* grounded generation

The agent architecture SHOULD use explicit tools.

Initial tools may include:

```text
knowledge_search
incident_search
ticket_search
product_search
runbook_search
similar_incident_search
```

Agents MUST have explicit boundaries around what actions they can perform.

The initial agent MUST NOT autonomously execute production network changes.

---

# 22. Memory

Memory SHALL be treated as a separate architectural concern.

The system SHALL distinguish:

```text
Conversation State
Long-Term Knowledge
Operational State
Agent Memory
```

The enterprise knowledge base MUST NOT automatically be treated as conversational memory.

Memory behavior MUST be explicit, testable, and observable.

---

# 23. Human Oversight

The system is intended to assist telecom employees, not replace operational authority.

High-impact operational decisions SHOULD remain subject to human review.

The initial system MUST NOT autonomously:

* modify network configuration
* disable services
* change customer subscriptions
* alter production infrastructure
* execute destructive operations

Agentic workflows SHALL clearly identify actions requiring human authorization.

---

# 24. Reliability

External AI and infrastructure dependencies are inherently unreliable.

The system SHALL handle:

* LLM timeouts
* embedding failures
* database failures
* transient network failures
* malformed documents
* malformed model responses
* rate limits

The system SHOULD implement:

* timeouts
* retries
* exponential backoff
* circuit breakers where appropriate
* graceful failure

Retries MUST NOT create uncontrolled duplicate operations.

---

# 25. Performance

Performance SHALL be measured rather than assumed.

The project SHOULD track:

```text
ingestion latency
retrieval latency
reranking latency
LLM latency
end-to-end latency
throughput
token usage
cost
```

Performance optimization MUST be based on observed bottlenecks.

Premature optimization MUST NOT compromise architectural clarity.

---

# 26. Cost Awareness

LLM and embedding usage SHALL be measurable.

The system SHOULD track:

```text
input tokens
output tokens
embedding calls
LLM calls
estimated cost
```

The architecture SHOULD allow cheaper models to be used for appropriate tasks.

Examples:

```text
classification → inexpensive model
query rewriting → inexpensive model
final answer → stronger model
```

---

# 27. Security and Privacy

Secrets MUST never be committed.

Sensitive information SHOULD be minimized in:

* logs
* traces
* metrics
* error messages

Enterprise documents MUST be treated as potentially confidential.

Access control MUST be enforced server-side.

Client-provided authorization claims MUST NOT be trusted without validation.

---

# 28. Documentation

Important architectural decisions SHALL be documented.

The project SHOULD maintain:

```text
docs/
├── architecture/
├── domain/
├── experiments/
└── decisions/
```

Architectural decisions SHOULD be recorded using ADRs.

Experiments SHOULD document:

```text
Hypothesis
Configuration
Dataset
Method
Results
Conclusion
Decision
```

This is particularly important for:

* chunking
* embeddings
* retrieval
* reranking
* prompts
* LLM selection

---

# 29. Development Workflow

Every significant feature SHOULD follow:

```text
Specification
    ↓
Design
    ↓
Implementation Plan
    ↓
Implementation
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
Evaluation
    ↓
Documentation
```

Features MUST NOT be implemented solely by modifying code without updating the relevant specification when the behavior changes.

---

# 30. Definition of Done

A feature is considered complete only when:

* The implementation exists.
* Relevant tests exist.
* Error behavior is handled.
* Security implications are considered.
* Observability is added where appropriate.
* Documentation is updated.
* Evaluation is performed when the feature affects RAG quality.
* The code passes the project quality checks.

For RAG changes, "it works on one example" is NOT sufficient evidence of completion.

---

# 31. Architecture Evolution

The project SHALL evolve through the following major stages:

```text
Stage 1
Basic RAG

Stage 2
Hybrid Retrieval

Stage 3
Reranking

Stage 4
Query Understanding

Stage 5
Enterprise Security

Stage 6
Evaluation

Stage 7
Observability

Stage 8
Production API

Stage 9
Agentic RAG

Stage 10
Production Hardening
```

Each stage MUST preserve the architectural boundaries established by previous stages.

---

# 32. Technology Principles

The initial technology stack SHALL be:

```text
Python 3.12+
uv
Pydantic
FastAPI
PostgreSQL
pgvector
SQLAlchemy
Alembic
OpenRouter
pytest
Docker
```

The project MAY introduce:

```text
LangChain
LangGraph
Ragas
OpenTelemetry
Prometheus
React
TypeScript
```

when justified by the corresponding implementation phase.

Framework adoption MUST solve a demonstrated problem rather than being introduced merely because it is popular.

---

# 33. Constitution Compliance

All feature specifications, implementation plans, and architectural decisions MUST be evaluated against this constitution.

When a proposed implementation conflicts with this constitution, the conflict MUST be explicitly identified.

Exceptions require:

1. A documented rationale.
2. Identification of the affected principle.
3. An explanation of the trade-off.
4. An explicit architectural decision.
5. Updating this constitution when the principle is permanently changed.

---

# 34. Final Engineering Principle

The project follows one overarching principle:

> **Build an enterprise RAG system that retrieves authoritative information, enforces authorization before generation, produces grounded and cited answers, measures its quality, exposes its behavior through observability, and only then evolves into an agentic system.**

---

## Constitution Status

**Version:** 1.0.0
**Status:** Active
**Project:** `telco-rag`

