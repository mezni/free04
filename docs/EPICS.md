---
status: draft
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - llmgw/PRD.md
  - llmgw/ARCHITECTURE.md
  - llmgw/ARCHITECTURE-SPINE.md
---

# Internal LLM Gateway - Epic Breakdown

## Overview

This document decomposes the PRD, Architecture, and Architecture Spine into epics and implementable stories. It is organized by user value and delivery phase so the team can ship the Phase 0 router first, then harden into the production platform.

**Delivery phases (from PRD §7):** Phase 0 Router → Phase 1 Production Pilot → Phase 2 Cost & Control → Phase 3 Safety & Quality.

**Decomposition rules:**

- Each story delivers observable value and is independently testable.
- Every functional requirement (REQ-*) maps to at least one story.
- Architecture decisions (AD-*) are enforced by stories, especially AD-1 to AD-3.
- P0 stories are required for the Phase 0 pilot; P1 for broad rollout; P2 post-rollout.
- No story assumes an unbuilt dependency without naming it.

---

## Requirements Inventory

### Functional Requirements

**Core Router (Rust Data Plane)**

- FR-ENG-01: Expose an OpenAI-compatible `/v1/chat/completions` endpoint with request and response schema. (REQ-ENG-01, P0)
- FR-ENG-02: Stream SSE chunks without buffering the full response. (REQ-ENG-02, P0)
- FR-ENG-03: Fail over to a secondary provider on 5xx or timeout before the first token. (REQ-ENG-03, P0)
- FR-ENG-04: Map internal model aliases to provider-specific model IDs. (REQ-ENG-04, P1)
- FR-ENG-05: Configure providers, aliases, base URLs, and fallback order at runtime; secrets via secrets manager. (REQ-ENG-05, P1)
- FR-ENG-06: Track provider/model capability support and exclude incompatible targets. (REQ-ENG-06, P1)
- FR-ENG-07: Select targets by declarative policy: cost, latency, context, residency, capability, weighting. (REQ-ENG-07, P1)
- FR-ENG-08: Classify upstream outcomes and act per class. (REQ-ENG-08, P0)

**Request Validation**

- FR-VAL-01: Validate requests against the OpenAI Chat Completions schema and reject malformed input with 400. (REQ-VAL-01, P0)
- FR-VAL-02: Enforce payload size, token, message, and parameter limits per team/model. (REQ-VAL-02, P1)
- FR-VAL-03: Reject unknown aliases/models and unsupported parameters before any upstream call. (REQ-VAL-03, P1)

**Authentication, Authorization & RBAC**

- FR-AUTH-01: Authenticate callers via OIDC/JWT and/or gateway-issued scoped API keys. (REQ-AUTH-01, P0)
- FR-AUTH-02: Enforce a role/permission model over teams, models, providers, and operations. (REQ-AUTH-02, P0)
- FR-AUTH-03: Issue, rotate, and revoke scoped API keys; never expose provider keys. (REQ-AUTH-03, P0)
- FR-AUTH-04: Record an append-only, queryable audit log of who called what and the decision. (REQ-AUTH-04, P1)
- FR-AUTH-05: Separate administrative actions from data-plane calls. (REQ-AUTH-05, P1)

**Rate Limiting & Quotas**

- FR-RATE-01: Enforce requests-per-minute per principal and team. (REQ-RATE-01, P1)
- FR-RATE-02: Enforce tokens-per-minute (input/output) per principal, team, and model. (REQ-RATE-02, P1)
- FR-RATE-03: Enforce daily/monthly quotas with hard (reject) or soft (alert) modes. (REQ-RATE-03, P1)
- FR-RATE-04: Prevent one principal/team from starving others; return 429 with Retry-After. (REQ-RATE-04, P2)

**Resilience: Retry & Circuit Breaker**

- FR-RES-01: Retry eligible failures with exponential backoff plus jitter, bounded by an attempt/time budget. (REQ-RES-01, P1)
- FR-RES-02: Never retry 4xx (except configured 429) and never retry after the first streamed token. (REQ-RES-02, P0)
- FR-RES-03: Per-provider circuit breaker with open, half-open, and closed states. (REQ-RES-03, P1)
- FR-RES-04: Active/passive health checks distinguishing down from slow, feeding routing and the dashboard. (REQ-RES-04, P1)
- FR-RES-05: Track attempts to avoid double billing and expose attempt metadata. (REQ-RES-05, P1)

**Usage & Cost Tracking**

- FR-COST-01: Record tokens, provider, model, latency, and outcome for every request. (REQ-COST-01, P1)
- FR-COST-02: Maintain per-provider/model pricing and compute cost per request. (REQ-COST-02, P1)
- FR-COST-03: Attribute usage and cost to team, principal, key, and model alias. (REQ-COST-03, P1)
- FR-COST-04: Configure budgets and alert or block on threshold breach. (REQ-COST-04, P2)

**Secrets Manager**

- FR-SEC-01: Store provider credentials in the company secrets manager, never in plaintext config or repos. (REQ-SEC-01, P0)
- FR-SEC-02: Support rotation and revocation with runtime resolution, caching, and access control. (REQ-SEC-02, P1)
- FR-SEC-03: Access only the secrets for served providers/teams; never expose secrets at the edge. (REQ-SEC-03, P0)
- FR-SEC-04: Guarantee secrets and credentials never appear in logs, traces, or error responses. (REQ-SEC-04, P0)

**Observability**

- FR-OBS-01: Emit OpenTelemetry traces across stages and upstream calls with request IDs propagated. (REQ-OBS-01, P0)
- FR-OBS-02: Emit Prometheus metrics for rate, errors, latency, TTFT, overhead, fallback, health, tokens, and cost. (REQ-OBS-02, P0)
- FR-OBS-03: Emit structured logs with consistent fields and PII/prompt redaction. (REQ-OBS-03, P1)
- FR-OBS-04: Provide alert rules for SLO breach, circuit-open, fallback spike, and quota/budget breach. (REQ-OBS-04, P1)

**Guardrails**

