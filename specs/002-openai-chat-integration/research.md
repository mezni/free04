# Research: OpenAI-Chat-Integration

## Language/Version → Rust 1.75 (inferred from project stack: Rust 1.99.1, axum 0.8.9, tokio 1.54.1)

**Rationale**: The llm-gw project uses Rust 1.99.1 as per ADR stack pinning. Rust 1.75+ is required for async/await features and trait generics used in the pipeline architecture.

**Alternatives considered**: 
- Rust 1.60+: Would lose some ecosystem features but still compatible
- Rust 1.80+: Would gain improved error tooling but no significant benefit for this feature

---

## Primary Dependencies → axum 0.8.9 + tokio 1.54.1 + serde 1.0.229 + tokio-util 0.7.9

**Rationale**: These are the core dependencies of the llm-gw project as per stack pinning. axum provides the HTTP framework, tokio the async runtime, serde the serialization, and tokio-util utilities.

**Alternatives considered**:
- Actix-web: Alternative Rust HTTP framework, but project is committed to axum per architecture
- warp: Another option, but axum has better OpenAI-compatible ecosystem support

---

## Testing → cargo test with contract tests

**Rationale**: The project uses cargo test as per NFR-08 (zero `unwrap` on production paths, `thiserror` error handling). Contract tests will validate the OpenAI schema compliance.

**Alternatives considered**:
- Specific test frameworks: pytest, go test, etc. - not applicable for Rust codebase
- Integration test strategies: Tests will follow project patterns (see Story 1.10 for integration test patterns)

---

## Target Platform → Kubernetes 1.35 (inferred from constitution)

**Rationale**: Constitution specifies Kubernetes 1.35 as the deployment envelope. The gateway runs as stateless data-plane pods behind a load balancer.

**Alternatives considered**:
- Docker Swarm: Simpler but doesn't meet project requirements
- Nomad: Lighter weight but not project-standard

---

## Project Type → library/cli/web-service (hexagonal architecture)

**Rationale**: The llm-gw is a Rust workspace with hexagonal (DDD) architecture: gateway → application → domain crates. It's a web-service providing an OpenAI-compatible API endpoint.

**Alternatives considered**:
- Pure library: Would not expose the API endpoint
- Mobile app: Not applicable for this gateway service

---

## Performance Goals → <5ms p99 proxy overhead (inferred from NFR-01)

**Rationale**: NFR-01 specifies "proxy-added overhead below 5ms p99, excluding upstream inference." This is the gateway performance target.

**Alternatives considered**:
- <1ms p99: Unrealistic for a proxy with validation/authentication/routing
- <10ms p99: Would violate NFR-01 constraint

---

## Constraints → Must comply with AD-1 to AD-3 (fixed pipeline, first-token commit boundary, no retry after commit); secrets must not leak (AD-4); no `unwrap`/`expect` on production paths (NFR-08)

**Rationale**: These are the architectural gates that constrain all implementation. The pipeline order cannot be changed, failover must stop at first token, and secrets must never appear in logs.

**Alternatives considered**:
- Relaxing AD-2: Would require governance approval and architectural review
- Adding retry after first token: Explicitly blocked by AD-3

---

## Scale/Scope → Pilot team(s); per-team quota enforcement; internal teams

**Rationale**: Phase 0 serves one pilot team (as per E1 exit criteria). Scope is bounded to the core OpenAI-compatible endpoint with basic validation and routing.

**Alternatives considered**:
- Multi-tenant from v1: Would violate Phase 0 exit criteria and sequencing (E1 delivers substrate; E2 and E9 unblock broad rollout)
- Full feature set from v1: Would block Phase 0 delivery; Stories 1.3-1.11 build incrementally