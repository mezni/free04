# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

**Language/Version**: Rust 1.75+ (project uses Rust 1.99.1, axum 0.8.9, tokio 1.54.1)

**Primary Dependencies**: axum 0.8.9, tokio 1.54.1, reqwest 0.13.5, serde 1.0.229, serde_json 1.0.154, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23, OpenTelemetry 0.33.1, prometheus 0.14.0

**Storage**: N/A (adapter contract focuses on request/response conversion; no persistent storage for this feature)

**Testing**: cargo test with contract tests against mock providers (project test infrastructure)

**Target Platform**: Linux server, Kubernetes 1.35 (project runs on K8s data plane)

**Project Type**: web-service (LLM gateway - OpenAI-compatible routing and adaptation layer)

**Performance Goals**: <5ms p99 proxy overhead (NFR-01: proxy-added overhead below 5ms p99, excluding upstream inference)

**Constraints**: Zero `unwrap` or `expect` on production request paths (NFR-08); no secret or PII leakage in logs or traces (NFR-04, AD-17); adapter contract must be provider-agnostic (AD-4); error envelope must be OpenAI-compatible (AD-11)

**Scale/Scope**: Phase 0 pilot team onboarding; adapter contract enables provider extensibility without routing modifications

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate G1: Hexagonal DDD Separation (Principle I)
- **Pass**: Adapter port is a trait defined in the gateway crate; all adapters (Ollama, vLLM, OpenAI) implement this port without domain crate dependencies. Dependencies flow gateway → application → domain; domain has no I/O dependencies.
- **Violation**: Adapter port or implementations leak into domain crate or depend on I/O libraries.

### Gate G2: Fixed Pipeline Order (Principle II)
- **Pass**: Adapter contract is a provider-agnostic interface; request conversion happens within the validated/authenticated path without altering the immutable stage sequence: transport → validate → authenticate → authorize → rate limit/quota → input guardrail → route → resilience → provider call → output guardrail → meter → audit.
- **Violation**: Adapter conversion inserts or bypasses pipeline stages, or allows provider-specific logic to short-circuit the fixed order.

### Gate G3: First-Token Commit Boundary (Principle III)
- **Pass**: Adapter contract operates on the canonical request before the first token is forwarded; after first token commitment, no retry/failover through adapter layer. Contract tests verify commit boundary is respected.
- **Violation**: Adapter enables retry or failover after first token has been forwarded.

### Gate G4: Secret Isolation (Principle IV)
- **Pass**: Adapter contract works with canonical request format; no provider-specific secrets appear in the OpenAI-compatible response. Adapters map failures to error taxonomy without exposing internal credentials.
- **Violation**: Adapter exposes provider credentials, or canonical request contains secret material.

### Gate G5: Immutable Usage & Cost Attribution (Principle V)
- **Pass**: Adapter contract does not intercept or modify usage event recording. Request passes through to provider, usage event is recorded after provider attempt completes.
- **Violation**: Adapter disrupts usage event flow or modifies cost attribution.

**Gate Status**: All gates G1-G5 pass. No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
