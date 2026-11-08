<!-- Sync Impact Report
version_change: initial_ratification → 1.0.0
modified_principles:
  [PRINCIPLE_1_NAME] → I. Hexagonal DDD Separation
  [PRINCIPLE_2_NAME] → II. Fixed Pipeline Order
  [PRINCIPLE_3_NAME] → III. First-Token Commit Boundary
  [PRINCIPLE_4_NAME] → IV. Secret Isolation
  [PRINCIPLE_5_NAME] → V. Immutable Usage & Cost Attribution
added_sections: Additional Constraints, Development Workflow, Governance
removed_sections: none (placeholder sections replaced with concrete content)
deferred_todos:
  - Identity provider and JWT claim mapping (PRD §10, ADR §17·1)
  - Secrets manager and rotation cadence (PRD §10, ADR §17·2)
  - Kubernetes cluster ownership and HA (PRD §10, ADR §17·3)
  - Quota/budget mode (hard-blocking vs alert-only) for pilot (PRD §10·4, ADR §17·4)
  - Retry budget (attempts and elapsed time) per team (PRD §10·5, ADR §17·5)
  - Alias conflict resolution across local and cloud targets (PRD §10·6, ADR §17·6)
  - Guardrail placement: inline vs opt-in by policy (PRD §10·8, ADR §17·7)
  - Evals ownership and golden dataset curation (PRD §10·9, ADR §17·8)
  - Audit and metrics retention requirements (PRD §10·10, ADR §17·9)
  - Non-chat modalities (embeddings, images) in v1 scope (PRD §10·12, ADR §17·10)
-->

# Internal LLM Gateway Constitution

## Core Principles

### I. Hexagonal DDD Separation
The domain crate owns routing policy, capability matching, and cost rules with zero I/O dependencies. Dependencies flow one way: gateway → application → domain. The domain depends on no other workspace crate and no I/O library. Application defines ports as traits; gateway supplies implementations. Any exception is a review blocker.

### II. Fixed Pipeline Order
Every data-plane request traverses one immutable stage sequence: transport, validate, authenticate, authorize, rate limit and quota, input guardrail, route, resilience loop, provider call, output guardrail, meter, audit. Each stage is a trait with a typed result of continue, reject, or terminate. Governance cannot be accidentally bypassed; the order is auditable. Only the resilience loop may call a provider, and it may call it more than once per AD-3 and AD-15.

### III. First-Token Commit Boundary
Failover and retry are allowed only before the first token is forwarded. After the first token, the stream is committed: no retry, no failover. A mid-stream upstream failure terminates the SSE stream with one gateway error event followed by the done sentinel. The first-token boundary is the single switch both routing and resilience read. This explicit boundary prevents double billing and corrupted responses.

### IV. Secret Isolation
Provider API keys never leave the gateway and are never returned by any API. Secrets live only in the company secret manager and are resolved at runtime through a secrets port, cached with a short TTL. Secrets are never written to persistent storage, never logged, and never returned by any API. Redaction is tested, not assumed. Missing principal or team mismatch is rejected before routing.

### V. Immutable Usage & Cost Attribution
Each provider attempt produces one immutable usage event keyed by request ID plus attempt ID, recording principal, team, alias, provider, model, token counts, latency, outcome, and a cost snapshot computed from the price table version active at event time. Aggregates are derived from events, never edited in place. Cost is a snapshot; editing prices creates a new version and does not alter past events.

## Additional Constraints

### Technology Stack Conventions
- Naming: snake_case for DB columns and JSON fields; PascalCase for Rust types; one trait per port named for the role, not the vendor; provider adapters named by provider id.
- Data and formats: UUIDv7 for request, attempt, and entity IDs; RFC 3339 UTC timestamps; all money as integer micro-units plus currency; all errors use the AD-11 envelope; SSE events follow the OpenAI delta shape with one done sentinel.
- State and cross-cutting: Writes go through control-plane use cases; data plane is read-only for config; errors via `thiserror` with no `unwrap` on request paths; structured `tracing` logs carry request id, team, alias, provider; rate limiting is token bucket in Redis via atomic scripts; config reads come from a versioned in-process snapshot.
- Stack: Rust (edition 2024), axum 0.8.9, tokio 1.54.1, tower 0.5.3, tower-http 0.7.1, reqwest 0.13.5, serde 1.0.229, serde_json 1.0.154, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23, opentelemetry 0.33.1, opentelemetry-otlp 0.33.1, prometheus 0.14.0, sqlx (PostgreSQL) 0.9.0, redis 1.8.1, PostgreSQL 17, Redis 7.4, Kubernetes 1.35, Python 3.12, httpx 0.28.1, pydantic 2.14.3.

