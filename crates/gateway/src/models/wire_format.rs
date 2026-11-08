use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WireFormat {
    pub adapter_name: String,
    pub raw_request: bytes::Bytes,
    pub raw_response: bytes::Bytes,
    pub mime_type: String,
}