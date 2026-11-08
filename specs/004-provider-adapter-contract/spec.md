# Feature Specification: Provider Adapter Contract

**Feature Branch**: `[004-provider-adapter-contract]`

**Created**: 2026-11-07

**Status**: Draft

**Input**: From docs/EPICS.md story 1.4 - "As a platform engineer, I want a single adapter contract with capability descriptors, so that providers can be added or swapped without changing routing or transport."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Provider Adapter Contract (Priority: P1)

As a platform engineer,
I want a single adapter contract with capability descriptors,
So that providers can be added or swapped without changing routing or transport.

**Why this priority**: This is the foundational adapter layer for the gateway (Phase 0 Router). It enables provider-agnostic routing and allows new providers to be integrated without modifying the core routing logic. It is independently testable through contract tests against mock providers.

**Independent Test**: Contract tests run each adapter (Ollama, vLLM, OpenAI) against a mock server and verify: (1) each adapter converts the canonical request to its wire format and back, (2) each adapter declares capabilities (tools, JSON mode, vision, context window, streaming), (3) each adapter maps failures into the shared error taxonomy, (4) no provider-specific field appears in the OpenAI-compatible response, and (5) the adapter port interface is satisfied.

**Acceptance Scenarios**:

1. **Given** the adapter port is implemented, **when** the Ollama adapter processes a canonical request, **then** it converts the request to Ollama's wire format and back without introducing provider-specific fields into the OpenAI-compatible response.

2. **Given** the adapter port is implemented, **when** the vLLM adapter processes a canonical request, **then** it converts the request to vLLM's wire format and back, and declares capabilities: tools, JSON mode, vision, context window, and streaming.

3. **Given** the adapter port is implemented, **when** the OpenAI adapter processes a canonical request, **then** it converts the request to OpenAI's wire format and back, and declares capabilities: tools, JSON mode, vision, context window, and streaming.

4. **Given** all three adapters are implemented, **when** contract tests run each adapter against a mock server, **then** all adapters satisfy the adapter contract: correct wire format conversion, capability declaration, and error taxonomy mapping.

5. **Given** any adapter is implemented, **when** a request is processed through the adapter, **then** no provider-specific field appears in the OpenAI-compatible response returned to the caller.

---

### User Story 2 - Capability Declaration (Priority: P2)

As a platform engineer,
I want each adapter to declare its capabilities through a standardized capability descriptor,
So that the routing logic can make informed decisions based on provider capabilities.

**Why this priority**: Capability declarations enable the declarative routing policy (FR-ENG-07) to exclude targets that cannot serve a request (e.g., a model without vision support for image requests, or without sufficient context window for long prompts). This is a P2 requirement because it directly impacts routing correctness for diverse request types.

**Independent Test**: A test sends a request requiring a specific capability (e.g., vision, JSON mode, tools) and verifies that adapters lacking the capability are excluded from the candidate list by the routing logic, while adapters with the capability are included.

**Acceptance Scenarios**:

1. **Given** a request requiring vision support, **when** the routing logic builds the candidate list, **then** only adapters declaring vision capability are included.

2. **Given** a request requiring JSON mode, **when** the routing logic builds the candidate list, **then** only adapters declaring JSON mode capability are included.

3. **Given** a request requiring tools support, **when** the routing logic builds the candidate list, **then** only adapters declaring tools capability are included.

4. **Given** a request with a minimum context window requirement, **when** the routing logic builds the candidate list, **then** only adapters with context window >= the requirement are included.

5. **Given** an adapter without a declared capability, **when** a request requiring that capability is routed, **then** the adapter is excluded and a clear error is returned rather than a silent downgrade.

---

### User Story 3 - Error Taxonomy Mapping (Priority: P2)

As an application developer,
I want each adapter to map failures into the shared error taxonomy,
So that my client can react correctly and never sees provider internals.

**Why this priority**: Consistent error mapping ensures that clients can reliably handle errors regardless of the underlying provider. This is a P2 requirement because it affects client experience across all providers.

**Independent Test**: Each adapter is tested with various failure scenarios (timeouts, HTTP errors, invalid responses) and verified that the mapped error follows the OpenAI-compatible error envelope with a gateway error code and request ID.

