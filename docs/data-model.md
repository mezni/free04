# telco-rag — Data Model

## 1. Document Information

| Field            | Value        |
| ---------------- | ------------ |
| Project          | `telco-rag`  |
| Document         | Data Model   |
| Version          | 1.0          |
| Status           | Draft        |
| Database         | PostgreSQL   |
| Vector Extension | pgvector     |
| ORM              | SQLAlchemy 2 |
| Migrations       | Alembic      |

---

# 2. Purpose

This document defines the logical data model for `telco-rag`.

The model must support:

* enterprise documents
* document versions
* chunks
* embeddings
* telecom technologies
* products
* services
* regions
* incidents
* support tickets
* runbooks
* SLAs
* users
* roles
* access policies
* evaluation datasets

The model must support both the initial RAG platform and the future agentic investigation platform.

---

# 3. Data Modeling Principles

## 3.1 Domain First

The data model represents telecom concepts rather than database implementation details.

---

## 3.2 Explicit Relationships

Important relationships must be represented explicitly.

For example:

```text
Incident
   ↓
Technology
   ↓
Region
   ↓
Service
   ↓
Support Tickets
   ↓
Resolution
```

---

## 3.3 Traceability

Every generated answer should eventually be traceable through:

```text
Answer
 ↓
Citation
 ↓
Chunk
 ↓
Document Version
 ↓
Document
 ↓
Source
```

---

## 3.4 Security-Aware Data

Authorization-related data must be part of the data model.

A document must be classifiable and associated with appropriate access policies.

---

## 3.5 Versionability

Enterprise documents change.

The system must preserve document versions rather than silently overwriting historical knowledge.

---

# 4. Core Entity Model

The primary entities are:

```text id="4jydw9"
Document
DocumentVersion
Chunk
Embedding
Technology
Region
Product
Service
SLA
Incident
SupportTicket
Runbook
ChangeProcedure
User
Role
AccessPolicy
```

---

# 5. Entity Relationship Overview

```text id="6cl8ms"
                         ┌──────────────┐
                         │   Document   │
                         └──────┬───────┘
                                │
                         1      │      N
                                ▼
                       ┌────────────────┐
                       │ DocumentVersion│
                       └───────┬────────┘
                               │
                        1      │      N
                               ▼
                          ┌─────────┐
                          │  Chunk  │
                          └────┬────┘
                               │
                        1      │      1
                               ▼
                         ┌───────────┐
                         │ Embedding │
                         └───────────┘


Technology ───────┐
                  │
Region ───────────┤
                  │
Service ──────────┤
                  ▼
              Incident
                  │
                  ▼
            SupportTicket


Product ───────── Service
                  │
                  ▼
                 SLA


User ─────────── Role
 │
 ▼
AccessPolicy
 │
 ▼
Document
```

---

# 6. Document

The `Document` entity represents a logical enterprise knowledge document.

Examples:

* 5G troubleshooting guide
* outage postmortem
* product specification
* support guide
* SLA document

### Attributes

```text id="iy7m3p"
id
title
source
document_type
classification
department
created_at
updated_at
```

---

# 7. Document Identity

A document ID represents the logical document.

Versions must not create new logical document identities.

Example:

```text id="1fys6u"
Document
  ID: DOC-001

Versions:
  v1
  v2
  v3
```

This allows historical versions to remain associated with the same logical document.

---

# 8. Document Version

`DocumentVersion` represents a specific version of a document.

### Attributes

```text id="c2f9m1"
id
document_id
version
content_hash
source_uri
published_at
ingested_at
created_at
```

A content hash can be used to detect duplicate ingestion.

---

# 9. Document Classification

Initial classifications:

```text id="g0sh4m"
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Classification is an explicit domain value.

It must not be represented as arbitrary free text.

---

# 10. Document Type

Initial document types:

```text id="cz4f5x"
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

Additional types can be introduced as the domain evolves.

---

# 11. Chunk

A `Chunk` represents the smallest independently retrievable unit of a document version.

### Attributes

```text id="6w4d8g"
id
document_version_id
chunk_index
text
token_count
section_title
page_number
start_offset
end_offset
metadata
created_at
```

---

# 12. Chunk Requirements

Every chunk must retain enough information to reconstruct its source.

At minimum:

```text id="a6q6m1"
document_id
document_version_id
chunk_id
chunk_index
source
```

This is required for citations and debugging.

---

# 13. Chunk Metadata

Chunks inherit relevant document metadata.

Possible fields:

