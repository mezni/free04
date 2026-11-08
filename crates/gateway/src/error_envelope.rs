use axum::http::StatusCode;
use serde::Serialize;

/// AD-11 Gateway Error Envelope
///
/// All errors must use this envelope format for stable SDK/UI behavior
/// and to prevent secret leakage (AD-4).
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum GatewayError {
    /// 400 Bad Request - validation or duplicate detection
    #[error("duplicate_spec")]
    DuplicateSpec,

    /// 400 Bad Request - general validation failure
    #[error("invalid_request")]
    InvalidRequest(String),

    /// 401 Unauthorized - missing/invalid credentials
    #[error("unauthorized")]
    Unauthorized,

    /// 403 Forbidden - principal lacks scope
    #[error("forbidden")]
    Forbidden,

    /// 429 Rate limited
    #[error("rate_limited")]
    RateLimited,

    /// 502 Upstream error
    #[error("upstream_error")]
    UpstreamError,

    /// 503 Unavailable
    #[error("unavailable")]
    Unavailable,
}

/// AD-11 Error Response (serialized format)
#[derive(serde::Serialize)]
pub struct ErrorResponse {
    /// Machine-readable error code
    pub code: String,
    /// Human-readable message
    pub message: String,
    /// Optional parameter that caused the error (null in most cases)
    pub param: Option<String>,
    /// Type classification
    pub r#type: String,
}

impl GatewayError {
    /// Convert to (StatusCode, ErrorResponse) for Axum response
    pub fn into_response(self) -> (StatusCode, axum::Json<ErrorResponse>) {
        let (status, code, message) = match self {
            GatewayError::DuplicateSpec => {
                (StatusCode::BAD_REQUEST, "duplicate_spec", "A request with this specification ID already exists")
            }
            GatewayError::InvalidRequest(ref msg) => {
                (StatusCode::BAD_REQUEST, "invalid_request", msg.as_str())
            }
            GatewayError::Unauthorized => (StatusCode::UNAUTHORIZED, "unauthorized", "Missing or invalid credentials"),
            GatewayError::Forbidden => (StatusCode::FORBIDDEN, "forbidden", "Principal lacks scope"),
            GatewayError::RateLimited => (StatusCode::TOO_MANY_REQUESTS, "rate_limited", "Gateway or team limit exceeded"),
            GatewayError::UpstreamError => (StatusCode::BAD_GATEWAY, "upstream_error", "Provider failed after all attempts"),
            GatewayError::Unavailable => (StatusCode::SERVICE_UNAVAILABLE, "unavailable", "No healthy target or gateway dependency down"),
        };

        let response = ErrorResponse {
            code: code.to_string(),
            message: message.to_string(),
            param: None,
            r#type: "invalid_request_error".to_string(),
        };

        (status, axum::Json(response))
    }
}