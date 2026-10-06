# API Design

## 1. Purpose

The API layer exposes the capabilities of the `telco-rag` platform to external clients.

The initial API is implemented with FastAPI and Pydantic.

The API provides access to:

* health and readiness
* RAG queries
* documents
* ingestion
* incidents
* future evaluation operations
* future agentic workflows

The API is an application boundary.

It must not contain domain logic, retrieval algorithms, database queries, or LLM-specific implementation details.

---

# 2. API Architecture

The API follows:

```text
Client
  ↓
FastAPI
  ↓
API Route
  ↓
Application Service
  ↓
Domain
  ↓
Infrastructure
```

For a RAG query:

```text
Client
  ↓
POST /api/v1/query
  ↓
Authentication
  ↓
Authorization
  ↓
Query Processing
  ↓
Retrieval
  ↓
Grounding
  ↓
Generation
  ↓
Response Validation
  ↓
Client
```

---

# 3. API Principles

The API must follow these principles:

1. Version all public APIs.
2. Validate all external input.
3. Use Pydantic request and response models.
4. Never expose database models directly.
5. Never expose infrastructure-specific objects.
6. Never expose LLM provider details unnecessarily.
7. Enforce authentication before protected operations.
8. Enforce authorization before accessing protected resources.
9. Never send unauthorized evidence to the LLM.
10. Return stable error structures.
11. Support request tracing.
12. Keep API operations observable.
13. Keep long-running operations asynchronous where appropriate.
14. Preserve backward compatibility within a major API version.

---

# 4. API Versioning

Initial API version:

```text
/api/v1
```

Example:

```text
/api/v1/query
/api/v1/documents
/api/v1/ingestion
/api/v1/incidents
```

Future incompatible changes should introduce:

```text
/api/v2
```

The API version must not be coupled to internal package versions.

---

# 5. Base URL

Development:

```text
http://localhost:8000
```

Production deployment may use:

```text
https://<api-domain>
```

The actual production URL is environment-specific.

---

# 6. Content Type

Requests containing JSON use:

```http
Content-Type: application/json
```

Responses use:

```http
Content-Type: application/json
```

File uploads use:

```http
multipart/form-data
```

---

# 7. Request IDs

Every request should have a request identifier.

Clients may provide:

```http
X-Request-ID: <request-id>
```

If absent, the API generates one.

The request ID must be included in the response:

```http
X-Request-ID: <request-id>
```

The request ID must propagate through:

```text
API
 ↓
Application
 ↓
Query
 ↓
Security
 ↓
Retrieval
 ↓
Generation
 ↓
LLM
```

---

# 8. Authentication

Protected endpoints require authentication.

The initial API contract should support bearer authentication.

Example:

```http
Authorization: Bearer <token>
```

Authentication implementation is infrastructure-dependent.

The API layer receives an authenticated principal such as:

```python
class AuthenticatedUser(BaseModel):
    user_id: str
    roles: list[str]
```

The actual authentication mechanism may evolve later.

---

# 9. Authorization

Authentication answers:

> Who is the caller?

Authorization answers:

> What is the caller allowed to access?

Authorization must occur before protected data is accessed.

The authorization context may include:

```python
class AuthorizationContext(BaseModel):
    user_id: str
    roles: list[str]
    permissions: list[str]
    policy_version: str
```

The API must not allow clients to submit their own authorization context.

For example, clients must not be able to send:

```json
{
  "role": "ADMIN"
}
```

and thereby become administrators.

---

# 10. API Error Model

All API errors should use a consistent structure.

