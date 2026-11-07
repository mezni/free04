# Product Requirement Document: Internal LLM Gateway & Python SDK

## Document Details

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 0.2 |
| Author | AI Systems Architecture Team |
| Document Owner | John (Product Manager) |
| Target Release | v1.0.0 |
| Target Audience | Engineering, Platform Infrastructure, Security, SDK Developers |
| Classification | Internal |

### Revision History

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-11-07 | Initial provider router + Python SDK PRD. |
| 0.2 | 2026-11-07 | Repositioned as an internal company platform; added production capabilities (auth/RBAC, rate limiting, retry/circuit breaker, usage/cost tracking, secrets, observability, validation, guardrails, evals, monitoring web app); introduced delivery phases and personas. |

---

## 1. Executive Summary

The Internal LLM Gateway is a company-owned, high-performance gateway written in Rust that sits between internal applications and every LLM provider (local: Ollama, vLLM; commercial: OpenAI, Anthropic, and future providers). It exposes an OpenAI-compatible API so teams can adopt it with minimal code change, while the company gains one place to control access, cost, reliability, safety, and visibility.

This is not a demo proxy. The product starts with the **provider router** as its first shippable increment, then hardens into a production platform through explicit phases: request validation and secrets, auth/RBAC, observability, rate limiting, retry/circuit breaker, usage and cost tracking, guardrails, a monitoring/analytics web app, and finally an evals capability.

A lightweight Python SDK (`LLMRouterClient`) provides synchronous and streaming primitives and acts as a drop-in replacement for standard OpenAI client workflows.

**The core bet:** centralizing LLM traffic behind one governed gateway is cheaper and safer than every team integrating providers independently — but only if adoption is easier than bypassing it.

---

## 2. Problem & Context

Today, teams integrate directly with providers. We hypothesize the following costs of that status quo (to be validated with the first 3–5 consuming teams):

- **Uncontrolled spend:** no shared view of token usage or per-team/provider cost; duplicate keys and untracked experiments.
- **Fragile integrations:** no failover when a provider is slow or down; each team re-implements retries.
- **Security exposure:** provider API keys scattered across repos and environments; no RBAC, no audit trail.
- **No policy:** prompts and responses flow to providers with no validation, moderation, or data-handling guardrails.
- **No shared learning:** model/prompt changes cannot be evaluated against a baseline before rollout.

If these are not real for our teams, the economic case for the platform weakens and v1 scope must shrink accordingly.

---

## 3. Users & Jobs to Be Done

| Persona | Role | Job to be done | What they need from us |
| --- | --- | --- | --- |
| Application Developer | Builds features against an LLM | "Give me one OpenAI-compatible endpoint and a simple SDK, with no provider lock-in." | Easy onboarding, streaming, stable API, clear errors. |
| Platform / SRE Engineer | Runs and pages on the gateway | "Let me see health, latency, errors, and fallback behavior and act on them without SSH." | Health per provider, SLO dashboards, alerting, traces. |
| Security / Compliance Reviewer | Approves data handling and access | "Prove who can call which model, with which data, and that it is audited." | RBAC, secrets isolation, audit logs, guardrails. |
| FinOps / Cost Owner | Owns the LLM budget | "Show me spend by team, model, and provider, and stop runaway usage." | Usage metering, cost allocation, quotas, budgets. |
| Engineering Leadership | Sponsors the platform | "Increase adoption and reduce cost/risk without slowing teams down." | Adoption + cost-savings metrics. |

---

## 4. Product Goals & Objectives

- **One governed front door:** an OpenAI-compatible `/v1/chat/completions` endpoint for all LLM traffic.
- **High throughput, low latency:** Rust async (Tokio/Axum), streaming forwards without buffering whole responses; proxy overhead < 5ms p99 excluding inference.
- **Resilience:** automatic failover, bounded retries, and circuit breaking so provider incidents do not become product incidents.
- **Control & security:** authentication, RBAC, secrets isolation, rate limits/quotas, request validation, and auditability.
- **Observability & accountability:** traces, metrics, logs, usage and cost attribution, and a monitoring/analytics web app.
- **Safety & quality:** configurable guardrails on input/output and an evals capability to validate model/prompt changes before rollout.
- **Domain isolation:** Domain-Driven Design keeps routing policy, budgeting, and fallback logic separate from HTTP transport.
- **Developer experience:** a Python SDK that is genuinely easier than calling providers directly.

