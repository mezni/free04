# Architecture Decision Records — Internal LLM Gateway

Each record captures a deliberate design choice, the context that motivated it, the decision itself (with the invariant it binds), and the consequences (trade‑offs). Records are intended to be stable: Status is set to **Proposed** or **Accepted**; if a decision is later superseded, its status is updated and a new record is added rather than mutating the existing one.

---

## AD-1 — Hexagonal Dependency Direction

- **Status:** Accepted
- **Context:** The gateway must enforce a one‑way dependency flow so that routing and cost logic cannot leak into HTTP handlers or provider adapters, making behavior untestable and inconsistent across providers.
- **Decision:** Dependencies point one way: `gateway → application → domain`. The domain crate depends on no other workspace crate and no I/O library. Application defines ports as traits; the gateway supplies implementations. Any exception is a review blocker.
- **Consequences:** Compile‑time enforcement of separation; future developers cannot accidentally couple routing to I/O without a review. The cost is a modest increase in verbosity when wiring adapters.

---

## AD-2 — Fixed Ordered Request Pipeline

- **Status:** Accepted
- **Context:** Without a fixed pipeline, teams could add, reorder, or skip stages, so a request could reach a provider without auth, validation, quota, or metering.
- **Decision:** Every data‑plane request traverses one immutable stage sequence: transport, validate, authenticate, authorize, rate limit and quota, input guardrail, route, resilience loop, provider call, output guardrail, meter, audit. Each stage is a trait with a typed result of *continue*, *reject*, or *terminate*. Only the resilience loop may call a provider, and it may call it more than once per AD‑3 and AD‑15.
- **Consequences:** Governance cannot be accidentally bypassed; the order is auditable. The cost is a rigid sequence that must be consciously altered through a formal pipeline redesign.

---

## AD-3 — Streaming and Failover Boundary

- **Status:** Accepted
- **Context:** Transparent mid‑stream failover is impossible without buffering duplicated output or billing twice; the system must make the boundary explicit.
- **Decision:** Failover and retry are allowed only before the first token is forwarded. After the first token, the stream is committed: no retry, no failover. A mid‑stream upstream failure terminates the SSE stream with one gateway error event followed by the done sentinel. The first‑token boundary is the single switch both routing and resilience read.
- **Consequences:** Guarantees that a caller never sees two providers emitting tokens into one stream and prevents double billing. The cost is that any logic requiring mid‑stream recovery must be designed around this hard boundary.

---

## AD-4 — Provider Adapter Contract

- **Status:** Accepted
- **Context:** Each provider integration previously invented its own request shape, error handling, and capability assumptions, so fallback silently selected a target that could not serve the request.
- **Decision:** Every adapter implements one port and converts the canonical internal request to the provider wire format and back. Each adapter declares a capability descriptor (tools, JSON mode, vision, context window, streaming) and maps failures into the shared error taxonomy. Provider‑specific fields never cross into the OpenAI‑compatible surface.
- **Consequences:** Makes fallback safe and prevents provider leakage. The cost is the upfront work of defining the canonical contract and writing adapters for each provider.

---

## AD-5 — Routing Policy is Pure

- **Status:** Accepted
- **Context:** Routing decisions hidden in adapters, wall‑clock calls, network lookups, or random tie‑breaks cannot be unit‑tested or reproduced.
- **Decision:** The domain exposes one pure function that takes the request, principal, resolved policy, capability requirements, and a provider‑health snapshot, and returns an ordered target list with its reasons. No I/O, no clock, no randomness inside it. The caller supplies time and health. Given the same inputs, the output is identical.
- **Consequences:** Deterministic, unit‑testable, and reproducible routing. The cost is that the function receives all needed inputs as parameters; hidden state (e.g., a global health cache) must be passed explicitly.

---

## AD-6 — State Ownership

- **Status:** Accepted
- **Context:** Two components owning the same record, dual writes, and counters that disagree after a pod restart.
- **Decision:** Postgres is the system of record for control‑plane configuration, usage events, and audit events. Redis holds only ephemeral, rebuildable state: rate‑limit counters, circuit‑breaker state, and the provider‑health cache. No durable business fact exists only in Redis. Configuration is read as a versioned snapshot cached in process and refreshed on a bounded interval.
- **Consequences:** Guarantees a single source of truth for business facts; Redis failures degrade but do not lose data. The cost is operational complexity of managing two stores with different durability guarantees.

---

