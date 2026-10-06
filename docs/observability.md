# Observability Architecture

## 1. Purpose

Observability provides the ability to understand what the RAG system is doing, why it behaved a certain way, and where failures or quality regressions occur.

The observability subsystem covers:

* structured logging
* distributed tracing
* metrics
* request correlation
* ingestion telemetry
* retrieval telemetry
* security telemetry
* generation telemetry
* evaluation telemetry
* latency
* token usage
* cost
* errors
* operational diagnostics

The system must be observable across the complete RAG lifecycle:

```text
User Request
    ↓
API
    ↓
Query Processing
    ↓
Security
    ↓
Retrieval
    ↓
Reranking
    ↓
Generation
    ↓
Validation
    ↓
Response
```

---

# 2. Observability Principles

## 2.1 Structured Observability

Logs, traces, and metrics must use structured fields rather than relying on unstructured text.

---

## 2.2 Correlation

Every request must be traceable across subsystems.

Example:

```text
request_id
    ↓
query
    ↓
retrieval
    ↓
security
    ↓
generation
    ↓
LLM request
```

---

## 2.3 No Sensitive Data by Default

Observability must not become a data-exfiltration mechanism.

Do not automatically log:

* passwords
* API keys
* authentication tokens
* full confidential documents
* unrestricted LLM context
* unnecessary PII
* full sensitive queries

---

## 2.4 Measure Before Optimizing

Architecture changes should be supported by telemetry.

For example:

```text
New Chunking Strategy
        ↓
Benchmark
        ↓
Retrieval Metrics
        ↓
Generation Metrics
        ↓
Latency
        ↓
Cost
        ↓
Decision
```

---

## 2.5 Quality and Operations Are Both Observable

A system can be operationally healthy while producing poor answers.

Therefore observability must measure both:

```text
System Health
```

and:

```text
RAG Quality
```

---

# 3. Observability Architecture

The initial architecture is:

```text
                    Application
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       Logging       Tracing       Metrics
          │             │             │
          └─────────────┼─────────────┘
                        ↓
              Observability Backend
```

The implementation should initially use:

* Python structured logging
* OpenTelemetry
* Prometheus-compatible metrics

Visualization and centralized collection can be introduced later.

---

# 4. Observability Layers

Observability exists at several levels.

```text
Infrastructure
      ↓
Application
      ↓
Pipeline
      ↓
Retrieval
      ↓
Generation
      ↓
Evaluation
```

Each layer should expose useful telemetry.

---

# 5. Request Correlation

Every incoming request should receive a unique request ID.

Example:

```text
request_id = req_8f4c...
```

The request ID should propagate through:

```text
API
 ↓
Application
 ↓
Query Processing
 ↓
Retrieval
 ↓
Security
 ↓
Generation
 ↓
LLM Provider
```

---

# 6. Trace ID

Distributed tracing should use a trace identifier.

Conceptually:

```text
trace_id
 ├── API span
 ├── query span
 ├── retrieval span
 ├── security span
 ├── reranking span
 ├── generation span
 └── provider span
```

This allows one user request to be inspected end-to-end.

---

# 7. Span Design

The initial trace hierarchy should be:

```text
RAG Request
│
├── Authentication
│
├── Authorization
│
├── Query Processing
│
├── Retrieval
│   ├── Vector Search
│   ├── Keyword Search
│   ├── Fusion
│   └── Reranking
│
├── Evidence Assembly
│
├── Generation
│   └── LLM Provider
│
└── Response Validation
```

---

# 8. API Span

The API span should capture:

```text
request_id
trace_id
endpoint
HTTP method
status code
latency
authenticated user reference
```

Avoid storing the raw authorization token.

---

# 9. Query Processing Span

Capture:

```text
query_id
query_type
rewritten
routing_decision
latency
```

Do not automatically store the complete query if it may contain sensitive information.

A hash or sanitized representation may be sufficient.

---

# 10. Retrieval Span

Retrieval telemetry should capture:

```text
retrieval_id
query_id
retrieval_strategy
top_k
candidate_count
authorized_count
latency
```