```text id="jy4e8s"
technology
region
service
product
department
classification
document_type
incident_severity
```

Structured fields should be preferred over arbitrary JSON where frequent filtering is expected.

JSON metadata may be used for extensible attributes.

---

# 14. Embedding

An `Embedding` represents the vector representation of a chunk.

### Attributes

```text id="25t4s8"
id
chunk_id
model
dimensions
vector
created_at
```

The model identifier must be stored so that different embedding models can coexist if necessary.

---

# 15. Embedding Versioning

Embedding models change.

Therefore:

```text id="mb2m15"
Chunk
 ├── Embedding Model A
 └── Embedding Model B
```

may exist temporarily during migrations or experiments.

The active embedding configuration determines which vectors are used for retrieval.

---

# 16. Technology

Represents a telecom technology.

Examples:

```text id="h39gk0"
5G
LTE
RAN
IMS
VoLTE
Fiber
Broadband
IoT
Core Network
Transport
```

### Attributes

```text id="h8t4rj"
id
name
code
description
created_at
```

---

# 17. Region

Represents a geographic or operational region.

Examples:

```text id="q4tx7z"
Ontario
Quebec
British Columbia
Atlantic
Prairies
```

### Attributes

```text id="h3m8nc"
id
name
code
description
created_at
```

---

# 18. Product

Represents a telecom product.

Examples:

```text id="y3p0qs"
Enterprise 5G
Business Fiber
Managed WAN
IoT Connectivity
```

### Attributes

```text id="5k2ez8"
id
name
code
description
status
created_at
updated_at
```

---

# 19. Service

Represents a telecom service.

Examples:

```text id="l6d3r2"
Mobile Connectivity
Enterprise Internet
Private 5G
Managed Connectivity
```

### Attributes

```text id="j6qk1m"
id
name
code
description
created_at
updated_at
```

---

# 20. Product-Service Relationship

A product may provide multiple services.

A service may be associated with multiple products.

Therefore:

```text id="3m5xgd"
Product
   │
   │ N:M
   │
Service
```

A junction table should represent the relationship.

---

# 21. SLA

Represents a service-level agreement.

### Attributes

```text id="9g5c3a"
id
service_id
name
description
availability_target
response_time
resolution_time
effective_from
effective_to
created_at
```

Additional SLA dimensions can be added later.

---

# 22. Incident

Represents a network or service incident.

### Attributes

```text id="1g1x3f"
id
incident_number
title
description
status
severity
technology_id
region_id
service_id
started_at
resolved_at
root_cause
resolution
created_at
updated_at
```

---

# 23. Incident Severity

Initial values:

```text id="tq9z3y"
LOW
MEDIUM
HIGH
CRITICAL
```

---

# 24. Incident Status

Initial values:

```text id="q2ef8d"
OPEN
INVESTIGATING
MITIGATED
RESOLVED
CLOSED
```

---

# 25. Incident Relationships

An incident may be related to:

* technologies
* regions
* services
* products
* support tickets
* runbooks
* postmortems

Conceptually:

```text id="w9k0rf"
Incident
 ├── Technology
 ├── Region
 ├── Service
 ├── Product
 ├── Support Tickets
 ├── Runbook
 └── Postmortem
```

---

# 26. Support Ticket

Represents a customer or internal support issue.

### Attributes

```text id="e7y0wj"
id
ticket_number
title
description
status
priority
customer_reference
product_id
service_id
technology_id
region_id
resolution
created_at
updated_at
resolved_at
```

---

# 27. Ticket Priority

Initial values:

```text id="v9a8sq"
LOW
MEDIUM
HIGH
URGENT
```

---

# 28. Ticket Status

Initial values:

```text id="a4kn2d"
OPEN
IN_PROGRESS
WAITING
RESOLVED
CLOSED
```

---

# 29. Incident-Ticket Relationship

An incident can affect multiple support tickets.

A support ticket may be associated with an incident.

Therefore:

```text id="ryx7j1"
Incident
   │
   │ 1:N
   ▼
SupportTicket
```

The relationship may initially be nullable because not every ticket belongs to a known incident.

---

# 30. Runbook

Represents an operational procedure used during troubleshooting or incident response.

### Attributes

```text id="xj7b8e"
id
name
description
technology_id
service_id
version
status
created_at
updated_at
```

Runbooks may also be represented as documents in the knowledge base.

---

# 31. Change Procedure

Represents a procedure for planned network or service changes.

### Attributes

```text id="3w5r4p"
id
name
description
technology_id
service_id
risk_level
approval_required
created_at
updated_at
```

