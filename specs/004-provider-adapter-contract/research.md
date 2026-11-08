# Research: Provider Adapter Contract

## Capability Descriptor Standardization

**Decision**: Adopt a standardized capability descriptor format for all provider adapters, including: `tools`, `json_mode`, `vision`, `context_window` (in tokens), and `streaming` support.

**Rationale**: Enables the declarative routing policy (FR-ENG-07) to make informed decisions about which targets can serve a given request. Without standardized capability declarations, routing cannot exclude targets that lack required capabilities, leading to silent downgrades or errors.

**Alternatives considered**:
- **No capability declarations**: Simpler implementation but prevents capability-aware routing; requires explicit model selection by user.
- **Provider-specific capability fields**: Fragment the contract; routing would need provider-specific knowledge, violating AD-4 (provider adapter contract).
- **Capability descriptor with versioning**: Added complexity for v1; deferred to future version since all target providers support the core capabilities.

---

## Error Taxonomy Mapping

**Decision**: Map all provider failures to the OpenAI-compatible error envelope with gateway error codes and request IDs; use `invalid_request` for validation errors, `context_length_exceeded` for context window limits, `rate_limit_error` for 429 responses, `internal_server_error` for 5xx, and `service_unavailable` for connection failures.

**Rationale**: Ensures clients can reliably handle errors regardless of the underlying provider (FR-ENG-08, AD-11). Consistent error mapping is essential for multi-provider gateway usability.

**Alternatives considered**:
- **Pass through provider errors**: Simpler but violates AD-11 (stable error envelope) and creates client complexity.
- **Custom error mapping per adapter**: Fragmented; clients would need to know which adapter is active to interpret errors.
- **No error mapping**: Violates FR-ENG-08 and AD-11; clients would see raw provider internals.

---

## Adapter Contract Interface

**Decision**: Define an adapter port trait with three methods: `convert_request(canonical_request) -> wire_format`, `convert_response(wire_format) -> canonical_response`, and `declare_capabilities() -> capability_descriptor`. Each adapter (Ollama, vLLM, OpenAI) implements this trait.

**Rationale**: Establishes the contract that all adapters must satisfy (AD-4). Contract tests verify adapter compliance. The port abstraction enables adding new adapters without modifying routing or transport logic.

**Alternatives considered**:
- **Function-based adapters instead of trait-based**: Less idiomatic for Rust hexagonal architecture; harder to test and compose.
- **No formal adapter port**: Each adapter implemented independently; risks interface drift and makes concurrent adapter development error-prone.
- **Inheritance-based hierarchy**: Rust trait composition is preferred over inheritance for this use case; traits provide clearer separation of concerns.

---

## Contract Test Patterns

**Decision**: Implement contract tests that verify: (1) request-to-wire-format conversion preserves required fields, (2) response-to-canonical-response conversion preserves the OpenAI-compatible shape, (3) capability declaration matches the standardized format, (4) failure mapping produces valid OpenAI error envelopes, (5) no provider-specific fields appear in the canonical response.

**Rationale**: Provides automated verification that all adapters satisfy the adapter contract (FR-ENG-06, AD-4). Contract tests run against mock servers and are independent of specific provider implementations.

**Alternatives considered**:
- **Integration tests against real providers**: Expensive, flaky, and difficult to CI; not suitable for every PR.
- **Manual verification**: Not scalable; errors would slip through to production.
- **Schema-only validation**: Validates format but not semantic correctness (capability mapping, error taxonomy).

---

## Summary of Research Findings

| Topic | Decision | Key Insight |
|-------|----------|-------------|
| Capability Descriptor | Standardized format with: tools, json_mode, vision, context_window, streaming | Enables capability-aware routing (FR-ENG-07) |
| Error Taxonomy | Map to OpenAI-compatible envelope with gateway error codes | Consistent client experience (FR-ENG-08, AD-11) |
| Adapter Port | Trait with convert_request/convert_response/declare_capabilities | Provider-agnostic contract (AD-4) |
| Contract Tests | Automated tests against mock servers | Verifies adapter compliance without provider dependencies |