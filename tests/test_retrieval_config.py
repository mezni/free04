"""Level 3 retrieval configuration contract (contracts/retrieval-config.md).

FR-004/FR-008: closed strategy set, rrf-only fusion, positive depths,
rerank clamp warning, rewriting off by default.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from config import RETRIEVAL_STRATEGIES, Settings

BASE = dict(chunk_size=500, chunk_overlap=50)


def test_defaults_match_contract():
    s = Settings(**BASE)
    assert s.retrieval_strategy == "vector"
    assert (s.stage_top_k_vector, s.stage_top_k_bm25) == (20, 20)
    assert (s.stage_top_k_hybrid, s.stage_top_k_final) == (20, 5)
    assert s.fusion_method == "rrf"
    assert s.fusion_k == 60
    assert s.retrieval_filters == {}
    assert s.rerank_enabled is True
    assert s.rerank_model == "BAAI/bge-reranker-base"
    assert (s.rerank_candidate_k, s.rerank_final_k) == (20, 5)
    assert s.query_rewrite_enabled is False  # Principle XXIX: default off
    assert s.top_k == 4  # legacy Level 1 depth untouched
    print("✓ contract defaults")


def test_all_four_strategies_accepted():
    for strategy in RETRIEVAL_STRATEGIES:
        s = Settings(retrieval_strategy=strategy, **BASE)
        assert s.retrieval_strategy == strategy
    print("✓ all four strategies accepted")


def test_invalid_strategy_rejected():
    """FR-008: unknown strategy fails loudly — no silent fallback."""
    with pytest.raises(ValueError, match="strategy"):
        Settings(retrieval_strategy="souped", **BASE)
    print("✓ invalid strategy rejected")


def test_non_rrf_fusion_rejected():
    with pytest.raises(ValueError, match="rrf"):
        Settings(fusion_method="weighted", **BASE)
    print("✓ non-rrf fusion rejected")


@pytest.mark.parametrize("field", ["fusion_k", "stage_top_k_final", "rerank_candidate_k"])
def test_non_positive_depths_rejected(field):
    with pytest.raises(ValueError):
        Settings(**{**BASE, field: 0})
    print(f"✓ {field}=0 rejected")


def test_yaml_defaults_loaded():
    """config/settings.yaml drives the Level 3 block (env-independent fields)."""
    s = Settings(chunk_size=500, chunk_overlap=50, top_k=4)
    assert s.retrieval_strategy == "vector"
    assert s.fusion_k == 60
    assert s.rerank_enabled is True
    assert s.query_rewrite_enabled is False
    print("✓ YAML Level 3 defaults loaded")


def test_final_k_above_candidate_k_warns_and_clamps():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = Settings(**{**BASE, "rerank_final_k": 50, "rerank_candidate_k": 20})
    assert s.rerank_final_k == 20  # clamped to the pool
    assert any("candidate_k" in str(w.message) for w in caught)
    print("✓ final_k > candidate_k warns + clamps")


def test_env_override_strategy(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_STRATEGY", "hybrid")
    s = Settings(**BASE)
    assert s.retrieval_strategy == "hybrid"
    print("✓ env overrides strategy")


if __name__ == "__main__":
    test_defaults_match_contract()
    test_all_four_strategies_accepted()
    test_invalid_strategy_rejected()
    test_non_rrf_fusion_rejected()
    test_final_k_above_candidate_k_warns_and_clamps()
    print("✓ retrieval config tests passed")