**Acceptance Scenarios**:

1. **Given** an upstream timeout, **when** the adapter processes the failure, **then** the error is mapped to a gateway timeout error code in the OpenAI-compatible envelope.

2. **Given** an upstream validation error, **when** the adapter processes the failure, **then** the error is mapped to `invalid_request` with appropriate details.

3. **Given** a connection error, **when** the adapter processes the failure, **then** the error is mapped to a connection-related gateway error code.

4. **Given** an invalid response from the provider, **when** the adapter processes the failure, **then** the error is mapped using the shared error taxonomy without exposing provider internals.

5. **Given** a 429 response from the provider, **when** the adapter processes the failure, **then** the error honors Retry-After and is mapped appropriately.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-ENG-01**: Expose an OpenAI-compatible `/v1/chat/completions` endpoint with request and response schema. (REQ-ENG-01, P0)
- **FR-ENG-06**: Track provider/model capability support and exclude incompatible targets. (REQ-ENG-06, P1)
- **FR-RES-02**: Never retry 4xx (except configured 429) and never retry after the first streamed token. (REQ-RES-02, P0)
- **AD-4**: Provider adapter contract with capability descriptor and error taxonomy. Enforced by E1.S4.

### Key Entities *(include if feature involves data)*

- **Adapter Port**: The canonical interface that all provider adapters implement, defining the contract for request/response conversion and capability declaration.
- **Capability Descriptor**: A standardized description of provider capabilities including: tools, JSON mode, vision, context window, and streaming support.
- **Canonical Request**: The normalized, provider-agnostic request format that all adapters convert from and to.
- **Wire Format**: The provider-specific request/response format (e.g., Ollama format, vLLM format, OpenAI format).
- **Error Taxonomy**: The shared error classification and mapping scheme that translates provider-specific errors into the OpenAI-compatible error envelope.
- **Adapter**: A concrete implementation of the adapter port for a specific provider (Ollama, vLLM, OpenAI).
- **Contract Test**: A test that verifies an adapter satisfies the adapter port interface against a mock server.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All provider adapters (Ollama, vLLM, OpenAI) can convert canonical requests to their wire format and back without loss of required information.
- **SC-002**: Each adapter declares capabilities (tools, JSON mode, vision, context window, streaming) through a standardized capability descriptor.
- **SC-003**: Contract tests run each adapter against a mock server and verify all adapter contract requirements pass.
- **SC-004**: No provider-specific field appears in the OpenAI-compatible response returned to the caller (100% of cases).
- **SC-005**: Each adapter maps failures into the shared error taxonomy, producing OpenAI-compatible error envelopes with gateway error codes and request IDs.
- **SC-006**: An request with unsupported capabilities returns a clear error indicating which capability is missing, rather than a silent downgrade.
- **SC-007**: The adapter port interface is satisfied by all implemented adapvers as verified by contract tests.

---

## Assumptions

- The gateway already has authentication (OIDC/JWT) and routing infrastructure in place (Phase 0 foundation)
- The OpenAI Chat Completions schema serves as the contract surface for all adapters
- Model aliases and capabilities are managed through the control-plane configuration (AD-6, AD-4)
- No prompt or response body persistence by default (AD-17, Constitution principle IV)
- The adapter port interface is stable and versioned; new adapters can be added without modifying existing ones
- Contract tests can be run against mock servers for each provider type
- Integer micro-units for cost; UUIDv7 for request/attempt IDs; RFC 3339 UTC timestamps
- Constitution Principle III (First-Token Commit Boundary) is enforced: failover and retry are allowed only before the first token is forwarded
- Each adapter declares capabilities in a standardized format compatible with the routing policy engine

---

## Edge Cases

- What happens when an adapter does not support a requested capability (e.g., vision for a text-only model)?
- How does the system handle a provider whose capabilities change during a session?
- What if the canonical request contains fields not supported by a particular provider's wire format?
- How are concurrent adapter conversions from the same principal handled?
- What if an adapter returns a failure type not covered by the current error taxonomy?
- How does the system handle adapter version compatibility (e.g., new adapter version vs. old routing configuration)?