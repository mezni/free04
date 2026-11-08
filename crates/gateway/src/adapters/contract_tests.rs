use crate::adapters::{ollama_adapter::OllamaAdapter, vllm_adapter::VllmAdapter, openai_adapter::OpenAiAdapter};
use crate::error_envelope::CanonicalResponse;
use crate::models::{capability_descriptor::CapabilityDescriptor, canonical_request::CanonicalRequest, wire_format::WireFormat};
use crate::ports::adapter_port::AdapterPort;

#[test]
fn test_ollama_declare_capabilities() {
    let adapter = OllamaAdapter;
    let capabilities = adapter.declare_capabilities();
    assert_eq!(capabilities.tools, false);
    assert_eq!(capabilities.json_mode, true);
    assert_eq!(capabilities.vision, false);
    assert_eq!(capabilities.context_window, 4096);
    assert_eq!(capabilities.streaming, true);
}

#[test]
fn test_vllm_declare_capabilities() {
    let adapter = VllmAdapter;
    let capabilities = adapter.declare_capabilities();
    assert_eq!(capabilities.tools, true);
    assert_eq!(capabilities.json_mode, true);
    assert_eq!(capabilities.vision, true);
    assert_eq!(capabilities.context_window, 8192);
    assert_eq!(capabilities.streaming, true);
}

#[test]
fn test_openai_declare_capabilities() {
    let adapter = OpenAiAdapter;
    let capabilities = adapter.declare_capabilities();
    assert_eq!(capabilities.tools, true);
    assert_eq!(capabilities.json_mode, true);
    assert_eq!(capabilities.vision, true);
    assert_eq!(capabilities.context_window, 16385);
    assert_eq!(capabilities.streaming, true);
}

#[test]
fn test_ollama_convert_request() {
    let adapter = OllamaAdapter;
    let req = CanonicalRequest {
        model_alias: "llama2".to_string(),
        messages: vec![
            crate::models::chat_message::ChatMessage {
                role: "user".to_string(),
                content: "Hello".to_string(),
            },
        ],
        stream: false,
        tools: None,
        temperature: None,
        max_tokens: None,
        top_p: None,
        stop: None,
        metadata: None,
    };

    let wire = adapter.convert_request(&req).await;
    assert!(wire.is_ok());
    let wire_format = wire.unwrap();
    assert_eq!(wire_format.adapter_name, "ollama");
    assert!(!wire_format.raw_request.is_empty());
    assert_eq!(wire_format.mime_type, "application/json");
}

#[test]
fn test_vllm_convert_request() {
    let adapter = VllmAdapter;
    let req = CanonicalRequest {
        model_alias: "gpt-3.5-turbo".to_string(),
        messages: vec![
            crate::models::chat_message::ChatMessage {
                role: "user".to_string(),
                content: "Hello".to_string(),
            },
        ],
        stream: false,
        tools: None,
        temperature: None,
        max_tokens: None,
        top_p: None,
        stop: None,
        metadata: None,
    };

    let wire = adapter.convert_request(&req).await;
    assert!(wire.is_ok());
    let wire_format = wire.unwrap();
    assert_eq!(wire_format.adapter_name, "vllm");
    assert!(!wire_format.raw_request.is_empty());
    assert_eq!(wire_format.mime_type, "application/json");
}

#[test]
fn test_openai_convert_request() {
    let adapter = OpenAiAdapter;
    let req = CanonicalRequest {
        model_alias: "gpt-3.5-turbo".to_string(),
        messages: vec![
            crate::models::chat_message::ChatMessage {
                role: "user".to_string(),
                content: "Hello".to_string(),
            },
        ],
        stream: false,
        tools: None,
        temperature: None,
        max_tokens: None,
        top_p: None,
        stop: None,
        metadata: None,
    };

    let wire = adapter.convert_request(&req).await;
    assert!(wire.is_ok());
    let wire_format = wire.unwrap();
    assert_eq!(wire_format.adapter_name, "openai");
    assert!(!wire_format.raw_request.is_empty());
    assert_eq!(wire_format.mime_type, "application/json");
}

#[test]
fn test_ollama_convert_response() {
    let adapter = OllamaAdapter;
    let wire_format = WireFormat {
        adapter_name: "ollama".to_string(),
        raw_request: vec![].into(),
        raw_response: r#"{"response":"Hello back","done":true}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    };

    let response = adapter.convert_response(&wire_format).await;
    assert!(response.is_ok());
    let canonical = response.unwrap();
    assert_eq!(canonical.model, Some("gpt-3.5-turbo".to_string()));
    assert!(canonical.choices.len() > 0);
}

#[test]
fn test_vllm_convert_response() {
    let adapter = VllmAdapter;
    let wire_format = WireFormat {
        adapter_name: "vllm".to_string(),
        raw_request: vec![].into(),
        raw_response: r#"{"text":"Hello back","token_count":12}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    };

    let response = adapter.convert_response(&wire_format).await;
    assert!(response.is_ok());
    let canonical = response.unwrap();
    assert!(canonical.choices.len() > 0);
}

#[test]
fn test_openai_convert_response() {
    let adapter = OpenAiAdapter;
    let wire_format = WireFormat {
        adapter_name: "openai".to_string(),
        raw_request: vec![].into(),
        raw_response: r#"{"id":"chatcmpl-123","object":"chat.completion","created":1234567890,"model":"gpt-3.5-turbo","choices":[{"index":0,"message":{"role":"assistant","content":"Hello"},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}}"#.as_bytes().to_vec(),
        mime_type: "application/json".to_string(),
    };

    let response = adapter.convert_response(&wire_format).await;
    assert!(response.is_ok());
    let canonical = response.unwrap();
    assert_eq!(canonical.model, Some("gpt-3.5-turbo".to_string()));
    assert_eq!(canonical.object, Some("chat.completion".to_string()));
}