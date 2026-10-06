# Telco RAG Domain Model

## 1. Purpose

The Domain Layer contains the core business concepts, rules, invariants, and relationships of the telecom RAG platform.

The domain must remain independent of:

* FastAPI
* SQLAlchemy
* PostgreSQL
* pgvector
* OpenRouter
* LangChain
* LangGraph
* Docker
* HTTP
* external APIs

The domain represents **what the telecom knowledge platform is**, not how the platform is implemented.

---

# 2. Domain-Driven Design Principles

The domain follows these principles:

1. Domain concepts use explicit business terminology.
2. Domain rules belong in the domain layer.
3. Infrastructure concerns do not enter the domain.
4. Entities have stable identities.
5. Value objects represent validated concepts without identity.
6. Aggregates protect consistency boundaries.
7. Domain services handle behavior that does not naturally belong to one entity.
8. Domain events represent meaningful state changes.
9. Domain models must be independently testable.
10. Security-sensitive domain concepts are explicit.
11. Document authority and classification are first-class concepts.
12. Retrieval operates primarily on document chunks.
13. LLM output is never treated as authoritative domain truth.

---

# 3. Telecom Domain

The initial business domain is enterprise telecommunications knowledge management.

The platform represents information about:

```text
Technologies
Regions
Products
Services
Network Components
Documents
Incidents
Support Tickets
Runbooks
Change Procedures
SLAs
Users
Roles
Access Policies
```

The platform then uses this domain information to support:

```text
Knowledge Retrieval
Troubleshooting
Incident Investigation
Product Questions
Support Questions
Operational Research
Enterprise Knowledge Discovery
```

---

# 4. Domain Boundaries

The initial domain can be divided into several logical areas.

```text
┌──────────────────────────────────────────────┐
│              Telco RAG Domain                │
│                                              │
│  Knowledge        Operations       Security  │
│      │                │                │     │
│  Documents         Incidents         Users   │
│  Chunks            Tickets           Roles   │
│  Runbooks          Products          ACLs    │
│  SLAs              Services                  │
│                                              │
└──────────────────────────────────────────────┘
```

The platform is initially implemented as a modular monolith.

These are logical domain boundaries, not separate microservices.

---

# 5. Core Domain Entities

The primary domain entities are:

```text
Document
DocumentVersion
Chunk
Incident
SupportTicket
Product
Service
Runbook
ChangeProcedure
SLA
User
Role
AccessPolicy
Technology
Region
```

Some are aggregate roots.

Others belong inside aggregates or represent supporting domain concepts.

---

# 6. Entity vs Value Object

An **Entity** has a stable identity.

Examples:

```text
Document
Incident
SupportTicket
Product
User
```

A **Value Object** represents a concept whose identity is defined by its values.

Examples:

```text
Classification
DocumentType
IncidentSeverity
TicketPriority
TechnologyCode
RegionCode
SourceLocation
TimeRange
```

Value objects should be immutable whenever practical.

---

# 7. Aggregate Roots

Initial aggregate roots:

```text
Document
Incident
SupportTicket
Product
User
```

The aggregate root controls access to the entities and value objects within its consistency boundary.

For example:

```text
Document
 ├── DocumentVersion
 │    └── Chunk
 └── metadata
```

The application layer should normally interact with the aggregate root rather than manipulating internal entities directly.

---

# 8. Document Aggregate

`Document` represents an enterprise knowledge source.

Example:

```text
Network Operations Runbook
5G Core Incident Procedure
VoLTE Troubleshooting Guide
Product SLA
```

A document has:

```text
id
title
document_type
classification
source
status
owner
created_at
updated_at
```

---

# 9. Document Identity

A document has a stable identifier.

Conceptually:

```python
class DocumentId:
    value: UUID
```

The identifier must remain stable across document versions.

Example:

```text
Document
    ID = DOC-123

Version 1
Version 2
Version 3
```

The document identity represents the logical knowledge object.

---

# 10. Document Classification

Every document has a classification.

Initial values:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Classification is a domain concept, not merely a database string.

Conceptually:

```python
class DocumentClassification(Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
```

Unknown classification must never silently become `PUBLIC`.

---

# 11. Document Type

Initial document types:

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

Document type affects:

* retrieval
* filtering
* authority
* evaluation
* presentation

It does not automatically determine security classification.

