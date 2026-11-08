use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CanonicalRequest {
    pub model_alias: String,
    pub messages: Vec<crate::models::chat_message::ChatMessage>,
    pub stream: bool,
    pub tools: Option<Vec<crate::models::tool_definition::ToolDefinition>>,
    pub temperature: Option<f64>,
    pub max_tokens: Option<u32>,
    pub top_p: Option<f64>,
    pub stop: Option<Vec<String>>,
    pub metadata: Option<std::collections::HashMap<String, String>>,
}