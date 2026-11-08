/// Capability requirement for routing decisions.
///
/// Defines which capabilities must be present for an adapter to serve a request.
#[derive(Clone, Debug, PartialEq)]
pub struct CapabilityRequirement {
    /// Whether tool use/function calling is required
    pub tools: bool,
    /// Whether JSON mode response formatting is required
    pub json_mode: bool,
    /// Whether multimodal/image inputs are required
    pub vision: bool,
    /// Minimum context window in tokens required
    pub context_window: u32,
    /// Whether streaming is required
    pub streaming: bool,
}

/// Check if an adapter's capabilities meet the requirements.
///
/// Returns `true` if the adapter has all the required capabilities.
pub fn has_required_capabilities(
    adapter_tools: bool,
    adapter_json_mode: bool,
    adapter_vision: bool,
    adapter_context_window: u32,
    adapter_streaming: bool,
    req: &CapabilityRequirement,
) -> bool {
    adapter_tools >= req.tools
        && adapter_json_mode >= req.json_mode
        && adapter_vision >= req.vision
        && adapter_context_window >= req.context_window
        && adapter_streaming >= req.streaming
}

/// Filter adapters by capability to serve a request.
///
/// Adapters that lack the required capabilities are excluded from the candidate list.
/// Adapters are represented as (name, tools, json_mode, vision, context_window, streaming).
pub fn filter_adapters_by_capability(
    adapters: &[(String, bool, bool, bool, u32, bool)],
    req: &CapabilityRequirement,
) -> Vec<(String, bool, bool, bool, u32, bool)> {
    adapters
        .iter()
        .filter(|(_, tools, json_mode, vision, ctx_win, streaming)| {
            has_required_capabilities(*tools, *json_mode, *vision, *ctx_win, *streaming, req)
        })
        .cloned()
        .collect()
}

/// Convert a CapabilityDescriptor to a CapabilityRequirement.
pub fn from_caps_descriptor(
    tools: bool,
    json_mode: bool,
    vision: bool,
    context_window: u32,
    streaming: bool,
) -> CapabilityRequirement {
    CapabilityRequirement {
        tools,
        json_mode,
        vision,
        context_window,
        streaming,
    }
}