Example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request is invalid.",
    "details": []
  },
  "request_id": "req-123"
}
```

Conceptual Pydantic model:

```python
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[dict] = []
```

The actual HTTP response may wrap this model with request metadata.

---

# 11. Error Codes

Initial error codes:

```text
VALIDATION_ERROR
AUTHENTICATION_REQUIRED
AUTHENTICATION_FAILED
AUTHORIZATION_DENIED
RESOURCE_NOT_FOUND
CONFLICT
INGESTION_FAILED
QUERY_FAILED
RETRIEVAL_FAILED
GENERATION_FAILED
GROUNDING_FAILED
RATE_LIMITED
DEPENDENCY_UNAVAILABLE
INTERNAL_ERROR
```

Error codes should remain stable even if internal implementations change.

---

# 12. HTTP Status Codes

Recommended mapping:

| Status | Meaning                                  |
| ------ | ---------------------------------------- |
| 200    | Successful request                       |
| 201    | Resource created                         |
| 202    | Accepted for asynchronous processing     |
| 204    | Successful request with no response body |
| 400    | Invalid request                          |
| 401    | Authentication required/failed           |
| 403    | Authorization denied                     |
| 404    | Resource not found                       |
| 409    | Resource conflict                        |
| 422    | Pydantic validation failure              |
| 429    | Rate limited                             |
| 500    | Internal server error                    |
| 502    | Upstream dependency failure              |
| 503    | Service unavailable                      |
| 504    | Upstream timeout                         |

---

# 13. Health Endpoints

Health endpoints should be lightweight and must not require authentication.

## GET `/health`

Returns application health.

Example:

```json
{
  "status": "ok"
}
```

The endpoint should not perform expensive dependency checks.

---

# 14. Readiness Endpoint

## GET `/ready`

Determines whether the service is ready to receive traffic.

Example:

```json
{
  "status": "ready",
  "dependencies": {
    "database": "ok",
    "vector_store": "ok"
  }
}
```

Readiness may verify:

* PostgreSQL connectivity
* pgvector availability
* required configuration
* critical infrastructure dependencies

LLM availability should only be considered mandatory if the deployment requires it for readiness.

---

# 15. Version Endpoint

## GET `/api/v1/version`

Returns application version information.

Example:

```json
{
  "service": "telco-rag",
  "version": "0.1.0",
  "api_version": "v1"
}
```

Additional build metadata may be exposed in controlled environments.

---

# 16. Query API

The primary API operation is the RAG query endpoint.

## POST `/api/v1/query`

Purpose:

Submit a question and receive a grounded answer.

Request:

```python
class QueryRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    filters: QueryFilters | None = None
    top_k: int = 10
```

The authenticated user is derived from the authentication layer.

The request must not contain:

```text
user_id
roles
permissions
classification_override
```

These values come from trusted application state.

---

# 17. Query Request Example

```json
{
  "query": "Why did the 5G service fail in Ontario last Tuesday?",
  "conversation_id": "conv-123",
  "filters": {
    "technology": "5G",
    "region": "Ontario"
  },
  "top_k": 10
}
```

---

# 18. Query Validation

The API should reject:

* empty queries
* excessively large queries
* invalid filter values
* invalid `top_k`
* malformed conversation IDs
* unsupported parameters

Example constraints:

```python
query: str = Field(min_length=1, max_length=10000)
top_k: int = Field(default=10, ge=1, le=100)
```

Exact limits should be configuration-driven.

---

# 19. Query Response

Conceptually:

```python
class QueryResponse(BaseModel):
    query_id: str
    answer: str

    citations: list[Citation]

    grounded: bool
    abstained: bool

    retrieval: RetrievalSummary
    metadata: QueryMetadata
