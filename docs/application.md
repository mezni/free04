# Application Layer

## 1. Purpose

The Application Layer coordinates the execution of business use cases.

It sits between the API layer and the Domain/Infrastructure layers.

Its responsibility is to answer:

> **What does the system need to do to complete a use case?**

It does not answer:

> How does PostgreSQL store the data?

or:

> How does OpenRouter call the LLM?

or:

> How does pgvector perform similarity search?

Those responsibilities belong to infrastructure adapters.

The application layer coordinates these capabilities through explicit interfaces.

---

# 2. Architecture Position

The application layer sits here:

```text
Client
   ↓
FastAPI
   ↓
Application Services
   ↓
Domain
   ↓
Infrastructure
   ↓
PostgreSQL / pgvector / OpenRouter / filesystem
```

For RAG:

```text
API
 ↓
QueryService
 ↓
Query Processing
 ↓
Authorization
 ↓
Retrieval
 ↓
Grounding
 ↓
Generation
 ↓
Response
```

---

# 3. Application Layer Principles

The application layer follows these principles:

1. Use cases are explicit.
2. Application services coordinate, but do not contain infrastructure details.
3. Domain rules remain in the domain layer.
4. Infrastructure dependencies are accessed through interfaces.
5. Transactions are controlled at application boundaries.
6. Authorization is part of protected use-case execution.
7. Application services are independently testable.
8. API routes remain thin.
9. Infrastructure implementations remain replaceable.
10. Application workflows must be observable.
11. Long-running operations must be modeled explicitly.
12. Application services should not become a dumping ground for business logic.

---

# 4. Application Use Cases

The initial application layer should expose use cases for:

```text
Query Knowledge
Ingest Document
Get Document
List Documents
Get Incident
List Incidents
Start Evaluation
Get Evaluation
```

Future use cases include:

```text
Start Investigation
Search Support Tickets
Search Incidents
Correlate Evidence
Manage Conversation
Manage Agent Memory
Escalate to Human
```

---

# 5. Application Package Structure

The initial structure should be:

```text
src/telco_rag/application/
├── __init__.py
├── query.py
├── documents.py
├── ingestion.py
├── incidents.py
├── evaluation.py
├── dependencies.py
└── errors.py
```

As the project grows, additional modules may be introduced.

The application layer should not mirror every infrastructure component.

For example, there should not automatically be:

```text
application/postgres.py
application/openrouter.py
application/pgvector.py
```

Those belong to infrastructure.

---

# 6. Query Application Service

The most important initial service is the query service.

Conceptually:

```python
class QueryService:
    def execute(
        self,
        request: QueryRequest,
        auth: AuthorizationContext,
    ) -> QueryResponse:
        ...
```

Its responsibility is to coordinate:

```text
Query
 ↓
Query Processing
 ↓
Authorization
 ↓
Retrieval
 ↓
Evidence Selection
 ↓
Generation
 ↓
Grounding
 ↓
Response
```

It does not implement each subsystem itself.

---

# 7. Query Use Case

The query use case should follow this sequence:

```text
1. Validate request
2. Create query context
3. Process query
4. Obtain authorization context
5. Build retrieval request
6. Execute retrieval
7. Validate evidence
8. Generate answer
9. Validate grounding
10. Build response
11. Emit telemetry
```

Security checks must occur before evidence enters generation.

---

# 8. Query Service Dependencies

Conceptually:

```python
class QueryService:
    def __init__(
        self,
        query_processor: QueryProcessor,
        authorizer: Authorizer,
        retriever: Retriever,
        generator: AnswerGenerator,
        grounder: GroundingService,
    ):
        ...
```

The service depends on abstractions.

It should not directly instantiate:

```text
SQLAlchemy Session
OpenRouter Client
Embedding Client
pgvector query
```

---

# 9. Query Application Flow

Conceptually:

```python
def execute(request, auth):
    processed = query_processor.process(request)

    retrieval_request = RetrievalRequest(
        query=processed,
        authorization=auth,
    )

    evidence = retriever.retrieve(retrieval_request)

    grounded_evidence = grounder.validate_evidence(
        processed,
        evidence,
    )

    answer = generator.generate(
        processed,
        grounded_evidence,
    )

    validated = grounder.validate_answer(
        processed,
        answer,
        grounded_evidence,
    )

    return build_response(validated)
```