Production changes must always remain subject to explicit operational authorization.

---

# 32. User

Represents an authenticated platform user.

### Attributes

```text id="j5v9r2"
id
username
display_name
department
status
created_at
updated_at
```

Authentication credentials should not be stored directly in the domain model unless required by the selected identity architecture.

---

# 33. User Status

Initial values:

```text id="e8m5k4"
ACTIVE
INACTIVE
SUSPENDED
```

---

# 34. Role

Represents an authorization role.

Initial roles:

```text id="x3b7a9"
NETWORK_ENGINEER
NOC_ENGINEER
SUPPORT_ENGINEER
PRODUCT_MANAGER
ADMIN
```

---

# 35. User-Role Relationship

A user may have multiple roles.

```text id="9h4rj1"
User
  │
  │ N:M
  ▼
Role
```

A junction table should represent this relationship.

---

# 36. Access Policy

Represents authorization rules for protected knowledge.

### Attributes

```text id="s2g7v5"
id
name
description
classification
department
technology
region
service
role
effect
created_at
updated_at
```

The exact authorization model will evolve toward RBAC/ABAC.

---

# 37. Access Policy Effect

Initial values:

```text id="1w5f4a"
ALLOW
DENY
```

Security evaluation must fail closed when authorization cannot be established.

---

# 38. Document Access

Documents may be protected by:

* classification
* role
* department
* region
* technology
* service
* explicit ACL

Conceptually:

```text id="w4x1hm"
User
 ↓
Roles
 ↓
Policies
 ↓
Document
 ↓
ALLOW / DENY
```

---

# 39. Explicit ACL

For more granular access control, an explicit document ACL may be introduced.

Conceptually:

```text id="2x4l1f"
Document
   ↓
DocumentACL
   ├── User
   ├── Role
   └── Permission
```

This is separate from general classification.

---

# 40. Permission Types

Initial permissions:

```text id="c8g5j2"
READ
SEARCH
ADMIN
```

Additional permissions may be introduced later.

---

# 41. Evaluation Case

Represents one RAG benchmark case.

### Attributes

```text id="q6s4y8"
id
question
expected_answer
metadata
created_at
```

---

# 42. Expected Evidence

An evaluation case should identify expected evidence.

Conceptually:

```text id="k5p9b4"
EvaluationCase
       │
       ▼
ExpectedEvidence
       │
       ▼
Document / Chunk
```

This allows retrieval metrics to be calculated.

---

# 43. Evaluation Run

Represents an execution of the RAG system against an evaluation dataset.

### Attributes

```text id="d8m2x7"
id
dataset_version
configuration_version
started_at
completed_at
status
```

---

# 44. Evaluation Result

Represents metrics from an evaluation run.

Examples:

```text id="4x9n5c"
recall_at_k
precision_at_k
mrr
ndcg
faithfulness
answer_relevance
citation_correctness
```

---

# 45. Database Tables

The initial relational schema is:

```text id="s1m4ko"
documents
document_versions
chunks
embeddings

technologies
regions
products
services
product_services
slas

incidents
incident_products
incident_tickets
support_tickets

runbooks
change_procedures

users
roles
user_roles
access_policies
document_acl

evaluation_cases
evaluation_expected_evidence
evaluation_runs
evaluation_results
```

Some relationships may be simplified during the first implementation.

---

# 46. Documents Table

Conceptual schema:

```sql
documents
---------
id                  UUID PK
title               VARCHAR
source               VARCHAR
document_type        VARCHAR
classification       VARCHAR
department           VARCHAR
created_at           TIMESTAMP
updated_at           TIMESTAMP
```

Constraints:

* `id` primary key
* classification must use a valid value
* document type must use a valid value

---

# 47. Document Versions Table

```sql
document_versions
-----------------
id                  UUID PK
document_id         UUID FK
version             VARCHAR
content_hash        VARCHAR
source_uri          TEXT
published_at        TIMESTAMP
ingested_at         TIMESTAMP
created_at          TIMESTAMP
```

Recommended constraint:

```text id="b5f4p0"
(document_id, version) UNIQUE
```

---

# 48. Chunks Table

```sql
chunks
------
id                    UUID PK
document_version_id   UUID FK
chunk_index           INTEGER
text                  TEXT
token_count           INTEGER
section_title         TEXT
page_number           INTEGER
start_offset          INTEGER
end_offset            INTEGER
metadata              JSONB
created_at            TIMESTAMP
```

Recommended constraint:

```text id="4r6q1w"
(document_version_id, chunk_index) UNIQUE
```

---

# 49. Embeddings Table

Conceptually:

```sql
embeddings
----------
id                    UUID PK
chunk_id              UUID FK
model                 VARCHAR
dimensions            INTEGER
vector                VECTOR
created_at            TIMESTAMP
```

The exact pgvector dimension must match the selected embedding model.

---

# 50. Vector Index

The vector index must be chosen based on:

* vector dimensions
* dataset size
* query latency
* update frequency

Possible pgvector indexes:

* HNSW
* IVFFlat

The initial implementation should use the simpler configuration appropriate for the development dataset and benchmark performance before optimizing.

---

# 51. Metadata Strategy

Metadata falls into two categories.

## Structured Metadata

Frequently filtered attributes:

```text id="x8l4qs"
technology
region
service
product
classification
document_type
department
severity
```

These should have explicit columns or relational associations.

## Flexible Metadata

Less frequently queried attributes can initially use:

```text id="o5y7z2"
JSONB
```

The schema should avoid turning JSONB into an unstructured replacement for relational modeling.

---

# 52. Referential Integrity

Foreign keys should enforce relationships.

Examples:

```text id="j3m4k7"
document_versions.document_id
        →
documents.id
```

```text id="1v7b3q"
chunks.document_version_id
        →
document_versions.id
```

```text id="8z1f6w"
embeddings.chunk_id
        →
chunks.id
```

Deletion policies must be explicitly defined.

---

# 53. Document Deletion

Documents should generally not be physically deleted immediately.

A future soft-delete strategy may be used.

Possible state:

```text id="c8v4y2"
ACTIVE
ARCHIVED
DELETED
```

This preserves auditability.

---

# 54. Version Lifecycle

A document version can progress through:

```text id="j7d4s8"
INGESTED
 ↓
PROCESSED
 ↓
INDEXED
 ↓
ACTIVE
 ↓
SUPERSEDED
 ↓
ARCHIVED
```

Only appropriate versions should participate in normal retrieval.

---

# 55. Data Lifecycle

The overall lifecycle is:

```text id="p5y7n1"
Source
 ↓
Ingest
 ↓
Parse
 ↓
Clean
 ↓
Metadata
 ↓
Chunk
 ↓
Embed
 ↓
Index
 ↓
Retrieve
 ↓
Evaluate
 ↓
Archive
```

---

# 56. Data Integrity Rules

The system must ensure:

1. Every chunk belongs to a document version.
2. Every document version belongs to a document.
3. Every embedding belongs to a chunk.
4. Every protected document has a classification.
5. Every active document version has valid content.
6. Every evaluation case has a question.
7. Evaluation evidence references valid knowledge objects.
8. Foreign-key relationships remain consistent.

---

# 57. Telecom Relationships

The model should preserve telecom context.

For example:

```text id="z4m8v2"
Technology
   │
   ├──────── Region
   │
   ├──────── Service
   │
   ├──────── Product
   │
   └──────── Incident
                 │
                 ├── Support Tickets
                 ├── Runbooks
                 └── Postmortem Documents
```

This is important for future multi-step investigations.

---

# 58. Search Model

The search system primarily operates over:

```text id="c2w8y5"
chunks
```

rather than directly over documents.

The chunk provides:

* text
* embedding
* source location
* metadata
* document relationship

Retrieval results can then be aggregated back to documents.

---

# 59. Retrieval Result Model

The database model should map to an application-level retrieval result.

Conceptually:

```python id="5d6k9r"
RetrievalResult(
    chunk_id=...,
    document_id=...,
    score=...,
    text=...,
    metadata=...,
    source=...,
)
```

The database schema must not leak directly into the generation layer.

---

# 60. Citation Model

Citations should reference stable identifiers.

Conceptually:

```text id="m4y7p2"
Citation
├── document_id
├── document_version_id
├── chunk_id
├── page
├── section
└── source
```

This enables:

```text
Answer
 ↓
Citation
 ↓
Chunk
 ↓
Document
```

---

# 61. Audit Data

Security-sensitive events should eventually be auditable.

Potential audit events:

```text id="r8x3m6"
document_access
search
authorization_decision
document_ingestion
policy_change
admin_action
```

Audit logging may be implemented separately from the initial domain tables.

---

# 62. Data Security

Sensitive fields must be protected.

The system must:

* minimize sensitive data
* avoid real customer data in development
* restrict database access
* avoid logging sensitive content
* enforce application-level authorization
* protect secrets externally

---

