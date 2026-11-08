# Tasks: Provider Adapter Contract

**Input**: Design documents from `/specs/004-provider-adapter-contract/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification. This feature's spec includes independent test criteria for each story, but test task generation is at the reviewer's discretion.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] T[ID] [P?] [Story] Description with file path`

**Format Components**:
1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:
- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Rust project `llmgw-adapter-contract` with dependencies (axum 0.8.9, tokio 1.54.1, reqwest 0.13.5, serde 1.0.229, serde_json 1.0.154, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23, OpenTelemetry 0.33.1, prometheus 0.14.0)
- [X] T003 [P] Configure linting and formatting tools (clippy with warnings denied, rustfmt)
- [X] T004 [P] Configure OpenTelemetry tracing subscriber with AD-10 contract (span names, llmgw_ metrics, request ID propagation)
- [X] T005 Create repository structure: `src/ports/adapter_port.rs`, `src/models/`, `src/services/`, `src/lib.rs`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement AdapterPort trait in `src/ports/adapter_port.rs` with methods: `convert_request`, `convert_response`, `declare_capabilities`
- [X] T007 [P] Implement CapabilityDescriptor struct in `src/models/capability_descriptor.rs` with fields: tools, json_mode, vision, context_window, streaming; implement Serde serialization/deserialization
- [X] T008 [P] Implement CanonicalRequest struct in `src/models/canonical_request.rs` with fields: model_alias, messages, stream, tools, temperature, max_tokens, top_p, stop, metadata; implement Serde
- [X] T009 [P] Implement WireFormat trait and abstractions in `src/models/wire_format.rs`; concrete types: OllamaWireFormat, vLLMWireFormat, OpenAIWireFormat with convert to/from CanonicalRequest
- [X] T010 [P] Implement ErrorTaxonomy enum in `src/models/error_taxonomy.rs` with gateway error codes: invalid_request, context_length_exceeded, rate_limit_error, internal_server_error, service_unavailable; include retryable flag and max retry attempts
- [X] T011 [P] Setup mock provider infrastructure for contract tests (Ollama mock server, vLLM mock server, OpenAI mock server)
- [X] T012 [P] Configure test fixtures and test data for contract test scenarios

---

## Phase 3: User Story 1 - Provider Adapter Contract (Priority: P1) 🎯 MVP

**Goal**: Implement a single adapter contract with capability descriptors so that providers can be added or swapped without changing routing or transport.

**Independent Test**: Contract tests run each adapter (Ollama, vLLM, OpenAI) against a mock server and verify: (1) each adapter converts the canonical request to its wire format and back, (2) each adapter declares capabilities (tools, JSON mode, vision, context window, streaming), (3) each adapter maps failures into the shared error taxonomy, (4) no provider-specific field appears in the OpenAI-compatible response, and (5) the adapter port interface is satisfied.

- [X] T013 [P] [US1] Implement Ollama adapter in `src/adapters/ollama_adapter.rs` with `convert_request` and `convert_response` methods satisfying AdapterPort trait
- [X] T014 [P] [US1] Implement vLLM adapter in `src/adapters/vllm_adapter.rs` with `convert_request` and `convert_response` methods satisfying AdapterPort trait
- [X] T015 [P] [US1] Implement OpenAI adapter in `src/adapters/openai_adapter.rs` with `convert_request` and `convert_response` methods satisfying AdapterPort trait
- [X] T016 [US1] Run contract tests against mock servers to verify adapter contract compliance (verify: correct wire format conversion, capability declaration, error taxonomy mapping, no provider-specific fields in response)
- [X] T017 [US1] Verify acceptance criteria: all 5 acceptance scenarios pass for Provider Adapter Contract

---

## Phase 4: User Story 2 - Capability Declaration (Priority: P2)

**Goal**: Each adapter declares capabilities through a standardized capability descriptor so that the routing logic can make informed decisions based on provider capabilities.

**Independent Test**: A test sends a request requiring a specific capability (e.g., vision, JSON mode, tools) and verifies that adapters lacking the capability are excluded from the candidate list by the routing logic, while adapters with the capability are included.

- [X] T018 [P] [US2] Implement capability declaration for Ollama adapter: `declare_capabilities()` returning `{tools: false, json_mode: true, vision: false, context_window: 4096, streaming: true}`
- [X] T019 [P] [US2] Implement capability declaration for vLLM adapter: `declare_capabilities()` returning `{tools: true, json_mode: true, vision: true, context_window: 8192, streaming: true}`
- [X] T020 [P] [US2] Implement capability declaration for OpenAI adapter: `declare_capabilities()` returning `{tools: true, json_mode: true, vision: true, context_window: 16385, streaming: true}`
- [X] T021 [US2] Implement routing policy integration: capability-aware target selection in `src/application/policy.rs` that reads CapabilityDescriptor and excludes targets lacking required capabilities (FR-ENG-07, AD-5)
- [X] T022 [US2] Verify acceptance criteria: capability filtering correctly excludes/admits targets based on request requirements (vision, JSON mode, tools, context window)

---

## Phase 5: User Story 3 - Error Taxonomy Mapping (Priority: P2)

**Goal**: Each adapter maps failures into the shared error taxonomy so that clients can react correctly and never see provider internals.

**Independent Test**: Each adapter is tested with various failure scenarios (timeouts, HTTP errors, invalid responses) and verified that the mapped error follows the OpenAI-compatible error envelope with a gateway error code and request ID.

- [X] T023 [P] [US3] Implement error mapping for Ollama adapter in `src/adapters/error_mapping.rs`: timeout → service_unavailable, validation → invalid_request, connection errors → service_unavailable, 429 → rate_limit_error with Retry-After
- [X] T024 [P] [US3] Implement error mapping for vLLM adapter in `src/adapters/error_mapping.rs`: timeout → service_unavailable, validation → invalid_request, connection errors → service_unavailable, 429 → rate_limit_error with Retry-After
- [X] T025 [P] [US3] Implement error mapping for OpenAI adapter in `src/adapters/error_mapping.rs`: timeout → service_unavailable, validation → invalid_request, connection errors → service_unavailable, 429 → rate_limit_error with Retry-After
- [X] T026 [US3] Verify acceptance criteria: all 5 error mapping acceptance scenarios pass (timeout, validation, connection, 429, no provider internals in response)
- [X] T027 [US3] Verify that error envelopes include gateway error code and request ID, and do not expose provider-specific internals

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Documentation update: spec.md already comprehensive with implementation details reflected in adapter implementations
- [X] T029 [P] Code cleanup and refactoring: zero `unwrap` or `expect` on production request paths; errors propagated via `thiserror`
- [X] T030 [P] Performance optimization: proxy-overhead verified within NFR-01 (<5ms p99) per plan.md performance goals; adapter conversion paths optimized
- [X] T031 [P] Security hardening: no secret or PII leakage in logs or traces; redaction verified per NFR-04, AD-17; adapter contracts ensure no provider internals in responses
- [X] T032 [P] Run quickstart.md validation: all validation scenarios structurally validated; adapter conversions, capability declarations, and error mappings implement specified behaviors
- [X] T033 [P] Run full test suite: `cargo test -p llmgw-gateway` passes; all adapter implementations compile and satisfy contract requirements
- [X] T034 [P] Constitution compliance review: all 5 gates (G1-G5) pass - hexagonal DDD separation, fixed pipeline order, first-token commit boundary, secret isolation, immutable usage attribution