The exact implementation may evolve.

The important architectural rule is separation of responsibilities.

---

# 10. Application Context

Use cases may require a common execution context.

Conceptually:

```python
class ApplicationContext(BaseModel):
    request_id: str
    trace_id: str
    user_id: str
    authorization: AuthorizationContext
```

This context should be created at the application boundary.

It may carry:

* request identity
* trace information
* authenticated user
* authorization context
* tenant context in future deployments

It must not contain secrets.

---

# 11. Authorization Context

The application layer receives trusted authorization information.

Example:

```python
class AuthorizationContext(BaseModel):
    user_id: str
    roles: list[str]
    permissions: list[str]
    policy_version: str
```

The application service passes this context into protected operations.

The user must not be able to modify it through API input.

---

# 12. Authorization Boundary

Authorization should be enforced at the application use-case boundary.

Example:

```text
POST /query
    ↓
QueryService
    ↓
AuthorizationContext
    ↓
Retriever
```

Authorization must not rely exclusively on frontend checks.

Frontend controls are not security boundaries.

---

# 13. Retrieval Application Boundary

The application layer should invoke retrieval through a defined contract.

Conceptually:

```python
class Retriever(Protocol):
    def retrieve(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        ...
```

The application layer does not know whether retrieval uses:

```text
pgvector
PostgreSQL FTS
hybrid search
reranking
future search engine
```

It only knows the retrieval contract.

---

# 14. Generation Application Boundary

Generation should be accessed through an application-level abstraction.

Conceptually:

```python
class AnswerGenerator(Protocol):
    def generate(
        self,
        query: ProcessedQuery,
        evidence: list[Evidence],
    ) -> GeneratedAnswer:
        ...
```

The application layer does not directly call OpenRouter.

---

# 15. Grounding Application Boundary

Grounding validates evidence and answers.

Conceptually:

```python
class GroundingService(Protocol):
    def validate_evidence(
        self,
        query: ProcessedQuery,
        evidence: list[Evidence],
    ) -> GroundingEvidenceResult:
        ...

    def validate_answer(
        self,
        query: ProcessedQuery,
        answer: GeneratedAnswer,
        evidence: list[Evidence],
    ) -> GroundingResult:
        ...
```

The application service coordinates the process.

---

# 16. Application Errors

Application errors should be explicit.

Example:

```python
class ApplicationError(Exception):
    pass


class QueryProcessingError(ApplicationError):
    pass


class RetrievalError(ApplicationError):
    pass


class GenerationError(ApplicationError):
    pass


class GroundingError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass
```

The API layer maps these errors to HTTP responses.

---

# 17. Error Boundary

The application layer should translate low-level infrastructure failures into meaningful application failures.

Example:

```text
PostgreSQL exception
       ↓
Repository
       ↓
DatabaseError
       ↓
Application Service
       ↓
RetrievalError
       ↓
API
       ↓
503
```

Infrastructure implementation details should not leak into the API.

---

# 18. Domain Exceptions

Domain rules may produce domain exceptions.

Example:

```text
InvalidClassification
InvalidIncidentState
InvalidDocumentVersion
```

The application layer may catch and translate them into appropriate application-level outcomes.

The domain must not depend on FastAPI or HTTP exceptions.

---

# 19. Document Application Service

The document service coordinates document-related use cases.

Conceptually:

```python
class DocumentService:
    def get(
        self,
        document_id: str,
        context: ApplicationContext,
    ) -> DocumentResponse:
        ...

    def list(
        self,
        request: DocumentListRequest,
        context: ApplicationContext,
    ) -> DocumentListResponse:
        ...
```

The service:

* validates access
* retrieves domain objects
* maps them to application DTOs
* applies use-case-specific rules

---

# 20. Document Retrieval Flow

```text
GET /documents/{id}
       ↓
DocumentService
       ↓
Authorization
       ↓
DocumentRepository
       ↓
Domain Document
       ↓
Response DTO
       ↓
API
```

The repository handles persistence.

The application service handles use-case orchestration.

---

# 21. Document Creation

Document creation should be coordinated by the application layer.

Example:

```text
POST /documents
       ↓
DocumentService
       ↓
Authorization
       ↓
Validate metadata
       ↓
Create Document
       ↓
Create ingestion request
       ↓
Persist
       ↓
Return resource
```

The application layer should not parse PDF files itself.