- FR-GRD-01: Configurable pre-flight input checks per team/model. (REQ-GRD-01, P1)
- FR-GRD-02: Configurable output checks before delivery. (REQ-GRD-02, P2)
- FR-GRD-03: Policy actions allow, flag, redact, block with fail-open or fail-closed modes. (REQ-GRD-03, P1)
- FR-GRD-04: Centrally configure, version, and audit guardrail policies. (REQ-GRD-04, P2)

**Evals**

- FR-EVAL-01: Run prompt/model/alias changes against golden datasets and compare to a baseline. (REQ-EVAL-01, P2)
- FR-EVAL-02: Define pass thresholds that gate promotion of alias/policy changes. (REQ-EVAL-02, P2)
- FR-EVAL-03: Optionally sample production traffic for continuous eval. (REQ-EVAL-03, P2)

**Monitoring & Analytics Web App**

- FR-UI-01: Health dashboard for provider and gateway health, circuit state, and fallback activity. (REQ-UI-01, P1)
- FR-UI-02: Usage and cost dashboard by team, principal, model, and provider over time. (REQ-UI-02, P1)
- FR-UI-03: Latency and reliability view: request rate, error rate, TTFT, overhead, retry/fallback. (REQ-UI-03, P1)
- FR-UI-04: Admin console for teams, keys, quotas, budgets, aliases, and policies. (REQ-UI-04, P2)
- FR-UI-05: Audit viewer queryable by principal, model, and time. (REQ-UI-05, P2)

**Python SDK**

- FR-SDK-01: Provide `LLMRouterClient` on top of `httpx`. (REQ-SDK-01, P0)
- FR-SDK-02: Support synchronous completion and streaming generators. (REQ-SDK-02, P0)
- FR-SDK-03: Support context management for connection cleanup. (REQ-SDK-03, P1)
- FR-SDK-04: Map errors to `LLMRouterError`, `UpstreamError`, `AuthError`, `RateLimitError`, `ValidationError`. (REQ-SDK-04, P1)
- FR-SDK-05: Send scoped API key/OIDC token, config via env, never embed provider keys. (REQ-SDK-05, P0)
- FR-SDK-06: Propagate and expose request/trace IDs. (REQ-SDK-06, P1)

### NonFunctional Requirements

- NFR-01 Performance: proxy-added overhead below 5ms p99, excluding upstream inference.
- NFR-02 Availability: 99.9% gateway SLO in v1, measured against defined upstreams.
- NFR-03 Scalability: non-blocking async execution; documented concurrency and payload limits.
- NFR-04 Security: authN/authZ on every data-plane call; managed secrets; no secret/PII leakage.
- NFR-05 Auditability: security-relevant admin and access actions are logged and queryable.
- NFR-06 Compatibility: OpenAI-compatible surface; versioned API; deprecation policy.
- NFR-07 Maintainability: DDD layout with enforced dependency direction; stages independently testable.
- NFR-08 Code Quality: zero `unwrap` on production request paths; `thiserror`; `tracing`/OpenTelemetry.
- NFR-09 Compliance: data classification, residency, and retention rules respected per provider/team.
- NFR-10 Reliability: graceful degradation for each dependency, with no silent hard failure.

### Additional Requirements

- AD-1: Hexagonal dependency direction (gateway → application → domain; domain has no I/O). Enforced by E1.S1.
- AD-2: Fixed ordered request pipeline; stages are traits with continue/reject/terminate results. Enforced by E1.S2 through E1.S6 and E2.
- AD-3: Failover and retry only before the first token; mid-stream failure terminates the stream. Enforced by E1.S3 and E1.S10.
- AD-4: Provider adapter contract with capability descriptor and error taxonomy. Enforced by E1.S4.
- AD-5: Pure, deterministic routing function. Enforced by E3.S5.
- AD-6: Postgres is the system of record; Redis is ephemeral and rebuildable. Enforced by E2.S4, E3.S2, E4.S1, E4.S4.
- AD-7: Secrets only from the managed secret store. Enforced by E1.S7.
- AD-8: OIDC or scoped API key; every call has a principal, team, and scopes. Enforced by E2.S1 to E2.S3.
- AD-9: Immutable usage events keyed by request plus attempt, with cost snapshots. Enforced by E4.S4 and E4.S5.
- AD-10: Fixed telemetry contract (span names, `llmgw_` metrics, request ID). Enforced by E1.S8 and E5.
- AD-11: Stable OpenAI-compatible error envelope; no raw provider errors. Enforced by E1.S5.
- AD-12: Control plane and data plane are separate deployments and credential scopes. Enforced by E2.S5.
- AD-13: Kubernetes stateless data plane, managed Postgres/Redis, OTel collector, separate control plane. Enforced by E9.S1 to E9.S5.
- AD-14: Guardrails are provider-agnostic stages with explicit fail-open/closed modes. Enforced by E6.S1.
- AD-15: Attempt budget and idempotency key; every attempt recorded. Enforced by E3.S1.
- AD-16: Python SDK is a thin transport and typed models, not a second router. Enforced by E1.S9 and E8.
- AD-17: No prompt/response body persistence by default; opt-in redacted capture. Enforced by E1.S8 and E5.S1.
- Stack pinning: Rust 1.99.1, axum 0.8.9, tokio 1.54.1, Postgres 17, Redis 7.4, Python 3.12, httpx 0.28.1, pydantic 2.14.3.
- Starter template: none specified in Architecture; use a Cargo workspace scaffold for the three crates.
- Migrations run as a gated job, not on pod startup. Enforced by E9.S2.
- API versioning and deprecation policy. Enforced by E1.S2 and NFR-06.

### UX Design Requirements

No formal UX contract exists. The monitoring and analytics web app is an internal operational tool; its stories use the control-plane API contract and standard internal dashboard patterns. If a UX contract is later authored, add UX-DR items and revisit E5.

### FR Coverage Map

