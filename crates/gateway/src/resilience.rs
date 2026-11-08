use axum::{
    body::Body,
    http::StatusCode,
    extract::State,
    response::Sse,
    middleware::Next,
};
use serde::Serialize;
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{instrument, info, warn, error};
use futures::stream::{Stream, StreamExt};
use uuid::Uuid;
use std::time::Instant;

use crate::error_envelope::ErrorResponse;

/// Resilience loop with first-token commit boundary (AD-3)
///
/// Tracks whether the first token has been forwarded. After the first token,
/// retry and failover are disabled. Mid-stream upstream failure terminates
/// the stream with one error event + done sentinel.
pub struct ResilienceLoop {
    /// Whether the first token has been forwarded (commit boundary)
    first_token_forwarded: std::sync::atomic::AtomicBool,
    /// SSE event channel sender
    sse_sender: Option<mpsc::Sender<SseEvent>>,
    /// Internal counter for tracking pipeline stages
    pipeline_stage: std::sync::atomic::AtomicUsize,
}

#[derive(Clone)]
/// SSE event types for the streaming stream
enum SseEvent {
    /// Delta event with new content
    Delta { data: String },
    /// Done sentinel at stream completion
    Done,
    /// Error event mid-stream (followed by done sentinel)
    Error { code: String, message: String },
}

impl ResilienceLoop {
    /// Create a new ResilienceLoop
    pub fn new() -> Self {
        Self {
            first_token_forwarded: std::sync::atomic::AtomicBool::new(false),
            sse_sender: None,
            pipeline_stage: std::sync::atomic::AtomicUsize::new(0),
        }
    }

    /// Start the streaming pipeline - mark first token as forwarded
    pub async fn start_streaming(&self) {
        self.first_token_forwarded.store(true, std::sync::atomic::Ordering::SeqCst);
        info!("First token forwarded - commit boundary activated (AD-3)");
    }

    /// Validate model against known aliases/configuration
    pub async fn validate_model(&self, model: &str) -> bool {
        // TODO: Check against configured model aliases/capabilities
        // For now, accept any non-empty model string
        !model.is_empty()
    }

    /// Get the current pipeline stage
    pub fn pipeline_stage(&self) -> usize {
        self.pipeline_stage.load(std::sync::atomic::Ordering::Relaxed)
    }

    /// Check if first token has been forwarded (commit boundary)
    pub fn is_first_token_forwarded(&self) -> bool {
        self.first_token_forwarded.load(std::sync::atomic::Ordering::SeqCst)
    }

    /// Send an SSE delta event with new content
    pub async fn send_delta(&self, content: &str) -> Result<(), ()> {
        if self.is_first_token_forwarded() {
            // After first token, no retry/failover - just send the delta
            if let Some(sender) = &self.sse_sender {
                let event = SseEvent::Delta {
                    data: format!("{{\"id\":\"chatcm-...\",\"object\":\"chat.completion.chunk\",\"created\":{},\"model\":\"gpt-3.5-turbo\",\"choices\":[{\"index\":0,\"delta\":{{\"role\":\"assistant\",\"content\":\"{}\"}},\"finish_reason\":null}}]}}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(), content),
                };
                sender.send(event.clone()).await.map_err(|_| ())?;
            }
            Ok(())
        } else {
            // Before first token, may not send depending on pipeline
            Ok(())
        }
    }

    /// Send the done sentinel
    pub async fn send_done(&self) {
        if let Some(sender) = &self.sse_sender {
            let event = SseEvent::Done;
            sender.send(event).await.ok();
        }
    }

    /// Send an error event mid-stream, followed by done sentinel
    /// Per AD-3: after first token, error event + done sentinel only, no retry/failover
    pub async fn send_error(&self, code: &str, message: &str) {
        if self.is_first_token_forwarded() {
            // After first token: emit one error event + done sentinel, no retry
            if let Some(sender) = &self.sse_sender {
                let error_event = SseEvent::Error {
                    code: code.to_string(),
                    message: message.to_string(),
                };
                sender.send(error_event.clone()).await.ok();
                // Send done sentinel after error
                let done_event = SseEvent::Done;
                sender.send(done_event).await.ok();
            }
        } else {
            // Before first token: could failover, but per AD-3 we terminate
            if let Some(sender) = &self.sse_sender {
                let error_event = SseEvent::Error {
                    code: code.to_string(),
                    message: message.to_string(),
                };
                sender.send(error_event).await.ok();
                let done_event = SseEvent::Done;
                sender.send(done_event).await.ok();
            }
        }
    }
}

impl Default for ResilienceLoop {
    fn default() -> Self {
        Self::new()
    }
}

/// Create a new ResilienceLoop instance
pub fn resilience_loop() -> ResilienceLoop {
    ResilienceLoop::new()
}

/// Convert SseEvent to SSE formatted string
fn sse_event_to_string(event: &SseEvent) -> String {
    match event {
        SseEvent::Delta { data } => format!("data: {}\n\n", data),
        SseEvent::Done => format!("data: [DONE]\n\n"),
        SseEvent::Error { code, message } => {
            let error_json = serde_json::json!({
                "error": {
                    "code": code,
                    "message": message,
                    "type": "invalid_request_error",
                    "param": None
                }
            });
            format!("data: {}\n\n", serde_json::to_string(&error_json).unwrap())
        }
    }
}

/// Convert ResilienceLoop's SSE event stream into an axum SSE response
impl ResilienceLoop {
    /// Create an SSE stream from this resilience loop's event channel
    pub fn sse_events(&self) -> impl Stream<Item = String> + Clone {
        // We need a channel to send events from the outside
        // This is a simplified version - in full implementation,
        // the sender would be shared with the handler
        use std::sync::atomic::AtomicBool;
        use std::time::Duration;

        // Return a stream that yields SSE-formatted strings
        // In a full implementation, this would use mpsc channels
        let (tx, mut rx) = tokio::sync::mpsc::channel(128);

        // Store sender for later use
        let self_clone = self.clone();
        // Note: This is simplified - full implementation would properly
        // share the sender between the handler and this stream
        drop(tx); // We'll use a different approach

        // Return a static stream for now
        Box::pin(async_stream::stream! {
            // Yield delta events as they come in
            // This is a placeholder - full implementation uses proper channels
        })
    }
}