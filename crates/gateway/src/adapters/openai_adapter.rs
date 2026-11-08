use crate::error_envelope::CanonicalResponse;
use crate::models::capability_descriptor::CapabilityDescriptor;
use crate::models::canonical_request::CanonicalRequest;
use crate::models::wire_format::WireFormat;
use crate::ports::adapter_port::AdapterPort;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum OpenAiAdapterError {
    #[error("Invalid model: {0}")]
    InvalidModel(String),
    #[error("Conversion failure: {0}")]
    ConversionFailure(String),
}

impl From<OpenAiAdapterError> for crate::ports::adapter_port::AdapterError {
    fn from(err: OpenAiAdapterError) -> Self {
        crate::ports::adapter_port::AdapterError::ConversionFailure(err.to_string())
    }
}

pub struct OpenAiAdapter;

impl AdapterPort for OpenAiAdapter {
    fn declare_capabilities(&self) -> CapabilityDescriptor {
        CapabilityDescriptor {
            tools: true,
            json_mode: true,
            vision: true,
            context_window: 16385,
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
            "temperature": canonical_request.temperature,
            "max_tokens": canonical_request.max_tokens,
            "top_p": canonical_request.top_p,
            "stop": canonical_request.stop,
        })).map_err(|e| OpenAiAdapterError::ConversionFailure(e.to_string()))?;

        Ok(WireFormat {
            adapter_name: "openai".to_string(),
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
            .map_err(|_| OpenAiAdapterError::ConversionFailure("Invalid response format".to_string()))?;

        let openai_response: serde_json::Value = serde_json::from_str(&raw_str)
            .map_err(|e| OpenAiAdapterError::ConversionFailure(e.to_string()))?;

        let choices = openai_response.get("choices").and_then(|c| c.as_array()).cloned().unwrap_or_default();

        let usage = openai_response.get("usage").and_then(|u| {
            Some(crate::error_envelope::Usage {
                prompt_tokens: u.get("prompt_tokens").and_then(|t| t.as_u64()).unwrap_or(0) as u64,
                completion_tokens: u.get("completion_tokens").and_then(|t| t.as_u64()).unwrap_or(0) as u64,
                total_tokens: u.get("total_tokens").and_then(|t| t.as_u64()).unwrap_or(0) as u64,
            })
        });

        Ok(CanonicalResponse {
            id: openai_response.get("id").and_then(|i| i.as_str()).map(|s| s.to_string()),
            object: openai_response.get("object").and_then(|o| o.as_str()).map(|s| s.to_string()),
            created: openai_response.get("created").and_then(|c| c.as_u64()).unwrap_or(0),
            model: openai_response.get("model").and_then(|m| m.as_str()).map(|s| s.to_string()),
            choices,
            usage,
            error: openai_response.get("error").cloned().map(|e| serde_json::Value::from(e)),
        })
    }
}