| Requirement | Epic / Story |
| --- | --- |
| REQ-ENG-01 | E1.S2 |
| REQ-ENG-02 | E1.S3 |
| REQ-ENG-03 | E1.S10 |
| REQ-ENG-04 | E3.S6 |
| REQ-ENG-05 | E2.S4 |
| REQ-ENG-06 | E3.S4 |
| REQ-ENG-07 | E3.S5 |
| REQ-ENG-08 | E1.S5 |
| REQ-VAL-01 | E1.S6 |
| REQ-VAL-02 | E2.S7 |
| REQ-VAL-03 | E2.S7 |
| REQ-AUTH-01 | E2.S1 |
| REQ-AUTH-02 | E2.S3 |
| REQ-AUTH-03 | E2.S2 |
| REQ-AUTH-04 | E2.S6 |
| REQ-AUTH-05 | E2.S5 |
| REQ-RATE-01 | E4.S1 |
| REQ-RATE-02 | E4.S2 |
| REQ-RATE-03 | E4.S3 |
| REQ-RATE-04 | E4.S7 |
| REQ-RES-01 | E3.S1 |
| REQ-RES-02 | E1.S3, E3.S1 |
| REQ-RES-03 | E3.S2 |
| REQ-RES-04 | E3.S3 |
| REQ-RES-05 | E3.S1 |
| REQ-COST-01 | E4.S4 |
| REQ-COST-02 | E4.S5 |
| REQ-COST-03 | E4.S6 |
| REQ-COST-04 | E4.S8 |
| REQ-SEC-01 | E1.S7 |
| REQ-SEC-02 | E2.S8 |
| REQ-SEC-03 | E1.S7 |
| REQ-SEC-04 | E1.S7 |
| REQ-OBS-01 | E1.S8 |
| REQ-OBS-02 | E1.S8 |
| REQ-OBS-03 | E5.S1 |
| REQ-OBS-04 | E5.S2 |
| REQ-GRD-01 | E6.S1 |
| REQ-GRD-02 | E6.S3 |
| REQ-GRD-03 | E6.S1 |
| REQ-GRD-04 | E6.S4 |
| REQ-EVAL-01 | E7.S1 |
| REQ-EVAL-02 | E7.S2 |
| REQ-EVAL-03 | E7.S3 |
| REQ-UI-01 | E5.S3 |
| REQ-UI-02 | E5.S4 |
| REQ-UI-03 | E5.S3 |
| REQ-UI-04 | E5.S5 |
| REQ-UI-05 | E5.S6 |
| REQ-SDK-01 | E1.S9 |
| REQ-SDK-02 | E1.S9 |
| REQ-SDK-03 | E8.S1 |
| REQ-SDK-04 | E8.S2 |
| REQ-SDK-05 | E1.S9 |
| REQ-SDK-06 | E8.S3 |

## Epic List

| Epic | Title | Phase | Primary value |
| --- | --- | --- | --- |
| E1 | Governed Front Door | Phase 0 | A pilot team can call, stream, and fail over through one governed endpoint. |
| E2 | Identity & Access | Phase 1 | Only authorized teams and keys can call allowed models; admin actions are separate and audited. |
| E3 | Resilience & Intelligent Routing | Phase 1–2 | Provider incidents degrade gracefully and routing picks the right target. |
| E4 | Limits, Usage & Cost Control | Phase 2 | Spend is visible, attributable, and bounded. |
| E5 | Operations, Health & Analytics | Phase 1–2 | SRE and FinOps can see and act on health, latency, and cost. |
| E6 | Safety & Guardrails | Phase 3 | Data and model use follow company policy. |
| E7 | Evals & Quality Gates | Phase 3 | Model and alias changes are validated before rollout. |
| E8 | Python SDK & Developer Experience | Phase 0–1 | Adoption is easier than bypassing the gateway. |
| E9 | Deployment & Environments | Phase 0–1 | The platform runs reliably and reproducibly. |

---

## Epic 1: Governed Front Door

**Goal:** A pilot team can call one OpenAI-compatible endpoint through the gateway, stream tokens, fail over before the first token, and be observable — with secrets safe.

**Phase:** 0 (Router). **Exit criteria:** one pilot team streams via the gateway; failover before first token works; no secrets in logs; traces and metrics visible.

### Story 1.1: Workspace Foundation and CI

As a platform engineer,
I want a Cargo workspace with enforced domain boundaries and CI,
So that routing rules cannot leak into infrastructure and every change is verified.

**Acceptance Criteria:**

**Given** a clean checkout
**When** `cargo build` and `cargo test` run
**Then** the three crates `llmgw-domain`, `llmgw-application`, and `llmgw-gateway` compile and tests pass.
**And** `llmgw-domain` has no dependency on workspace crates or I/O libraries (AD-1).
**And** CI runs format, clippy with warnings denied, unit tests, and a no-`unwrap` lint on request paths.
**And** the workspace scaffold records the pinned toolchain.

**Covers:** AD-1, NFR-07, NFR-08.

### Story 1.2: OpenAI-Compatible Non-Streaming Endpoint

As an application developer,
I want `POST /v1/chat/completions` to accept and return the OpenAI schema,
So that I can call the gateway without changing my client code.

**Acceptance Criteria:**

**Given** a valid chat completion request
**When** the caller posts to `/v1/chat/completions`
**Then** the response matches the OpenAI Chat Completions response shape.
**And** a request ID is generated and returned in a response header.
**And** an unknown model or alias returns 404 or 400 with the stable error envelope (AD-11).
**And** the endpoint is versioned under `/v1` with a documented deprecation policy.

**Covers:** FR-ENG-01, AD-2, AD-11, NFR-06.

### Story 1.3: SSE Streaming with Commit Boundary

As an application developer,
I want the gateway to stream tokens as they arrive,
So that time-to-first-token matches a direct provider call.

**Acceptance Criteria:**

**Given** a request with `stream=true`
**When** the upstream emits chunks
**Then** each chunk is forwarded as an SSE delta without buffering the full response.
**And** the stream ends with the done sentinel.
**And** after the first forwarded token no retry or failover occurs (AD-3).
**And** a mid-stream upstream failure emits one gateway error event followed by the done sentinel.
**And** contract tests cover normal completion, client disconnect, and mid-stream failure.

