# Implementation Plan: SSE Streaming with Commit Boundary

**Branch**: `[003-sse-streaming]` | **Date**: [DATE] | **Spec**: specs/003-sse-streaming/spec.md

**Input**: Feature specification from `/specs/003-sse-streaming/spec.md`

## Summary

SSE streaming with commit boundary for the OpenAI-compatible `/v1/chat/completions` endpoint. Implements `stream=true` to forward upstream chunks as SSE deltas without buffering, with done sentinel `[DONE]` at stream completion. Enforces AD-3: no retry or failover after the first forwarded token.

## Technical Context

**Language/Version**: Rust 1.75 (edition 2024)

**Primary Dependencies**: axum 0.8.9, tokio 1.54.1, tower 0.5.3, tower-http 0.7.1, serde 1.0.229, serde_json 1.0.154, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23

**Storage**: None (data-plane is request-response or SSE stream only)

**Testing**: cargo test; integration tests for SSE scenarios, contract tests for streaming

**Target Platform**: Linux (Kubernetes data-plane pods), also local development

**Project Type**: Library/WS crate (llmgw-gateway) — three-crate workspace: llmgw-domain, llmgw-application, llmgw-gateway

**Performance Goals**: TTFT overhead below 5ms p99 (NFR-01); proxy-added overhead excluding upstream inference

**Constraints**:
- AD-3: Failover and retry only before the first token; mid-stream failure terminates the stream
- AD-11: Stable OpenAI-compatible error envelope; no raw provider errors
- Constitution Principle III: First-token commit boundary
- No prompt or response body persistence by default (AD-17)
- SSE events follow OpenAI delta shape with one done sentinel

**Performance Goals**: Proxy-added overhead below 5ms p99, excluding upstream inference

**Constraints**: 
- AD-3: Failover and retry only before the first token; mid-stream failure terminates the stream
- AD-11: Stable OpenAI-compatible error envelope; no raw provider errors
- Constitution Principle III: First-token commit boundary
- No prompt or response body persistence by default (AD-17)
- SSE events follow OpenAI delta shape with one done sentinel

**Scale/Scope**: Phase 0 pilot — one team can stream through the gateway; exit criteria: pilot team streams via gateway; failover before first token works; no secrets in logs; traces and metrics visible

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gates**:
- I. Hexagonal DDD Separation: Gateway → application → domain; domain has no I/O. Ensure streaming trait implementations do not leak I/O into domain layer.
- II. Fixed Pipeline Order: Stage sequence (transport, validate, authenticate, authorize, rate limit/quota, input guardrail, route, resilience loop, provider call, output guardrail, meter, audit). Streaming must integrate into fixed pipeline without reordering.
- III. First-Token Commit Boundary: **CRITICAL** — Ensure the resilience loop tracks whether the first token has been forwarded and disables retry/failover thereafter. This is the single most important gate for Story 1.3.
- IV. Secret Isolation: Ensure no secrets appear in SSE events, logs, or error responses during streaming.
- V. Immutable Usage & Cost Attribution: Ensure one immutable usage event per attempt, even with streaming. Cost snapshot computed from price table version active at event time.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-sse-streaming/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — all NEEDS CLARIFICATION resolved
├── data-model.md        # Phase 1 output — ChatCompletionRequest, SSE Delta, Done Sentinel, Usage Event
├── quickstart.md        # Phase 1 output — validation scenarios for streaming
├── contracts/           # Phase 1 output — API contract for SSE streaming
│   └── contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Single project (DEFAULT) — Cargo workspace

crates/
├── domain/              # llmgw-domain — pure data types, no I/O
├── application/         # Ports & traits (pipeline stages, adapter port, secrets port)
└── gateway/             # axum handler, resilience loop, SSE stream producer

tests/
├── unit/
├── integration/         # SSE streaming contract tests
└── contract/           # API contract tests
```

**Structure Decision**: Single project (Cargo workspace with 3 crates). The gateway crate implements the SSE streaming handler; domain and application crates remain unchanged from Phase 0 foundation.

---

## Complexity Tracking

*No Constitution Check violations require justification for this feature.*

---

## User Stories & Acceptance Criteria (from spec.md)

| US# | Priority | Title | Key Gates |
|-----|----------|-------|-----------|
| US1 | P1 | SSE streaming with commit boundary | AD-3, AD-11 |
| US2 | P2 | Unknown model/alias returns 404/400 with AD-11 envelope | AD-11 |
| US3 | P3 | X-Request-Id present in all responses | AD-10 |
```

---

## Phase Structure

- **Phase 1**: Setup (project initialization) — workspace checks, tracing/telemetry setup
- **Phase 2**: Foundational (blocking prerequisites) — pipeline stage for streaming, resilience loop first-token tracking
- **Phase 3**: User Story 1 (P1) — SSE streaming handler in gateway, delta event production, done sentinel
- **Phase 4**: User Story 2 (P2) — model alias validation before streaming, error envelope for unknown models
- **Phase 5**: User Story 3 (P3) — request ID propagation in SSE headers and logs
- **Final Phase**: Polish & Cross-Cutting Concerns — documentation, quickstart validation, edge cases