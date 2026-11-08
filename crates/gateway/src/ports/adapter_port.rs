use crate::models::capability_descriptor::CapabilityDescriptor;
use crate::models::canonical_request::CanonicalRequest;
use crate::models::wire_format::WireFormat;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AdapterError {
    #[error("Invalid request: {0}")]
    InvalidRequest(String),
    #[error("Context length exceeded: {0}")]
    ContextLengthExceeded(String),
    #[error("Rate limit error: {0}")]
    RateLimitError(String),
    #[error("Internal server error: {0}")]
    InternalServerError(String),
    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),
    #[error("Conversion failure: {0}")]
    ConversionFailure(String),
}

impl From<AdapterError> for axum::http::StatusCode {
    fn from(err: AdapterError) -> Self {
        match err {
            AdapterError::InvalidRequest(_) => axum::http::StatusCode::BAD_REQUEST,
            AdapterError::ContextLengthExceeded(_) => axum::http::StatusCode::BAD_REQUEST,
            AdapterError::RateLimitError(_) => axum::http::StatusCode::TOO_MANY_REQUESTS,
            AdapterError::InternalServerError(_) => axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            AdapterError::ServiceUnavailable(_) => axum::http::StatusCode::SERVICE_UNAVAILABLE,
            AdapterError::ConversionFailure(_) => axum::http::StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}

#[async_trait::async_trait]
pub trait AdapterPort: Send + Sync + 'static {
    fn declare_capabilities(&self) -> CapabilityDescriptor;

    async fn convert_request(
        &self,
        canonical_request: &CanonicalRequest,
    ) -> Result<WireFormat, AdapterError>;

    async fn convert_response(
        &self,
        wire_format: &WireFormat,
    ) -> Result<crate::error_envelope::CanonicalResponse, AdapterError>;
}