Example:

```text
retrieval_strategy = hybrid
top_k = 20
candidate_count = 20
authorized_count = 13
```

This is useful for diagnosing security filtering and retrieval quality.

---

# 11. Vector Search Span

Vector search should record:

```text
embedding_model
index_name
top_k
candidate_count
latency
```

Potentially:

```text
distance_threshold
```

if the retrieval strategy uses one.

---

# 12. Keyword Search Span

Keyword retrieval should record:

```text
search_engine
query_type
candidate_count
latency
```

For PostgreSQL-based search, relevant query strategy metadata may be recorded without storing sensitive query text.

---

# 13. Hybrid Retrieval Span

The hybrid retrieval span should capture:

```text
vector_candidates
keyword_candidates
fusion_method
fusion_parameters
final_candidates
latency
```

This makes retrieval experiments measurable.

---

# 14. Reranking Span

Reranking telemetry:

```text
reranker
input_count
output_count
latency
```

For example:

```text
reranker = cross_encoder
input_count = 30
output_count = 8
```

---

# 15. Security Span

Security operations should be observable.

Capture:

```text
authorization_decision
policy_version
candidate_count
authorized_count
denied_count
latency
```

Example:

```text
candidate_count = 20
authorized_count = 14
denied_count = 6
```

Do not log restricted document content.

---

# 16. Generation Span

Generation telemetry should include:

```text
generation_id
model
prompt_version
evidence_count
input_tokens
output_tokens
latency
status
grounded
abstained
citation_count
```

This provides a complete view of generation behavior.

---

# 17. LLM Provider Span

The provider adapter should create a child span.

Example:

```text
Generation
    └── OpenRouter
```

Capture:

```text
provider
model
request latency
time to first token
input tokens
output tokens
status
retry count
```

Sensitive request content should not be stored by default.

---

# 18. Ingestion Observability

Ingestion is a long-running pipeline and requires detailed telemetry.

Trace:

```text
Ingestion
│
├── Discovery
├── Validation
├── Parsing
├── Cleaning
├── Metadata
├── Classification
├── Chunking
├── Embedding
├── Persistence
├── Indexing
└── Validation
```

---

# 19. Ingestion Metrics

Record:

```text
documents_processed
documents_succeeded
documents_failed
documents_quarantined
chunks_created
embeddings_created
processing_time
embedding_time
indexing_time
```

Also track failure reasons.

---

# 20. Ingestion Request Identifiers

Every ingestion operation should have:

```text
ingestion_id
source_id
document_id
document_version_id
```

Example:

```text
ingestion_id = ING-2026-000123
document_id = DOC-00452
version_id = VER-00003
```

These identifiers must appear in logs and traces.

---

# 21. Ingestion State Telemetry

The state machine:

```text
DISCOVERED
    ↓
VALIDATING
    ↓
PARSING
    ↓
CLEANING
    ↓
METADATA_READY
    ↓
CHUNKING
    ↓
EMBEDDING
    ↓
INDEXING
    ↓
VALIDATING_INDEX
    ↓
ACTIVE
```

Each transition should be observable.

Failures:

```text
FAILED
QUARANTINED
```

should include an error category.

---

# 22. Database Observability

Database operations should expose:

* query latency
* connection pool utilization
* active connections
* errors
* transaction duration
* slow queries
* deadlocks
* lock waits

Do not log arbitrary SQL parameters if they may contain sensitive information.

---

# 23. Connection Pool Metrics

Track:

```text
db_pool_size
db_pool_in_use
db_pool_idle
db_pool_wait_time
db_connection_errors
```

Connection exhaustion should be visible before it becomes an outage.

---

# 24. API Metrics

Minimum HTTP metrics:

```text
http_requests_total
http_request_duration_seconds
http_requests_in_flight
http_errors_total
```

Labels should remain bounded.

Good:

```text
method
route
status
```

Bad:

```text
raw_user_query
document_id
full_url_with_sensitive_parameters
```

High-cardinality labels can severely damage metric systems.