**Covers:** FR-ENG-02, FR-RES-02, AD-3.

### Story 1.4: Provider Adapter Contract and First Adapters

As a platform engineer,
I want a single adapter contract with capability descriptors,
So that providers can be added or swapped without changing routing or transport.

**Acceptance Criteria:**

**Given** the adapter port
**When** Ollama, vLLM, and OpenAI adapters are implemented
**Then** each converts the canonical request to its wire format and back.
**And** each declares capabilities: tools, JSON mode, vision, context window, streaming.
**And** each maps failures into the shared error taxonomy.
**And** contract tests run each adapter against a mock server.
**And** no provider-specific field appears in the OpenAI-compatible response.

**Covers:** FR-ENG-01, FR-ENG-06, FR-RES-02, AD-4.

### Story 1.5: Error Taxonomy and Error Envelope

As an application developer,
I want stable, documented errors,
So that my client can react correctly and never sees provider internals.

**Acceptance Criteria:**

**Given** an upstream or gateway failure
**When** the request fails
**Then** the response uses the OpenAI-compatible error envelope with a gateway error code and request ID.
**And** 4xx errors do not trigger failover; 5xx and connect/read timeouts do.
**And** 429 responses honor Retry-After and are retried only when the policy allows.
**And** raw provider bodies and secrets never appear in the response (AD-11).

**Covers:** FR-ENG-08, AD-11.

### Story 1.6: Request Schema Validation

As a platform engineer,
I want malformed requests rejected before any provider call,
So that bad input cannot waste quota, cost, or upstream capacity.

**Acceptance Criteria:**

**Given** a request body
**When** it is malformed, exceeds the size limit, or contains unsupported parameters
**Then** it is rejected with 400 and `invalid_request`.
**And** the error includes the request ID and a human-readable message.
**And** no upstream call is made for a rejected request.
**And** validation runs before authentication-sensitive side effects.

**Covers:** FR-VAL-01, AD-2, AD-11.

### Story 1.7: Secrets Port and Provider Credentials

As a security reviewer,
I want provider credentials resolved from the managed secret store,
So that keys never live in config, repositories, logs, or traces.

**Acceptance Criteria:**

**Given** a configured provider
**When** the gateway starts or refreshes config
**Then** its credentials are resolved through the secrets port with a short TTL cache.
**And** no secret is written to Postgres, config maps, environment files, logs, traces, or error responses (AD-7, AD-17).
**And** the gateway accesses only secrets for providers and teams it serves.
**And** a redaction test proves secrets do not appear in telemetry.

**Covers:** FR-SEC-01, FR-SEC-03, FR-SEC-04, AD-7.

### Story 1.8: Observability Baseline

As an SRE engineer,
I want traces, metrics, and a request ID for every request,
So that I can see what happened without SSHing into a pod.

**Acceptance Criteria:**

**Given** a data-plane request
**When** it completes or fails
**Then** one trace contains spans named for the pipeline stages.
**And** Prometheus exposes `llmgw_requests_total`, request duration, TTFT, proxy overhead, and fallback counters.
**And** the request ID is returned to the caller and present in logs and traces.
**And** prompt and response bodies are absent from telemetry by default (AD-17).

**Covers:** FR-OBS-01, FR-OBS-02, AD-10, AD-17.

### Story 1.9: Python SDK Sync, Stream, and Keys

As an application developer,
I want a small Python client for sync and streaming calls,
So that adopting the gateway is faster than integrating a provider directly.

**Acceptance Criteria:**

**Given** an API key and base URL from environment or arguments
**When** I call `LLMRouterClient(...).chat.completions.create(...)`
**Then** the request is sent to the gateway and the response is parsed into typed models.
**And** `stream=True` returns an iterator of typed deltas.
**And** the client sends the scoped API key or OIDC token and never embeds provider keys.
**And** the client implements no routing, failover, or retry logic (AD-16).

**Covers:** FR-SDK-01, FR-SDK-02, FR-SDK-05, AD-16.

### Story 1.10: Failover Before First Token

As a platform engineer,
I want automatic failover before tokens are emitted,
So that a primary provider outage does not fail the caller's request.

**Acceptance Criteria:**

**Given** an ordered target list from routing
**When** the primary returns 5xx or times out before the first token
**Then** the gateway attempts the next eligible target.
**And** a successful fallback is recorded in metrics and traces.
**And** if the primary fails only after the first token, no failover occurs (AD-3).
**And** integration tests simulate primary 5xx, timeout, and mid-stream failure.

**Covers:** FR-ENG-03, FR-RES-02, AD-3, AD-15.

### Story 1.11: Phase 0 Pilot Readiness

As a product owner,
I want a pilot team onboarded and load-tested,
So that we can validate the core bet before broadening scope.

**Acceptance Criteria:**

**Given** the Phase 0 build
**When** a pilot team requests access
**Then** they complete onboarding and their first call in under 30 minutes.
**And** a load test reports p99 proxy overhead and TTFT overhead against the NFR target.
**And** an on-call runbook and rollback procedure exist.
**And** exit criteria for Phase 0 are recorded with evidence.

**Covers:** NFR-01, NFR-02, Phase 0 exit criteria.

---

## Epic 2: Identity & Access

**Goal:** Only authorized teams and scoped keys can call allowed models; admin actions are separate and audited.

**Phase:** 1 (Production Pilot).

### Story 2.1: OIDC/JWT Authentication

As an application developer,
I want to authenticate with my company identity,
So that I do not need a separate credential to use the gateway.

**Acceptance Criteria:**

**Given** a valid OIDC JWT
**When** I call the gateway
**Then** the gateway resolves a principal and team from the configured claims.
**And** an expired, malformed, or missing token returns 401 `unauthorized`.
**And** the identity port isolates the IdP choice so it can be replaced.
**And** token validation tests cover expiry, signature, issuer, and audience.

**Covers:** FR-AUTH-01, AD-8.

### Story 2.2: Scoped API Keys