### State Ownership
- Postgres is the system of record for control-plane configuration, usage events, and audit events.
- Redis holds only ephemeral, rebuildable state: rate-limit counters, circuit-breaker state, and the provider-health cache.
- No durable business fact exists only in Redis.
- Configuration is read as a versioned snapshot cached in process and refreshed on a bounded interval.

### Deployment Envelope
- Data-plane pods are stateless and horizontally scaled behind a load balancer on Kubernetes.
- Postgres and Redis are managed services.
- Secrets arrive through the secret manager.
- Telemetry goes to an OpenTelemetry collector feeding Prometheus and the log store.
- The control plane and web app deploy separately from the data plane.
- Every environment is provisioned from the same manifests with environment-specific values only.

## Development Workflow

### Delivery Phases
- **Phase 0 — Router**: OpenAI-compatible endpoint, streaming, failover before first token, validation, secrets, observability baseline, SDK sync/stream. Exit: one pilot team streams through the gateway.
- **Phase 1 — Production Pilot**: Identity and RBAC, retry and health, config snapshots, alerting, health dashboard, SDK hardening. Exit: 3–5 teams onboarded; RBAC enforced; on-call runbook.
- **Phase 2 — Cost & Control**: Rate limits and quotas, usage/cost attribution, circuit automation, capability-aware routing, cost dashboard, admin console. Exit: spend attributable; quotas enforced.
- **Phase 3 — Safety & Quality**: Input guardrails, budgets/alerts, eval harness and gates. Exit: guardrails configurable; eval gate for alias/model changes.

### Code Quality Requirements
- Zero `unwrap` or `expect` on production request paths; errors via `thiserror`.
- Telemetry follows the AD-10 contract; no prompt bodies or secrets in logs.
- RBAC and audit requirements apply where the story touches admin actions.
- The story's FR/AD references are updated in the coverage map.
- Docs or runbooks are updated when behavior or operations change.
- The change is reviewed against the architecture spine; a violation of AD-1 to AD-3 blocks merge.

### Testing Requirements
- Each principle section: succinct name line, paragraph capturing non-negotiable rules, explicit rationale if not obvious.
- Ensure each Principle section is declarative, testable, and free of vague language ("should" replaced with MUST/SHOULD rationale where appropriate).
- Principles are testable via unit tests that verify the invariant holds.

## Governance

**Amendment Procedure**: Constitutions amendments require documentation, approval, and a migration plan. All PRs/reviews must verify compliance with the current constitution. Complexity must be justified against existing principles. Amendments that remove or redefine backward-incompatible principles require MAJOR version bump. New principles or materially expanded guidance require MINOR version bump. Clarifications, wording fixes, and typo fixes require PATCH version bump.

**Versioning Policy**: Version format is MAJOR.MINOR.PATCH. The version line tracks: `Version: X.Y.Z | Ratified: YYYY-MM-DD | Last Amended: YYYY-MM-DD`. VERSION starts at 1.0.0 for initial ratification. RATIFICATION_DATE is the original adoption date. LAST_AMENDED_DATE is today if changes are made, otherwise the previous date is preserved.

**Compliance Review Expectations**: Each phase gate verifies constitution compliance. Phase 0 validates principles I and II. Phase 1 validates principles III and IV. Phase 2 validates principle V. Phase 3 validates all principles with operational evidence. Compliance review expects: amendment history is recorded, version bumps are justified, and no principle is violated by implemented features.

**Guidance File**: Runtime development guidance is maintained in `docs/constitution-guidance.md` which maps each AD and REQ to the corresponding principle and governance rule. This file is kept current through the amendment process and reviewed at each phase gate.

***

**Version**: 1.0.0 | **Ratified**: 2026-11-07 | **Last Amended**: 2026-11-07