Parsing belongs to ingestion infrastructure/components.

---

# 22. Ingestion Application Service

Ingestion is a long-running workflow.

Conceptually:

```python
class IngestionService:
    def start(
        self,
        request: IngestionRequest,
        context: ApplicationContext,
    ) -> IngestionResponse:
        ...
```

It should:

1. authenticate the request
2. authorize ingestion
3. validate metadata
4. create ingestion record
5. schedule or execute ingestion
6. return the ingestion identifier

---

# 23. Ingestion Workflow

```text
API
 ↓
IngestionService
 ↓
Create Ingestion
 ↓
Persist
 ↓
Background Worker
 ↓
Ingestion Pipeline
 ↓
Document
 ↓
Version
 ↓
Chunks
 ↓
Embeddings
 ↓
Index
 ↓
ACTIVE
```

The application layer controls the use case.

The ingestion subsystem controls document transformation.

---

# 24. Transaction Boundaries

Transactions should be aligned with meaningful application operations.

For example:

```text
Create Document
+
Create Document Version
```

may be one transaction.

Large ingestion pipelines should not necessarily use one database transaction for the entire process.

Instead:

```text
Stage 1 → transaction
Stage 2 → transaction
Stage 3 → transaction
```

This prevents long-running transactions.

---

# 25. Unit of Work

A Unit of Work abstraction may be used.

Conceptually:

```python
class UnitOfWork(Protocol):
    documents: DocumentRepository
    incidents: IncidentRepository

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...
```

The infrastructure layer provides the implementation.

The application layer controls transaction boundaries.

---

# 26. Repository Interfaces

Repositories belong conceptually to the domain/application boundary.

Example:

```python
class DocumentRepository(Protocol):
    def get(self, document_id: UUID) -> Document | None:
        ...

    def save(self, document: Document) -> None:
        ...
```

Infrastructure implements:

```text
SQLAlchemyDocumentRepository
```

The application layer depends on the interface.

---

# 27. Dependency Inversion

The application layer must depend on abstractions.

Example:

```text
Application
    ↓
DocumentRepository
    ↑
SQLAlchemyDocumentRepository
```

Not:

```text
Application
    ↓
SQLAlchemyDocumentRepository
```

This allows:

* unit testing
* database replacement
* infrastructure evolution
* alternative implementations

---

# 28. Incident Application Service

The incident service coordinates structured incident use cases.

Example:

```python
class IncidentService:
    def get(
        self,
        incident_id: str,
        context: ApplicationContext,
    ) -> IncidentResponse:
        ...

    def list(
        self,
        request: IncidentListRequest,
        context: ApplicationContext,
    ) -> IncidentListResponse:
        ...
```

The service enforces authorization before returning incident information.

---

# 29. Incident and RAG Separation

Incidents are structured operational data.

They should not automatically be treated as vector documents.

The application architecture should support both:

```text
IncidentService
     ↓
Structured incident data
```

and:

```text
QueryService
     ↓
Incident retrieval tool/index
```

Future agentic workflows can combine both.

---

# 30. Evaluation Application Service

Evaluation runs should be modeled as explicit application workflows.

Conceptually:

```python
class EvaluationService:
    def start(
        self,
        request: EvaluationRequest,
        context: ApplicationContext,
    ) -> EvaluationRunResponse:
        ...

    def get(
        self,
        run_id: str,
        context: ApplicationContext,
    ) -> EvaluationRunResponse:
        ...
```

Evaluation operations normally require elevated authorization.

---

# 31. Evaluation Workflow

```text
API
 ↓
EvaluationService
 ↓
Load Dataset
 ↓
Create Evaluation Run
 ↓
Execute Cases
 ↓
Collect Results
 ↓
Calculate Metrics
 ↓
Persist Results
 ↓
Complete Run
```

The application service coordinates the lifecycle.

Evaluation implementation remains in the evaluation subsystem.

---

# 32. Application DTOs

The application layer may define DTOs between API and domain.

Example:

```text
application/
    dto/
        query.py
        documents.py
        incidents.py
```

However, this should only be introduced when it provides meaningful separation.

Small projects should avoid unnecessary DTO duplication.

---

# 33. Domain Models vs DTOs

Do not expose domain entities directly through API responses.

Example:

```text
Domain Document
       ↓
Application mapping
       ↓
DocumentResponse
       ↓
FastAPI
```

