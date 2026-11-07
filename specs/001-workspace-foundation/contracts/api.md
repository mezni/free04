# Contracts: Duplicate Specs Handling

## OpenAI-Compatible API Contract

### Request: POST /v1/chat/completions

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer <jwt-or-apikey>`
- `OpenAI-Client-Timeout`: optional, integer seconds

**JSON Body**:
```json
{
  "model": "string",
  "messages": [
    {
      "role": "string",
      "content": "string"
    }
  ],
  "temperature": "number",
  "max_tokens": "integer",
  "stream": "boolean",
  "spec_id": "UUIDv7 string (optional)"
}
```

**Field Descriptions**:
- `model`: Required. The target model alias (e.g., "gpt-4o", "claude-3-opus")
- `messages`: Required. Array of message objects with role and content
- `temperature`: Optional. Floating point, default 1.0
- `max_tokens`: Optional. Integer, maximum tokens to generate
- `stream`: Optional. Boolean, default false. If true, establishes SSE stream
- `spec_id`: Optional. UUIDv7 string. When provided, enables duplicate detection. If a request with the same spec_id is received within 5 minutes, the second request is rejected.

**Contract Notes**:
- `spec_id` is an optional field per this contract
- When `spec_id` is omitted, duplicate detection is not active (existing behavior)
- When `spec_id` is provided, the duplicate detection pipeline stage checks for repeats
- The spec_id field does not affect the core OpenAI schema; it's an extension mechanism
- Providers do not see the spec_id; it's processed entirely within the gateway

### Response: 200 OK (non-streaming)

```json
{
  "id": "string (request_uuid)",
  "object": "chat.completion",
  "created": "integer (unix_timestamp)",
  "model": "string",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "string"
      },
      "finish_reason": "string"
    }
  ],
  "usage": {
    "prompt_tokens": integer,
    "completion_tokens": integer,
    "total_tokens": integer
  }
}
```

### Response: 400 Invalid Request (duplicate spec detected)

```json
{
  "error": {
    "message": "A request with this specification ID already exists",
    "type": "invalid_request_error",
    "param": null,
    "code": "duplicate_spec"
  }
}
```

### Response: 400 Invalid Request (general validation failure)

Per AD-11 error taxonomy, same format as other validation errors.

## Internal Redis Contract

### Key: `active_spec_ids`
- **Type**: Redis SET
- **Members**: UUIDv7 hex strings
- **TTL**: 300 seconds (5 minutes, set via EXPIRE command)
- **Operations**:
  - `SISMEMBER key member` → returns integer (0 or 1)
  - `SADD key member` → returns integer (0 or 1, 1 if member was added)
  - `EXPIRE key seconds` → returns boolean

## Contract Compliance

- **AD-11 (Gateway error taxonomy)**: All errors use the AD-11 envelope format
- **AD-4 (Secret isolation)**: spec_id does not contain or leak secrets; it's a UUIDv7 with no security-sensitive data
- **AD-3 (First-token commit boundary)**: spec_id processing completes before any tokens are forwarded; if duplicate detected, no tokens are sent
- **AD-2 (Fixed pipeline order)**: spec_id check fits between limits and route stages; no stage is bypassed