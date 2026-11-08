use crate::models::error_taxonomy::ErrorTaxonomy;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum OpenAiErrorMappingError {
    #[error("Unknown error type: {0}")]
    UnknownError(String),
    #[error("Failed to map error: {0}")]
    MappingFailure(String),
}

impl OpenAiErrorMappingError {
    pub fn map_timeout() -> ErrorTaxonomy {
        ErrorTaxonomy {
            gateway_error_code: "service_unavailable".to_string(),
            provider_error_code: "timeout".to_string(),
            category: "server_error".to_string(),
            retryable: true,
            max_retry_attempts: 2,
            description: "Request timeout - service unavailable".to_string(),
        }
    }

    pub fn map_validation() -> ErrorTaxonomy {
        ErrorTaxonomy {
            gateway_error_code: "invalid_request".to_string(),
            provider_error_code: "validation".to_string(),
            category: "validation".to_string(),
            retryable: false,
            max_retry_attempts: 0,
            description: "Invalid request parameter".to_string(),
        }
    }

    pub fn map_connection_error() -> ErrorTaxonomy {
        ErrorTaxonomy {
            gateway_error_code: "service_unavailable".to_string(),
            provider_error_code: "connection".to_string(),
            category: "connection_error".to_string(),
            retryable: true,
            max_retry_attempts: 2,
            description: "Connection error - service unavailable".to_string(),
        }
    }

    pub fn map_rate_limit(retry_after: Option<u32>) -> ErrorTaxonomy {
        ErrorTaxonomy {
            gateway_error_code: "rate_limit_error".to_string(),
            provider_error_code: "429".to_string(),
            category: "rate_limit".to_string(),
            retryable: true,
            max_retry_attempts: 2,
            description: format!("Rate limit error{}", retry_after.map(|ra| format!(" - Retry-After: {}", ra)).unwrap_or_default()),
        }
    }
}