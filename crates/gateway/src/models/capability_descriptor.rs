#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct CapabilityDescriptor {
    pub tools: bool,
    pub json_mode: bool,
    pub vision: bool,
    pub context_window: u32,
    pub streaming: bool,
}