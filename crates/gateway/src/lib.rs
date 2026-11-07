use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
    extract::Json,
};
use serde::Deserialize;
use std::sync::Arc;
use tracing::instrument;

use crate::error_envelope::GatewayError;

/// Request body for /v1/chat/completions
#[derive(Deserialize)]
pub struct CompletionRequest {
    /// The target model alias
    pub model: String,
    /// Chat messages
    pub messages: Vec<Message>,
    /// Temperature sampling parameter
    #[serde(default = "default_temp")]
    pub temperature: f64,
    /// Maximum number of tokens to generate
    #[serde(default)]
    pub max_tokens: Option<u32>,
    /// Whether to stream SSE tokens
    #[serde(default)]
    pub stream: bool,
    /// Optional specification ID for duplicate detection
    #[serde(default)]
    pub spec_id: Option<String>,
}

#[derive(Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}

/// Default temperature
fn default_temp() -> f64 {
    1.0
}

/// Axum handler for /v1/chat/completions
#[instrument(skip(state, json))]
async fn handler(
    _: axum::extract::State<Arc<redis::aio::RedisConnection>>>,
    Json(req): Json<CompletionRequest>,
) -> Result<(StatusCode, Body), (StatusCode, axum::Json<crate::error_envelope::ErrorResponse>)> {
    // Extract spec_id for duplicate detection if provided
    if let Some(spec_id) = req.spec_id {
        // TODO: Check Redis for duplicate
        // For now, just mark it as seen (will be implemented fully later)
        tracing::info!("Received request with spec_id: {}", spec_id);
    }

    // Continue with normal processing
    let error_response = crate::error_envelope::ErrorResponse {
        code: "invalid_request_error".to_string(),
        message: "".to_string(),
        param: None,
        r#type: "invalid_request_error".to_string(),
    };

    Ok((
        StatusCode::OK,
        Body::from(serde_json::to_string(&serde_json::json!({
            "id": "req_123",
            "object": "chat.completion",
            "created": std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Mock response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        })).unwrap()),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_without_spec_id() {
        let req_body = serde_json::json!({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let req = serde_json::from_value::<CompletionRequest>(req_body).unwrap();
        assert!(req.spec_id.is_none());
    }

    #[test]
    fn test_request_with_spec_id() {
        let req_body = serde_json::json!({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "spec_id": "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
        });
        let req = serde_json::from_value::<CompletionRequest>(req_body).unwrap();
        assert_eq!(req.spec_id, Some("69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b".to_string()));
    }
}
