use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
};
use redis::aio::MultiplexedConnection;
use serde::Deserialize;
use std::sync::Arc;
use tracing::instrument;

/// Duplicate detection middleware for the Axum pipeline.
///
/// This stage checks if a request's specification ID has been seen recently.
/// If a duplicate is detected, it returns a 400 error with the AD-11 envelope.
///
/// Must be placed between the rate limit/quota stage and the route stage
/// in the fixed pipeline (AD-2 compliance).
#[instrument(skip(ctx, next))]
pub async fn duplicate_detection_middleware(
    ctx: Arc<DuplicateDetectionContext>,
    req: Request<Body>,
    next: Next<Body>,
) -> Result<(StatusCode, Body), (StatusCode, Body)> {
    // Extract spec_id from request extensions or query params
    // For now, we look for it in a simple way
    let spec_id = extract_spec_id(&req);

    if let Some(spec_id) = spec_id {
        // Check if this spec ID has been seen recently
        if ctx.is_duplicate(&spec_id).await.unwrap_or(false) {
            // Duplicate detected - return 400 with AD-11 error
            let error_body = serde_json::json!({
                "error": {
                    "message": "A request with this specification ID already exists",
                    "type": "invalid_request_error",
                    "code": "duplicate_spec"
                }
            });
            let body = Body::from(serde_json::to_string(&error_body).unwrap());
            return Ok((StatusCode::BAD_REQUEST, body));
        }

        // Mark this spec ID as seen with a 5-minute TTL
        ctx.mark_seen(&spec_id).await.unwrap_or_else(|_| {});
    }

    // Continue down the pipeline
    Ok(next.run(req).await)
}

/// Extract spec_id from the request.
/// In a real implementation, this would parse the JSON body or query parameters.
fn extract_spec_id(_req: &Request<Body>) -> Option<String> {
    // Placeholder: in production, parse from request body
    None
}

/// Context for duplicate detection with Redis connection
pub struct DuplicateDetectionContext {
    connection: Arc<Mutex<MultiplexedConnection>>,
}

impl DuplicateDetectionContext {
    /// Create a new duplicate detection context
    pub fn new(connection: MultiplexedConnection) -> Self {
        Self {
            connection: Arc::new(Mutex::new(connection)),
        }
    }

    /// Check if a spec ID is a duplicate (SISMEMBER)
    #[instrument(skip(self))]
    pub async fn is_duplicate(&self, spec_id: &str) -> Result<bool, redis::RedisError> {
        let mut conn = self.connection.lock().await;
        let result: redis::RedisResult<i32> = redis::cmd("SISMEMBER")
            .arg("active_spec_ids")
            .arg(spec_id)
            .query(&mut *conn)
            .await;
        match result {
            Ok(n) => Ok(n == 1),
            Err(e) => {
                tracing::warn!("Redis SISMEMBER error: {}", e);
                Ok(false) // Allow request through on error
            }
        }
    }

    /// Mark a spec ID as seen (SADD) and set TTL (EXPIRE)
    #[instrument(skip(self))]
    pub async fn mark_seen(&self, spec_id: &str) -> Result<(), redis::RedisError> {
        let mut conn = self.connection.lock().await;

        // Add to the set
        let _: redis::RedisResult<usize> = redis::cmd("SADD")
            .arg("active_spec_ids")
            .arg(spec_id)
            .query(&mut *conn)
            .await?;

        // Set TTL to 5 minutes (300 seconds)
        let _: redis::RedisResult<()> = redis::cmd("EXPIRE")
            .arg("active_spec_ids")
            .arg(300)
            .query(&mut *conn)
            .await?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use http::Request;

    #[test]
    fn test_duplicate_detection_middleware_extracts_none() {
        let req = Request::get("/v1/chat/completions")
            .body(Body::empty())
            .unwrap();
        let spec_id = extract_spec_id(&req);
        assert!(spec_id.is_none());
    }

    #[test]
    fn test_duplicate_detection_context_creation() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let client = rt.block_on(async {
            redis::aio::Client::open("redis://localhost:6379")
                .await
                .unwrap()
                .get_async_connection()
                .await
                .unwrap()
        });
        let ctx = DuplicateDetectionContext::new(client);
        let result = ctx.is_duplicate("test").await;
        assert!(result.unwrap_or(true));
    }
}