As a team admin,
I want to issue, rotate, and revoke keys scoped to my team and models,
So that services can call the gateway without sharing provider credentials.

**Acceptance Criteria:**

**Given** a team admin with the right scope
**When** they create a key
**Then** the plaintext key is returned once and stored only as a hash.
**And** the key is scoped to a team and allowed aliases/models.
**And** a rotated key invalidates the previous key; a revoked key returns 401 on next use.
**And** provider keys remain internal to the gateway.

**Covers:** FR-AUTH-03, AD-8.

### Story 2.3: RBAC Enforcement

As a security reviewer,
I want roles and scopes enforced on every call,
So that no principal can exceed its granted access.

**Acceptance Criteria:**

**Given** the roles platform admin, team admin, developer, viewer, and service
**When** a principal calls a model or performs an operation outside its scopes
**Then** the gateway returns 403 `forbidden` before routing.
**And** cross-team access is denied by default.
**And** authorization decisions are unit-tested for every role and resource combination.

**Covers:** FR-AUTH-02, AD-8.

### Story 2.4: Versioned Configuration and Aliases

As a platform engineer,
I want runtime provider, alias, and fallback configuration with versioning,
So that policy changes take effect without redeploying and can be rolled back.

**Acceptance Criteria:**

**Given** a control-plane configuration change
**When** it is saved
**Then** it is versioned with an author and timestamp.
**And** data-plane pods refresh a versioned snapshot within a bounded interval.
**And** a rollback restores the previous snapshot.
**And** the active config version is exposed in telemetry.

**Covers:** FR-ENG-04, FR-ENG-05, AD-6.

### Story 2.5: Control-Plane and Data-Plane Separation

As a security reviewer,
I want admin operations isolated from inference traffic,
So that a compromised data-plane pod cannot rewrite policy or keys.

**Acceptance Criteria:**

**Given** the two deployments
**When** the data plane runs
**Then** it holds read-only config access and appends only usage and audit events.
**And** the control-plane API is separately authenticated and not reachable from the data plane.
**And** data-plane pods hold no admin credentials (AD-12).

**Covers:** FR-AUTH-05, AD-12.

### Story 2.6: Audit Log

As a security reviewer,
I want an append-only audit log,
So that I can prove who called what and who changed policy.

**Acceptance Criteria:**

**Given** a security-relevant action
**When** it occurs
**Then** an immutable audit event records principal, team, action, resource, decision, and timestamp.
**And** the log is queryable by principal and time.
**And** events cannot be edited or deleted through the API.

**Covers:** FR-AUTH-04, AD-6, NFR-05.

### Story 2.7: Request Limits and Parameter Guard

As a platform engineer,
I want per-team and per-model request limits,
So that a single caller cannot exhaust capacity or send unsupported parameters.

**Acceptance Criteria:**

**Given** configured limits
**When** a request exceeds payload, token, message, or parameter limits
**Then** it is rejected before any upstream call with a 400 or 413 and a stable error code.
**And** unknown aliases/models and unsupported parameters are rejected before routing.
**And** limit changes are versioned control-plane data.

**Covers:** FR-VAL-02, FR-VAL-03.

### Story 2.8: Secret Rotation and Least Privilege

As a security reviewer,
I want credential rotation without downtime and least-privilege secret access,
So that a leaked key can be replaced quickly and blast radius is small.

**Acceptance Criteria:**

**Given** a rotated provider secret
**When** the secret manager publishes it
**Then** the gateway uses the new value after cache refresh without a restart.
**And** the gateway can read only secrets for providers and teams it serves.
**And** rotation and failed resolution are logged without secret values.

**Covers:** FR-SEC-02, AD-7.

---

## Epic 3: Resilience & Intelligent Routing

**Goal:** Provider incidents degrade gracefully and routing selects the right target deterministically.

**Phase:** 1–2.

### Story 3.1: Bounded Retry, Attempt Budget, and Idempotency

As a platform engineer,
I want retries bounded by an attempt and time budget,
So that transient failures recover without retry storms or double billing.

**Acceptance Criteria:**

**Given** a retryable failure
**When** the resilience loop retries
**Then** it uses exponential backoff with jitter and stops at the attempt or time budget.
**And** every attempt produces its own usage event (AD-9, AD-15).
**And** a request carries an idempotency key generated by the gateway or supplied by the client.
**And** no retry occurs after the stream is committed.

**Covers:** FR-RES-01, FR-RES-05, AD-15.

### Story 3.2: Per-Provider Circuit Breaker

As an SRE engineer,
I want a circuit breaker per provider,
So that a failing provider stops receiving traffic until it recovers.

**Acceptance Criteria:**

**Given** a provider exceeding the error-rate or latency threshold
**When** the breaker opens
**Then** routing excludes that provider from new attempts.
**And** the breaker enters half-open and restores only after successful probes.
**And** circuit state is shared across pods and exported as a metric.
**And** state rebuilds safely after a Redis restart.

**Covers:** FR-RES-03, AD-6.

### Story 3.3: Provider Health (Down vs Slow)

As an SRE engineer,
I want health to distinguish down from slow,
So that I can route latency-sensitive traffic away without discarding a usable provider.

**Acceptance Criteria:**

**Given** active probes and passive request signals
**When** a provider is failing or slow
**Then** health reports down or degraded separately.
**And** the health snapshot is an input to routing, not a mid-stream check.
**And** health state appears in the metrics and dashboard contracts.

**Covers:** FR-RES-04, AD-5, AD-10.

### Story 3.4: Provider Capability Matrix

As a platform engineer,
I want routing to know what each model supports,
So that failover never selects a target that cannot serve the request.

**Acceptance Criteria:**

**Given** a request requiring tools, JSON mode, vision, or a minimum context window
**When** routing builds the candidate list
**Then** targets lacking the capability are excluded.
**And** the capability matrix is versioned control-plane data.
**And** an unsupported requirement returns a clear error rather than a silent downgrade.

**Covers:** FR-ENG-06, AD-4.

### Story 3.5: Declarative Routing Policy

