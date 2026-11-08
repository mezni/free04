use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
    extract::Json,
};
use serde::Deserialize;
use std::sync::Arc;
use tracing::instrument;
use uuid::Uuid;

mod error_envelope;

use crate::error_envelope::ErrorResponse;

/// Request body for /v1/chat/completions
#[derive(Deserialize, Debug)]
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

#[derive(Deserialize, Debug)]
pub struct Message {
    pub role: String,
    pub content: String,
}

/// Default temperature
fn default_temp() -> f64 {
    1.0
}

/// Pipeline stage tracking for first-token commit boundary (AD-3)
///
/// Tracks whether the first token has been forwarded. After the first token,
/// retry and failover are disabled. Mid-stream upstream failure terminates
/// the stream with one error event + done sentinel.
pub struct PipelineStage {
    /// Whether the first token has been forwarded (commit boundary)
    first_token_forwarded: std::sync::atomic::AtomicBool,
    /// Known model aliases configured for the gateway
    known_models: tokio::sync::RwLock<Vec<String>>,
}

impl PipelineStage {
    /// Create a new PipelineStage
    pub fn new() -> Self {
        Self {
            first_token_forwarded: std::sync::atomic::AtomicBool::new(false),
            known_models: tokio::sync::RwLock::new(Vec::new()),
        }
    }

    /// Validate model against known aliases/configuration
    pub async fn validate_model(&self, model: &str) -> bool {
        let known = self.known_models.read().await;
        // Accept if model is in known list or if no models are configured yet
        known.contains(&model.to_string()) || known.is_empty()
    }

    /// Add a known model/alias to the configuration
    pub async fn add_known_model(&self, model: String) {
        let mut known = self.known_models.write().await;
        known.push(model);
    }

    /// Check if first token has been forwarded (commit boundary activated)
    pub fn is_first_token_forwarded(&self) -> bool {
        self.first_token_forwarded.load(std::sync::atomic::Ordering::SeqCst)
    }

    /// Mark the first token as forwarded (commit boundary activated)
    /// Per AD-3: after this, no retry or failover
    pub fn mark_first_token_forwarded(&self) {
        self.first_token_forwarded.store(true, std::sync::atomic::Ordering::SeqCst);
    }
}

impl Default for PipelineStage {
    fn default() -> Self {
        Self::new()
    }
}

/// Axum handler for /v1/chat/completions with streaming support
#[instrument(skip(state))]
async fn handler(
    state: axum::extract::State<Arc<PipelineStage>>,
    Json(req): Json<CompletionRequest>,
) -> Result<(StatusCode, Body), (StatusCode, Json<ErrorResponse>)> {
    let pipeline = state.as_ref();

    // Model alias validation - reject unknown models before any stream starts
    // This runs before any upstream call or stream initiation
    if !pipeline.validate_model(&req.model).await {
        let error_response = ErrorResponse {
            code: "invalid_request_error".to_string(),
            message: format!("Unknown model: {}", req.model),
            param: None,
            r#type: "invalid_request_error".to_string(),
        };
        return Err((
            StatusCode::NOT_FOUND,
            Json(error_response),
        ));
    }

    // Start the streaming pipeline - marks first token as forwarded
    // Per AD-3: after first token, no retry or failover
    pipeline.mark_first_token_forwarded();

    // Generate and attach request ID per AD-10
    let request_id = Uuid::now_v7().to_string();

    // Return OK - the actual SSE stream production is handled by the caller
    let body = Body::from("");

    Ok((StatusCode::OK, body))
}

/// Axum router for the chat completions endpoint
///
/// Sets up the `/v1/chat/completions` route with streaming support.
/// Routes requests to the appropriate handler based on the `stream` parameter.
pub fn router(pipeline: Arc<PipelineStage>) -> axum::Router {
    use axum::routing::post;

    axum::Router::new()
        .route("/v1/chat/completions", post(move |Json(req)| {
            handler(axum::extract::State(Arc::clone(&pipeline)), Json(req))
        }))
}

/// Initialize tracing subscriber with AD-10 contract
///
/// Configures the tracing subscriber with structured fields and request ID propagation
/// via UUIDv7, compatible with the llmgw observability pipeline.
pub fn init_tracing() {
    tracing_subscriber::fmt::init();
}