---

# 25. Retrieval Metrics

Track:

```text
retrieval_requests_total
retrieval_latency_seconds
retrieval_candidates_total
retrieval_authorized_results_total
retrieval_empty_results_total
```

Quality metrics from evaluation include:

```text
Recall@K
Precision@K
MRR
NDCG@K
Hit Rate@K
```

Operational telemetry and evaluation metrics should remain conceptually separate.

---

# 26. Generation Metrics

Track:

```text
generation_requests_total
generation_latency_seconds
generation_failures_total
generation_abstentions_total
generation_tokens_input
generation_tokens_output
generation_citations_total
```

Also track:

```text
grounded_answers
ungrounded_answers
```

when grounding validation supports the distinction.

---

# 27. Security Metrics

Track:

```text
authorization_requests_total
authorization_denials_total
security_filter_latency_seconds
unauthorized_candidates_total
prompt_injection_events_total
security_validation_failures_total
```

Security metrics should be monitored separately from normal application errors.

---

# 28. Evaluation Metrics

Evaluation runs should record:

```text
evaluation_run_id
dataset_version
model
prompt_version
retrieval_version
embedding_model
reranker
git_commit
timestamp
```

Quality metrics include:

```text
Recall@K
MRR
NDCG
answer correctness
groundedness
citation correctness
citation completeness
abstention accuracy
```

---

# 29. Cost Observability

LLM usage must be measurable.

Track:

```text
input_tokens
output_tokens
total_tokens
estimated_cost
```

Group costs by:

```text
model
endpoint
use_case
environment
evaluation_run
```

For example:

```text
generation
evaluation
query_rewriting
reranking
```

---

# 30. Cost Calculation

Cost calculation should be performed outside core domain logic.

Conceptually:

```python
class CostCalculator:
    def calculate(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        ...
```

Pricing should be configuration-driven rather than hard-coded throughout the application.

---

# 31. Token Observability

Token usage should be tracked separately for:

```text
input
output
total
```

For RAG, input tokens are particularly important because evidence can significantly increase context size.

Track:

```text
retrieval_context_tokens
prompt_tokens
output_tokens
```

where available.

---

# 32. Latency Budget

A query latency budget should be defined.

Example:

```text
Total Request
├── Authentication
├── Query Processing
├── Retrieval
├── Reranking
├── Context Assembly
├── LLM
└── Response Validation
```

This enables identification of the dominant bottleneck.

---

# 33. Latency Percentiles

Do not rely only on average latency.

Track:

```text
P50
P90
P95
P99
```

Example:

```text
P50 = 1.8s
P95 = 5.2s
P99 = 9.7s
```

Tail latency is especially important for production systems.

---

# 34. Error Classification

Errors should be categorized.

Example:

```text
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
VALIDATION_ERROR
RETRIEVAL_ERROR
DATABASE_ERROR
EMBEDDING_ERROR
LLM_TIMEOUT
LLM_RATE_LIMIT
LLM_PROVIDER_ERROR
GENERATION_VALIDATION_ERROR
SECURITY_ERROR
INTERNAL_ERROR
```

This makes monitoring and incident analysis easier.

---

# 35. Error Telemetry

Every significant error should include:

```text
request_id
trace_id
component
operation
error_type
timestamp
environment
```

Stack traces should be available internally but should not be exposed to API clients.

---

# 36. Structured Logging

Use structured JSON logging in production.

Example:

```json
{
  "timestamp": "2026-10-05T20:15:30Z",
  "level": "INFO",
  "event": "retrieval_completed",
  "request_id": "REQ-123",
  "trace_id": "TRACE-456",
  "retrieval_id": "RET-789",
  "candidate_count": 20,
  "authorized_count": 14,
  "latency_ms": 82
}
```

Logs should be machine-readable.

---

# 37. Log Levels

Use consistent log levels.

### DEBUG

Detailed development diagnostics.

### INFO

Normal operational events.

### WARNING

Unexpected but recoverable conditions.

### ERROR

Failed operations.

### CRITICAL

