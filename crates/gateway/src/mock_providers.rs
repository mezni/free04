use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
    extract::Json,
};
use serde::Deserialize;
use std::sync::Arc;
use tracing::instrument;

use crate::error_envelope::ErrorResponse;

#[derive(Deserialize, Debug)]
pub struct MockCompletionRequest {
    pub model: String,
    pub messages: Vec<MockMessage>,
    pub stream: bool,
    #[serde(default)]
    pub temperature: Option<f64>,
    #[serde(default)]
    pub max_tokens: Option<u32>,
}

#[derive(Deserialize, Debug)]
pub struct MockMessage {
    pub role: String,
    pub content: String,
}

/// Mock Ollama server handler
pub async fn ollama_handler(
    _state: axum::extract::State<Arc<()>>,
    Json(req): Json<MockCompletionRequest>,
) -> Result<(StatusCode, Body), (StatusCode, Json<ErrorResponse>)> {
    let response = serde_json::json!({
        "model": req.model,
        "response": "Ollama mock response",
        "done": true,
    });

    let body = Body::from(serde_json::to_string(&response).unwrap_or_default());
    Ok((StatusCode::OK, body))
}

/// Mock vLLM server handler
pub async fn vllm_handler(
    _state: axum::extract::State<Arc<()>>,
    Json(req): Json<MockCompletionRequest>,
) -> Result<(StatusCode, Body), (StatusCode, Json<ErrorResponse>)> {
    let response = serde_json::json!({
        "model": req.model,
        "text": "vLLM mock response",
        "token_count": 42,
    });

    let body = Body::from(serde_json::to_string(&response).unwrap_or_default());
    Ok((StatusCode::OK, body))
}

/// Mock OpenAI server handler
pub async fn openai_handler(
    _state: axum::extract::State<Arc<()>>,
    Json(req): Json<MockCompletionRequest>,
) -> Result<(StatusCode, Body), (StatusCode, Json<ErrorResponse>)> {
    let choices = req.messages.iter().map(|msg| {
        serde_json::json!({
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "OpenAI mock response"
            },
            "finish_reason": "stop"
        })
    });

    let response = serde_json::json!({
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 1234567890,
        "model": &req.model,
        "choices": choices,
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    });

    let body = Body::from(serde_json::to_string(&response).unwrap_or_default());
    Ok((StatusCode::OK, body))
}

/// Setup mock provider routers
pub fn mock_router(provider: &str) -> axum::Router {
    use axum::routing::post;

    let route = match provider {
        "ollama" => axum::Router::new().route("/v1/chat/completions", post(ollama_handler)),
        "vllm" => axum::Router::new().route("/v1/chat/completions", post(vllm_handler)),
        "openai" => axum::Router::new().route("/v1/chat/completions", post(openai_handler)),
        _ => axum::Router::new(),
    };

    route
}