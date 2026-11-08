# Adapter Contract

## Adapter Port Interface

The adapter port defines the contract that all provider adapters must satisfy. It is a Rust trait with the following methods:

### `convert_request`

**Signature**: `fn(&CanonicalRequest) -> Result<WireFormat, AdapterError>`

**Description**: Converts a canonical, provider-agnostic request into the provider-specific wire format. This is the core translation layer that enables provider-agnostic routing.

**Input**: `CanonicalRequest` - the normalized request format (see data-model.md)

**Output**: `WireFormat` - the provider-specific wire format containing the raw request bytes and MIME type

**Error**: `AdapterError` - mapped to OpenAI-compatible error envelope (AD-11). Errors include: invalid request, unsupported capability, conversion failure.

### `convert_response`

**Signature**: `fn(&WireFormat) -> Result<CanonicalResponse, AdapterError>`

**Description**: Converts a provider-specific wire format response into the canonical, provider-agnostic format. The result is an OpenAI-compatible Chat Completions response shape.

**Input**: `WireFormat` - the provider-specific wire format

**Output**: `CanonicalResponse` - OpenAI-compatible response with `id`, `object`, `created`, `model`, `choices`, `usage`, and `error` (if applicable)

**Error**: `AdapterError` - mapped to OpenAI-compatible error envelope. Ensures no provider-specific internals leak into the response (AD-11).

### `declare_capabilities`

**Signature**: `fn() -> CapabilityDescriptor`

**Description**: Returns the capability descriptor for this adapter, declaring which features the provider supports. This is consumed by the declarative routing policy (FR-ENG-07, AD-5).

**Output**: `CapabilityDescriptor` - standardized capability description including: tools, json_mode, vision, context_window, streaming

---

## Capability Descriptor Contract

The capability descriptor is a standardized data structure that describes provider capabilities. It follows this schema:

```json
{
  "tools": boolean,
  "json_mode": boolean,
  "vision": boolean,
  "context_window": integer (tokens),
  "streaming": boolean
}
```

**Usage**: The routing policy engine reads capability descriptors to build the candidate target list for a given request. Targets lacking required capabilities (e.g., vision for image requests, context_window below minimum) are excluded.

**Versioning**: The capability descriptor format is versioned; v1 includes: tools, json_mode, vision, context_window, streaming. Future versions may add additional capabilities.

---

## Error Taxonomy Contract

The error taxonomy defines how provider-specific errors are mapped to the OpenAI-compatible error envelope. The mapping must satisfy:

- **AD-11**: Stable OpenAI-compatible error envelope; no raw provider errors
- **FR-ENG-08**: Map failures into the shared error taxonomy
- **FR-RES-02**: Never retry 4xx (except configured 429); never retry after first streamed token

**Mapping rules**:
- Provider validation errors → `invalid_request` with detailed message
- Provider rate limit (429) → `rate_limit_error` with Retry-After header
- Provider 5xx/connection errors → `internal_server_error` or `service_unavailable`
- Context window exceeded → `context_length_exceeded`
- Unsupported parameters → `invalid_request`
- All errors include: gateway error code, request ID, human-readable message

**No error mapping should expose**: provider internal error codes, stack traces, credential material, or prompt/response bodies.