---

# 12. Document Lifecycle

A document progresses through explicit states.

Conceptually:

```text
DISCOVERED
    ↓
VALIDATED
    ↓
PROCESSING
    ↓
INDEXING
    ↓
ACTIVE
```

Failure states may include:

```text
QUARANTINED
FAILED
DEACTIVATED
```

A quarantined document must not participate in retrieval.

---

# 13. Document Version

`DocumentVersion` represents an immutable version of a document.

Example:

```text
Document: 5G Troubleshooting Guide

Version 1
Version 2
Version 3
```

Each version has:

```text
version_id
document_id
version_number
content_hash
source_timestamp
created_at
status
```

Once activated, a version should be treated as immutable.

---

# 14. Version Identity

A document version is uniquely identified by:

```text
Document ID
+
Version ID
```

Content identity may additionally use:

```text
SHA-256(content)
```

This supports:

* deduplication
* reproducibility
* ingestion idempotency
* auditability

---

# 15. Document Authority

Documents may have different levels of authority.

Examples:

```text
Official Network Runbook
Official Product Documentation
Support Knowledge Base
Incident Report
Informal Notes
```

Authority should be represented explicitly when required.

The retrieval system may use authority as a ranking signal.

However:

> Authority must not override authorization.

A highly authoritative restricted document remains inaccessible to unauthorized users.

---

# 16. Document Freshness

Document versions have temporal information.

Important fields include:

```text
created_at
effective_from
effective_until
updated_at
```

This allows the system to distinguish:

```text
current information
```

from:

```text
historical information
```

Historical versions must remain available when business requirements require historical retrieval.

---

# 17. Chunk

A `Chunk` represents a retrievable portion of a document version.

Relationship:

```text
Document
   ↓
DocumentVersion
   ↓
Chunk
```

A chunk should contain:

```text
chunk_id
document_version_id
text
position
section
page
source_location
metadata
```

---

# 18. Chunk Identity

A chunk must have a stable identifier.

Conceptually:

```python
class ChunkId:
    value: UUID
```

Chunk identity should be unique within the document-version context.

---

# 19. Chunk Source Location

Chunks must preserve source location information.

Examples:

```text
page = 14
section = "Troubleshooting"
paragraph = 3
```

or:

```text
section = "5GC / AMF"
offset_start = 1250
offset_end = 1870
```

This information supports citation generation.

---

# 20. Chunk Invariants

A chunk must:

* belong to exactly one document version
* contain non-empty content
* have a deterministic position
* preserve source information where available
* never belong to a quarantined document in the active index

---

# 21. Technology

`Technology` represents a telecom technology or technical platform.

Examples:

```text
4G
5G
LTE
VoLTE
IMS
EPC
5GC
RAN
```

Technology may be referenced by:

```text
Documents
Incidents
Products
Services
Support Tickets
```

---

# 22. Network Component

A network component represents an operational telecom element.

Examples:

```text
gNodeB
eNodeB
AMF
SMF
UPF
MME
HSS
PCRF
```

A network component may have:

```text
id
name
component_type
technology
vendor
```

Network components are important retrieval entities because technical questions frequently contain exact identifiers.

---

# 23. Region

`Region` represents a geographical or operational deployment region.

Examples:

```text
Ontario
Quebec
Western Canada
US East
US West
National
```

A region may be associated with:

```text
Documents
Incidents
Products
Services
Network Components
```

Region should use a controlled representation rather than arbitrary user-provided strings wherever possible.

---

# 24. Product

`Product` represents a telecom product offered or managed by the organization.

Example:

```text
5G Enterprise Connectivity
Business VoLTE
Private 5G
Managed SD-WAN
```

A product may contain:

```text
id
name
description
status
technology
```

Products may be related to multiple services.

---

# 25. Service

`Service` represents an operational or customer-facing telecom service.

Examples:

```text
Voice
Mobile Data
5G Connectivity
Internet
Enterprise VPN
Messaging
```

Products and services may have a many-to-many relationship.

```text
Product
  ↕
Service
```

---

# 26. SLA

`SLA` represents a service-level agreement.

An SLA may contain:

```text
id
service
product
effective_from
effective_until
availability_target
response_target
resolution_target
classification
```

SLA documents can be retrieved through RAG.

Structured SLA data should remain available for deterministic queries.