## AD-7 — Config versus Secrets

- **Status:** Accepted
- **Context:** Provider keys in env files, config maps, database rows, logs, or traces, and secret sprawl across deployments.
- **Decision:** Non‑secret configuration lives in versioned control‑plane records. Secrets live only in the company secret manager and are resolved at runtime through a secrets port, cached with a short TTL. Secrets are never written to persistent storage, never logged, and never returned by any API. Redaction is tested, not assumed.
- **Consequences:** Removes a class of key‑sprawl and audit risk. The cost is the need for a secrets‑manager integration and a runtime‑resolution layer.

---

## AD-8 — Identity, Tenancy, and Authorization

- **Status:** Accepted
- **Context:** Unauthenticated or cross‑tenant access, shared keys with unlimited scope, and provider credentials reaching callers.
- **Decision:** Every data‑plane call carries a principal resolved from an OIDC JWT or a gateway‑issued scoped API key. Every principal belongs to exactly one team and holds scopes for teams, aliases, models, and operations. Every query and every usage record is scoped by team. Provider keys exist only inside the gateway. Missing principal, missing scope, or team mismatch is rejected before routing.
- **Consequences:** Tenant isolation and attribution require a first‑class principal. The cost is the need for an OIDC or key‑issuance flow and the operational overhead of key rotation.

---

## AD-9 — Usage and Cost are Immutable Facts

- **Status:** Accepted
- **Context:** Retroactive price edits rewriting history, double counting on retries, and reports that cannot be reconciled to requests.
- **Decision:** Each provider attempt produces one immutable usage event keyed by request ID plus attempt ID, recording principal, team, alias, provider, model, token counts, latency, outcome, and a cost snapshot computed from the price table version active at event time. Aggregates are derived from events, never edited in place.
- **Consequences:** Reconciliation and historical cost truth. The cost is that past cost figures cannot be altered; any price change creates a new version.

---

## AD-10 — Telemetry Contract

- **Status:** Accepted
- **Context:** Each module emitting ad‑hoc metric names and attributes, so dashboards and alerts cannot be shared or predicted.
- **Decision:** All spans and metrics follow one published contract: a request ID is generated at transport and propagated to callers and upstream calls; spans use the fixed pipeline stage names from AD‑2; Prometheus metrics live in the `llmgw_` namespace with a fixed label set. New metrics require a contract change, not a local name.
- **Consequences:** Shared dashboards and alerts; predictable cardinality. The cost is that adding a new metric requires a contract change rather than a local addition.

---

## AD-11 — Error Envelope

- **Status:** Accepted
- **Context:** Raw provider errors, stack traces, or secret‑bearing messages reaching clients, and the SDK and web app each parsing a different shape.
- **Decision:** Every rejection uses one OpenAI‑compatible error envelope with a stable gateway error code, a human message, and a request ID. Internal errors map to HTTP status through one table. Provider bodies and internal details are logged server‑side and never forwarded.
- **Consequences:** Stable SDK/UI behavior and no secret leakage. The cost is that provider‑specific diagnostics must be logged server‑side and are never visible to callers.

---

## AD-12 — Control Plane and Data Plane Separation

- **Status:** Accepted
- **Context:** Admin operations and dashboards sitting on the hot request path, and data‑plane pods gaining write access to configuration.
- **Decision:** The data plane is read‑only against configuration and appends only usage and audit events. The control plane owns writes to teams, keys, quotas, policies, providers, and aliases, and exposes a separate authenticated API for the web app. Data‑plane pods hold no admin credentials and never call the web app.
- **Consequences:** Prevents admin actions on the hot path and limits the blast radius if a data‑plane pod is compromised. The cost is the operational complexity of maintaining two deployments.

---

## AD-13 — Deployment Envelope

- **Status:** Accepted
- **Context:** Environment drift and a target that cannot reach the stated SLO because state is trapped in one pod.
- **Decision:** Data‑plane pods are stateless and horizontally scaled behind a load balancer on Kubernetes. Postgres and Redis are managed services. Secrets arrive through the secret manager. Telemetry goes to an OpenTelemetry collector feeding Prometheus and the log store. The control plane and web app deploy separately from the data plane. Every environment is provisioned from the same manifests with environment‑specific values only.
- **Consequences:** Predictable, reproducible deployments across environments. The cost is the need for Kubernetes and managed stateful services.

---

## AD-14 — Guardrails as Provider‑Agnostic Stages