System-wide or security-critical failures.

Production should avoid excessive DEBUG logging.

---

# 38. Security-Sensitive Logs

Security events should be clearly identifiable.

Example:

```json
{
  "level": "WARNING",
  "event": "authorization_denied",
  "request_id": "REQ-123",
  "actor_id": "USER-456",
  "resource_type": "document",
  "decision": "DENY"
}
```

Do not include the protected document content.

---

# 39. PII in Logs

Logs should use data minimization.

Instead of:

```text
customer_email=user@example.com
```

prefer:

```text
customer_reference=hashed-value
```

when the actual email is not required for diagnosis.

Sensitive fields should have explicit logging policies.

---

# 40. Query Logging

Queries should not automatically be logged in full.

Preferred approaches:

```text
query_hash
query_length
query_type
```

If debugging requires raw queries in development, that behavior must be explicitly enabled.

Production should default to sanitized logging.

---

# 41. Evidence Logging

Do not log full retrieved evidence by default.

Instead log:

```text
evidence_count
document_ids
chunk_ids
scores
classification
```

Even identifiers may be restricted depending on deployment requirements.

---

# 42. Generation Context Logging

The complete LLM context must not be logged by default.

This is especially important because context may contain:

* confidential information
* restricted information
* PII
* proprietary network information

If context capture is required for debugging, it should be:

* explicitly enabled
* access-controlled
* time-limited
* sanitized
* audited

---

# 43. Trace Sampling

Tracing every request at maximum detail may become expensive.

Use configurable sampling.

Example:

```yaml
observability:
  tracing:
    enabled: true
    sample_rate: 0.1
```

Security events and errors may require higher sampling or guaranteed capture.

---

# 44. Metrics Cardinality

Metrics labels must remain bounded.

Good labels:

```text
route
method
status
model
environment
```

Potentially dangerous labels:

```text
user_id
document_id
query
chunk_id
request_id
```

High-cardinality identifiers belong in logs/traces rather than metric labels.

---

# 45. Health Checks

The API should expose health endpoints.

Example:

```text
GET /health
GET /health/live
GET /health/ready
```

### Liveness

Determines whether the process is running.

### Readiness

Determines whether dependencies required for serving traffic are available.

---

# 46. Dependency Health

Readiness may check:

```text
PostgreSQL
pgvector
required configuration
critical provider connectivity
```

External LLM provider health should be handled carefully.

The API should not necessarily become unavailable simply because an external provider is temporarily unavailable if other endpoints remain functional.

---

# 47. Operational Dashboards

Future dashboards should cover:

### API

* request rate
* latency
* errors

### Retrieval

* latency
* empty retrievals
* candidate counts

### Generation

* latency
* tokens
* failures
* abstentions

### Security

* authorization denials
* suspicious activity
* security failures

### Ingestion

* throughput
* failures
* quarantined documents

### Cost

* tokens
* estimated cost
* cost per query

---

# 48. Suggested Dashboard

A high-level production dashboard:

```text
┌─────────────────────────────────────────┐
│             RAG PLATFORM                │
├──────────────┬──────────────┬───────────┤
│ Requests     │ P95 Latency  │ Error %   │
├──────────────┼──────────────┼───────────┤
│ Retrieval    │ Generation   │ Cost      │
├──────────────┼──────────────┼───────────┤
│ Grounding    │ Abstention   │ Citations │
├──────────────┼──────────────┼───────────┤
│ Security     │ Ingestion    │ Database  │
└──────────────┴──────────────┴───────────┘
```

---

# 49. Alerting

Alerts should focus on actionable conditions.

Examples:

```text
P95 latency > threshold
```

```text
LLM error rate > threshold
```

```text
database connection exhaustion
```

```text
retrieval failure rate > threshold
```

```text
security validation failures
```

```text
ingestion quarantine rate unexpectedly high
```

```text
cost exceeds expected budget
```

---

# 50. Quality Alerts

Operational monitoring should eventually detect quality regressions.

Examples:

```text
groundedness drops
citation correctness drops
retrieval Recall@K drops
abstention rate changes unexpectedly
```

These should generally come from evaluation pipelines rather than simple request metrics.

---

# 51. Experiment Observability

Every RAG experiment should record:

```text
experiment_id
dataset_version
configuration_version
prompt_version
model
embedding_model
chunking_version
retrieval_strategy
reranker
results
```

This enables comparison.

Example:

```text
Experiment 01
chunk_size=500
top_k=10
reranker=none

Experiment 02
chunk_size=800
top_k=20
reranker=cross_encoder
```

---

# 52. Reproducibility

A production or evaluation result should be reproducible from:

```text
git_commit
configuration
prompt_version
model
embedding_model
retrieval_version
dataset_version
```

This metadata should be persisted with evaluation results.

---

# 53. Observability Configuration

Initial configuration:

```yaml
observability:
  logging:
    level: INFO
    format: json

  tracing:
    enabled: true
    sample_rate: 0.1

  metrics:
    enabled: true

  capture:
    raw_queries: false
    raw_context: false
    raw_documents: false

  cost:
    enabled: true

  audit:
    enabled: true
```

Production should default to privacy-preserving behavior.

---

# 54. Package Structure

Initial observability package:

```text
src/telco_rag/observability/
├── __init__.py
├── logging.py
├── tracing.py
└── metrics.py
```

Responsibilities:

### `logging.py`

Structured application logging.

### `tracing.py`

OpenTelemetry spans and trace context.

### `metrics.py`

Prometheus-compatible metrics.

---

# 55. Observability Abstractions

Application code should use simple abstractions.

Conceptually:

```python
class Metrics:
    def increment(...)
    def observe(...)
```

```python
class Tracer:
    def span(...)
```

This avoids tightly coupling domain code to a telemetry backend.

---

# 56. OpenTelemetry

OpenTelemetry should be the primary tracing abstraction.

The architecture should allow future export to systems such as:

* Jaeger
* Tempo
* OTLP-compatible collectors
* cloud observability platforms

Application code should depend on OpenTelemetry abstractions rather than directly on one visualization platform.

---

# 57. Prometheus

Prometheus-compatible metrics should initially expose:

```text
HTTP metrics
retrieval metrics
generation metrics
LLM metrics
database metrics
ingestion metrics
security metrics
cost metrics
```

Metric names should be stable and documented.

---

# 58. Observability and Docker

Local development should be able to run the application and core infrastructure using Docker Compose.

Future development environments may include:

```text
PostgreSQL
Prometheus
Grafana
OpenTelemetry Collector
Jaeger/Tempo
```

These components should remain optional for the earliest development stages.

---

# 59. Observability and Testing

Observability itself must be tested.

Tests should verify:

```text
request_id propagation
trace creation
metric emission
error telemetry
security event logging
token tracking
cost calculation
```

Sensitive information must also be tested for absence from logs.

---

# 60. Security Tests for Observability

Mandatory tests include:

### Secret leakage

Verify API keys never appear in logs.

### Context leakage

Verify confidential context is not logged by default.

### Token leakage

Verify authentication tokens are not logged.

### PII leakage

Verify sensitive fields are sanitized.

### Authorization metadata

Verify security events retain enough information for investigation without exposing protected content.

---

# 61. Failure Observability

Every pipeline should produce useful failure telemetry.

Example:

```text
Document
 ↓
Parsing
 ↓
FAILED
```

Telemetry:

```text
document_id
ingestion_id
stage=parsing
error_type=INVALID_PDF
duration_ms
```

For RAG:

```text
Query
 ↓
Retrieval
 ↓
FAILED
```

Telemetry:

```text
request_id
retrieval_id
stage=vector_search
error_type=DATABASE_TIMEOUT
```

---

# 62. End-to-End Example

A user asks:

```text
Why did the 5G service degrade in Ontario?
```

The trace might look like:

```text
TRACE-001
│
├── API                10ms
├── Authentication      2ms
├── Authorization       3ms
├── Query Processing    8ms
├── Retrieval          90ms
│   ├── Vector Search  35ms
│   ├── Keyword Search 20ms
│   ├── Fusion          5ms
│   └── Reranking      30ms
├── Evidence Assembly   4ms
├── Generation        1400ms
│   └── OpenRouter    1380ms
└── Validation          8ms

Total: ~1525ms
```

This immediately identifies the LLM call as the dominant latency component.

---

# 63. End-to-End Cost Example

For the same request:

```text
Input tokens: 3,200
Output tokens: 420
Total tokens: 3,620
```

The system should associate token usage with:

```text
request_id
model
use_case=rag_generation
```

The cost calculator can then estimate the request cost.

---

# 64. Observability and Evaluation

Evaluation results should be connected to operational telemetry where practical.

For example:

```text
Evaluation Run
      ↓
Retrieval Metrics
      ↓
Generation Metrics
      ↓
Latency
      ↓
Token Usage
      ↓
Cost
```

This prevents quality improvements from being evaluated in isolation.

---

# 65. Observability and Security

Security events should remain traceable through the same request.

Example:

```text
TRACE-002
│
├── Authentication
├── Authorization
│     └── DENIED
└── Request terminated
```

The system should be able to answer:

* who made the request?
* what was requested?
* what authorization decision occurred?
* what resources were considered?
* what was returned?
* what was logged?

without exposing protected content unnecessarily.

---

# 66. Observability and Agentic RAG

Future agents require additional telemetry.

Agent traces may include:

```text
Agent Run
│
├── Planning
├── Tool Selection
├── Tool Call
├── Retrieval
├── Tool Result
├── Memory Read
├── Memory Write
├── Replanning
└── Final Answer
```

Each tool invocation must have:

```text
tool_name
input_schema
authorization_decision
duration
result_status
```

Sensitive tool inputs and outputs must be handled carefully.

---

# 67. Agent Safety Telemetry

Future agent metrics should include:

* tool calls per request
* repeated tool calls
* failed tool calls
* unauthorized tool attempts
* maximum iterations
* termination reason
* human escalation rate
* memory operations
* external side effects

---

# 68. Cost Controls

The system should support configurable budgets.

Example:

```yaml
cost:
  max_input_tokens: 12000
  max_output_tokens: 2000
  max_estimated_cost_per_request: 0.05
```

A future implementation may terminate or downgrade expensive operations when limits are exceeded.

---

# 69. Observability Data Retention

Telemetry should have explicit retention policies.

Different data types may require different retention:

```text
Metrics
    short/medium retention

Traces
    medium retention

Application logs
    medium retention

Security audit logs
    longer retention

Raw generation context
    preferably disabled
```

Retention requirements must ultimately follow organizational policy and applicable regulations.

---

# 70. Definition of Done

Observability is considered complete for the baseline system when:

* [ ] structured logging exists
* [ ] request IDs exist
* [ ] trace IDs propagate
* [ ] OpenTelemetry integration exists
* [ ] API spans exist
* [ ] retrieval spans exist
* [ ] security spans exist
* [ ] generation spans exist
* [ ] provider spans exist
* [ ] ingestion telemetry exists
* [ ] Prometheus-compatible metrics exist
* [ ] latency metrics exist
* [ ] token metrics exist
* [ ] cost tracking exists
* [ ] error classification exists
* [ ] health checks exist
* [ ] sensitive data logging is disabled by default
* [ ] security events are auditable
* [ ] retrieval metrics exist
* [ ] generation metrics exist
* [ ] evaluation metadata is captured
* [ ] observability tests exist
* [ ] dashboards can be built from emitted telemetry
* [ ] alerting requirements are documented

---

# 71. Final Observability Rule

The system should make every important RAG decision explainable operationally.

The desired chain is:

```text
Request
   ↓
Trace
   ↓
Logs
   ↓
Metrics
   ↓
Evidence
   ↓
Decision
   ↓
Answer
```

The fundamental rule is:

> **If we cannot observe and measure a critical part of the RAG pipeline, we cannot reliably operate, debug, secure, or improve it.**

