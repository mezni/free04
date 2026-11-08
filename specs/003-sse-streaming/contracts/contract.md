# API Contract: SSE Streaming Chat Completions

## Endpoint
`POST /v1/chat/completions` with `stream=true` parameter

## Request Format
OpenAI Chat Completions JSON schema with `stream: true`.

**Key request fields**:
- `model`: string - model alias or specific model name
- `messages`: array of {role: string, content: string} - conversation history
- `stream`: boolean - **Must be `true`** for streaming mode
- `temperature`: number - sampling temperature (0-2), optional
- `max_tokens`: integer - max tokens in response, optional
- `top_p`: number - nucleus sampling, optional
- `stop`: array of strings - stop sequences, optional
- `presence_penalty`: number, optional
- `frequency_penalty`: number, optional

## Response Format
Server-Sent Events (SSE) stream with the following event types:

### Delta Events (forwarded upstream chunks)
```
event: <optional>
data: <JSON-encoded delta object>\n\n
```

**Delta object** (JSON):
```json
{
  "id": "chatcm-...",
  "object": "chat.completion.chunk",
  "created": 1234567890,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "partial content"
      },
      "finish_reason": null
    }
  ]
}
```

**Constraints**:
- Sent as individual SSE events with `data:` prefix and double newline suffix
- `choices[].index` identifies which choice the delta applies to
- `choices[].delta.content` contains new token(s) for this chunk
- `choices[].finish_reason` is `null` for all delta events
- `id`, `object`, `created`, `model` are consistent across all events for one request

### Done Sentinel (stream completion)
```
data: [DONE]\n\n
```

**Constraints**:
- Exactly one done sentinel is sent per stream
- Sent after the last delta event (or as the only event if no tokens emitted)
- After the first forwarded token, no retry or failover occurs (AD-3)
- A mid-stream upstream failure emits one gateway error event followed by the done sentinel

### Error Events (mid-stream failure)
```
event: gateway_error
data: <JSON-encoded AD-11 error envelope>\n\n
```

**AD-11 Error Envelope**:
```json
{
  "error": {
    "message": "descriptive error message",
    "type": "invalid_request_error",
    "code": "upstream_error",
    "param": null
  }
}
```

**Constraints**:
- At most one error event sent (mid-stream failure terminates the stream)
- Error event followed immediately by done sentinel
- Raw provider bodies and secrets never appear in the response (AD-11)
- 5xx and connect/read timeouts trigger failover before first token (AD-3); after first token, error event + done sentinel only

## Response Headers
- `X-Request-Id`: Unique request identifier (RFC 3339 / UUID format)

## Error Responses (non-streaming fallback)
- `400`: Invalid request - malformed JSON, schema validation failure
- `401`: Unauthorized - missing/invalid OIDC JWT or API key
- `403`: Forbidden - insufficient scopes/permissions
- `404`: Unknown model or alias - returns stable error envelope (AD-11)
- `429`: Rate limited - with Retry-After header
- `5xx`: Provider failures - with stable error envelope (AD-11)

## Contract Compliance
- All responses use the AD-11 stable error envelope
- No raw provider bodies or secrets in responses (AD-11, AD-17)
- Request ID propagated in headers and telemetry (AD-10)
- Versioned under `/v1` with documented deprecation policy