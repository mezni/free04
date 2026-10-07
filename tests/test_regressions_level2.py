"""Named Level 2 regression tests (FR-021; US6, T034/T035).

Each test guards one named requirement from research R8:
  - answers stay grounded in the retrieved evidence (no outside knowledge)
  - unknown questions abstain
  - fabricated citations (unknown doc / unretrieved chunk) are rejected
  - supported answers carry citations
  - conflicting evidence is reported, never merged

Deterministic FakeLLM fixtures only (FR-022); no network or live model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from domain import Chunk
from rag.pipeline import RAGPipeline
from retrieval.vector_store import VectorStore

DIM = 8


class FakeEmbedder:
    """Zero-vector embedder: deterministic, no models."""

    def __init__(self, dim=DIM):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        return np.zeros(self.dim, dtype=np.float32)

    def embed_batch(self, texts) -> list:
        return [self.embed(t) for t in texts]

    def embed_query(self, question: str) -> np.ndarray:
        return self.embed(question)

    def embed_documents(self, documents):
        return self.embed_batch(documents)

    def dimension(self) -> int:
        return self.dim


def _chunk(i: int = 0, doc_id: str = "test") -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#{i + 1:04d}",
        content=(
            "Radio signal interference causes intermittent packet loss on 5G "
            "networks. Reconfigure the affected cells."
            if i == 0
            else "Congestion in crowded areas can also cause packet loss."
        ),
        document_id=doc_id,
        document_name=f"{doc_id}.md",
        source=f"data/documents/{doc_id}.md",
        chunk_index=i + 1,
    )


def _empty_store(tmp_path) -> VectorStore:
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"), collection_name="test_collection", dimension=DIM
    )
    return store


class FakeLLM:
    """Deterministic structured-output fake (FR-022)."""

    def __init__(self, payload: str):
        self.payload = payload
        self.json_calls = 0
        self.prompts: list[str] = []

    def generate_json(self, prompt: str) -> str:
        self.json_calls += 1
        self.prompts.append(prompt)
        return self.payload

    def generate(self, prompt: str) -> object:
        raise AssertionError("structured output must be used")


def _pipeline(tmp_path, payload: str, chunks, top_k: int = 4):
    store = _empty_store(tmp_path)
    if chunks:
        store.add(chunks, [np.ones(DIM, dtype=np.float32) for _ in chunks])
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=FakeLLM(payload),  # type: ignore[arg-type]
        top_k=top_k,
    )
    return pipeline


def _valid_payload() -> str:
    return (
        '{"answer": "Radio signal interference causes packet loss on 5G '
        'networks. Reconfigure the affected cells.",'
        ' "citations": [{"document_id": "test", "chunk_id": "test#0001"}],'
        ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
    )


def test_answer_does_not_use_external_knowledge(tmp_path):
    """FR-021: the answer is implied by the retrieved evidence alone."""
    from evaluation.groundedness import evaluate_claim

    pipeline = _pipeline(tmp_path, _valid_payload(), [_chunk()])
    result = pipeline.run_grounded("What causes 5G packet loss?")

    evidence = result["evidence"]
    claims = [result["answer"]]
    for claim in claims:
        verdict = evaluate_claim(claim, evidence)
        assert verdict.status == "SUPPORTED", verdict


def test_unknown_question_abstains(tmp_path):
    """FR-021: an out-of-corpus question abstains instead of guessing."""
    pipeline = _pipeline(tmp_path, _valid_payload(), [])

    result = pipeline.run("What is the boiling point of xenon?")

    assert result["abstained"] is True
    assert "don't have enough information" in result["answer"]


def test_invalid_citation_rejected(tmp_path):
    """FR-021: citations to nonexistent documents are rejected (SC-002)."""
    payload = (
        '{"answer": "Packet loss stems from solar interference.",'
        ' "citations": [{"document_id": "nonexistent_doc",'
        ' "chunk_id": "nonexistent_doc#0001"}], "abstained": false,'
        ' "sufficient_evidence": true, "conflicts": []}'
    )
    pipeline = _pipeline(tmp_path, payload, [_chunk()])

    result = pipeline.run_grounded("What causes 5G packet loss?")

    assert result["citation_validation"]
    assert all(not v.is_valid for v in result["citation_validation"])


def test_unretrieved_citation_rejected(tmp_path):
    """FR-021: citations to chunks never retrieved are NOT_RETRIEVED."""
    payload = (
        '{"answer": "Congestion in crowded areas can cause packet loss.",'
        ' "citations": [{"document_id": "test", "chunk_id": "test#0003"}],'
        ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
    )
    # top_k=1 keeps chunk #0003 out of every retrieval regardless of ordering.
    pipeline = _pipeline(tmp_path, payload, [_chunk(), _chunk(1)], top_k=1)

    result = pipeline.run_grounded("What causes 5G packet loss?")

    verdicts = result["citation_validation"]
    assert [v.status for v in verdicts] == ["NOT_RETRIEVED"]
    assert all(not v.is_valid for v in verdicts)


def test_supported_answer_has_citation(tmp_path):
    """FR-021: a grounded answer carries at least one VALID citation."""
    from domain import GroundedEvaluationCase
    from evaluation.answer_metrics import citation_completeness

    pipeline = _pipeline(tmp_path, _valid_payload(), [_chunk()])
    result = pipeline.run_grounded("What causes 5G packet loss?")

    assert result["citation_validation"]
    assert any(v.is_valid for v in result["citation_validation"])
    case = GroundedEvaluationCase(
        id="reg",
        question="q",
        answerable=True,
        case_type="answerable",
        expected_answer="Radio signal interference causes packet loss.",
    )
    assert (
        citation_completeness(case, abstained=False, verdicts=result["citation_validation"]) == 1.0
    )


def test_conflicting_evidence_is_reported(tmp_path):
    """FR-021: disagreements surface as Conflicts, never silently merged."""
    payload = (
        '{"answer": "Speeds vary by network load and location.",'
        ' "citations": [{"document_id": "test", "chunk_id": "test#0001"}],'
        ' "abstained": false, "sufficient_evidence": true,'
        ' "conflicts": [{"description": "1 Gbps ideal vs 100-300 Mbps real",'
        ' "positions": [{"document_id": "test", "chunk_id": "test#0001"},'
        ' {"document_id": "test", "chunk_id": "test#0002"}]}]}'
    )
    pipeline = _pipeline(tmp_path, payload, [_chunk(), _chunk(1)])

    result = pipeline.run_grounded("What speed should I quote a customer?")

    assert result["conflicts"]
    assert "1 Gbps ideal vs 100-300 Mbps real" in result["conflicts"][0].description
    assert len(result["conflicts"][0].positions) == 2
