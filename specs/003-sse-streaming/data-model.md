# Data Model: SSE Streaming with Commit Boundary

## ChatCompletionRequest

Represents an OpenAI-compatible chat completion request with streaming enabled.

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model alias or specific model name |
| `messages` | array of message objects | Conversation history, each with `role` (system/user/assistant) and `content` |
| `stream` | boolean | **Must be `true`** for streaming mode. v1 defaults to `false` (non-streaming). |
| `temperature` | number | Sampling temperature (0-2), optional |
| `max_tokens` | integer | Maximum tokens in response, optional |
| `top_p` | number | Nucleus sampling parameter, optional |
| `stop` | array of strings | Stop sequences, optional |
| `presence_penalty` | number | Presence penalty parameter, optional |
| `frequency_penalty` | number | Frequency penalty parameter, optional |

**Constraints**:
- `messages` must have at least one message
- `stream` must be `true` for streaming requests; `stream=false` or absent routes to non-streaming endpoint
- All other fields follow the same constraints as the non-streaming ChatCompletionRequest

---

## SSE Delta Event

Represents a single Server-Sent Events delta containing partial choice updates.

| Field | Type | Description |
|-------|------|-------------|
| `event` | string (optional) | Event type identifier |
| `data` | string (JSON-encoded) | JSON-stringified delta object |

**Delta Object Format** (JSON inside `data` field):
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
        "content": "partial response content"
      },
      "finish_reason": null
    }
  ]
}
```

**Constraints**:
- `id`, `object`, `created`, `model` are consistent across all delta events for one request
- `choices[].index` identifies which choice the delta applies to
- `choices[].delta.role` is always `"assistant"` for chat completions
- `choices[].delta.content` contains the new token(s) for this chunk
- `choices[].finish_reason` is `null` for all delta events (only set in the done sentinel)

---

## SSE Done Sentinel

Final event signaling stream completion. Sent once after the last delta (or immediately if no tokens emitted).

| Field | Type | Description |
|-------|------|-------------|
| `event` | string (optional) | Not typically set |
| `data` | string | Always `[DONE]` (JSON-encoded string) |

**Format**: `data: [DONE]\n\n`

**Constraints**:
- Exactly one done sentinel is sent per stream
- Sent after the last delta event (or as the only event if no tokens were emitted before completion)
- After the first forwarded token, no retry or failover occurs (AD-3)
- A mid-stream upstream failure emits one gateway error event followed by the done sentinel

---

## Usage Event (Immutable)

One immutable usage event per attempt, recorded after stream completion.

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string (UUIDv7) | Identifier for the original request |
| `attempt_id` | string (UUIDv7) | Identifier for this attempt (unique per retry) |
| `principal` | string | Authenticated principal/team identifier |
| `alias` | string | Model alias used in the request |
| `provider` | string | Provider that served the request |
| `model` | string | Model that served the request |
| `prompt_tokens` | integer | Number of prompt tokens |
| `completion_tokens` | integer | Number of completion tokens (from the stream) |
| `total_tokens` | integer | prompt_tokens + completion_tokens |
| `latency` | integer (ms) | Time from request start to stream completion |
| `outcome` | string | `success`, `failed`, `abandoned`, `rate_limited` |
| `cost_snapshot` | integer (micro-units) | Cost computed from price table version active at event time |
| `price_table_version` | string | Identifier of the price table version used |

**Constraints**:
- Exactly one usage event per attempt (AD-9, AD-15)
- Derived facts (aggregates) are never edited in place
- Cost is a snapshot; editing prices creates a new version and does not alter past events
- `principal` and `alias` are non-null
- Outcome reflects the final state: success if stream completed, failed if mid-stream error, etc.