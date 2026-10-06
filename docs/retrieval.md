# Retrieval Architecture

## 1. Purpose

The retrieval subsystem is responsible for finding the most relevant, authorized, and high-quality enterprise knowledge for a user's query.

The retrieval system is a first-class component of the `telco-rag` platform.

Its output is not an answer. Its output is **evidence** that can safely be provided to the generation layer.

The retrieval pipeline must therefore optimize for:

* relevance
* authorization
* factual coverage
* diversity
* metadata precision
* ranking quality
* latency
* cost
* explainability

The fundamental pipeline is:

```text
User Query
    ↓
Query Processing
    ↓
Security Context
    ↓
Metadata Filtering
    ↓
Candidate Retrieval
    ├── Vector Search
    └── Keyword Search
    ↓
Hybrid Fusion
    ↓
Reranking
    ↓
Top-K Evidence Selection
    ↓
Evidence Validation
    ↓
Generation
```

---

# 2. Retrieval Principles

## 2.1 Retrieval Is Not Generation

The retrieval subsystem must not generate natural-language answers.

Its responsibility is to identify evidence.

Generation is a separate responsibility handled by the generation subsystem.

```text
Retrieval:
"What information should the model see?"

Generation:
"What answer should be produced from that information?"
```

---

## 2.2 Security Comes Before Retrieval Results Reach the LLM

Authorization must be enforced before retrieved content is passed to the generation layer.

The following rule is mandatory:

```text
Unauthorized content
        ↓
must never
        ↓
enter LLM context
```

Security filtering should occur as early as practical and must also be validated before final evidence construction.

---

## 2.3 Retrieval Must Be Deterministic Where Possible

Given the same:

* query
* indexed corpus
* metadata filters
* security context
* retrieval configuration

the retrieval system should produce the same result ordering within reasonable database/index tolerances.

Random behavior must not be introduced into the retrieval pipeline.

---

## 2.4 Evidence Must Be Traceable

Every retrieved chunk must retain its source information.

At minimum:

```text
Chunk
 ├── Document
 ├── Document Version
 ├── Source
 ├── Metadata
 └── Retrieval Score
```

This allows the generation layer to produce citations.

---

# 3. Retrieval Pipeline

The retrieval pipeline consists of the following stages:

```text
1. Query validation
2. Query classification
3. Query normalization
4. Query rewriting
5. Security context construction
6. Metadata filter construction
7. Candidate retrieval
8. Hybrid fusion
9. Reranking
10. Evidence selection
11. Evidence validation
12. Retrieval result
```

Not every stage must be enabled initially.

The implementation will evolve incrementally.

---

# 4. Query Validation

The retrieval system must validate incoming queries before performing retrieval.

Example:

```text
"What causes 5G handover failures?"
```

Valid.

Example:

```text
""
```

Invalid.

Example:

```text
"hello"
```

Technically valid but potentially unsuitable for knowledge retrieval.

The query layer should distinguish:

```text
VALID_KNOWLEDGE_QUERY
INVALID_QUERY
NON_KNOWLEDGE_QUERY
```

The first implementation may simply validate:

* non-empty input
* maximum length
* valid encoding
* reasonable whitespace
* allowed characters

More advanced intent classification will be introduced later.

---

# 5. Query Normalization

Normalization prepares the query for retrieval.

Example:

```text
"Why does 5G UE handover fail during mobility?"
```

may be normalized to:

```text
"5G UE handover failure during mobility"
```

Normalization must not remove information that affects retrieval.

Important telecom terminology must be preserved.

Examples:

```text
5G
NR
LTE
VoLTE
RAN
AMF
SMF
UPF
gNodeB
eNodeB
IMS
QoS
SLA
```

The system must avoid generic text normalization that damages technical terminology.

---

# 6. Query Classification

The system may classify queries before retrieval.

Initial categories:

```text
NETWORK_TROUBLESHOOTING
PRODUCT_INFORMATION
SLA_QUERY
INCIDENT_INVESTIGATION
SUPPORT_TICKET
RUNBOOK_LOOKUP
CHANGE_PROCEDURE
GENERAL_KNOWLEDGE
```