### Non-Goals (v1.0.0)

- Public/external multi-tenant SaaS operation; this is an internal tool.
- Full billing system, invoicing, or chargeback automation beyond usage/cost reporting.
- Non-chat modalities (embeddings, images, audio, rerank) unless a validated consumer requires them.
- Building our own model inference runtime; we route to providers, we do not host models.
- Becoming a prompt/agent framework; applications own their prompts and orchestration.

---

## 5. High-Level Architecture

Two planes, cleanly separated:

- **Data plane:** request validation → auth/RBAC → rate limiting/quota → guardrails → routing policy → resilience (retry/circuit breaker) → provider adapter → streaming response → usage metering.
- **Control plane:** configuration (providers, aliases, policies, quotas), secrets, the monitoring/analytics web app, and the eval runner.

```
+---------------------------+        +------------------------------+
|  Python / App clients     |        |  Monitoring & Analytics UI   |
|  (OpenAI-compatible SDK)  |        |  (control plane)             |
+------------+--------------+        +--------------+---------------+
             | HTTP / SSE                           |
             v                                      v
+------------+--------------------------------------+---------------+
|                          Axum Web Gateway                        |  Infrastructure
+------------+--------------------------------------+---------------+
             |                                      |
             v                                      v
+---------------------------+        +------------------------------+
|  Request Pipeline         |        |  Admin / Config / Secrets     |
|  validation, auth, RBAC,  |        |  (providers, aliases, quotas, |
|  rate limit, guardrails,  |        |   policies, API keys)         |
|  usage metering           |        +--------------+---------------+
+------------+--------------+                       |
             v                                      |
+---------------------------+                       |
|  Router Use-Case Engine   |<----------------------+  Application
+------------+--------------+
             v
+---------------------------+
|  Domain Routing Policy    |  Domain: target selection, budgets,
|  (rules, scoring, fallback)|  fallback order, capability matching
+------------+--------------+
             |
      +------+------+
      v             v
+-----------+  +-----------+
| Primary   |  | Fallback  |  Infrastructure adapters
| Local     |  | Cloud     |
| vLLM/Oll. |  | OpenAI/..  |
+-----------+  +-----------+
             |
             v
+---------------------------+
| Observability (OTel)      |  traces / metrics / logs (cross-cutting)
+---------------------------+
```

Design constraints:
- Every cross-cutting concern (auth, rate limit, guardrails, metering) is a pipeline stage, independently testable and individually configurable.
- Domain layer has no dependency on Axum, HTTP providers, or the database.
- No `unwrap` in production request paths; errors via `thiserror`; telemetry via `tracing`/OpenTelemetry.

---

## 6. Functional Requirements

Priorities: **P0** = required for first production pilot; **P1** = required before broad rollout; **P2** = post-rollout enhancement.

### 6.1 Core Router (Rust Data Plane)

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-ENG-01 | Interface | Expose an OpenAI-compatible `/v1/chat/completions` endpoint (request and response schema). | P0 |
| REQ-ENG-02 | Streaming | Stream SSE chunks to the client without buffering the full response. | P0 |
| REQ-ENG-03 | Failover Routing | Attempt a secondary provider when the primary returns 5xx or times out, before the first token is emitted. | P0 |
| REQ-ENG-04 | Model Overrides | Map internal aliases (`auto`, `fast`, `cheap`, `smart`) to provider-specific model IDs. | P1 |
| REQ-ENG-05 | Config Management | Runtime configuration of providers, aliases, base URLs, and fallback order (non-secret via config; secrets via the secrets manager). | P1 |
| REQ-ENG-06 | Provider Capability Matrix | Track which providers/models support tools, JSON mode, vision, context length; exclude incompatible targets from routing. | P1 |
| REQ-ENG-07 | Routing Policy | Select targets by declarative policy: cost ceiling, latency SLO, context length, data residency, capability requirements, weighting. | P1 |
| REQ-ENG-08 | Error Taxonomy | Classify upstream outcomes (4xx no-failover, 429 with Retry-After, 5xx, timeout, mid-stream failure) and act per class. | P0 |

### 6.2 Request Validation

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-VAL-01 | Schema Validation | Validate request body against the OpenAI Chat Completions schema; reject malformed requests with 400 and a clear error. | P0 |
| REQ-VAL-02 | Limits | Enforce max payload size, max tokens, max messages, and allowed parameter sets per team/model. | P1 |
| REQ-VAL-03 | Model/Param Guard | Reject unknown aliases/models and unsupported parameters before any upstream call. | P1 |