# 63. Synthetic Data Requirements

Synthetic data must be realistic enough to test relationships.

The generator should create:

```text id="8z3k1w"
Technologies
Regions
Products
Services
SLAs
Documents
Incidents
Tickets
Runbooks
```

Relationships must be intentionally generated rather than completely random.

---

# 64. Example Synthetic Dataset

A small example:

```text id="f2x7c9"
Technology:
    5G

Region:
    Ontario

Service:
    Mobile Connectivity

Incident:
    INC-1001
    "Intermittent 5G handover failures"

Related:
    5G
    Ontario
    Mobile Connectivity

Support Tickets:
    TCK-1001
    TCK-1002
    TCK-1003

Runbook:
    "5G Handover Troubleshooting"

Postmortem:
    "INC-1001 Postmortem"
```

This creates a meaningful retrieval and investigation graph.

---

# 65. Future Knowledge Graph Capability

The relational model should leave room for future knowledge-graph-like relationships.

Eventually:

```text id="5r8n2y"
Entity
  ↓
Relationship
  ↓
Entity
```

Example:

```text
Incident
   ├── CAUSED_BY → Technology
   ├── AFFECTED → Region
   ├── IMPACTED → Service
   ├── RELATED_TO → Ticket
   └── RESOLVED_BY → Runbook
```

This should not be implemented as a separate graph database prematurely.

---

# 66. Database Migration Strategy

All schema changes must use Alembic.

Workflow:

```text id="7w1z9c"
Model Change
    ↓
Alembic Migration
    ↓
Review
    ↓
Apply
    ↓
Integration Tests
```

Database changes must not be made manually in production environments.

---

# 67. Indexing Strategy

Indexes should support:

### Relational lookup

* foreign keys
* document IDs
* incident numbers
* ticket numbers
* product codes

### Filtering

* classification
* technology
* region
* service
* document type
* status

### Search

* full-text search fields
* vector embeddings

Indexes should be introduced based on measured query patterns.

---

# 68. Data Retention

Retention policies will eventually be defined for:

* document versions
* audit events
* evaluation runs
* application logs
* generated responses

The MVP will prioritize correctness and traceability over aggressive deletion.

---

# 69. Data Model Evolution

The data model will evolve in stages.

### Stage 1

```text
Documents
Versions
Chunks
Embeddings
```

### Stage 2

```text
Technology
Region
Product
Service
SLA
```

### Stage 3

```text
Incidents
Support Tickets
Runbooks
```

### Stage 4

```text
Users
Roles
Access Policies
ACL
```

### Stage 5

```text
Evaluation
Audit
Agent State
Memory
```

---

# 70. Final Logical Model

```text id="s4q2mz"
                         ┌───────────────┐
                         │   Document    │
                         └───────┬───────┘
                                 │
                                 ▼
                      ┌────────────────────┐
                      │  Document Version  │
                      └──────────┬─────────┘
                                 │
                                 ▼
                           ┌──────────┐
                           │  Chunk   │
                           └────┬─────┘
                                │
                                ▼
                         ┌────────────┐
                         │ Embedding  │
                         └────────────┘


 ┌────────────┐       ┌────────────┐       ┌────────────┐
 │ Technology │       │   Region   │       │  Service   │
 └─────┬──────┘       └─────┬──────┘       └─────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            ▼
                      ┌────────────┐
                      │  Incident  │
                      └─────┬──────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ SupportTicket│
                    └──────────────┘

 ┌───────────┐         ┌───────────┐
 │  Product  │────────▶│  Service  │
 └───────────┘         └─────┬─────┘
                             │
                             ▼
                           ┌─────┐
                           │ SLA │
                           └─────┘


 ┌────────┐       ┌────────┐       ┌────────────────┐
 │  User  │──────▶│  Role  │       │ Access Policy  │
 └────────┘       └────────┘       └───────┬────────┘
                                            │
                                            ▼
                                        Document
```

---

# 71. Core Data Model Principle

The data model must support the complete evidence chain:

```text
Enterprise Source
       ↓
Document
       ↓
Version
       ↓
Chunk
       ↓
Embedding
       ↓
Retrieval
       ↓
Evidence
       ↓
Citation
       ↓
Answer
```

At the same time, it must preserve telecom operational relationships:

```text
Technology
     ↓
Region
     ↓
Service
     ↓
Incident
     ↓
Tickets
     ↓
Resolution
     ↓
Runbook / Postmortem
```

This combination provides the foundation for both reliable RAG and future agentic telecom investigation.