As a product owner,
I want routing to weigh cost, latency, residency, and capability,
So that alias intent maps to the cheapest or fastest valid target.

**Acceptance Criteria:**

**Given** a request, principal, policy, and health snapshot
**When** the pure routing function runs
**Then** it returns an ordered target list with reasons and no I/O, clock, or randomness.
**And** identical inputs produce identical output.
**And** unit tests cover cost ceilings, latency objectives, residency allow-lists, and capability requirements.

**Covers:** FR-ENG-07, AD-5.

### Story 3.6: Model Aliases

As an application developer,
I want to request `auto`, `fast`, `cheap`, or `smart`,
So that I can express intent instead of hard-coding a provider model.

**Acceptance Criteria:**

**Given** an alias request
**When** the alias is resolved
**Then** it maps to one or more provider-specific models according to policy.
**And** alias conflicts across local and cloud targets follow the documented resolution rule.
**And** an explicit model request bypasses alias resolution.

**Covers:** FR-ENG-04, AD-5.

---

## Epic 4: Limits, Usage & Cost Control

**Goal:** Spend is visible, attributable to teams and models, and bounded.

**Phase:** 2 (Cost & Control).

### Story 4.1: Request Rate Limits

As a team admin,
I want requests-per-minute limits per principal and team,
So that one caller cannot monopolize the gateway.

**Acceptance Criteria:**

**Given** a configured limit
**When** a principal exceeds it
**Then** the gateway returns 429 `rate_limited` with Retry-After.
**And** counters are stored in Redis using atomic token-bucket operations.
**And** limits are enforced before any upstream call.
**And** losing Redis follows the documented degradation policy.

**Covers:** FR-RATE-01, AD-6.

### Story 4.2: Token Rate Limits

As a FinOps owner,
I want tokens-per-minute limits for input and output,
So that expensive long-context traffic is bounded.

**Acceptance Criteria:**

**Given** a configured token limit
**When** a request would exceed the input or output budget
**Then** it is rejected with 429 before the upstream call, or terminated per policy.
**And** actual usage is reconciled after completion.
**And** limits can be scoped per principal, team, and model.

**Covers:** FR-RATE-02.

### Story 4.3: Daily and Monthly Quotas

As a FinOps owner,
I want hard or soft quotas,
So that runaway usage either alerts or stops according to policy.

**Acceptance Criteria:**

**Given** a configured quota in hard or soft mode
**When** usage crosses the threshold
**Then** hard mode rejects subsequent requests with `quota_exceeded`, and soft mode alerts only.
**And** quota state resets on the configured period.
**And** quota changes are versioned and audited.

**Covers:** FR-RATE-03, AD-9.

### Story 4.4: Immutable Usage Metering

As a FinOps owner,
I want one immutable usage event per attempt,
So that reports reconcile to requests and retries are visible.

**Acceptance Criteria:**

**Given** a provider attempt
**When** it completes, fails, or is abandoned
**Then** one immutable usage event records request ID, attempt ID, principal, team, alias, provider, model, tokens, latency, and outcome.
**And** the event is deduplicated by request ID plus attempt ID.
**And** events are written by a bounded async writer and never edited in place.

**Covers:** FR-COST-01, AD-9.

### Story 4.5: Price Table and Cost Snapshot

As a FinOps owner,
I want cost computed from a versioned price table,
So that historical reports do not change when prices change.

**Acceptance Criteria:**

**Given** a price table version
**When** a usage event is created
**Then** the cost is computed and stored as a snapshot in integer micro-units with currency.
**And** editing prices creates a new version and does not alter past events.
**And** a reconciliation job detects price or token mismatches.

**Covers:** FR-COST-02, AD-9.

### Story 4.6: Cost Attribution and Reporting

As a FinOps owner,
I want usage attributed to team, principal, key, alias, provider, and model,
So that I can allocate spend accurately.

**Acceptance Criteria:**

**Given** recorded usage events
**When** I query a time range
**Then** totals are available by team, principal, key, alias, provider, and model.
**And** every event has a non-null team and alias.
**And** aggregates are derived views, never edited facts.

**Covers:** FR-COST-03, AD-9.

### Story 4.7: Fairness

As a platform engineer,
I want fair sharing across teams and principals,
So that one caller cannot starve others during contention.

**Acceptance Criteria:**

**Given** contention between teams
**When** limits are enforced
**Then** a single team cannot consume all capacity beyond its configured share.
**And** rejected requests return 429 with Retry-After.
**And** fairness behavior is covered by a load test.

**Covers:** FR-RATE-04.

### Story 4.8: Budgets and Alerts

As a FinOps owner,
I want budgets with alerts or blocking,
So that spend cannot silently exceed plan.

**Acceptance Criteria:**

**Given** a team budget and threshold
**When** spend crosses the threshold
**Then** an alert fires, and in blocking mode further requests return `quota_exceeded`.
**And** budget changes are versioned and audited.
**And** alerts include team, period, spend, and threshold.

**Covers:** FR-COST-04.

---

## Epic 5: Operations, Health & Analytics

**Goal:** SRE and FinOps can see and act on health, latency, reliability, and cost.

**Phase:** 1–2.

### Story 5.1: Structured Logs and Redaction

As an SRE engineer,
I want structured logs without prompt bodies or secrets,
So that debugging does not create a data leak.

**Acceptance Criteria:**

**Given** a request
**When** logs are emitted
**Then** each log line carries request ID, team, alias, provider, and outcome.
**And** prompt and response bodies are absent by default.
**And** a redaction test proves secrets and PII do not appear.
**And** opt-in body capture is per team, redacted, and retention-bounded.

**Covers:** FR-OBS-03, AD-17.

### Story 5.2: Alert Rules

As an SRE engineer,
I want alerts for the failure modes that page me,
So that I can respond before users notice.

**Acceptance Criteria:**

**Given** Prometheus metrics
**When** an SLO burn, circuit-open, fallback spike, quota/budget breach, secret resolution failure, or config refresh failure occurs
**Then** the corresponding alert fires with a runbook link.
**And** alert thresholds are versioned in the deployment repo.
**And** a test validates each alert rule against synthetic metrics.

