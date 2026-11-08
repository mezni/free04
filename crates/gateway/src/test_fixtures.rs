use crate::models::capability_descriptor::CapabilityDescriptor;
use crate::models::canonical_request::CanonicalRequest;
use crate::models::chat_message::ChatMessage;
use crate::models::tool_definition::ToolDefinition;
use crate::models::wire_format::WireFormat;
use serde_json::json;

/// Canonical request fixture for testing adapter conversions
pub fn canonical_request_fixture() -> CanonicalRequest {
    CanonicalRequest {
        model_alias: "gpt-3.5-turbo".to_string(),
        messages: vec![
            ChatMessage {
                role: "user".to_string(),
                content: "Hello, how are you?".to_string(),
            },
            ChatMessage {
                role: "assistant".to_string(),
                content: "I'm doing well, thank you!".to_string(),
            },
        ],
        stream: false,
        tools: None,
        temperature: Some(0.7),
        max_tokens: Some(100),
        top_p: None,
        stop: None,
        metadata: Some(std::collections::HashMap::from([
            ("request_id".to_string(), "test-12345".to_string()),
        ])),
    }
}

/// Ollama wire format fixture
pub fn ollama_wire_format_fixture() -> WireFormat {
    WireFormat {
        adapter_name: "ollama".to_string(),
        raw_request: bytes::From::from(r#"{"model":"llama2","messages":[{"role":"user","content":"Hello"}],"stream":false}"#.as_bytes().to_vec(),
        raw_response: bytes::From::from(r#"{"model":"llama2","response":"I'm doing well","done":true}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    }
}

/// vLLM wire format fixture
pub fn vllm_wire_format_fixture() -> WireFormat {
    WireFormat {
        adapter_name: "vllm".to_string(),
        raw_request: bytes::From::from(r#"{"prompt":"Hello","sampling_params":{"temperature":0.7,"max_tokens":100}}"#.as_bytes().to_vec(),
        raw_response: bytes::From::from(r#"{"text":"I'm doing well","token_count":12}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    }
}

/// OpenAI wire format fixture
pub fn openai_wire_format_fixture() -> WireFormat {
    WireFormat {
        adapter_name: "openai".to_string(),
        raw_request: bytes::From::from(r#"{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello"}],"stream":false}"#.as_bytes().to_vec(),
        raw_response: bytes::From::from(r#"{"id":"chatcmpl-123","object":"chat.completion","created":1234567890,"model":"gpt-3.5-turbo","choices":[{"index":0,"message":{"role":"assistant","content":"I'm doing well"},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    }
}

/// Capability descriptor fixtures per adapter
pub fn ollama_capabilities() -> CapabilityDescriptor {
    CapabilityDescriptor {
        tools: false,
        json_mode: true,
        vision: false,
        context_window: 4096,
        streaming: true,
    }
}

pub fn vllm_capabilities() -> CapabilityDescriptor {
    CapabilityDescriptor {
        tools: true,
        json_mode: true,
        vision: true,
        context_window: 8192,
        streaming: true,
    }
}

pub fn openai_capabilities() -> CapabilityDescriptor {
    CapabilityDescriptor {
        tools: true,
        json_mode: true,
        vision: true,
        context_window: 16385,
        streaming: true,
    }
}

/// Error taxonomy fixtures
pub fn service_unavailable_error() -> crate::models::error_taxonomy::ErrorTaxonomy {
    crate::models::error_taxonomy::ErrorTaxonomy {
        gateway_error_code: "service_unavailable".to_string(),
        provider_error_code: "500".to_string(),
        category: "server_error".to_string(),
        retryable: true,
        max_retry_attempts: 2,
        description: "Service temporarily unavailable".to_string(),
    }
}

pub fn invalid_request_error() -> crate::models::error_taxonomy::ErrorTaxonomy {
    crate::models::error_taxonomy::ErrorTaxonomy {
        gateway_error_code: "invalid_request".to_string(),
        provider_error_code: "400".to_string(),
        category: "validation".to_string(),
        retryable: false,
        max_retry_attempts: 0,
        description: "Invalid request parameter".to_string(),
    }
}