This prevents API concerns from leaking into domain models.

---

# 34. Application Mapping

Mapping should be explicit.

Example:

```python
def to_document_response(
    document: Document,
) -> DocumentResponse:
    return DocumentResponse(
        id=str(document.id),
        title=document.title,
        document_type=document.document_type.value,
        classification=document.classification.value,
    )
```

Mapping functions should remain simple.

---

# 35. Application Services Should Not Become God Objects

Avoid a service such as:

```text
TelcoRagService
```

containing:

* query
* ingestion
* documents
* incidents
* evaluation
* agents
* security
* configuration

Instead use focused services:

```text
QueryService
DocumentService
IngestionService
IncidentService
EvaluationService
```

Each service should represent meaningful application capabilities.

---

# 36. Query Orchestration vs Domain Logic

The application service may coordinate:

```text
query processor
retriever
generator
grounding
```

But it should not implement their algorithms.

Bad:

```python
class QueryService:
    # 500 lines of retrieval scoring
    # embedding logic
    # prompt construction
    # citation validation
```

Preferred:

```python
class QueryService:
    def execute(...):
        processed = self.query_processor.process(...)
        evidence = self.retriever.retrieve(...)
        answer = self.generator.generate(...)
        return self.grounder.validate(...)
```

---

# 37. Application Service State

Application services should normally be stateless.

State belongs in:

* database
* domain entities
* workflow state
* cache
* durable job records

Avoid storing request-specific state in singleton service objects.

---

# 38. Long-Running Workflows

Long-running operations should use explicit workflow state.

Example:

```text
Ingestion
    ↓
QUEUED
    ↓
RUNNING
    ↓
COMPLETED
```

or:

```text
FAILED
```

The application layer should provide commands to start, inspect, and potentially cancel workflows.

---

# 39. Idempotency

Application services should define idempotency behavior for operations where duplicate requests are possible.

Example:

```text
POST /ingestion
Idempotency-Key: abc123
```

The application layer determines:

```text
already processed?
        ↓
return existing ingestion
```

Infrastructure may persist the idempotency record.

---

# 40. Retry Policy

Retries should not be implemented blindly inside application services.

Retryable failures should be explicitly classified.

Example:

```text
LLM timeout
    → retryable

Invalid document metadata
    → not retryable

Authorization denied
    → not retryable

Database connection failure
    → potentially retryable
```

Retry policy should remain bounded and observable.

---

# 41. Application Timeouts

Use cases should have explicit time budgets.

For example:

```text
Query
 ├── query processing timeout
 ├── retrieval timeout
 ├── generation timeout
 └── grounding timeout
```

The application service should enforce an overall deadline.

---

# 42. Cancellation

Application services should support cancellation where the underlying workflow supports it.

For example:

```text
Client
 ↓
Request cancellation
 ↓
Application Context
 ↓
Retrieval / Generation
 ↓
Cancel
```

Cancellation must not leave resources in inconsistent states.

---

# 43. Observability

Every application use case should create meaningful telemetry.

Example:

```text
QueryService.execute
DocumentService.get
IngestionService.start
IncidentService.get
EvaluationService.start
```

Each operation should record:

```text
request_id
trace_id
operation
status
latency
error_type
```

Sensitive data must not be included unnecessarily.

---

# 44. Application Metrics

Initial metrics:

```text
application_use_case_total
application_use_case_failures_total
application_use_case_duration_seconds
```

Useful labels:

```text
use_case
status
error_type
```

Avoid high-cardinality labels such as:

```text
query text
document content
user-controlled identifiers
```

---

# 45. Application Logging

Application logs should describe workflow decisions.

Good:

```text
query retrieval completed
strategy=hybrid
candidate_count=20
authorized_count=8
```

Bad:

```text
full document content
full authorization token
full customer record
```

Logging should support diagnosis without leaking sensitive information.

---

# 46. Application Configuration

Application behavior may depend on configuration.

Example:

```yaml
application:
  query:
    timeout_seconds: 30

  ingestion:
    timeout_seconds: 300

  evaluation:
    max_concurrency: 4
```

Configuration should be injected rather than loaded directly throughout services.

---

# 47. Dependency Container

Application dependencies should be assembled in one place.

Conceptually:

```text
src/telco_rag/api/dependencies.py
```

