/// DuplicateEvent - Usage event recorded when a duplicate specification is detected
///
/// Per AD-9: Each usage event is immutable once written
/// Per AD-10: Telemetry carries request id, team, alias, provider; no prompt bodies
#[derive(Debug, Clone)]
pub struct DuplicateEvent {
    /// The original request identifier
    pub request_id: String,
    /// The attempt number (1-based)
    pub attempt_id: u32,
    /// The duplicate specification ID
    pub spec_id: String,
    /// The principal/team who sent the duplicate
    pub principal: String,
    /// The outcome of the duplicate detection
    pub outcome: DuplicateOutcome,
    /// Tokens consumed upstream before duplicate detection
    pub tokens_upstream: u32,
    /// Cost snapshot from the price table version active at event time
    pub cost_micros: i64,
    /// RFC 3339 UTC timestamp
    pub timestamp: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum DuplicateOutcome {
    /// The request was rejected as a duplicate
    Duplicate,
    /// The request was processed normally (not a duplicate)
    Normal,
}

impl DuplicateEvent {
    /// Create a new DuplicateEvent
    pub fn new(
        request_id: String,
        attempt_id: u32,
        spec_id: String,
        principal: String,
        outcome: DuplicateOutcome,
        tokens_upstream: u32,
        cost_micros: i64,
        timestamp: String,
    ) -> Self {
        Self {
            request_id,
            attempt_id,
            spec_id,
            principal,
            outcome,
            tokens_upstream,
            cost_micros,
            timestamp,
        }
    }

    /// Convert to JSON string (manual serialization)
    pub fn to_json(&self) -> String {
        format!(
            r#"{{\"request_id\":\"{}\",\"attempt_id\":{},\"spec_id\":\"{}\",\"principal\":\"{}\",\"outcome\":\"{}\",\"tokens_upstream\":{},\"cost_micros\":{},\"timestamp\":\"{}\"}}"#,
            self.request_id,
            self.attempt_id,
            self.spec_id,
            self.principal,
            match self.outcome {
                DuplicateOutcome::Duplicate => "duplicate",
                DuplicateOutcome::Normal => "normal",
            },
            self.tokens_upstream,
            self.cost_micros,
            self.timestamp
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_duplicate_event_creation() {
        let event = DuplicateEvent::new(
            "req_123".to_string(),
            1,
            "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b".to_string(),
            "team_alpha".to_string(),
            DuplicateOutcome::Duplicate,
            0,
            1500,
            "2026-01-01T00:00:00Z".to_string(),
        );

        let json = event.to_json();
        assert!(json.contains("req_123"));
        assert!(json.contains("duplicate"));
        assert!(json.contains("69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"));
    }

    #[test]
    fn test_duplicate_outcome_equality() {
        let dup = DuplicateOutcome::Duplicate;
        let normal = DuplicateOutcome::Normal;
        assert!(dup != normal);
    }
}