### 6.3 Authentication, Authorization & RBAC

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-AUTH-01 | Authentication | Authenticate callers via internal identity (OIDC/JWT) and/or scoped API keys issued by the gateway. | P0 |
| REQ-AUTH-02 | RBAC | Role/permission model governing which teams, models, providers, and operations a principal may use. | P0 |
| REQ-AUTH-03 | Scoped Keys | Issue, rotate, and revoke API keys scoped to a team and allowed models; never expose provider keys to callers. | P0 |
| REQ-AUTH-04 | Audit Log | Record who called what, when, with which model/provider, and the decision — tamper-evident and queryable. | P1 |
| REQ-AUTH-05 | Admin Separation | Separate administrative actions (manage keys, quotas, policies) from data-plane calls. | P1 |

### 6.4 Rate Limiting & Quotas

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-RATE-01 | Request Rate Limit | Enforce requests-per-minute per principal and per team. | P1 |
| REQ-RATE-02 | Token Rate Limit | Enforce tokens-per-minute (input/output) per principal, team, and model. | P1 |
| REQ-RATE-03 | Quotas | Enforce daily/monthly usage quotas with configurable hard (reject) or soft (alert) modes. | P1 |
| REQ-RATE-04 | Fairness | Prevent one team/principal from starving others; return 429 with `Retry-After`. | P2 |

### 6.5 Resilience: Retry & Circuit Breaker

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-RES-01 | Bounded Retry | Retry eligible failures with exponential backoff + jitter, capped by an attempt/time budget. | P1 |
| REQ-RES-02 | Non-Retryable Cases | Never retry 4xx (except configured 429), and never retry after the first streamed token. | P0 |
| REQ-RES-03 | Circuit Breaker | Per-provider circuit breaker (open/half-open/closed) based on error rate/latency; route away from open circuits. | P1 |
| REQ-RES-04 | Health Checks | Active/passive provider health distinguishing *down* from *slow*; feed routing and the web app. | P1 |
| REQ-RES-05 | Idempotency & Double-Billing Guard | Track attempts to avoid double billing; expose attempt metadata in traces/usage. | P1 |

### 6.6 Usage & Cost Tracking

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-COST-01 | Metering | Record tokens (input/output), provider, model, latency, and outcome for every request. | P1 |
| REQ-COST-02 | Price Table | Maintain per-provider/model pricing and compute cost per request. | P1 |
| REQ-COST-03 | Attribution | Attribute usage/cost to team, principal, key, and model alias. | P1 |
| REQ-COST-04 | Budgets & Alerts | Configure budgets per team and alert (or block, per quota mode) on threshold breach. | P2 |

### 6.7 Secrets Manager

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-SEC-01 | Secret Store | Store provider API keys and credentials in the company secrets manager (e.g., Vault / cloud secret manager); never in plaintext config or repos. | P0 |
| REQ-SEC-02 | Secret Lifecycle | Support rotation and revocation; resolve at runtime with caching and access control. | P1 |
| REQ-SEC-03 | Least Privilege | Gateway accesses only the secrets for the providers/teams it serves; no secret exposure at the API edge. | P0 |
| REQ-SEC-04 | No Secret Logging | Guarantee secrets and raw credentials never appear in logs, traces, or error responses. | P0 |

### 6.8 Observability

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-OBS-01 | Traces | OpenTelemetry traces spanning gateway stages and upstream calls, with request IDs propagated to callers. | P0 |
| REQ-OBS-02 | Metrics | Prometheus metrics: request rate, error rate, latency (incl. TTFT and proxy overhead), fallback rate, provider health, token/cost counters. | P0 |
| REQ-OBS-03 | Structured Logs | Structured logs with consistent fields; PII/prompt-content redaction by policy. | P1 |
| REQ-OBS-04 | Alerting | Alert rules for SLO breach, circuit-open, fallback spike, quota/budget breach. | P1 |

### 6.9 Guardrails

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-GRD-01 | Input Guardrails | Configurable pre-flight checks (moderation, PII/sensitive-data detection, prompt-injection heuristics) per team/model. | P1 |
| REQ-GRD-02 | Output Guardrails | Configurable post-generation checks on streamed/complete output before delivery. | P2 |
| REQ-GRD-03 | Policy Modes | Policy actions: allow, flag, redact, block; explicit fail-open vs fail-closed per policy. | P1 |
| REQ-GRD-04 | Governance | Policies are centrally configured, versioned, and auditable. | P2 |