```

Example:

```json
{
  "query_id": "qry-123",
  "answer": "The outage was associated with...",
  "citations": [
    {
      "citation_id": "cite-1",
      "document_id": "doc-123",
      "version_id": "ver-4",
      "chunk_id": "chunk-92",
      "source_location": "Section 4.2"
    }
  ],
  "grounded": true,
  "abstained": false,
  "retrieval": {
    "strategy": "hybrid",
    "result_count": 6
  }
}
```

---

# 20. Query Response Security

The response must never contain:

* unauthorized document content
* unauthorized citations
* security policy internals
* access-control implementation details
* hidden system prompts
* provider credentials
* internal infrastructure secrets

If evidence was denied, the API should not reveal the contents of that evidence.

---

# 21. Query Diagnostics

Detailed retrieval diagnostics should not be returned to ordinary users by default.

Possible internal diagnostics include:

```text
candidate_count
authorized_count
reranking_used
retrieval_latency
grounding_score
```

These may be exposed through:

* admin endpoints
* debugging mode
* internal telemetry
* evaluation APIs

They should not expose sensitive content.

---

# 22. Streaming Responses

Streaming may be introduced later.

Potential endpoint:

```text
POST /api/v1/query/stream
```

However, streaming must not bypass:

* grounding
* citation validation
* authorization
* output validation

The preferred initial implementation is a complete validated response.

Streaming can be added once answer validation semantics are well established.

---

# 23. Conversation API

Future conversational support may introduce:

## POST `/api/v1/conversations`

Creates a conversation.

## GET `/api/v1/conversations/{conversation_id}`

Retrieves conversation metadata.

## DELETE `/api/v1/conversations/{conversation_id}`

Deletes or deactivates a conversation.

Conversation history must follow the same authorization boundaries as other resources.

---

# 24. Document API

The document API provides document metadata access.

## GET `/api/v1/documents`

Lists documents available to the authenticated user.

Supported filters may include:

```text
document_type
classification
technology
region
product
service
status
```

Example:

```text
GET /api/v1/documents?technology=5G&region=Ontario
```

Security filters are always applied.

---

# 25. Document List Response

Example:

```json
{
  "items": [
    {
      "id": "doc-123",
      "title": "5G Registration Runbook",
      "document_type": "RUNBOOK",
      "classification": "INTERNAL",
      "status": "ACTIVE",
      "updated_at": "2026-09-15T10:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

The API should return metadata appropriate to the caller's permissions.

---

# 26. Document Detail

## GET `/api/v1/documents/{document_id}`

Returns document metadata.

Example:

```json
{
  "id": "doc-123",
  "title": "5G Registration Runbook",
  "document_type": "RUNBOOK",
  "classification": "INTERNAL",
  "status": "ACTIVE",
  "versions": [
    {
      "id": "ver-4",
      "version": "4",
      "created_at": "2026-09-15T10:00:00Z"
    }
  ]
}
```

The endpoint must not return content the caller is not authorized to access.

---

# 27. Document Version API

## GET `/api/v1/documents/{document_id}/versions`

Returns versions accessible to the user.

Version information should include:

```text
version_id
version
created_at
updated_at
status
effective_at
```

Historical versions may require additional authorization.

---

# 28. Document Creation

Document creation should normally be performed through ingestion.

Therefore the initial API should avoid exposing unrestricted direct document creation.

If required:

## POST `/api/v1/documents`

should:

* authenticate caller
* authorize operation
* validate metadata
* validate classification
* create document metadata
* create an ingestion job

It should not directly manipulate vector indexes.

---

# 29. Ingestion API

Ingestion is potentially long-running.

## POST `/api/v1/ingestion`

Accepts a document or ingestion request.

Example response:

```json
{
  "ingestion_id": "ing-123",
  "status": "ACCEPTED"
}
```

HTTP status:

```text
202 Accepted
```

---

# 30. Ingestion Status

## GET `/api/v1/ingestion/{ingestion_id}`

Example:

```json
{
  "ingestion_id": "ing-123",
  "status": "EMBEDDING",
  "document_id": "doc-123",
  "version_id": "ver-4",
  "progress": {
    "chunks": 120,
    "embedded": 80
  }
}
```

---

# 31. Ingestion States

The API should reflect the ingestion state machine:

```text
DISCOVERED
VALIDATING
PARSING
CLEANING
METADATA_READY
CHUNKING
EMBEDDING
INDEXING
VALIDATING_INDEX
ACTIVE
FAILED
QUARANTINED
```

The API should not allow clients to arbitrarily transition states.

State transitions belong to the ingestion application service.

---

# 32. Ingestion Cancellation

Future endpoint:

## POST `/api/v1/ingestion/{ingestion_id}/cancel`

Cancellation must be authorized.

A cancellation request should be idempotent.

---

# 33. Incident API

Incidents are important structured telecom data.

## GET `/api/v1/incidents`

Supports filters such as:

```text
technology
region
severity
status
start_date
end_date
```

Example:

```text
GET /api/v1/incidents?severity=CRITICAL&status=RESOLVED
```

Authorization must be applied before results are returned.

---

# 34. Incident Detail

## GET `/api/v1/incidents/{incident_id}`

Example:

```json
{
  "id": "INC-2026-00142",
  "title": "5G Registration Failure",
  "severity": "HIGH",
  "status": "RESOLVED",
  "technology": "5G",
  "region": "Ontario",
  "started_at": "2026-09-20T14:32:00Z",
  "resolved_at": "2026-09-20T17:15:00Z"
}
```

Incident content must respect authorization.

---

# 35. Incident Relationships

The API may expose related resources:

```text
GET /api/v1/incidents/{incident_id}/tickets
GET /api/v1/incidents/{incident_id}/documents
```

These relationships are useful for future agentic investigation workflows.

---

# 36. Evaluation API

Evaluation endpoints are primarily administrative/internal.

Future endpoints may include:

## POST `/api/v1/evaluations/runs`

Starts an evaluation run.

## GET `/api/v1/evaluations/runs/{run_id}`

Returns evaluation status.

## GET `/api/v1/evaluations/runs/{run_id}/results`

Returns evaluation results.

These endpoints require elevated authorization.

---

# 37. Evaluation Request

Example:

```json
{
  "dataset": "baseline-v1",
  "evaluation_type": "full"
}
```

The system should record:

```text
dataset version
model
prompt version
retrieval version
embedding model
reranker
configuration
git commit
timestamp
```

---

# 38. Agent API

Agentic RAG is a future capability.

A future endpoint may be:

## POST `/api/v1/agents/investigate`

Example:

```json
{
  "question": "Investigate the repeated 5G registration failures in Ontario."
}
```

The agent may use controlled tools such as:

```text
knowledge_search
incident_search
ticket_search
product_search
```

The agent API must not automatically receive unrestricted production capabilities.

---

# 39. Agent Safety Boundary

The initial agentic API must not allow autonomous production network changes.

The future agent may:

* investigate
* retrieve evidence
* correlate incidents
* summarize findings
* recommend actions
* request human escalation

It should not autonomously:

* modify network configuration
* restart production services
* change routing
* disable security controls
* execute destructive operations

---

# 40. Pagination

Collection endpoints should use consistent pagination.

Initial query parameters:

```text
page
page_size
```

Example:

```text
GET /api/v1/documents?page=1&page_size=20
```

Recommended limits:

```python
page_size: int = Field(default=20, ge=1, le=100)
```

Cursor pagination may be introduced later for very large datasets.

---

# 41. Filtering

Filtering should use explicit query parameters.

Example:

```text
GET /api/v1/documents
    ?technology=5G
    &region=Ontario
    &document_type=RUNBOOK
```

Filters must be validated against domain enums where appropriate.

Unknown filters should not silently be ignored.

---

# 42. Sorting

Collection APIs may support controlled sorting.

Example:

```text
?sort=updated_at
&order=desc
```

Only approved sort fields should be allowed.

Clients must not supply arbitrary SQL expressions.

---

# 43. Idempotency

Operations that create asynchronous resources should support idempotency where appropriate.

Example:

```http
Idempotency-Key: <unique-key>
```

This is particularly useful for:

* ingestion requests
* evaluation runs
* future agent workflows

The idempotency implementation belongs to the application/infrastructure layers.

---

# 44. Rate Limiting

The API should support rate limiting.

Limits should differ by operation.

Example categories:

```text
query
ingestion
evaluation
agent
```

LLM-backed endpoints may require stricter limits because of:

* token cost
* provider rate limits
* latency
* resource consumption

A rate-limit response should return:

```text
429 Too Many Requests
```

---

# 45. Request Size Limits

The API must enforce request size limits.

This protects against:

* accidental oversized requests
* denial-of-service attempts
* excessive LLM token consumption

File uploads should have separate configurable limits.

---

# 46. File Upload Security

Uploaded documents are untrusted.

The API must validate:

* file size
* file type
* extension
* content type
* file integrity

The API must not trust the filename or MIME type alone.

Files should be passed into the ingestion validation pipeline.

---

# 47. API Security Headers

Production deployment should use appropriate security headers.

Examples include:

```text
X-Content-Type-Options
X-Frame-Options
Strict-Transport-Security
```

Exact headers depend on deployment architecture.

TLS termination may occur at:

```text
load balancer
reverse proxy
API gateway
```

---

# 48. CORS

CORS must be explicitly configured.

Development may allow the local frontend.

Production should allow only approved origins.

Example configuration:

```yaml
api:
  cors:
    allowed_origins:
      - http://localhost:3000
```

Production values must be environment-specific.

Wildcard origins should not be used for authenticated production applications without a specific security rationale.

---

# 49. API Logging

API logs should contain:

```text
request_id
trace_id
method
path
status_code
latency
authenticated_user_reference
error_code
```

Do not log:

* bearer tokens
* passwords
* API keys
* unrestricted query content
* document content
* LLM prompts containing sensitive information

---

# 50. API Metrics

Initial metrics:

```text
http_requests_total
http_request_duration_seconds
http_requests_in_flight
http_errors_total
```

Useful dimensions:

```text
method
route
status
```

Avoid raw URLs or user-controlled values as metric labels.

---

# 51. API Tracing

API requests should create an OpenTelemetry span.

Example:

```text
HTTP Request
    ↓
Query Application Service
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
```

The trace ID should be propagated to downstream infrastructure.

---

# 52. API and Application Boundary

Routes should remain thin.

Bad:

```python
@router.post("/query")
def query(request):
    # database queries
    # embedding generation
    # vector search
    # prompt creation
    # LLM call
    # citation validation
```

Preferred:

```python
@router.post("/query")
def query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    return service.execute(request)
```

Business logic belongs in application/domain services.

---

# 53. API and Domain Boundary

The API should use API-specific DTOs.

Do not expose domain entities directly.

Example:

```text
API Request
    ↓
QueryRequest
    ↓
Application Command
    ↓
Domain Model
```

and:

```text
Domain Result
    ↓
Application Result
    ↓
QueryResponse
```

This protects the domain from API evolution.

---

# 54. Pydantic Models

Pydantic v2 is the validation boundary for API input/output.

Example:

```python
class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    conversation_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=100)
```

Models should reject invalid values early.

---

# 55. OpenAPI

FastAPI automatically generates OpenAPI documentation.

Development endpoints:

```text
/docs
/redoc
/openapi.json
```

Production exposure should be configurable.

Sensitive internal endpoints should not automatically become public merely because they exist in OpenAPI.

---

# 56. API Documentation

Each endpoint should document:

* purpose
* authentication requirements
* authorization requirements
* request schema
* response schema
* error responses
* examples
* rate limits where relevant
* idempotency behavior where relevant

OpenAPI descriptions should remain synchronized with the implementation.

---

# 57. API Testing

Tests should be separated into:

```text
tests/
├── unit/
└── integration/
```

API integration tests should verify:

```text
authentication
authorization
validation
HTTP status codes
response schemas
error schemas
request IDs
security filtering
query execution
ingestion operations
incident access
```

---

# 58. Security Tests

Important API security tests include:

```text
unauthenticated request → 401

authenticated unauthorized request → 403

authorized request → 200

invalid token → 401

user cannot override role → rejected

user cannot bypass classification → rejected

restricted evidence never appears in response

restricted evidence never reaches generation
```

---

# 59. API Contract Testing

The API contract should be tested independently of internal implementation.

For each public endpoint verify:

```text
request schema
response schema
status codes
error schema
required headers
authorization behavior
```

This allows internal components to evolve without unexpectedly breaking clients.

---

# 60. Dependency Failures

The API must translate infrastructure failures into controlled responses.

Example:

```text
PostgreSQL unavailable
        ↓
503 Service Unavailable
```

LLM provider timeout:

```text
LLM timeout
        ↓
controlled generation error
        ↓
502/503 depending on policy
```

Internal stack traces must not be returned to clients.

---

# 61. Query Failure Semantics

A RAG query may fail at:

```text
query processing
retrieval
generation
grounding
```

The API should distinguish these where useful.

Example:

```json
{
  "error": {
    "code": "RETRIEVAL_FAILED",
    "message": "Knowledge retrieval is temporarily unavailable.",
    "details": []
  },
  "request_id": "req-123"
}
```

Internal details remain in logs and traces.

---

# 62. Graceful Degradation

Where possible, the API should support controlled degradation.

Examples:

```text
Reranker unavailable
    ↓
Hybrid retrieval without reranking
```

```text
LLM unavailable
    ↓
Return controlled service error
```

```text
Optional query rewriting unavailable
    ↓
Use normalized query
```

Degradation must never weaken security.

---

# 63. API Configuration

Example:

```yaml
api:
  host: 0.0.0.0
  port: 8000

  limits:
    max_query_length: 10000
    max_top_k: 100
    max_page_size: 100

  cors:
    allowed_origins: []

  docs:
    enabled: true

  rate_limit:
    enabled: true
```

Environment-specific configuration belongs under:

```text
config/profiles/
```

Secrets belong in environment variables or a secret-management system.

---

# 64. API Package Structure

The API package follows:

```text
src/telco_rag/api/
├── __init__.py
├── app.py
├── dependencies.py
└── routes/
    ├── health.py
    ├── query.py
    ├── documents.py
    ├── ingestion.py
    └── incidents.py
```

Future routes may include:

```text
evaluations.py
conversations.py
agents.py
```

---

# 65. Application Service Interfaces

The API should depend on application services.

Examples:

```python
class QueryService:
    def execute(
        self,
        request: QueryRequest,
        auth: AuthorizationContext,
    ) -> QueryResponse:
        ...
```

```python
class IngestionService:
    def start(
        self,
        request: IngestionRequest,
        auth: AuthorizationContext,
    ) -> IngestionResponse:
        ...
```

```python
class IncidentService:
    def get(
        self,
        incident_id: str,
        auth: AuthorizationContext,
    ) -> IncidentResponse:
        ...
```

The exact interfaces may evolve during implementation.

---

# 66. API Dependency Injection

FastAPI dependency injection should provide:

* authenticated user
* authorization context
* application services
* database/session dependencies
* configuration
* request metadata

Example:

```python
@router.post("/query")
def query(
    request: QueryRequest,
    auth: AuthorizationContext = Depends(get_auth_context),
    service: QueryService = Depends(get_query_service),
):
    return service.execute(request, auth)
```

Dependencies must not contain large business workflows.

---

# 67. API Transactions

API routes should not manually manage complex database transactions.

Transaction boundaries belong to application/infrastructure services.

For example:

```text
API
 ↓
Application Service
 ↓
Unit of Work
 ↓
Repository
 ↓
Database
```

This makes transaction behavior testable.

---

# 68. API and Background Jobs

Long-running tasks should not block HTTP requests.

Candidates include:

* document ingestion
* embedding generation
* large evaluations
* index rebuilding
* future agent investigations

Initial architecture may use a simple background mechanism.

A production deployment may later introduce:

```text
Celery
RQ
Arq
Temporal
cloud queue
```

The choice should be based on operational requirements rather than introduced prematurely.

---

# 69. API Observability Context

Every API request should carry:

```text
request_id
trace_id
user_reference
route
```

Downstream operations should inherit the same trace context.

This allows an operator to follow:

```text
HTTP request
   ↓
query processing
   ↓
security
   ↓
retrieval
   ↓
database
   ↓
LLM
   ↓
grounding
```

---

# 70. API Performance Targets

Initial targets should be measured rather than assumed.

The system should track:

```text
P50 latency
P90 latency
P95 latency
P99 latency
```

Separate measurements should be maintained for:

```text
health
documents
incidents
query
ingestion
evaluation
```

LLM-backed operations will naturally have different latency profiles.

---

# 71. API Cost Awareness

The API should expose enough internal telemetry to calculate:

```text
requests
LLM calls
input tokens
output tokens
embedding tokens
estimated cost
```

Cost should normally remain internal rather than being returned to ordinary users.

Administrative dashboards may expose aggregated cost information later.

---

# 72. API Resource Naming

Use plural nouns for collections:

```text
/documents
/incidents
/evaluations
/conversations
```

Use singular action-oriented paths only when an operation is not naturally represented as a resource.

Examples:

```text
/query
/ingestion
```

Future agent operations may use:

```text
/agents/investigate
```

because investigation represents a workflow rather than a persistent resource in the initial design.

---

# 73. API Naming Conventions

Use:

```text
snake_case
```

for JSON fields.

Example:

```json
{
  "document_type": "RUNBOOK",
  "created_at": "2026-09-15T10:00:00Z"
}
```

Use ISO 8601 timestamps in UTC.

Example:

```text
2026-09-15T10:00:00Z
```

---

# 74. API Compatibility

Within `/api/v1`:

* avoid removing fields
* avoid changing field meaning
* avoid changing enum meanings
* avoid changing response semantics
* add optional fields when possible

Breaking changes require a new API version.

---

# 75. API Security Invariants

The API must guarantee:

1. Protected endpoints require authentication.
2. Authorization is evaluated server-side.
3. Clients cannot provide their own roles.
4. Clients cannot override classification restrictions.
5. Security filters cannot be disabled by query parameters.
6. Unauthorized evidence never reaches generation.
7. Unauthorized evidence never appears in responses.
8. Sensitive credentials are never logged.
9. File uploads are treated as untrusted.
10. Internal errors do not expose stack traces or secrets.
11. Rate limits cannot be bypassed through arbitrary parameters.
12. API-level observability does not leak sensitive content.

---

# 76. Definition of Done

The initial API layer is complete when:

* [ ] FastAPI application exists.
* [ ] `/health` exists.
* [ ] `/ready` exists.
* [ ] `/api/v1/version` exists.
* [ ] Query endpoint exists.
* [ ] Document endpoints exist.
* [ ] Ingestion endpoints exist.
* [ ] Incident endpoints exist.
* [ ] Pydantic request/response models exist.
* [ ] Authentication boundary exists.
* [ ] Authorization context is propagated.
* [ ] Stable error responses exist.
* [ ] Request IDs are implemented.
* [ ] OpenAPI documentation is generated.
* [ ] API logging is implemented.
* [ ] API metrics are implemented.
* [ ] API tracing is implemented.
* [ ] Rate limiting is configurable.
* [ ] CORS is configurable.
* [ ] File upload validation exists.
* [ ] Security tests exist.
* [ ] API integration tests exist.
* [ ] Dependency failures are handled.
* [ ] Long-running operations use asynchronous processing where appropriate.
* [ ] API contracts are documented.

---

# 77. Final API Rule

The API is the **boundary of the system, not the implementation of the system**.

Its responsibility is to:

```text
Validate
   ↓
Authenticate
   ↓
Authorize
   ↓
Invoke Application Services
   ↓
Validate Results
   ↓
Return Stable Contracts
```

It must remain thin, secure, observable, versioned, and independent of the internal implementation details of retrieval, generation, storage, and future agentic workflows.

The most important invariant is:

> **No API request may cause unauthorized enterprise information to enter the retrieval, grounding, generation, or response pipeline.**