Example:

```text
"What are the troubleshooting steps for a 5G handover failure?"
```

Classification:

```text
NETWORK_TROUBLESHOOTING
```

Another example:

```text
"What is the enterprise SLA for Fiber Business Premium?"
```

Classification:

```text
SLA_QUERY
```

Classification may later influence:

* metadata filters
* query rewriting
* retrieval sources
* ranking weights
* reranking strategy

---

# 7. Query Rewriting

Query rewriting transforms a user query into a retrieval-friendly representation.

Example:

```text
User query:

"Why are phones dropping calls when moving between cells?"
```

Possible retrieval query:

```text
LTE handover failure
inter-cell mobility
call drop
handover failure causes
```

The rewriting layer must preserve the original query.

The original query remains authoritative for generation.

```text
original_query
rewritten_query
```

Both should be available to downstream components.

---

# 8. Security Context

Retrieval must receive a security context describing what the requesting user is allowed to access.

Example:

```python
SecurityContext(
    user_id="user-001",
    roles=[
        "NETWORK_ENGINEER"
    ],
    departments=[
        "NETWORK_OPERATIONS"
    ],
    regions=[
        "ONTARIO"
    ],
    classifications=[
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL"
    ],
)
```

The exact implementation will evolve during the security phase.

The retrieval interface should nevertheless be designed to accept security information from the beginning.

---

# 9. Metadata Filtering

Metadata filtering narrows the retrieval search space.

Potential filters include:

```text
technology
region
product
service
document_type
classification
department
incident_severity
date range
```

Example:

```text
Query:
"Show me the troubleshooting procedure for 5G handover failures in Ontario."

Filters:

technology = 5G
region = Ontario
```

The filter should be represented explicitly rather than hidden inside arbitrary query text.

Example:

```python
RetrievalFilters(
    technology=["5G"],
    region=["ONTARIO"],
    document_type=["RUNBOOK", "NETWORK_DOCUMENTATION"],
)
```

---

# 10. Vector Search

Vector search retrieves semantically similar chunks.

Each chunk has an embedding:

```text
chunk
   ↓
embedding
   ↓
vector database
```

The user query is embedded:

```text
query
   ↓
query embedding
   ↓
vector similarity search
```

PostgreSQL with `pgvector` is the initial vector store.

Conceptually:

```sql
SELECT
    chunk_id,
    content,
    embedding <=> :query_embedding AS distance
FROM chunks
WHERE ...
ORDER BY embedding <=> :query_embedding
LIMIT :candidate_k;
```

The exact SQL implementation belongs to the infrastructure layer.

The retrieval domain should not depend directly on PostgreSQL SQL syntax.

---

# 11. Vector Similarity

The initial implementation will use cosine-style similarity/distance supported by `pgvector`.

The system should consistently distinguish between:

```text
distance
```

and:

```text
similarity
```

Lower distance does not necessarily mean higher score unless the scoring convention explicitly defines it that way.

The application layer should normalize scores into a consistent representation before combining vector and keyword results.

---

# 12. Keyword Search

Vector search alone is insufficient for enterprise telecom knowledge.

Exact terminology matters.

Examples:

```text
AMF
SMF
UPF
gNodeB
5QI
QCI
S1AP
NGAP
IMS
VoLTE
```

Keyword search helps retrieve documents containing exact technical terms.

PostgreSQL full-text search may be used initially.

The architecture must keep keyword retrieval behind an abstraction.

Example:

```python
class KeywordRetriever:
    def search(
        self,
        query: str,
        filters: RetrievalFilters,
        limit: int,
    ) -> list[RetrievalCandidate]:
        ...
```

---

# 13. Hybrid Retrieval

Production retrieval should combine semantic and lexical retrieval.

```text
                 ┌──────────────┐
                 │    Query     │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
       Vector Search        Keyword Search
              │                   │
              └─────────┬─────────┘
                        ↓
                  Fusion Layer
                        ↓
                 Candidate Set
```

Hybrid retrieval improves robustness because:

* vector search handles semantic similarity
* keyword search handles exact terminology
* together they cover different retrieval failure modes

---

# 14. Candidate Generation

The first stage should retrieve more documents than are ultimately returned.

Example:

```text
final_k = 8

vector_k = 30
keyword_k = 30
```

This produces a candidate pool.

```text
Vector candidates
       +
Keyword candidates
       ↓
Deduplication
       ↓
Fusion
       ↓
60 → approximately 40 unique candidates
```

The exact values must be configuration-driven.

---

# 15. Fusion

Hybrid results must be combined into a single ranking.

The initial implementation may use:

## Reciprocal Rank Fusion

For each result:

```text
RRF(d) = Σ 1 / (k + rank(d))
```

where:

* `rank(d)` is the rank of the document
* `k` is a configurable constant

RRF is preferred initially because it does not require the vector and keyword scores to have identical distributions.

Later experiments may compare:

* weighted score fusion
* normalized score fusion
* reciprocal rank fusion
* learned ranking

The selected approach should be benchmarked rather than chosen purely by intuition.

---

# 16. Deduplication

The same chunk may appear in both vector and keyword retrieval results.

Duplicates must be removed before reranking.

The preferred identity is:

```text
chunk_id
```

not:

```text
content
```

because two different chunks may contain identical or very similar text but represent different source locations.

---

# 17. Reranking

Reranking is applied after candidate generation.

```text
Query
  ↓
Vector + Keyword Retrieval
  ↓
Candidate Pool
  ↓
Reranker
  ↓
Final Ranking
```

The reranker receives:

```text
query
candidate chunk
```

and produces a relevance score.

Reranking should be introduced only after baseline and hybrid retrieval are working.

Possible future implementations include:

* cross-encoder reranker
* hosted reranking API
* provider-specific reranking model
* local reranking model

The reranker must be abstracted behind an interface.

```python
class Reranker:
    def rerank(
        self,
        query: str,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:
        ...
```

---

# 18. Top-K Selection

After reranking, the system selects the final evidence set.

Example:

```text
candidate_k = 50
rerank_k = 20
final_k = 8
```

The final number must not be hard-coded into application logic.

Configuration should control:

```yaml
retrieval:
  vector_top_k: 30
  keyword_top_k: 30
  rerank_top_k: 20
  final_top_k: 8
```

Values will be tuned through evaluation.

---

# 19. Evidence Diversity

Returning eight nearly identical chunks is usually inferior to returning eight complementary pieces of evidence.

The final evidence selection should consider:

* document diversity
* section diversity
* source diversity
* relevance
* metadata compatibility

For example:

```text
Chunk 1 → 5G troubleshooting guide
Chunk 2 → network runbook
Chunk 3 → historical incident
Chunk 4 → postmortem
```

may provide better investigative coverage than:

```text
Chunk 1 → same document
Chunk 2 → same document
Chunk 3 → same document
Chunk 4 → same document
```

Diversity optimization will be introduced after basic ranking is reliable.

---

# 20. Evidence Validation

Before retrieval results are passed to generation, the system should validate:

* chunk exists
* document exists
* document version is valid
* source metadata is available
* security policy permits access
* chunk is not deleted
* chunk belongs to the current index
* required citation metadata exists

Invalid evidence must be removed.

---

# 21. Retrieval Result Model

The retrieval subsystem should expose a structured result.

Example:

```python
class RetrievalCandidate:
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID

    content: str

    vector_score: float | None
    keyword_score: float | None
    fusion_score: float | None
    rerank_score: float | None

    metadata: ChunkMetadata
```

The final retrieval response may contain:

```python
class RetrievalResult:
    query: str
    candidates: list[RetrievalCandidate]

    retrieval_strategy: str

    latency_ms: float
```

The exact Pydantic models will be implemented during the retrieval phase.

---

# 22. Retrieval Strategies

The system should support explicit retrieval strategies.

Initial strategies:

```text
vector
keyword
hybrid
```

Future strategies:

```text
hybrid_reranked
metadata_aware
query_routed
incident_investigation
agentic
```

Example:

```python
RetrievalStrategy.HYBRID
```

This allows experiments without rewriting the entire retrieval architecture.

---

# 23. Retrieval Interface

The application should depend on an abstract retrieval interface.

Example:

```python
class Retriever(Protocol):
    def retrieve(
        self,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        security_context: SecurityContext | None = None,
        top_k: int = 10,
    ) -> RetrievalResult:
        ...
```

Concrete implementations may include:

```text
VectorRetriever
KeywordRetriever
HybridRetriever
RerankedRetriever
```

The generation layer should depend on the interface, not the concrete implementation.

---

# 24. Retrieval Configuration

Retrieval behavior must be configuration-driven.

Example:

```yaml
retrieval:
  strategy: hybrid

  vector:
    enabled: true
    top_k: 30

  keyword:
    enabled: true
    top_k: 30

  fusion:
    method: rrf
    k: 60

  reranking:
    enabled: false
    top_k: 20

  final:
    top_k: 8
```

Configuration must be environment/profile aware.

Examples:

```text
dev
test
prod
```

---

# 25. Retrieval Logging

Each retrieval operation should produce structured telemetry.

Important fields:

```text
request_id
user_id
query
query_type
retrieval_strategy
filters
candidate_count
final_count
latency_ms
```

Scores may also be logged:

```text
vector_score
keyword_score
fusion_score
rerank_score
```

Sensitive query content must follow the platform's privacy and logging policies.

---

# 26. Retrieval Evaluation

Retrieval quality must be measured independently from answer generation.

A retrieval evaluation case should contain:

```json
{
  "question": "What causes 5G handover failures?",
  "expected_evidence": [
    "chunk-123",
    "chunk-456"
  ]
}
```

Important metrics include:

### Recall@K

Measures whether relevant evidence appears within the top K results.

```text
Recall@K =
relevant retrieved evidence
---------------------------
total relevant evidence
```

### Precision@K

Measures how much of the retrieved set is relevant.

```text
Precision@K =
relevant retrieved results
--------------------------
retrieved results
```

### MRR

Mean Reciprocal Rank measures how highly the first relevant result appears.

### NDCG

Normalized Discounted Cumulative Gain measures ranking quality while accounting for graded relevance.

Initial evaluation should focus on:

```text
Recall@5
Recall@10
MRR
NDCG@10
```

---

# 27. Retrieval Experiments

Retrieval changes must be evaluated experimentally.

Examples:

```text
Experiment 01:
Vector search vs keyword search

Experiment 02:
Vector vs keyword vs hybrid

Experiment 03:
RRF parameter tuning

Experiment 04:
Chunk size comparison

Experiment 05:
Reranker evaluation

Experiment 06:
Metadata filtering impact

Experiment 07:
Query rewriting impact
```

Each experiment should record:

```text
Hypothesis
Configuration
Dataset
Metrics
Results
Conclusion
```

---

# 28. Retrieval Failure Modes

The system must explicitly account for retrieval failures.

## Failure: No Results

Possible causes:

* query too specific
* poor embeddings
* incorrect filters
* missing documents
* incorrect chunking
* indexing failure

Possible response:

```text
No sufficiently relevant evidence found.
```

The generation layer must not fabricate an answer.

---

## Failure: Low-Confidence Results

The system may retrieve weak candidates.

Example:

```text
top_score < configured_threshold
```

The system should mark the retrieval result as low confidence.

---

## Failure: Conflicting Evidence

Different documents may contain contradictory information.

The retrieval system should preserve both relevant sources.

Generation must not silently choose one without considering source authority and recency.

---

## Failure: Unauthorized Evidence

Any unauthorized candidate must be discarded.

This is a security failure if unauthorized content reaches generation.

---

# 29. Retrieval and Recency

Telecom information changes over time.

Examples:

```text
network configuration
product SLA
support procedure
incident status
runbook
change procedure
```

Retrieval should eventually support temporal relevance.

Potential ranking factors:

```text
semantic relevance
lexical relevance
authority
recency
classification
document status
```

Recency must not automatically override authoritative historical evidence.

For incident investigation, historical documents may be more relevant than current documentation.