- **Status:** Accepted
- **Context:** Guardrail logic welded to one vendor or one model, and blocking behavior that differs per team with no audit trail.
- **Decision:** Guardrails are pipeline stages behind one interface returning allow, flag, redact, or block, with an explicit per‑policy fail‑open or fail‑closed mode. Policies are versioned control‑plane data. Input guardrails run before routing. Output guardrails for streaming are deferred and must not buffer tokens once the stream is committed.
- **Consequences:** Provider‑agnostic guardrails; policies are centrally configurable and auditable. The cost is that output guardrails for streaming are deferred (Phase 3).

---

## AD-15 — Attempt Budget and Idempotency

- **Status:** Accepted
- **Context:** Unbounded retries, thundering herds after a provider incident, and silent double billing.
- **Decision:** Each request carries an attempt budget (maximum attempts and maximum elapsed time) plus an idempotency key generated by the gateway or supplied by the client. Retries stop when either budget is exhausted or when AD‑3 commits the stream. Every attempt is recorded as its own usage event.
- **Consequences:** Prevents storms and double billing; every attempt is visible in usage metrics. The cost is that the client or gateway must manage idempotency keys and budgets.

---

## AD-16 — Python SDK is a Thin Client

- **Status:** Accepted
- **Context:** Failover, retry, or cost logic duplicated in the SDK and diverging from gateway behavior, and a second source of truth for routing.
- **Decision:** The SDK is transport and typed models only: build requests, send them, parse SSE, and raise mapped exceptions. It implements no failover, no circuit breaking, and no routing. It targets the gateway as an OpenAI‑compatible base URL and does not embed provider keys. If a native OpenAI client can replace it for an audience, that is the supported path.
- **Consequences:** One source of truth for behavior; the SDK stays lightweight. The cost is that SDK users must still manage failover at the gateway layer.

---

## AD-17 — Data Minimization

- **Status:** Accepted
- **Context:** Prompts and completions landing in logs, traces, or analytics by default, creating an uncontrolled copy of company and customer data.
- **Decision:** Prompt and response bodies are not persisted by default. Telemetry records metadata only. Body capture is opt‑in per team, redacted through a declared policy, retained for a bounded period, and access‑controlled. Any new sink that would store bodies requires an explicit decision and review.
- **Consequences:** Data‑minimization and compliance with privacy expectations. The cost is that teams needing body data must explicitly opt in and declare a policy.

---

## Open Questions — Decision Records

| # | Decision | Status | Context |
|---|---|---|---|
| 1 | Which IdP/OIDC provider, and which claim carries team and role? | Open | The identity port isolates the choice; the team must confirm the provider before E2. |
| 2 | Which secret manager and rotation cadence? | Open | The secrets port is built; the team must confirm the manager before E2. |
| 3 | Which Kubernetes cluster(s), and who owns HA and capacity? | Open | The deployment envelope (AD‑13) assumes K8s; the team must finalize environment specifics. |
| 4 | Are quotas and budgets hard‑blocking or alert‑only for the pilot? | Open | Affects E4.S3 and E4.S8; decision before Phase 2 broad rollout. |
| 5 | What is the exact retry budget (attempts and elapsed time) per team? | Open | Determines AD‑15 budgets; must be agreed before E3. |
| 6 | Which provider wins when an alias conflicts across local and cloud targets? | Open | Governs AD‑5 and alias resolution (E3.S6). |
| 7 | Are guardrails inline for all teams or opt‑in by policy? | Open | Affects AD‑14 and E6; decision before Phase 3. |
| 8 | Who owns golden datasets and eval thresholds? | Open | Governs E7; the team must assign ownership before Phase 3. |
| 9 | What are audit and metrics retention requirements? | Open | Affects compliance and SRE operations; must be defined before Phase 2. |
| 10 | Do any teams need non‑chat modalities in v1? | Open | Governs scope; if yes, the architecture must be extended (AD‑4, AD‑17). |

---

## How to Use This File

- **New starters:** read the ADs first; they are the invariants that every subsequent story must honor.
- **Story writers:** reference the AD number in the “Covers” field of each story; if a story violates an AD, it must be reviewed by the architect.
- **Decision changes:** if a decision must be revisited, add a new record with an updated status rather than mutating this file. Link the old record from the memlog (`.memlog.md`).
- **Reference:** this file is the canonical list of decisions for the project; the `.memlog.md` is the provenance log of *how* each decision was made.