---

# 27. Incident

`Incident` represents an operational event affecting a telecom service or network.

An incident has:

```text
id
title
description
severity
status
technology
region
affected_service
started_at
resolved_at
created_at
```

---

# 28. Incident Severity

Initial values:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Severity is a domain value object.

Severity can influence:

* operational workflows
* retrieval
* investigation
* support escalation
* reporting

---

# 29. Incident Lifecycle

Initial incident states:

```text
OPEN
INVESTIGATING
MITIGATED
RESOLVED
CLOSED
```

Valid transitions should be explicit.

Example:

```text
OPEN
 ↓
INVESTIGATING
 ↓
MITIGATED
 ↓
RESOLVED
 ↓
CLOSED
```

Invalid transitions should be rejected by the domain.

---

# 30. Incident Relationships

An incident may relate to:

```text
Technology
Region
Product
Service
Network Component
Support Tickets
Documents
Postmortems
Runbooks
```

Example:

```text
Incident INC-1001
 ├── Technology: 5G
 ├── Region: Ontario
 ├── Service: Mobile Data
 ├── Component: AMF
 ├── Tickets: TCK-2001
 └── Postmortem: DOC-5001
```

---

# 31. Support Ticket

`SupportTicket` represents a customer or internal support request.

Fields include:

```text
id
customer_reference
title
description
priority
status
product
service
created_at
resolved_at
```

Support tickets may reference incidents.

Relationship:

```text
Incident
   │
   └── SupportTicket
```

An incident may have multiple associated tickets.

---

# 32. Ticket Priority

Initial values:

```text
LOW
MEDIUM
HIGH
URGENT
```

Priority is independent from incident severity.

For example:

```text
Incident Severity = HIGH
Ticket Priority = URGENT
```

These concepts must not be conflated.

---

# 33. Ticket Lifecycle

Initial ticket states:

```text
OPEN
IN_PROGRESS
WAITING
RESOLVED
CLOSED
```

State transitions should be validated.

---

# 34. Runbook

A `Runbook` represents operational procedures for handling technical situations.

Examples:

```text
5G Core Restart Procedure
AMF Troubleshooting
gNodeB Connectivity Recovery
VoLTE Incident Procedure
```

A runbook may be represented as a specialized document type.

The initial implementation may model it using:

```text
Document.document_type = RUNBOOK
```

rather than creating a separate database hierarchy.

---

# 35. Change Procedure

A `ChangeProcedure` represents an approved operational procedure for changing infrastructure or configuration.

Examples:

```text
5GC Configuration Change
RAN Software Upgrade
Network Maintenance Procedure
```

Change procedures may have stronger authorization requirements.

They must never automatically grant permission to execute the described change.

---

# 36. User

`User` represents an authenticated platform user.

Fields include:

```text
id
username
status
roles
created_at
```

Initial statuses:

```text
ACTIVE
INACTIVE
SUSPENDED
```

---

# 37. User Roles

Initial roles:

```text
NETWORK_ENGINEER
NOC_ENGINEER
SUPPORT_ENGINEER
PRODUCT_MANAGER
ADMIN
```

Roles determine capabilities through authorization policies.

Roles should not be interpreted directly by retrieval components without an authorization layer.

---

# 38. Access Policy

`AccessPolicy` represents authorization rules.

Conceptually:

```text
Subject
   ↓
Policy
   ↓
Resource
   ↓
Effect
```

Effects:

```text
ALLOW
DENY
```

A policy may constrain access based on:

```text
user
role
classification
department
region
product
resource
```

---

# 39. Security Domain Invariants

The domain must enforce or represent the following invariants:

1. Unknown classification cannot silently become `PUBLIC`.
2. Quarantined documents cannot become active evidence.
3. Inactive document versions cannot be treated as current.
4. Restricted information requires appropriate authorization.
5. Domain entities must have stable identity.
6. Document versions are immutable once activated.
7. Incident state transitions must be valid.
8. Ticket state transitions must be valid.
9. Security context must not be derived from untrusted LLM output.

---

# 40. Domain Relationships

The major relationships are:

```text
Document
   │
   ├── DocumentVersion
   │       │
   │       └── Chunk
   │
   ├── Technology
   ├── Region
   ├── Product
   └── Service
```

Operational relationships:

```text
Incident
   ├── Technology
   ├── Region
   ├── Product
   ├── Service
   ├── NetworkComponent
   └── SupportTicket
```

Commercial relationships:

```text
Product
   ↕
Service
   │
   └── SLA
```

Security relationships:

```text
User
   ↓
Role
   ↓
AccessPolicy
   ↓
Resource
```

---

# 41. Domain Context Map

The logical context map is:

```text
                    ┌──────────────────┐
                    │ Knowledge        │
                    │ Context          │
                    │                  │
                    │ Documents        │
                    │ Versions         │
                    │ Chunks           │
                    │ Runbooks         │
                    │ SLAs             │
                    └────────┬─────────┘
                             │
                             │
             ┌───────────────┼───────────────┐
             │               │               │
             ▼               ▼               ▼
      ┌────────────┐  ┌────────────┐  ┌────────────┐
      │ Operations │  │ Commercial │  │ Security   │
      │ Context    │  │ Context    │  │ Context    │
      │            │  │            │  │            │
      │ Incidents  │  │ Products   │  │ Users      │
      │ Tickets    │  │ Services   │  │ Roles      │
      │ Network    │  │ SLAs       │  │ Policies   │
      └────────────┘  └────────────┘  └────────────┘
```

These are logical boundaries inside the modular monolith.

---

# 42. Domain Services

A domain service is appropriate when a business rule does not naturally belong to one entity.

Potential domain services include:

```text
DocumentClassificationService
IncidentSeverityService
AccessPolicyService
EvidenceAuthorityService
```

Do not create a domain service simply to move ordinary code out of an entity.

---

# 43. Domain Service Example

An evidence authority calculation might conceptually be:

```python
class EvidenceAuthorityService:
    def calculate(
        self,
        document: Document,
        version: DocumentVersion,
    ) -> AuthorityScore:
        ...
```

This is domain logic because it represents a business concept.

The service should not know about:

```text
SQLAlchemy
pgvector
OpenRouter
FastAPI
```

---

# 44. Domain Events

Important domain events may include:

```text
DocumentCreated
DocumentVersionCreated
DocumentVersionActivated
DocumentDeactivated
IncidentCreated
IncidentSeverityChanged
IncidentResolved
TicketCreated
TicketResolved
UserSuspended
AccessPolicyChanged
```

Domain events represent meaningful state transitions.

They should not be used simply as a replacement for ordinary method calls.

---

# 45. Document Version Activation

One important domain operation is version activation.

Conceptually:

```python
document.activate_version(version_id)
```

The domain should ensure:

```text
version exists
version is valid
version is not quarantined
version belongs to document
```

Activation may emit:

```text
DocumentVersionActivated
```

---

# 46. Incident State Transition

The domain should control incident transitions.

Example:

```python
incident.start_investigation()
incident.mitigate()
incident.resolve()
incident.close()
```

Rather than allowing arbitrary assignment:

```python
incident.status = "CLOSED"
```

This keeps lifecycle rules explicit.

---

# 47. Ticket State Transition

Likewise:

```python
ticket.start()
ticket.wait()
ticket.resolve()
ticket.close()
```

should enforce valid transitions.

---

# 48. Domain Invariants vs Application Rules

Not every rule belongs in the domain.

### Domain rule

```text
An incident cannot transition from CLOSED back to INVESTIGATING.
```

This belongs in the domain.

### Application rule

```text
Only NOC engineers may access a particular API endpoint.
```

This belongs in authorization/application security.

### Infrastructure rule

```text
Use HNSW for pgvector.
```

This belongs in infrastructure/configuration.

---

# 49. Domain and Retrieval

Retrieval is not itself a domain entity.

It is a platform capability operating over domain knowledge.

The domain defines:

```text
Document
DocumentVersion
Chunk
Classification
Technology
Region
Product
Service
Incident
```

The retrieval subsystem defines:

```text
vector search
keyword search
hybrid search
reranking
candidate fusion
```

This separation is intentional.

---

# 50. Domain and Generation

Generation is not a domain authority.

The LLM produces:

```text
candidate answer
```

The domain provides:

```text
authoritative enterprise information
```

Therefore:

```text
LLM output
≠
Domain truth
```

Answers must be grounded against authorized evidence.

---

# 51. Domain and Security

Security is a cross-cutting concern.