---

# 30. Retrieval and Source Authority

Not all documents have equal authority.

Potential authority hierarchy:

```text
Approved Runbook
    ↓
Official Network Documentation
    ↓
Approved Product Documentation
    ↓
Postmortem
    ↓
Incident Report
    ↓
Support Ticket
```

This hierarchy is domain-dependent and must be validated with telecom stakeholders.

Authority should be represented as metadata or a configurable ranking policy rather than embedded permanently into retrieval code.

---

# 31. Retrieval Security Boundary

The retrieval subsystem has a strict security boundary:

```text
User
  ↓
Authentication
  ↓
Authorization Context
  ↓
Retrieval Filters
  ↓
Candidate Retrieval
  ↓
Security Validation
  ↓
Evidence
  ↓
LLM
```

The following architecture is forbidden:

```text
User
  ↓
Vector Search
  ↓
LLM
  ↓
Security Filtering
```

Security filtering after LLM context construction is too late.

---

# 32. Initial Implementation Strategy

The retrieval subsystem will be implemented incrementally.

## Stage 1 — Vector Retrieval

Implement:

```text
query
→ embedding
→ pgvector
→ top-K chunks
```

No reranking.

No hybrid retrieval.

---

## Stage 2 — Keyword Retrieval

Implement:

```text
query
→ PostgreSQL keyword search
→ top-K chunks
```

---

## Stage 3 — Hybrid Retrieval

Implement:

```text
vector retrieval
+
keyword retrieval
↓
RRF
↓
candidate set
```

---

## Stage 4 — Metadata Filtering

Add:

```text
technology
region
product
service
document_type
classification
```

---

## Stage 5 — Reranking

Add a reranker behind an abstraction.

---

## Stage 6 — Security Filtering

Integrate:

```text
user
→ roles
→ access policies
→ retrieval constraints
```

---

## Stage 7 — Retrieval Evaluation

Create benchmark datasets and measure:

```text
Recall@K
MRR
NDCG
latency
```

---

## Stage 8 — Query-Aware Retrieval

Add:

```text
classification
rewriting
routing
```

Only after baseline retrieval is measurable.

---

# 33. Retrieval Package Structure

The implementation should follow the repository architecture.

```text
src/telco_rag/retrieval/
├── __init__.py
├── vector.py
├── keyword.py
├── hybrid.py
├── reranker.py
├── filters.py
└── retriever.py
```

Supporting models may live in:

```text
src/telco_rag/query/
src/telco_rag/domain/
```

Database-specific implementations belong behind infrastructure boundaries.

---

# 34. Definition of Done

The retrieval subsystem is considered complete for the initial RAG milestone when:

* vector retrieval works
* keyword retrieval works
* hybrid retrieval works
* metadata filtering works
* unauthorized content is excluded
* retrieval results are traceable to source documents
* retrieval is configurable
* retrieval latency is measured
* retrieval failures are handled
* retrieval evaluation dataset exists
* Recall@K is measured
* MRR is measured
* tests cover retrieval behavior
* retrieval does not generate answers
* generation receives only validated evidence

---

# 35. Future Evolution

The retrieval architecture is intentionally designed to evolve.

### Current

```text
Vector Search
```

### Next

```text
Vector + Keyword
```

### Production RAG

```text
Hybrid
+
Metadata Filtering
+
Reranking
+
Security
+
Evaluation
```

### Query-Aware RAG

```text
Classification
+
Rewriting
+
Routing
```

### Agentic RAG

```text
Planner
+
Retrieval Tools
+
Incident Search
+
Ticket Search
+
Runbook Search
+
Memory
+
Multi-step Investigation
```

The agentic layer must consume retrieval capabilities rather than bypassing them.

---

# 36. Architectural Rule

The most important retrieval rule is:

```text
Retrieve first.
Validate evidence.
Authorize evidence.
Rank evidence.
Then generate.
```

The LLM is not the retrieval system.

The LLM is not the enterprise knowledge base.

The LLM receives evidence produced by the retrieval subsystem and generates an answer grounded in that evidence.

