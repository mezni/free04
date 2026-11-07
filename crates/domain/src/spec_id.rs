use std::fmt;

use uuid::Uuid;

/// SpecID is a unique identifier for a specification entry
///
/// Used for duplicate detection in the LLM gateway pipeline.
/// Stored in Redis SET with TTL for recent spec ID tracking.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct SpecId(Uuid);

impl SpecId {
    /// Create a new SpecId from a UUID
    pub fn from_uuid(uuid: Uuid) -> Self {
        Self(uuid)
    }

    /// Create a SpecId from a hex string
    ///
    /// # Returns
    ///
    /// Returns `InvalidFormat` if the string is not a valid UUID.
    pub fn from_hex(hex: &str) -> Result<Self, SpecIdError> {
        let uuid = Uuid::parse_str(hex).map_err(|_| SpecIdError::InvalidFormat)?;
        Ok(Self(uuid))
    }

    /// Get the underlying UUID
    pub fn get(&self) -> &Uuid {
        &self.0
    }

    /// Convert to hex string
    pub fn to_hex(&self) -> String {
        self.0.to_string()
    }
}

impl From<SpecId> for Uuid {
    fn from(s: SpecId) -> Self {
        s.0
    }
}

impl TryFrom<Uuid> for SpecId {
    type Error = SpecIdError;

    fn try_from(u: Uuid) -> Result<Self, Self::Error> {
        Ok(SpecId(u))
    }
}

/// Error type for SpecId operations
#[derive(Debug, Clone, PartialEq)]
pub enum SpecIdError {
    /// Invalid UUID format
    InvalidFormat,
}

impl std::error::Error for SpecIdError {}

impl fmt::Display for SpecIdError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SpecIdError::InvalidFormat => write!(f, "Invalid UUID format"),
        }
    }
}

impl fmt::Display for SpecId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_specid_from_hex() {
        let spec_id = SpecId::from_hex("69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b").unwrap();
        let hex = spec_id.to_hex();
        assert_eq!(hex, "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b");
    }

    #[test]
    fn test_specid_invalid_format() {
        let result = SpecId::from_hex("not-a-uuid");
        assert!(matches!(result, Err(SpecIdError::InvalidFormat)));
    }

    #[test]
    fn test_specid_from_uuid() {
        let uuid = Uuid::nil();
        let spec_id = SpecId::from_uuid(uuid);
        assert_eq!(spec_id.to_hex(), uuid.to_string());
    }

    #[test]
    fn test_specid_display() {
        let spec_id = SpecId::from_hex("69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b").unwrap();
        let display = format!("{}", spec_id);
        assert!(!display.is_empty());
    }
}
