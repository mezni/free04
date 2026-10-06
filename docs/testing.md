# Testing Strategy

## 1. Purpose

Testing is a first-class architectural concern of `telco-rag`.

The testing strategy must validate:

* Domain correctness.
* Application behavior.
* Retrieval quality.
* Generation quality.
* Security.
* API contracts.
* Provider integrations.
* Ingestion.
* Configuration.
* Observability.
* End-to-end behavior.

The project must not rely exclusively on unit tests.

RAG quality requires both software testing and evaluation.

---

# 2. Testing Philosophy

The testing strategy follows:

```text
Fast Tests
    ↓
Integration Tests
    ↓
Contract Tests
    ↓
Security Tests
    ↓
RAG Evaluation
    ↓
End-to-End Tests
```

The majority of tests should be fast and deterministic.

Expensive or external tests should run less frequently.

---

# 3. Test Pyramid

The project uses:

```text
             E2E
           /     \
       Evaluation
        /       \
   Integration  Contract
      /             \
    Application     Security
        \           /
             Unit
```

Unit tests form the largest layer.

---

# 4. Test Directory

Recommended structure:

```text
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   ├── ingestion/
│   ├── retrieval/
│   ├── query/
│   ├── generation/
│   ├── security/
│   └── config/
│
├── integration/
│   ├── test_database.py
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_rag.py
│   └── test_security.py
│
├── contract/
│   ├── test_llm_provider.py
│   ├── test_embedding_provider.py
│   └── test_reranker_provider.py
│
├── evaluation/
│   ├── test_retrieval_quality.py
│   └── test_generation_quality.py
│
└── e2e/
    └── test_api_flow.py
```

Tests remain outside `src/`.

---

# 5. Unit Tests

Unit tests validate isolated behavior.

They should not require:

* PostgreSQL.
* OpenRouter.
* Docker.
* Network access.

Examples:

```text
Document classification
Chunking
Metadata extraction
Query classification
Query rewriting
Access policy evaluation
Citation validation
Grounding validation
Application service orchestration
Configuration validation
```

---

# 6. Domain Tests

Domain tests validate business invariants.

Examples:

```text
A document must have a classification.
A document version cannot be mutated after activation.
A closed incident cannot transition directly to an invalid state.
A ticket priority must be valid.
A user role must be recognized.
```

Domain tests must not import:

```text
FastAPI
SQLAlchemy
PostgreSQL
OpenRouter
LangChain
LangGraph
```

---

# 7. Application Tests

Application tests validate use-case orchestration.

Examples:

```text
QueryService retrieves evidence and generates an answer.
DocumentService creates a document.
IngestionService coordinates ingestion.
IncidentService retrieves incidents.
Authorization context reaches retrieval.
Generation is not called when evidence is insufficient.
```

Application tests should use fake dependencies.

---

# 8. Ingestion Tests

Ingestion tests validate:

* File validation.
* Loader selection.
* PDF parsing.
* DOCX parsing.
* Markdown parsing.
* Text loading.
* Cleaning.
* Metadata extraction.
* Classification.
* Chunking.
* Embedding.
* Idempotency.
* Quarantine behavior.

Malformed files must be tested.

---

# 9. Ingestion Security Tests

Security tests must verify:

```text
Unknown classification
    → Quarantine

Unauthorized metadata
    → Rejected

Oversized file
    → Rejected

Unsupported extension
    → Rejected

Malformed document
    → Safe failure
```

The ingestion pipeline must never silently convert uncertain content into PUBLIC content.

---

# 10. Chunking Tests

Chunking requires deterministic tests.

Test:

* Target size.
* Overlap.
* Section boundaries.
* Paragraph boundaries.
* Tables.
* Lists.
* Headings.
* Telecom identifiers.
* Source locations.

Example telecom tokens:

```text
5G
LTE
NR
AMF
SMF
UPF
gNodeB
eNodeB
IMS
APN
```

Chunking must preserve important technical identifiers.

---

# 11. Retrieval Tests

Retrieval tests validate:

* Vector search.
* Keyword search.
* Hybrid search.
* Filtering.
* Ranking.
* Reranking.
* Evidence selection.

Tests should use known documents and expected results.

---

# 12. Retrieval Metrics

Retrieval quality is measured using:

```text
Recall@K
Precision@K
MRR
NDCG@K
Hit Rate@K
```

Example:

```text
Recall@5
Recall@10
MRR
NDCG@10
```

Quality thresholds belong to evaluation configuration.

---

# 13. Security Retrieval Tests

These are mandatory.

The tests must prove:

```text
Unauthorized document
        ↓
Not retrieved
        ↓
Not evidence
        ↓
Not prompt context
        ↓
Not citation
```

Security filtering must happen before evidence reaches generation.

---

# 14. Metadata Filter Tests

Tests must verify that:

```text
User Filters
      AND
Security Filters
```

are always combined.

A user must never be able to provide a filter that disables an authorization constraint.

---

# 15. Query Tests

Query tests validate:

* Normalization.
* Intent classification.
* Entity extraction.
* Query rewriting.
* Temporal constraints.
* Routing.
* Structured output.
* Ambiguity handling.

Example:

```text
"Why did the LTE service fail in Ontario yesterday?"
```

should preserve:

```text
technology = LTE
region = Ontario
temporal_constraint = yesterday
intent = incident/troubleshooting
```

---

# 16. Generation Tests

Generation tests validate:

* Prompt construction.
* Evidence inclusion.
* Citation formatting.
* Structured output.
* Abstention.
* Conflict handling.
* Insufficient evidence behavior.

The model must not be treated as authoritative.

---

# 17. Grounding Tests

Grounding tests must verify:

```text
Supported claim
    → Accepted

Unsupported claim
    → Rejected

Contradicted claim
    → Rejected

Insufficient evidence
    → Abstention or partial answer
```

Citation validation must verify that citations point to actual retrieved evidence.

---

# 18. Hallucination Tests

The test suite should include cases where:

* Evidence does not contain the answer.
* Evidence contradicts the model's likely prior knowledge.
* Evidence is incomplete.
* Multiple sources conflict.
* The question asks for information not present in the corpus.

Expected behavior:

```text
Do not invent.
State uncertainty.
Cite available evidence.
Abstain when necessary.
```

---

# 19. Temporal Tests

The system must distinguish:

```text
Current information
Historical information
Future information
```

Tests should include:

```text
"What is the current SLA?"
"What was the SLA in 2024?"
"What changed last month?"
```

Historical documents must not automatically override newer authoritative documents.

---

# 20. Evaluation Dataset

Evaluation data belongs under:

```text
data/eval/
├── questions.jsonl
├── retrieval_cases.jsonl
└── expected_answers.jsonl
```

Evaluation cases should contain:

```text
question
expected_evidence
expected_answer
metadata
difficulty
security_context
```

---

# 21. Evaluation Versioning

Every evaluation run should identify:

```text
dataset_version
git_commit
model
embedding_model
retrieval_configuration
reranker
prompt_version
timestamp
```

This makes experiments reproducible.

---

# 22. Security Evaluation

Security evaluation is a hard requirement.

Important invariant:

```text
Unauthorized content in final context = 0
```

Tests must cover:

* Classification enforcement.
* User roles.
* Document ACLs.
* Tenant boundaries if introduced.
* Cache isolation.
* Citation authorization.
* Prompt injection.
* Malicious documents.

---

# 23. Prompt Injection Tests

Documents are untrusted data.

A document may contain text such as:

```text
Ignore previous instructions...
```

The retrieval system must treat that text as evidence content, not as an instruction to the application.

Tests must verify that retrieved documents cannot override:

* System instructions.
* Security policies.
* Application rules.
* Tool permissions.

---

# 24. Provider Contract Tests

Provider adapters must be tested independently.

Contract tests validate:

* Request format.
* Response normalization.
* Authentication.
* Timeout.
* Retry.
* Error mapping.
* Token usage.
* Structured output.

External provider tests may require credentials and network access.

---

# 25. Fake Providers

Unit and application tests should use deterministic fake providers.

Example:

```python
class FakeLLMProvider:
    def generate(self, request):
        return LLMResponse(
            text="test response",
            model="fake",
        )
```

Fake embeddings should return deterministic vectors.

Fake rerankers should return deterministic rankings.

---

# 26. Database Integration Tests

Database integration tests use PostgreSQL.

They validate:

* Schema.
* Constraints.
* Foreign keys.
* Indexes.
* pgvector.
* Repositories.
* Transactions.
* Migrations.

These tests must run against a real PostgreSQL instance rather than an incompatible mock.

---

# 27. Migration Tests

Every migration must be tested.

Tests should verify:

```text
Empty database
    ↓
Alembic upgrade
    ↓
Current schema
```

and:

```text
Current schema
    ↓
Alembic downgrade
    ↓
Previous schema
```

Production migrations must be reviewed before deployment.

---

# 28. API Tests

API tests validate:

* Request validation.
* Response schemas.
* Authentication.
* Authorization.
* HTTP status codes.
* Error format.
* Pagination.
* Filtering.
* File upload limits.
* Health endpoints.

The API tests should use FastAPI's test client or an equivalent HTTP test mechanism.

---

# 29. End-to-End Tests

E2E tests validate complete flows.

Example:

```text
Upload Document
      ↓
Ingestion
      ↓
Chunking
      ↓
Embedding
      ↓
Persistence
      ↓
Query
      ↓
Retrieval
      ↓
Generation
      ↓
Grounded Answer
      ↓
Citation
```

E2E tests should remain limited because they are slower and more expensive.

---

# 30. Observability Tests

Tests must verify that critical operations produce telemetry.

Examples:

```text
API request
Query
Authorization
Retrieval
Generation
LLM call
Ingestion
```

Tests should verify:

* Trace propagation.
* Required fields.
* Error classification.
* Sensitive-value redaction.

---

# 31. Performance Tests