**Covers:** FR-OBS-04.

### Story 5.3: Health, Latency, and Reliability Dashboard

As an SRE engineer,
I want one dashboard for gateway and provider health,
So that I can diagnose an incident in the first 60 seconds.

**Acceptance Criteria:**

**Given** the monitoring web app
**When** I open the health view
**Then** I see provider down vs slow, circuit state, fallback activity, request rate, error rate, TTFT, and proxy overhead.
**And** data is filterable by team, alias, and provider.
**And** the view reflects the fixed telemetry contract (AD-10).

**Covers:** FR-UI-01, FR-UI-03, AD-10.

### Story 5.4: Usage and Cost Dashboard

As a FinOps owner,
I want usage and cost over time by team and model,
So that I can find anomalies and allocate spend.

**Acceptance Criteria:**

**Given** usage events
**When** I open the cost view
**Then** I see usage and cost by team, principal, model, and provider over a selected period.
**And** I can filter and export the data.
**And** totals reconcile with the usage event store.

**Covers:** FR-UI-02, AD-9.

### Story 5.5: Admin Console

As a team admin,
I want to manage teams, keys, quotas, budgets, aliases, and policies,
So that I can operate without direct database access.

**Acceptance Criteria:**

**Given** an authenticated admin with the right role
**When** I manage a resource
**Then** changes are validated, versioned, and audited.
**And** unauthorized roles see a 403 and no data.
**And** destructive actions require confirmation.

**Covers:** FR-UI-04, AD-12.

### Story 5.6: Audit Viewer

As a security reviewer,
I want to query the audit log,
So that I can investigate access and policy changes.

**Acceptance Criteria:**

**Given** audit events
**When** I query by principal, model, or time range
**Then** I see matching events with decision, resource, and timestamp.
**And** results are exportable.
**And** the viewer cannot modify or delete events.

**Covers:** FR-UI-05, NFR-05.

---

## Epic 6: Safety & Guardrails

**Goal:** Data and model use follow company policy, with auditable, configurable controls.

**Phase:** 3 (Safety & Quality).

### Story 6.1: Input Guardrail Stage and Policy Modes

As a security reviewer,
I want configurable input checks with explicit modes,
So that each team's data policy is enforced before traffic reaches a provider.

**Acceptance Criteria:**

**Given** a guardrail policy
**When** an input is evaluated
**Then** the stage returns allow, flag, redact, or block.
**And** each policy declares fail-open or fail-closed behavior.
**And** input guardrails run before routing (AD-2, AD-14).
**And** the provider of the check is swappable behind one interface.

**Covers:** FR-GRD-01, FR-GRD-03, AD-14.

### Story 6.2: Moderation and PII Detection

As a security reviewer,
I want moderation and PII detection per team and model,
So that unsafe or sensitive content is handled consistently.

**Acceptance Criteria:**

**Given** an enabled policy
**When** input contains unsafe or sensitive content
**Then** the configured action (flag, redact, or block) applies and is audited.
**And** the check meets its per-stage latency budget.
**And** disabling the policy restores pass-through behavior.

**Covers:** FR-GRD-01.

### Story 6.3: Output Guardrails

As a security reviewer,
I want output checks before delivery,
So that unsafe completions do not reach callers.

**Acceptance Criteria:**

**Given** an output policy
**When** a non-streaming completion is produced
**Then** the policy is applied before delivery and its action is audited.
**And** for streaming, the guardrail must not buffer a committed stream; deferred behavior is documented.
**And** a blocked output returns a stable error or redaction per policy.

**Covers:** FR-GRD-02, AD-3, AD-14.

### Story 6.4: Guardrail Governance

As a security reviewer,
I want guardrail policies versioned, auditable, and access-controlled,
So that policy changes are reviewable and reversible.

**Acceptance Criteria:**

**Given** a guardrail policy change
**When** it is saved
**Then** it is versioned with author and timestamp.
**And** only authorized roles can change it.
**And** a rollback restores the previous version.
**And** changes appear in the audit log.

**Covers:** FR-GRD-04, AD-12, NFR-05.

---

## Epic 7: Evals & Quality Gates

**Goal:** Model and alias changes are validated against a baseline before rollout.

**Phase:** 3.

### Story 7.1: Eval Harness and Golden Datasets

As a product owner,
I want to run a model or alias against a golden dataset,
So that I can compare quality to a baseline before changing production.

**Acceptance Criteria:**

**Given** a golden dataset and a candidate alias or model
**When** an eval run executes
**Then** results are stored with scores, inputs, and the baseline comparison.
**And** datasets and thresholds are versioned.
**And** eval runs never persist unredacted production bodies by default.

**Covers:** FR-EVAL-01, AD-17.

### Story 7.2: Regression Gates

As a product owner,
I want promotion blocked when a candidate fails its threshold,
So that quality cannot silently regress.

**Acceptance Criteria:**

**Given** a promotion request for an alias or policy change
**When** the eval run fails its threshold
**Then** promotion is blocked with the failing metrics shown.
**And** an override requires an explicit authorized decision recorded in audit.
**And** a passing run allows promotion.

**Covers:** FR-EVAL-02.

### Story 7.3: Online Sampling for Continuous Eval

As a product owner,
I want optional sampling of production traffic,
So that I can detect drift after rollout.

**Acceptance Criteria:**

**Given** an opt-in team policy
**When** traffic is sampled
**Then** only redacted samples are stored for a bounded period.
**And** sampling can be disabled per team.
**And** sampled data access is role-controlled and audited.

**Covers:** FR-EVAL-03, AD-17.

---

## Epic 8: Python SDK & Developer Experience

**Goal:** Adoption is easier than bypassing the gateway.

**Phase:** 0–1.

### Story 8.1: Context Manager Support

As an application developer,
I want to use the client as a context manager,
So that connections are cleaned up reliably.

**Acceptance Criteria:**

