"""Evidence-sufficiency / abstention tests (spec US3, FR-010/FR-011;

research R3 layered decision; data-model.md decision order).
Deterministic: no live LLM calls (FR-022).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from config import settings
from domain import Evidence, GroundedAnswer

DIM = 4

VALID_STRUCTURED_PAYLOAD = (
    '{"answer": "Begin by checking the base station cell for RF interference.",'
    ' "citations": [{"document_id": "test", "chunk_id": "test#0001"}],'
    ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
)


class FakeEmbedder:
    def __init__(self, dim=DIM):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        return np.zeros(self.dim, dtype=np.float32)

    def embed_batch(self, texts) -> list:
        return [np.zeros(self.dim, dtype=np.float32) for _ in texts]

    def embed_query(self, question: str) -> np.ndarray:
        return np.zeros(self.dim, dtype=np.float32)

    def embed_documents(self, documents):
        return self.embed_batch(documents)

    def dimension(self) -> int:
        return self.dim


class FakeLLM:
    """Deterministic structured-output fake (FR-022)."""

    def __init__(self, payload: str):
        self.payload = payload
        self.json_calls = 0

    def generate_json(self, prompt: str) -> str:
        self.json_calls += 1
        return self.payload


def _ev(score: float = 0.9, rank: int = 1) -> Evidence:
    return Evidence(
        evidence_id=f"EVIDENCE-{rank:03d}",
        document_id="5g_packet_loss",
        chunk_id=f"5g_packet_loss-{rank:03d}",
        title="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        text="evidence text",
        retrieval_score=score,
        rank=rank,
    )


def test_no_evidence_reason(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 1)
    d = decide([])
    assert d.sufficient is False
    assert d.reason == "NO_EVIDENCE"
    assert d.evidence_count == 0
    assert d.mean_score is None


def test_below_min_count_reason(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 3)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.0)
    d = decide([_ev(0.95)])
    assert d.sufficient is False
    assert d.reason == "BELOW_MIN_COUNT"
    assert d.evidence_count == 1


def test_below_threshold_reason(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.5)
    d = decide([_ev(0.1), _ev(0.2, rank=2)])
    assert d.sufficient is False
    assert d.reason == "BELOW_THRESHOLD"
    assert d.evidence_count == 2
    assert d.mean_score is not None and d.mean_score < 0.5


def test_model_reports_insufficient_reason(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.0)
    model = GroundedAnswer(answer="I cannot answer reliably.", sufficient_evidence=False)
    d = decide([_ev(0.9)], model_answer=model)
    assert d.sufficient is False
    assert d.reason == "MODEL_REPORTS_INSUFFICIENT"
    assert d.mean_score is not None


def test_sufficient_when_all_layers_pass(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.0)
    model = GroundedAnswer(
        answer="Packet loss causes include interference.", sufficient_evidence=True
    )
    d = decide([_ev(0.9), _ev(0.8, rank=2)], model_answer=model)
    assert d.sufficient is True
    assert d.reason == "SUFFICIENT"
    assert d.evidence_count == 2
    assert d.mean_score is not None


def test_reason_ordering_no_evidence_beats_model():
    """First match wins: NO_EVIDENCE even when the model also reports insufficient."""
    from grounding.abstention import decide

    model = GroundedAnswer(answer="x", sufficient_evidence=False)
    d = decide([], model_answer=model)
    assert d.reason == "NO_EVIDENCE"


def test_reason_ordering_below_count_beats_model(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 2)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.0)
    model = GroundedAnswer(answer="x", sufficient_evidence=False)
    d = decide([_ev(0.9)], model_answer=model)
    assert d.reason == "BELOW_MIN_COUNT"


def test_reason_ordering_threshold_beats_model(monkeypatch):
    from grounding.abstention import decide

    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.95)
    model = GroundedAnswer(answer="x", sufficient_evidence=False)
    d = decide([_ev(0.5)], model_answer=model)
    assert d.reason == "BELOW_THRESHOLD"


def _pipeline_with(tmp_path, payload: str, chunks: int = 1):
    from rag.pipeline import RAGPipeline
    from retrieval.vector_store import VectorStore

    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_abstention",
        dimension=DIM,
    )
    if chunks:
        chunk = _chunk()
        store.add([chunk], [np.ones(DIM, dtype=np.float32)])
    fake = FakeLLM(payload)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=fake,  # type: ignore[arg-type]
        top_k=4,
    )
    return pipeline, fake


def _chunk():
    from domain import Chunk

    return Chunk(
        chunk_id="test#0001",
        content="5G packet loss troubleshooting steps number 0",
        document_id="test",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=1,
    )


def test_zero_evidence_fast_path_no_llm_call(tmp_path, monkeypatch):
    """Pipeline: zero evidence -> abstain without generation (FR-006)."""
    monkeypatch.setattr(settings, "min_evidence", 1)

    pipeline, fake = _pipeline_with(tmp_path, "{}", chunks=0)
    result = pipeline.run_grounded("what is the meaning of tea?")

    assert fake.json_calls == 0
    assert result["abstained"] is True
    assert result["used_context"] is False
    assert result["evidence_sufficiency"].reason == "NO_EVIDENCE"
    assert result["sufficient_evidence"] is False
    assert "I don't have enough information" in result["answer"]
    print("✓ zero-evidence fast path abstains without LLM call")


def test_pipeline_abstains_when_config_threshold_unmet(tmp_path, monkeypatch):
    """Pipeline: below-threshold evidence -> abstention overrides model answer."""
    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.95)

    pipeline, fake = _pipeline_with(tmp_path, VALID_STRUCTURED_PAYLOAD)
    result = pipeline.run_grounded("How do I troubleshoot 5G packet loss?")

    assert fake.json_calls == 1
    assert result["evidence_sufficiency"].reason == "BELOW_THRESHOLD"
    assert result["abstained"] is True
    assert result["sufficient_evidence"] is False
    assert "I don't have enough information" in result["answer"]
    assert len(result["evidence"]) == 1  # evidence retained for debug
    print("✓ config threshold triggers abstention")


def test_pipeline_model_insufficient_triggers_abstention(tmp_path):
    """Pipeline: model sufficient_evidence=false -> abstain (layer 3)."""
    payload = (
        '{"answer": "I cannot answer reliably.", "citations": [],'
        ' "abstained": false, "sufficient_evidence": false, "conflicts": []}'
    )
    pipeline, _ = _pipeline_with(tmp_path, payload)
    result = pipeline.run_grounded("How do I troubleshoot 5G packet loss?")

    assert result["abstained"] is True
    assert result["evidence_sufficiency"].reason == "MODEL_REPORTS_INSUFFICIENT"
    assert "I don't have enough information" in result["answer"]
    print("✓ model-reported insufficient evidence triggers abstention")


def test_pipeline_sufficient_answer_not_abstained(tmp_path, monkeypatch):
    """Sufficient evidence + model answer -> normal answer preserved."""
    monkeypatch.setattr(settings, "min_evidence", 1)
    monkeypatch.setattr(settings, "sufficiency_threshold", 0.0)

    pipeline, _ = _pipeline_with(tmp_path, VALID_STRUCTURED_PAYLOAD)
    result = pipeline.run_grounded("How do I troubleshoot 5G packet loss?")

    assert result["abstained"] is False
    assert result["sufficient_evidence"] is True
    assert result["evidence_sufficiency"].reason == "SUFFICIENT"
    assert result["answer"].startswith("Begin by checking")
    assert result["abstention"] == ""
    print("✓ sufficient evidence yields normal grounded answer")