### 6.10 Evals

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-EVAL-01 | Eval Harness | Run prompt/model/alias changes against golden datasets and compare against a baseline. | P2 |
| REQ-EVAL-02 | Regression Gates | Define pass thresholds that must be met before a model alias/policy change is promoted. | P2 |
| REQ-EVAL-03 | Online Sampling | Optionally sample production traffic (consented/redacted) for continuous eval. | P2 |

### 6.11 Monitoring & Analytics Web App

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-UI-01 | Health Dashboard | Provider + gateway health (down vs slow), circuit state, fallback activity. | P1 |
| REQ-UI-02 | Usage & Cost Dashboard | Usage/cost by team, principal, model, provider over time. | P1 |
| REQ-UI-03 | Latency & Reliability | Request rate, error rate, TTFT, proxy overhead, retry/fallback rates. | P1 |
| REQ-UI-04 | Admin Console | Manage teams, keys, quotas, budgets, aliases, and policies. | P2 |
| REQ-UI-05 | Audit Viewer | Query the audit log by principal, model, and time. | P2 |

### 6.12 Python SDK

| Requirement ID | Module | Feature Description | Priority |
| --- | --- | --- | --- |
| REQ-SDK-01 | Client Core | `LLMRouterClient` built on `httpx` for reliable HTTP execution. | P0 |
| REQ-SDK-02 | Sync & Stream | Synchronous completion calls and streaming response generators (`stream=True`). | P0 |
| REQ-SDK-03 | Context Manager | `with LLMRouterClient(...) as client:` for connection cleanup. | P1 |
| REQ-SDK-04 | Exception Handling | Map upstream/gateway errors to domain exceptions (`LLMRouterError`, `UpstreamError`, `AuthError`, `RateLimitError`, `ValidationError`). | P1 |
| REQ-SDK-05 | Identity & Keys | Send scoped API key/OIDC token; support config via env; never embed provider keys. | P0 |
| REQ-SDK-06 | Observability Friendly | Propagate request/trace IDs; expose them on responses for support. | P1 |

---

## 7. Delivery Phases

Broad rollout is gated on each phase's exit criteria. This prevents "production-ready" from being an unbounded promise.

| Phase | Scope | Exit Criteria |
| --- | --- | --- |
| **Phase 0 — Router** (first increment) | REQ-ENG-01/02/03/08, REQ-VAL-01, REQ-SEC-01/03/04, REQ-OBS-01/02, REQ-SDK-01/02/05 | One pilot team streams via the gateway; failover before first token works; no secrets in logs; traces/metrics visible. |
| **Phase 1 — Production Pilot** | REQ-AUTH-01/02/03, REQ-RES-01/04, REQ-ENG-04/05, REQ-VAL-02/03, REQ-OBS-03/04, REQ-UI-01/03, REQ-SDK-03/04/06 | 3–5 teams onboarded; RBAC enforced; per-provider health; SLO alerts; on-call runbook exists. |
| **Phase 2 — Cost & Control** | REQ-RATE-01/02/03, REQ-COST-01/02/03, REQ-RES-02/03/05, REQ-ENG-06/07, REQ-UI-02/04/05, REQ-AUTH-04/05 | Cost reported by team/model; quotas enforced; circuit breakers active; capability-aware routing. |
| **Phase 3 — Safety & Quality** | REQ-GRD-01/03, REQ-COST-04, REQ-RATE-04, REQ-EVAL-01/02, REQ-GRD-02/04, REQ-EVAL-03 | Guardrails configurable per team; eval gate for model/alias changes; budgets/alerts live. |

---

## 8. Non-Functional Requirements

- **Performance:** Proxy-added overhead < 5ms p99 (excluding upstream inference); time-to-first-token overhead measured and reported.
- **Availability:** 99.9% gateway SLO in v1, measured against defined upstreams; 99.99% is a stretch target once HA and health orchestration are funded.
- **Scalability:** Non-blocking async execution; documented concurrency and payload limits for capacity planning.
- **Security:** AuthN/AuthZ on every data-plane call; secrets in a managed store; no secret/PII leakage in telemetry; least privilege everywhere.
- **Auditability:** Security-relevant admin and access actions are logged and queryable.
- **Compatibility:** OpenAI-compatible surface; versioned API; deprecation policy for breaking changes.
- **Maintainability:** DDD layout (`domain/`, `application/`, `infrastructure/`); cross-cutting stages independently testable.
- **Code Quality:** Zero `unwrap` on production request paths; errors via `thiserror`; telemetry via `tracing`/OpenTelemetry.
- **Compliance:** Data classification, residency, and retention rules respected per provider/team policy.

