use crate::error_envelope::CanonicalResponse;
use crate::models::capability_descriptor::CapabilityDescriptor;
use crate::models::canonical_request::CanonicalRequest;
use crate::models::wire_format::WireFormat;
use crate::ports::adapter_port::AdapterPort;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum OllamaAdapterError {
    #[error("Invalid model: {0}")]
    InvalidModel(String),
    #[error("Conversion failure: {0}")]
    ConversionFailure(String),
}

impl From<OllamaAdapterError> for crate::ports::adapter_port::AdapterError {
    fn from(err: OllamaAdapterError) -> Self {
        crate::ports::adapter_port::AdapterError::ConversionFailure(err.to_string())
    }
}

pub struct OllamaAdapter;

impl AdapterPort for OllamaAdapter {
    fn declare_capabilities(&self) -> CapabilityDescriptor {
        CapabilityDescriptor {
            tools: false,
            json_mode: true,
            vision: false,
            context_window: 4096,
            streaming: true,
        }
    }

    async fn convert_request(
        &self,
        canonical_request: &CanonicalRequest,
    ) -> Result<WireFormat, crate::ports::adapter_port::AdapterError> {
        let raw = serde_json::to_string(&serde_json::json!({
            "model": canonical_request.model_alias,
            "messages": canonical_request.messages.iter().map(|m| {
                serde_json::json!({
                    "role": m.role,
                    "content": m.content
                })
            }).collect::<Vec<_>>(),
            "stream": canonical_request.stream,
        })).map_err(|e| OllamaAdapterError::ConversionFailure(e.to_string()))?;

        Ok(WireFormat {
            adapter_name: "ollama".to_string(),
            raw_request: raw.into_bytes(),
            raw_response: vec![].into(),
            mime_type: "application/json".to_string(),
        })
    }

    async fn convert_response(
        &self,
        wire_format: &WireFormat,
    ) -> Result<CanonicalResponse, crate::ports::adapter_port::AdapterError> {
        let raw_str = String::from_utf8(&wire_format.raw_response)
            .map_err(|_| OllamaAdapterError::ConversionFailure("Invalid response format".to_string()))?;

        let ollama_response: serde_json::Value = serde_json::from_str(&raw_str)
            .map_err(|e| OllamaAdapterError::ConversionFailure(e.to_string()))?;

        let choice = ollama_response.get("response")
            .and_then(|r| r.as_str())
            .map(|c| serde_json::json!({
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": c
                },
                "finish_reason": "stop"
            }))
            .unwrap_or(serde_json::json!({
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": ""
                },
                "finish_reason": "stop"
            }));

        let usage = if ollama_response.get("done").and_then(|d| d.as_bool()).unwrap_or(false) {
            Some(crate::error_envelope::Usage {
                prompt_tokens: 0,
                completion_tokens: 0,
                total_tokens: 0,
            })
        } else {
            None
        };

        Ok(CanonicalResponse {
            id: Some("chatcmpl-mock".to_string()),
            object: Some("chat.completion".to_string()),
            created: 0,
            model: Some(canonical_request.model_alias.clone()),
            choices: vec![choice],
            usage,
            error: None,
        })
    }
}