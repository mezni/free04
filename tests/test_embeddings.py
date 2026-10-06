"""Embedding sanity tests (FR-001, US1 acceptance 4, constitution XI).

Uses the fast deterministic all-MiniLM-L6-v2 model (per spec Assumptions the
test model may differ from the production BAAI/bge-small-en-v1.5).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from embeddings.embedder import Embedder

TEST_MODEL = "all-MiniLM-L6-v2"


def _embedder() -> Embedder:
    return Embedder(provider="local-sentence-transformers", model=TEST_MODEL)


def test_dimension_is_384():
    emb = _embedder()
    assert emb.dimension() == 384


def test_embed_returns_float_vector():
    emb = _embedder()
    vec = emb.embed("5G packet loss troubleshooting")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    assert vec.dtype == np.float32


def test_embed_query_alias():
    emb = _embedder()
    assert np.allclose(emb.embed_query("question"), emb.embed("question"))


def test_similar_sentences_closer_than_unrelated():
    emb = _embedder()
    a = emb.embed("What causes 5G packet loss on the network?")
    b = emb.embed("Packet loss on a 5G connection can be caused by interference.")
    c = emb.embed("The monthly billing statement includes line item details.")

    sim_ab = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    sim_ac = float(a @ c / (np.linalg.norm(a) * np.linalg.norm(c)))

    assert sim_ab > sim_ac, f"Expected related pair closer: ab={sim_ab:.3f} ac={sim_ac:.3f}"


def test_embed_batch_matches_individual():
    emb = _embedder()
    texts = ["5G packet loss", "SIM activation", "billing statement"]
    batch = emb.embed_batch(texts)
    assert len(batch) == len(texts)
    for text, vec in zip(texts, batch, strict=True):
        assert np.allclose(vec, emb.embed(text), atol=1e-4)


if __name__ == "__main__":
    test_dimension_is_384()
    test_embed_returns_float_vector()
    test_embed_query_alias()
    test_similar_sentences_closer_than_unrelated()
    test_embed_batch_matches_individual()
    print("✓ Embedding tests passed")