---

## 9. Success Metrics & KPIs

| KPI | Definition | Target |
| --- | --- | --- |
| Adoption | % of internal LLM traffic routed through the gateway | ≥ 70% by end of Phase 2 |
| Onboarding time | Time from requesting access to first successful call | < 30 minutes |
| Fallback success rate | Requests served by a secondary provider after primary failure | > 95% |
| Latency overhead | Direct upstream vs gateway TTFT difference (p99) | < 5ms |
| Cost visibility | % of LLM spend attributable to a team/model | 100% |
| Cost savings | Reduction vs pre-gateway spend baseline | Measure; target set after baseline |
| Policy enforcement | % of requests passing validation/authN/rate-limit as configured | ≥ 99.9% |
| Guardrail efficacy | Blocked-unsafe / total-unsafe on eval set | Target set after baseline |
| Reliability | Gateway availability vs SLO | ≥ 99.9% |
| MTTR | Median time to detect + restore a provider incident | Decrease vs baseline |
| Eval regression | % of model/alias changes gated by evals | 100% after Phase 3 |

---

## 10. Assumptions & Open Questions

### Assumptions
- Consumers speak the OpenAI Chat Completions schema for request and streaming response.
- Local providers (Ollama, vLLM) are OpenAI-compatible or can be adapted at the infrastructure boundary.
- The company has an identity provider (OIDC) and a secrets manager we can integrate with.
- The gateway is deployed internally, not on the public internet.
- The first 3–5 consuming teams can be recruited as design partners.

### Open Questions
1. **Identity:** Which IdP/OIDC provider, and do we need service-to-service credentials as well as user tokens?
2. **Secrets:** Which secrets manager (Vault, cloud-native), and what rotation cadence?
3. **Deployment:** Where does the gateway run (Kubernetes, VM), and who owns its HA and scaling?
4. **Data classification:** What data classes are allowed to which providers, and does residency apply?
5. **Failover semantics:** Confirm failover only before first token; define retry budget and which 429s are retryable.
6. **Alias authority:** Which provider/model wins when an alias conflicts across local and cloud targets?
7. **Cost enforcement:** Are quotas/budgets hard-blocking or alert-only for the pilot?
8. **Guardrails placement:** Inline pipeline stage vs sidecar service — latency and ownership trade-off?
9. **Evals ownership:** Which team curates golden datasets and owns pass thresholds?
10. **Audit retention:** How long must audit/metrics data be retained, and where?
11. **SDK vs base_url:** Validate whether the custom SDK beats pointing the official OpenAI client at the gateway; if not, descope SDK.
12. **Non-chat APIs:** Confirm embeddings/other modalities remain out of scope for v1.

---

## 11. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Competing with mature gateways (LiteLLM, Portkey, Envoy AI Gateway) | Build cost with low differentiation | Validate the internal-controls angle; adopt/buy before build for commodity parts. |
| Scope sprawl across 10+ capabilities | Nothing ships | Phase gates with explicit exit criteria; ship Phase 0 fast. |
| Adoption resistance ("harder than calling OpenAI directly") | Low usage, no cost data | SDK + <30 min onboarding; dogfood with design partners. |
| Latency overhead from guardrails/validation | Breaks <5ms target | Measure per-stage; make guardrails async/optional. |
| Secrets/audit failure | Security incident | Managed secrets, least privilege, no-secret-in-logs tests, audit log from Phase 1. |
| Upstream availability limits 99.99% | SLO unachievable | Realistic 99.9% v1 SLO; fund health orchestration + HA before stretch target. |
| Double billing on retries | Cost overruns | Attempt budget, monitoring, avoid retrying after tokens stream. |

---

## 12. Traceability

Each requirement maps to a functional area and an explicit priority (P0/P1/P2) and a delivery phase, so it can be translated directly into epics and stories. Phase 0 is the smallest increment that validates the central bet: *teams will route traffic through one governed gateway if adoption is easier than bypassing it.*