The domain represents security concepts:

```text
Classification
User
Role
AccessPolicy
```

The security/application layers enforce access.

Therefore:

```text
Domain
   ↓
defines security concepts

Security/Application
   ↓
enforces access

Infrastructure
   ↓
persists and evaluates policies
```

---

# 52. Domain and Temporal Information

Temporal concepts are important in telecom operations.

Examples:

```text
Incident started yesterday
Current 5G configuration
SLA effective in 2025
Postmortem from 2024
Historical network outage
```

The domain must preserve temporal information rather than flattening everything into current state.

---

# 53. Current vs Historical Knowledge

The system must distinguish:

```text
CURRENT
```

from:

```text
HISTORICAL
```

For example:

```text
Document Version 3
effective_from = 2026-01-01

Document Version 2
effective_until = 2025-12-31
```

A query asking:

> What was the procedure in 2025?

must be able to retrieve the historically valid version.

---

# 54. Domain Metadata

Important controlled metadata includes:

```text
classification
document_type
technology
region
product
service
department
incident_severity
vendor
network_component
```

Metadata should use structured domain types wherever practical.

Flexible metadata may exist as an extension mechanism, but important business fields should not be hidden inside arbitrary JSON.

---

# 55. Domain Package

Initial implementation:

```text
src/telco_rag/domain/
├── __init__.py
├── documents.py
├── chunks.py
├── users.py
├── access.py
├── incidents.py
├── tickets.py
└── products.py
```

Potential future organization:

```text
domain/
├── knowledge/
├── operations/
├── commercial/
├── security/
└── shared/
```

Do not introduce deeper packaging until the domain actually requires it.

---

# 56. Shared Kernel

Some concepts are shared across multiple contexts.

Potential shared concepts:

```text
EntityId
Classification
Technology
Region
ProductId
ServiceId
TimeRange
SourceLocation
```

Keep the shared kernel small.

A large shared kernel creates excessive coupling between domain areas.

---

# 57. Domain Validation

Domain objects must validate their invariants.

Examples:

```text
Document title cannot be empty.
Document classification must be valid.
Chunk content cannot be empty.
Incident severity must be valid.
Incident state transitions must be valid.
Ticket priority must be valid.
User status must be valid.
```

Pydantic may be used for boundary validation.

Core domain behavior should not become dependent on Pydantic-specific infrastructure behavior unnecessarily.

---

# 58. Domain Testing

Domain tests should be fast and deterministic.

Examples:

```text
test_document_requires_classification
test_document_version_is_immutable
test_document_can_activate_valid_version
test_quarantined_version_cannot_activate
test_incident_valid_transition
test_incident_invalid_transition
test_ticket_valid_transition
test_ticket_invalid_transition
test_classification_values
test_authorization_policy_values
```

These tests should not require:

```text
PostgreSQL
Docker
OpenRouter
FastAPI
```

---

# 59. Domain Test Example

Conceptually:

```python
def test_incident_can_be_resolved():
    incident = Incident.open(...)

    incident.start_investigation()
    incident.mitigate()
    incident.resolve()

    assert incident.status == IncidentStatus.RESOLVED
```

Invalid behavior:

```python
def test_closed_incident_cannot_be_reopened():
    incident = Incident.closed(...)

    with pytest.raises(InvalidIncidentTransition):
        incident.start_investigation()
```

---

# 60. Persistence Independence

The domain model must not contain SQLAlchemy declarations such as:

```python
Column(...)
relationship(...)
Mapped(...)
```

inside the core domain entities if this can be avoided.

Instead:

```text
Domain Model
     ↑
Repository Interface
     ↑
SQLAlchemy Infrastructure Model
```

This keeps the domain independent.

---

# 61. Domain-to-Database Mapping

The infrastructure layer maps domain concepts to database structures.

Example:

```text
Domain Document
       ↓
SQLAlchemy DocumentModel
       ↓
documents table
```

The reverse mapping occurs when loading data:

```text
documents table
       ↓
SQLAlchemy DocumentModel
       ↓
Domain Document
```

---

# 62. Domain-to-API Mapping

The API should not expose domain objects directly.

The flow is:

```text
Domain
 ↓
Application DTO
 ↓
API DTO
 ↓
JSON
```

This keeps domain evolution independent from API contracts.

---

