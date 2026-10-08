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
from pydantic import Field, field_validator, model_validator
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

    # Level 3 advanced retrieval (contracts/retrieval-config.md).
    mapping.setdefault("retrieval_strategy", sec.get("strategy", "vector"))
    stage = sec.get("stage_top_k") or {}
    mapping.setdefault("stage_top_k_vector", stage.get("vector", 20))
    mapping.setdefault("stage_top_k_bm25", stage.get("bm25", 20))
    mapping.setdefault("stage_top_k_hybrid", stage.get("hybrid", 20))
    mapping.setdefault("stage_top_k_final", stage.get("final", 5))
    fusion = sec.get("fusion") or {}
    mapping.setdefault("fusion_method", fusion.get("method", "rrf"))
    mapping.setdefault("fusion_k", fusion.get("k", 60))
    mapping.setdefault("retrieval_filters", sec.get("filters") or {})

    sec = raw.get("reranking") or {}
    mapping.setdefault("rerank_enabled", sec.get("enabled", True))
    mapping.setdefault("rerank_model", sec.get("model", "BAAI/bge-reranker-base"))
    mapping.setdefault("rerank_candidate_k", sec.get("candidate_k", 20))
    mapping.setdefault("rerank_final_k", sec.get("final_k", 5))

    sec = raw.get("query_rewriting") or {}
    mapping.setdefault("query_rewrite_enabled", sec.get("enabled", False))

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


RETRIEVAL_STRATEGIES = ("vector", "bm25", "hybrid", "hybrid_reranked")


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

    # Level 3 advanced retrieval (contracts/retrieval-config.md).
    retrieval_strategy: str = "vector"
    stage_top_k_vector: int = 20
    stage_top_k_bm25: int = 20
    stage_top_k_hybrid: int = 20
    stage_top_k_final: int = 5
    fusion_method: str = "rrf"
    fusion_k: int = 60
    retrieval_filters: dict[str, Any] = Field(default_factory=dict)
    rerank_enabled: bool = True
    rerank_model: str = "BAAI/bge-reranker-base"
    rerank_candidate_k: int = 20
    rerank_final_k: int = 5
    # Principle XXIX (NON-NEGOTIABLE): rewriting is off unless measured.
    query_rewrite_enabled: bool = False

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

    # --- Level 3 retrieval settings (FR-004/FR-005/FR-008, research R7) ---

    @field_validator("retrieval_strategy")
    @classmethod
    def _strategy_closed_set(cls, v: str) -> str:
        if v not in RETRIEVAL_STRATEGIES:
            raise ValueError(
                f"retrieval strategy must be one of {', '.join(RETRIEVAL_STRATEGIES)}, got {v!r}"
            )
        return v

    @field_validator("fusion_method")
    @classmethod
    def _fusion_rrf_only(cls, v: str) -> str:
        if v != "rrf":
            raise ValueError(f"level 3 supports rrf fusion only, got {v!r}")
        return v

    @field_validator(
        "stage_top_k_vector",
        "stage_top_k_bm25",
        "stage_top_k_hybrid",
        "stage_top_k_final",
        "fusion_k",
        "rerank_candidate_k",
        "rerank_final_k",
    )
    @classmethod
    def _positive_int(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"expected value >= 1, got {v}")
        return v

    @field_validator("rerank_model")
    @classmethod
    def _rerank_model_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reranking.model must be non-empty")
        return v

    @model_validator(mode="after")
    def _rerank_final_within_pool(self) -> "Settings":
        # Contract: final_k > candidate_k is a warning + clamp, not an error.
        if self.rerank_final_k > self.rerank_candidate_k:
            import warnings

            warnings.warn(
                f"reranking.final_k ({self.rerank_final_k}) > candidate_k "
                f"({self.rerank_candidate_k}); clamping to {self.rerank_candidate_k}",
                stacklevel=2,
            )
            self.rerank_final_k = self.rerank_candidate_k
        return self


def build_settings() -> Settings:
    """Construct Settings with the standard source hierarchy (env > YAML)."""
    return Settings()


# Global instance for easy import (Level 0 call sites use `settings.*`).
settings = build_settings()
