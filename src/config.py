"""Externalized configuration (constitution X, FR-011).

Loads config/settings.yaml as the base, with environment variables taking
precedence (contracts/config-contract.md). Level 0 env var names are
preserved so existing tests and workflows keep working unchanged.

Source priority (implemented via settings_customise_sources):
    init args  >  environment  >  .env dotenv  >  config/settings.yaml  >  defaults
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def load_yaml_dict(path: str | Path | None = None) -> dict[str, Any]:
    """Load the nested YAML settings mapping (empty dict if file absent)."""
    yaml_path = Path(path or "config/settings.yaml")
    if not yaml_path.exists():
        return {}
    with yaml_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Settings file must contain a YAML mapping: {yaml_path}")
    return data


def _yaml_defaults() -> dict[str, Any]:
    """Flatten config/settings.yaml into pydantic field values."""
    raw = load_yaml_dict()
    mapping: dict[str, Any] = {}

    sec = raw.get("corpus") or {}
    mapping.setdefault("document_dir", sec.get("document_dir", "data/documents"))

    sec = raw.get("chunking") or {}
    mapping.setdefault("chunk_size", sec.get("chunk_size", 500))
    mapping.setdefault("chunk_overlap", sec.get("chunk_overlap", 50))

    sec = raw.get("retrieval") or {}
    mapping.setdefault("top_k", sec.get("top_k", 4))
    mapping.setdefault("similarity_threshold", sec.get("similarity_threshold", 0.0))
    mapping.setdefault("vector_db_path", sec.get("vector_db_path", "data/chroma"))
    mapping.setdefault("collection", sec.get("collection", "telco_documents"))

    sec = raw.get("embedding") or {}
    mapping.setdefault("embedding_provider", sec.get("provider", "local-sentence-transformers"))
    mapping.setdefault("embedding_model", sec.get("model", "BAAI/bge-small-en-v1.5"))

    sec = raw.get("evaluation") or {}
    mapping.setdefault(
        "eval_dataset_path",
        sec.get("dataset_path", "data/evaluation/retrieval_questions.jsonl"),
    )
    mapping.setdefault("eval_k", sec.get("default_k", 5))
    mapping.setdefault(
        "grounded_dataset_path",
        sec.get("grounded_dataset_path", "data/evaluation/grounded_answers.jsonl"),
    )

    sec = raw.get("llm") or {}
    mapping.setdefault("llm_base_url", sec.get("base_url", "https://openrouter.ai/api/v1"))
    mapping.setdefault("llm_api_key", sec.get("api_key", ""))
    mapping.setdefault("llm_model", sec.get("model", ""))
    mapping.setdefault("llm_max_tokens", sec.get("max_tokens", 512))
    mapping.setdefault("llm_temperature", sec.get("temperature", 0.0))

    sec = raw.get("grounding") or {}
    mapping.setdefault("sufficiency_threshold", sec.get("sufficiency_threshold", 0.0))
    mapping.setdefault("min_evidence", sec.get("min_evidence", 1))
    mapping.setdefault("structured_output", sec.get("structured_output", True))

    # Empty YAML values must not clobber field defaults for optional fields.
    for key in ("llm_base_url", "llm_model", "llm_api_key"):
        if not mapping.get(key):
            mapping.pop(key, None)

    return mapping


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Settings source backed by config/settings.yaml (ranked below env)."""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        self._data = _yaml_defaults()

    def get_field_value(self, *args: Any, **kwargs: Any):
        # Not used: __call__ returns the whole mapping directly.
        raise NotImplementedError

    def __call__(self) -> dict[str, Any]:
        return self._data


class Settings(BaseSettings):
    """Telco RAG configuration (YAML base, env overrides)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    document_dir: str = "data/documents"

    chunk_size: int = 500
    chunk_overlap: int = 50

    top_k: int = 4
    similarity_threshold: float = 0.0
    vector_db_path: str = "data/chroma"
    collection: str = "telco_documents"

    embedding_provider: str = "local-sentence-transformers"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    eval_dataset_path: str = "data/evaluation/retrieval_questions.jsonl"
    eval_k: int = 5
    grounded_dataset_path: str = "data/evaluation/grounded_answers.jsonl"

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_max_tokens: int = 512
    llm_temperature: float = 0.0

    # Level 2 grounding (FR-011; research R3) — sufficiency decision signals.
    sufficiency_threshold: float = 0.0
    min_evidence: int = 1
    structured_output: bool = True

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @field_validator("chunk_size")
    @classmethod
    def _chunk_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"CHUNK_SIZE must be > 0, got {v}")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def _chunk_overlap(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"CHUNK_OVERLAP must be >= 0, got {v}")
        return v

    @field_validator("top_k")
    @classmethod
    def _top_k(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"TOP_K must be >= 1, got {v}")
        return v

    @field_validator("similarity_threshold")
    @classmethod
    def _threshold(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise ValueError(f"SIMILARITY_THRESHOLD must be in [-1, 1], got {v}")
        return v

    @field_validator("sufficiency_threshold")
    @classmethod
    def _sufficiency_threshold(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise ValueError(f"SUFFICIENCY_THRESHOLD must be in [-1, 1], got {v}")
        return v

    @field_validator("min_evidence")
    @classmethod
    def _min_evidence(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"MIN_EVIDENCE must be >= 0, got {v}")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def _temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError(f"LLM_TEMPERATURE must be in [0., 2.], got {v}")
        return v

    @field_validator("llm_max_tokens")
    @classmethod
    def _max_tokens(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"LLM_MAX_TOKENS must be >= 1, got {v}")
        return v

    @field_validator("llm_base_url")
    @classmethod
    def _base_url(cls, v: str) -> str:
        if not v:
            raise ValueError("Missing required setting: LLM_BASE_URL")
        return v

    @field_validator("llm_model")
    @classmethod
    def _model(cls, v: str) -> str:
        if not v:
            raise ValueError("Missing required setting: LLM_MODEL")
        return v

    @model_validator(mode="after")
    def _overlap_lt_size(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP must be < CHUNK_SIZE ({self.chunk_size}), got {self.chunk_overlap}"
            )
        return self


def build_settings() -> Settings:
    """Construct Settings with the standard source hierarchy (env > YAML)."""
    return Settings()


# Global instance for easy import (Level 0 call sites use `settings.*`).
settings = build_settings()