# 63. Domain and Agentic RAG

The future agentic layer will operate on domain capabilities.

An investigation agent may ask:

```text
Search knowledge
Search incidents
Search tickets
Search products
```

But the agent does not redefine the domain.

The agent orchestrates existing capabilities.

---

# 64. Agent Boundaries

The future architecture should look like:

```text
Agent
  │
  ├── Knowledge Search
  │       ↓
  │   Domain Knowledge
  │
  ├── Incident Search
  │       ↓
  │   Incident Domain
  │
  ├── Ticket Search
  │       ↓
  │   Support Domain
  │
  └── Product Search
          ↓
      Commercial Domain
```

This prevents the agent from becoming the domain model.

---

# 65. Memory Is Not Domain Knowledge

Agent memory should remain distinct from enterprise knowledge.

```text
Enterprise Knowledge
    ↓
Documents / Incidents / Products

Agent Memory
    ↓
Conversation / Preferences / Working State
```

Memory must not silently become an authoritative source.

---

# 66. Domain Security Invariants

The following rules are non-negotiable:

```text
1. Unauthorized information must never become accessible evidence.

2. RESTRICTED information requires explicit authorization.

3. Unknown classification must not default to PUBLIC.

4. Quarantined documents must not become active knowledge.

5. Inactive versions must not be treated as current.

6. LLM output cannot change authorization state.

7. LLM output cannot grant permissions.

8. Agents cannot bypass domain security.

9. Historical data must retain temporal identity.

10. Domain entities must preserve stable identity.
```

---

# 67. Initial Domain Model Summary

```text
                         TELCO DOMAIN
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      KNOWLEDGE           OPERATIONS          COMMERCIAL
          │                   │                   │
     Document             Incident             Product
        │                   │                   │
     Version             Ticket               Service
        │                   │                   │
      Chunk            Network Element          SLA
        │
   Classification
          │
   Technology / Region
          │
          └───────────────┐
                          ▼
                      SECURITY
                          │
                       User
                          │
                        Role
                          │
                    Access Policy
```

---

# 68. Implementation Priority

Implement the domain in this order:

```text
1. Shared identifiers
2. Enumerations/value objects
3. Document
4. DocumentVersion
5. Chunk
6. Technology
7. Region
8. Product
9. Service
10. SLA
11. Incident
12. SupportTicket
13. User
14. Role
15. AccessPolicy
16. Domain services
17. Domain events
18. Domain tests
```

Do not implement all entities simultaneously.

Build and test each aggregate incrementally.

---

# 69. Definition of Done

The domain layer is complete for the initial platform when:

* [ ] Core entities are defined.
* [ ] Aggregate roots are identified.
* [ ] Value objects are defined.
* [ ] Domain enums are explicit.
* [ ] Domain invariants are implemented.
* [ ] Document lifecycle is modeled.
* [ ] Document versioning is modeled.
* [ ] Chunk identity and source location are modeled.
* [ ] Telecom technologies are modeled.
* [ ] Regions are modeled.
* [ ] Products and services are modeled.
* [ ] Incidents are modeled.
* [ ] Support tickets are modeled.
* [ ] Users and roles are modeled.
* [ ] Access policies are modeled.
* [ ] Incident transitions are validated.
* [ ] Ticket transitions are validated.
* [ ] Domain events are identified.
* [ ] Domain tests do not require infrastructure.
* [ ] Domain code contains no FastAPI dependency.
* [ ] Domain code contains no SQLAlchemy dependency.
* [ ] Domain code contains no OpenRouter dependency.
* [ ] Domain code contains no LangChain dependency.

---

# 70. Final Domain Rule

The domain layer represents the **authoritative business concepts and rules** of the telecom platform.

The fundamental separation is:

```text
DOMAIN
What is true?
What is valid?
What entities exist?
What state transitions are allowed?
What relationships exist?

APPLICATION
What use case are we executing?
How do we coordinate the operation?

INFRASTRUCTURE
How do we persist, retrieve, embed, or call external systems?

API
How does the outside world communicate with the application?

RAG
How do we retrieve and ground knowledge?

AGENTS
How do we orchestrate multiple capabilities?
```

The core principle is:

> **The domain defines the meaning and invariants of the telecom system; everything else must adapt to that domain rather than allowing infrastructure or LLM behavior to define it.**