Performance testing should measure:

```text
API latency
Retrieval latency
Vector search latency
Keyword search latency
Reranking latency
LLM latency
End-to-end latency
```

Important percentiles:

```text
P50
P90
P95
P99
```

Performance targets must be established from measured baselines rather than arbitrary assumptions.

---

# 32. Failure Injection

The system should eventually test failures such as:

```text
Database unavailable
LLM timeout
Embedding timeout
Provider rate limit
Malformed provider response
Vector search failure
Keyword search failure
Invalid document
```

Expected behavior must be defined for each failure.

---

# 33. Test Markers

Pytest markers may separate test categories.

Example:

```text
unit
integration
contract
security
evaluation
e2e
slow
external
```

Examples:

```bash
pytest -m unit
pytest -m integration
pytest -m security
pytest -m evaluation
```

---

# 34. Local Development

The default developer workflow should be fast.

Example:

```bash
pytest
```

should execute deterministic tests without requiring external AI providers.

Integration tests can be run separately.

---

# 35. CI Test Strategy

CI should execute progressively:

```text
Pull Request
    ↓
Lint
    ↓
Type Checks
    ↓
Unit Tests
    ↓
Security Tests
    ↓
Integration Tests
    ↓
Evaluation Gates
```

Expensive E2E tests may run on protected branches or scheduled workflows.

---

# 36. Quality Gates

A change must not be considered complete if it:

* Breaks unit tests.
* Breaks integration tests.
* Violates security invariants.
* Significantly degrades retrieval quality.
* Significantly degrades grounding quality.
* Introduces unauthorized context exposure.
* Removes required observability.

---

# 37. RAG Evaluation vs Software Testing

These are separate concerns.

Software tests answer:

> Does the system behave according to its implementation contract?

RAG evaluation answers:

> Does the system produce useful, relevant, grounded results?

Both are required.

A system can pass all unit tests while producing poor RAG answers.

---

# 38. Regression Testing

Every significant retrieval or generation change should be evaluated against the existing evaluation dataset.

Examples of changes requiring regression evaluation:

* Chunking changes.
* Embedding model changes.
* Retrieval changes.
* Hybrid weighting changes.
* Reranking changes.
* Query rewriting changes.
* Prompt changes.
* LLM model changes.
* Security filtering changes.

---

# 39. Experiment Tracking

Experiments should record:

```text
Hypothesis
Configuration
Dataset
Implementation
Metrics
Results
Conclusion
```

Existing experiment documents:

```text
docs/experiments/
├── 01_baseline-rag.md
├── 02_chunking.md
├── 03_hybrid-retrieval.md
├── 04_reranking.md
└── 05_query-routing.md
```

---

# 40. Test Data

Synthetic telecom data is the default test data.

It should include:

* Network documents.
* Product documentation.
* Support tickets.
* Incidents.
* Runbooks.
* SLAs.
* Different classifications.
* Multiple regions.
* Multiple technologies.
* Conflicting versions.

Production customer data must not be used for ordinary development tests.

---

# 41. Test Isolation

Tests must avoid unintended shared state.

Use:

* Fresh database state where required.
* Transaction rollback.
* Unique test identifiers.
* Temporary files.
* Deterministic fake providers.

Tests must be independently repeatable.

---

# 42. Determinism

Tests should minimize nondeterminism.

For LLM tests:

* Use fake providers where possible.
* Use deterministic prompts.
* Use temperature `0`.
* Validate structured output.
* Avoid exact natural-language matching unless necessary.

LLM-based evaluation should use tolerances and explicit metrics.

---

# 43. Testing Agentic RAG

When agentic RAG is introduced, tests must additionally cover:

```text
Agent state
Tool selection
Tool arguments
Authorization
Planning
Loop termination
Maximum iterations
Tool failures
Memory access
Evidence provenance
Human escalation
```

Agents must never bypass the existing retrieval/security architecture.

---

# 44. Testing Memory

When memory is introduced, tests must distinguish:

```text
Knowledge
    ≠
Conversation Context
    ≠
Agent Memory
```

Tests must verify:

* Correct memory scope.
* User isolation.
* Retention policies.
* Retrieval relevance.
* Memory authorization.
* Memory deletion.
* No unauthorized cross-user memory access.

---

# 45. Definition of Done

Testing is complete when:

* Unit testing structure exists.
* Domain tests exist.
* Application tests exist.
* Ingestion tests exist.
* Retrieval tests exist.
* Generation tests exist.
* Security tests exist.
* Provider contract tests exist.
* Database integration tests exist.
* API tests exist.
* Evaluation datasets exist.
* RAG quality metrics exist.
* Regression evaluation exists.
* E2E tests exist for critical flows.
* CI runs appropriate test tiers.
* Security violations are treated as release blockers.

---

# 46. Final Rule

**A production RAG system is not validated by software tests alone.**

`telco-rag` must prove both:

```text
Software Correctness
        +
RAG Quality
        +
Security Correctness
```

before it can be considered production-ready.