**Given** a client created with a context manager
**When** the block exits
**Then** underlying HTTP connections are closed.
**And** sync and supported async variants behave consistently.
**And** an exception inside the block still closes the client.

**Covers:** FR-SDK-03.

### Story 8.2: Exception Mapping

As an application developer,
I want gateway and upstream errors mapped to typed exceptions,
So that my code can handle failures without parsing strings.

**Acceptance Criteria:**

**Given** a failed call
**When** the gateway returns an error
**Then** the SDK raises `LLMRouterError`, `UpstreamError`, `AuthError`, `RateLimitError`, or `ValidationError` as appropriate.
**And** each exception exposes the gateway error code and request ID.
**And** no provider internals are surfaced.

**Covers:** FR-SDK-04, AD-11.

### Story 8.3: Request and Trace ID Propagation

As an application developer,
I want request and trace IDs exposed,
So that I can correlate my logs with gateway traces for support.

**Acceptance Criteria:**

**Given** a successful or failed call
**When** the SDK receives the response
**Then** the request ID is available on the response and on exceptions.
**And** a caller-supplied trace context is forwarded.
**And** IDs are stable across retries at the gateway.

**Covers:** FR-SDK-06, AD-10.

### Story 8.4: Quickstart and Migration Docs

As an application developer,
I want a quickstart and an OpenAI migration guide,
So that I can adopt the gateway in under 30 minutes.

**Acceptance Criteria:**

**Given** the SDK and gateway
**When** I follow the quickstart
**Then** I complete a first call in under 30 minutes.
**And** the migration guide shows the base URL and client changes from the official OpenAI client.
**And** the guide states when to use the native OpenAI client instead (AD-16).

**Covers:** NFR-06, AD-16, adoption KPI.

---

## Epic 9: Deployment & Environments

**Goal:** The platform runs reliably and reproducibly across environments.

**Phase:** 0–1.

### Story 9.1: Kubernetes Manifests and Environments

As a platform engineer,
I want reproducible deployments for data plane, control plane, and web app,
So that environments do not drift.

**Acceptance Criteria:**

**Given** the deployment manifests
**When** I deploy to dev, staging, or production
**Then** the same manifests are used with environment-specific value overlays.
**And** data-plane pods are stateless and horizontally scalable behind a load balancer.
**And** control plane and web app deploy separately (AD-13).

**Covers:** AD-13.

### Story 9.2: Managed Postgres/Redis and Migrations

As a platform engineer,
I want managed stateful services and gated migrations,
So that data is durable and schema changes are controlled.

**Acceptance Criteria:**

**Given** a new schema version
**When** a migration is applied
**Then** it runs as a separate gated job, not on pod startup.
**And** Postgres is the system of record and Redis is ephemeral (AD-6).
**And** a failed migration blocks rollout with a clear error.

**Covers:** AD-6, AD-13.

### Story 9.3: Telemetry Pipeline

As an SRE engineer,
I want traces, metrics, and logs flowing to the company telemetry stack,
So that dashboards and alerts have data.

**Acceptance Criteria:**

**Given** the OpenTelemetry collector
**When** the gateway emits telemetry
**Then** traces and metrics reach Prometheus and the trace backend.
**And** logs reach the log store with correlation IDs.
**And** telemetry survives a collector restart without blocking requests.

**Covers:** FR-OBS-01, FR-OBS-02, AD-10, AD-13.

### Story 9.4: Secret Manager Integration

As a security reviewer,
I want secret-manager integration in deployment,
So that credentials are never provisioned through manifests.

**Acceptance Criteria:**

**Given** a deployed environment
**When** the gateway needs provider credentials
**Then** they are mounted through the secret manager integration (for example Vault with External Secrets Operator).
**And** no secret value appears in manifests, images, or environment dumps.
**And** access policies follow least privilege.

**Covers:** FR-SEC-01, AD-7, AD-13.

### Story 9.5: HA, Graceful Shutdown, and Runbooks

As an SRE engineer,
I want high availability and safe shutdown,
So that deploys and incidents do not drop in-flight requests.

**Acceptance Criteria:**

**Given** multiple replicas and a rolling deploy
**When** a pod shuts down
**Then** it stops accepting new requests, drains in-flight streams to a deadline, and terminates.
**And** a PodDisruptionBudget protects availability.
**And** runbooks exist for provider outage, Redis loss, Postgres loss, and secret failure.
**And** the measured v1 SLO target is 99.9%.

**Covers:** NFR-02, NFR-10, AD-13.

---

## Definition of Done

A story is done when:

- Acceptance criteria are met and covered by automated tests.
- No `unwrap` or `expect` on production request paths.
- Telemetry follows the AD-10 contract; no prompt bodies or secrets in logs.
- RBAC and audit requirements apply where the story touches admin actions.
- The story's FR/AD references are updated in the coverage map.
- Docs or runbooks are updated when behavior or operations change.
- The change is reviewed against the architecture spine; a violation of AD-1 to AD-3 blocks merge.

## Dependencies and Sequencing

- E1 delivers the substrate; E2 and E9 unblock broad rollout.
- E3 depends on E1.S4, E1.S5, and E1.S10.
- E4 depends on E2 identity (attribution) and E1.S8 telemetry.
- E5 depends on E1.S8 and E4 usage events for the cost view.
- E6 and E7 are last and depend on stable routing and telemetry contracts.
- E8 runs alongside E1 and E2; SDK work must not implement routing or retries.

## Open Questions Carried from PRD

1. Which OIDC provider, and which claim carries team and role?
2. Which secret manager and rotation cadence?
3. Which Kubernetes cluster(s), and who owns HA and capacity?
4. Are quotas and budgets hard-blocking or alert-only for the pilot?
5. What is the exact retry budget per team?
6. Which provider wins when an alias conflicts across local and cloud?
7. Are guardrails inline for all teams or opt-in by policy?
8. Who owns golden datasets and eval thresholds?
9. What are audit and metrics retention requirements?
10. Do any teams need non-chat modalities in v1?

These questions do not block Phase 0; they must be resolved before the phase that depends on them.
