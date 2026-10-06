import os
from typing import Optional

class Settings:
    """Configuration loaded from environment variables."""

    def __init__(self):
        # Corpus directory
        self.document_dir = os.getenv("DOCUMENT_DIR", "data/documents")

        # Chunking parameters
        chunk_size_str = os.getenv("CHUNK_SIZE", "500")
        try:
            self.chunk_size = int(chunk_size_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid CHUNK_SIZE: {chunk_size_str}")

        overlap_str = os.getenv("CHUNK_OVERLAP", "50")
        try:
            self.chunk_overlap = int(overlap_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid CHUNK_OVERLAP: {overlap_str}")

        # Retrieval parameters
        top_k_str = os.getenv("TOP_K", "4")
        try:
            self.top_k = int(top_k_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid TOP_K: {top_k_str}")

        # Embedding
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "local-sentence-transformers")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        # LLM
        self.llm_base_url = os.getenv("LLM_BASE_URL")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL")
        self.llm_max_tokens_str = os.getenv("LLM_MAX_TOKENS", "512")
        try:
            self.llm_max_tokens = int(self.llm_max_tokens_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid LLM_MAX_TOKENS: {self.llm_max_tokens_str}")
        self.llm_temperature_str = os.getenv("LLM_TEMPERATURE", "0.0")
        try:
            self.llm_temperature = float(self.llm_temperature_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid LLM_TEMPERATURE: {self.llm_temperature_str}")

        # Validate required variables
        self._validate()

    def _validate(self):
        """Validate required settings and fail fast with variable name."""
        missing = []
        if not self.llm_base_url:
            missing.append("LLM_BASE_URL")
        if not self.llm_model:
            missing.append("LLM_MODEL")

        if missing:
            raise ValueError(f"Missing required environment variable(s): {', '.join(missing)}")

        # Validation rules
        if self.chunk_size <= 0:
            raise ValueError(f"CHUNK_SIZE must be > 0, got {self.chunk_size}")
        if self.chunk_overlap < 0:
            raise ValueError(f"CHUNK_OVERLAP must be >= 0, got {self.chunk_overlap}")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"CHUNK_OVERLAP must be < CHUNK_SIZE ({self.chunk_size}), got {self.chunk_overlap}")
        if self.top_k < 1:
            raise ValueError(f"TOP_K must be >= 1, got {self.top_k}")
        if not (0.0 <= self.llm_temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be in [0., 2.], got {self.llm_temperature}")
        if self.llm_max_tokens < 1:
            raise ValueError(f"LLM_MAX_TOKENS must be >= 1, got {self.llm_max_tokens}")

    @property
    def required_vars(self):
        """Return list of required variable names that are missing."""
        missing = []
        if not self.llm_base_url:
            missing.append("LLM_BASE_URL")
        if not self.llm_model:
            missing.append("LLM_MODEL")
        return missing


# Global instance for easy import
settings = Settings()