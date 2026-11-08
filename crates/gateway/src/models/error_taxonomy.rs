use thiserror::Error;

#[derive(Error, Debug)]
pub enum ErrorTaxonomyError {
    #[error("Unknown error code: {0}")]
    UnknownCode(String),
    #[error("Failed to map error: {0}")]
    MappingFailure(String),
}