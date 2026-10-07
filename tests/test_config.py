"""US3 config tests: env overrides and validation (contracts/config-contract.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from config import Settings


def test_env_var_overrides_yaml(monkeypatch):
    """CHUNK_SIZE / TOP_K env vars override the config/settings.yaml values."""
    monkeypatch.setenv("CHUNK_SIZE", "333")
    monkeypatch.setenv("TOP_K", "7")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost")
    monkeypatch.setenv("LLM_MODEL", "test")

    s = Settings()

    assert s.chunk_size == 333
    assert s.top_k == 7
    # YAML fallback for fields not overridden (config/settings.yaml: overlap 50)
    assert s.chunk_overlap == 50
    print("✓ env overrides YAML")


def test_chunk_overlap_ge_chunk_size_rejected(monkeypatch):
    """chunk_overlap >= chunk_size is invalid."""
    monkeypatch.delenv("CHUNK_SIZE", raising=False)
    monkeypatch.delenv("CHUNK_OVERLAP", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost")
    monkeypatch.setenv("LLM_MODEL", "test")

    with pytest.raises(ValueError, match="CHUNK_OVERLAP must be < CHUNK_SIZE"):
        Settings(chunk_size=100, chunk_overlap=101)
    print("✓ overlap >= size rejected")


def test_top_k_lt_1_rejected(monkeypatch):
    """top_k < 1 is invalid."""
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost")
    monkeypatch.setenv("LLM_MODEL", "test")

    with pytest.raises(ValueError, match="TOP_K must be >= 1"):
        Settings(top_k=0, chunk_size=500, chunk_overlap=50)
    print("✓ top_k<1 rejected")


def test_similarity_threshold_out_of_range_rejected(monkeypatch):
    """similarity_threshold outside [-1, 1] is invalid."""
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost")
    monkeypatch.setenv("LLM_MODEL", "test")

    with pytest.raises(ValueError, match="SIMILARITY_THRESHOLD must be in"):
        Settings(similarity_threshold=1.5)
    print("✓ threshold out of range rejected")


def test_settings_loads_valid_config(monkeypatch):
    """A complete valid config constructs without error."""
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost")
    monkeypatch.setenv("LLM_MODEL", "test")

    s = Settings()
    assert s.similarity_threshold == 0.0
    assert s.top_k >= 1
    assert s.chunk_overlap < s.chunk_size
    print("✓ valid config loads")


if __name__ == "__main__":
    test_env_var_overrides_yaml()
    test_chunk_overlap_ge_chunk_size_rejected()
    test_top_k_lt_1_rejected()
    test_similarity_threshold_out_of_range_rejected()
    test_settings_loads_valid_config()
    print("✓ All config tests passed")