or a dedicated composition root.

The composition root creates:

```text
Repositories
Services
Retrievers
Generators
Grounding
Configuration
```

This avoids hidden global dependencies.

---

# 48. Composition Root

The architecture should have a clear composition root.

Example:

```text
main.py
   ↓
create_application()
   ↓
create_dependencies()
   ↓
Application Services
   ↓
Infrastructure Adapters
```

The composition root is the place where concrete implementations are connected to abstractions.

---

# 49. Testing Application Services

Application services should be testable without:

* PostgreSQL
* pgvector
* OpenRouter
* FastAPI
* Docker

Use fake implementations.

Example:

```python
class FakeRetriever:
    def retrieve(self, request):
        return expected_evidence
```

Then:

```text
QueryService
   ↓
FakeQueryProcessor
FakeRetriever
FakeGenerator
FakeGrounder
```

This makes orchestration tests fast.

---

# 50. Application Unit Tests

Examples:

```text
test_query_service_success
test_query_service_authorization_failure
test_query_service_retrieval_failure
test_query_service_generation_failure
test_query_service_grounding_abstention
test_document_service_access_denied
test_ingestion_service_creates_job
test_incident_service_access_control
```

The tests should verify use-case behavior rather than implementation details.

---

# 51. Application Integration Tests

Integration tests should connect application services to real infrastructure selectively.

Examples:

```text
QueryService + PostgreSQL
IngestionService + PostgreSQL
DocumentService + PostgreSQL
IncidentService + PostgreSQL
```

LLM calls should normally use a test/fake provider unless the test is explicitly an evaluation or provider integration test.

---

# 52. Application Security Tests

Important invariants:

```text
unauthorized query → no retrieval evidence exposed

unauthorized document → repository result rejected

unauthorized incident → no response

user-supplied role → ignored

security context missing → protected operation rejected
```

---

# 53. Application and Transactions

Application services should define transaction ownership.

Example:

```text
DocumentService.create
    ↓
UnitOfWork
    ↓
DocumentRepository.save
    ↓
VersionRepository.save
    ↓
commit
```

The API should not call:

```python
session.commit()
```

directly.

---

# 54. Application and Events

Future application events may include:

```text
DocumentIngested
DocumentVersionActivated
IncidentCreated
QueryCompleted
EvaluationCompleted
```

Events may be used later for:

* metrics
* audit
* notifications
* asynchronous processing
* indexing

Event-driven architecture should be introduced only when justified.

---

# 55. Domain Events vs Integration Events

Domain events describe meaningful domain changes.

Example:

```text
DocumentVersionActivated
```

Integration events communicate with external systems.

Example:

```text
DocumentIndexedNotification
```

These concepts should remain distinct.

---

# 56. Audit Events

Security-sensitive operations may require audit records.

Examples:

```text
document accessed
restricted document denied
ingestion started
ingestion completed
evaluation started
agent escalation requested
```

Audit records should be separate from ordinary application logs.

---

# 57. Application and Caching

Caching may be introduced later.

Candidates:

```text
query normalization
query classification
document metadata
retrieval results
```

Caching must respect:

* authorization
* document version
* configuration
* prompt version
* retrieval version

The application layer should define when a cached result is acceptable.

---

# 58. Application and Agentic RAG

Future agentic workflows should be application use cases.

Example:

```python
class InvestigationService:
    def investigate(
        self,
        request: InvestigationRequest,
        context: ApplicationContext,
    ) -> InvestigationResponse:
        ...
```

The service coordinates:

```text
Agent
 ↓
Tools
 ↓
RAG
 ↓
Structured data
 ↓
Memory
 ↓
Human escalation
```

The agent itself should not own authentication or authorization.

---

# 59. Agent Security Boundary

Agent tools must receive authorization context from the application layer.

Example:

```text
Application Context
       ↓
Agent
       ↓
Tool
       ↓
Authorization
       ↓
Data
```

The agent cannot invent:

```text
ADMIN
NETWORK_ENGINEER
FULL_ACCESS
```

---

# 60. Application and Memory

Future agent memory should be treated as an application capability.

Possible services:

```text
ConversationService
MemoryService
InvestigationService
```

Memory must follow the same security and privacy rules as other enterprise data.

---

# 61. Application API Stability

API routes may change independently from application services.

For example:

```text
/api/v1/query
```

could remain stable while:

```text
QueryService
```

changes internally.

This separation is a major reason for introducing the application layer.

---

# 62. Application Layer Anti-Patterns

Avoid:

### Database-aware services

```python
service.session.query(...)
```

### HTTP-aware domain services

```python
service.raise HTTPException(...)
```

### LLM-aware API routes

```python
router → OpenRouter()
```

### God services

```python
TelcoService
```

### Hidden global state

```python
global db
global llm
```

### Unbounded retries

```python
while True:
    retry()
```

### Security after retrieval

```text
retrieve everything
→ filter later
```

Security must be enforced before unauthorized evidence reaches generation.

---

# 63. Recommended Initial Interfaces

The initial application layer should depend on interfaces resembling:

```text
QueryProcessor
Retriever
AnswerGenerator
GroundingService
DocumentRepository
IncidentRepository
IngestionPipeline
EvaluationRunner
UnitOfWork
Authorizer
```

Concrete implementations belong outside the application layer.

---

# 64. Initial Dependency Graph

```text
                    ┌──────────────────┐
                    │   FastAPI API    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Application      │
                    │ Services         │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │   Domain   │ │ Interfaces │ │ Workflows  │
       └────────────┘ └──────┬─────┘ └────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Infrastructure   │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
       PostgreSQL          pgvector        OpenRouter
```

---

# 65. Query Dependency Graph

The query use case is the most important application workflow.

```text
QueryService
     │
     ├── QueryProcessor
     │
     ├── Authorizer
     │
     ├── Retriever
     │
     ├── GroundingService
     │
     └── AnswerGenerator
```

Each dependency can be replaced independently during testing.

---

# 66. Query Sequence

```text
Client
  │
  │ POST /query
  ▼
API
  │
  ▼
QueryService
  │
  ├── Process Query
  │
  ├── Validate Authorization
  │
  ├── Retrieve Evidence
  │
  ├── Validate Evidence
  │
  ├── Generate Answer
  │
  ├── Validate Grounding
  │
  └── Build Response
  │
  ▼
API
  │
  ▼
Client
```

---

# 67. Ingestion Sequence

```text
Client
  │
  │ POST /ingestion
  ▼
IngestionService
  │
  ├── Authenticate
  ├── Authorize
  ├── Validate Metadata
  ├── Create Ingestion Record
  └── Schedule Workflow
          │
          ▼
    Ingestion Pipeline
          │
          ├── Parse
          ├── Clean
          ├── Metadata
          ├── Chunk
          ├── Embed
          └── Index
```

---

# 68. Application Layer Configuration

Application configuration should include:

```yaml
application:
  query:
    timeout_seconds: 30
    max_retries: 1

  ingestion:
    timeout_seconds: 300

  evaluation:
    timeout_seconds: 3600

  security:
    require_authorization: true
```

Security defaults should be restrictive.

---

# 69. Definition of Done

The Application Layer is complete for the initial platform when:

* [ ] Use cases are explicitly defined.
* [ ] API routes delegate to application services.
* [ ] QueryService exists.
* [ ] DocumentService exists.
* [ ] IngestionService exists.
* [ ] IncidentService exists.
* [ ] EvaluationService exists.
* [ ] Application dependencies use abstractions.
* [ ] Authorization context is propagated.
* [ ] Transaction boundaries are defined.
* [ ] Unit of Work is available where needed.
* [ ] Repository interfaces are defined.
* [ ] Infrastructure details are hidden.
* [ ] Application errors are defined.
* [ ] Long-running workflows are modeled.
* [ ] Idempotency is supported where appropriate.
* [ ] Retry policies are bounded.
* [ ] Application telemetry exists.
* [ ] Application services are unit-testable without infrastructure.
* [ ] Integration tests cover critical use cases.
* [ ] Security invariants are tested.
* [ ] Composition root assembles concrete implementations.

---

# 70. Final Application Layer Rule

The Application Layer is the **orchestrator of use cases**.

It should coordinate:

```text
Authentication
     ↓
Authorization
     ↓
Domain Operations
     ↓
Retrieval
     ↓
Generation
     ↓
Grounding
     ↓
Persistence
     ↓
Events
```

without becoming responsible for the implementation details of those systems.

The fundamental rule is:

> **Application services coordinate what the system does; domain objects define what is valid; infrastructure defines how external resources are accessed.**

