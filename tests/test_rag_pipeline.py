"""Deterministic end-to-end tests for RAG pipeline using mocked clients."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import MagicMock

import numpy as np

from domain import Answer, Chunk, GroundedAnswer, StructuredOutputError
from generation.llm import LLMClient
from rag.pipeline import RAGPipeline
from retrieval.retriever import Retriever
from retrieval.vector_store import VectorStore

DIM = 4


class FakeEmbedder:
    """Deterministic fake embedder for pipeline tests."""

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


def _chunk(i: int = 0, doc_id: str = "test") -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#000{i + 1}",
        content=f"5G packet loss troubleshooting steps number {i}",
        document_id=doc_id,
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=i + 1,
    )


def _empty_store(tmp_path):
    return VectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_pipeline",
        dimension=DIM,
    )


def test_pipeline_abstention_no_chunks(tmp_path):
    """Test pipeline abstention when no chunks found."""
    store = _empty_store(tmp_path)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        top_k=4,
        llm_client=MagicMock(spec=LLMClient),
    )

    result = pipeline.run("What is the procedure for satellite network handover?")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    assert result["retrieved_documents"] == []
    assert result["retrieval_scores"] == []
    print("✓ Pipeline abstention no chunks")


def test_pipeline_with_mocked_llm(tmp_path):
    """Test pipeline with mocked LLM client."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    retriever = Retriever(vector_store=store, embedder=FakeEmbedder())

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(
        text="Begin by checking the base station cell for RF interference",
        used_context=True,
    )

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        retriever=retriever,
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("How do I troubleshoot 5G packet loss?")

    assert result["used_context"] is True
    assert result["answer"] == "Begin by checking the base station cell for RF interference"
    assert "5g_packet_loss.md" in result["retrieved_documents"]
    print("✓ Pipeline with mocked LLM")


def test_pipeline_abstention_on_empty_answer(tmp_path):
    """Test pipeline uses abstention when LLM returns empty answer without context."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="", used_context=False)

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("Some question")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    print("✓ Pipeline abstention on empty answer")


def test_pipeline_top_k_limit(tmp_path):
    """Test pipeline respects top-k limit."""
    store = _empty_store(tmp_path)
    chunks = [_chunk(i=i, doc_id=f"doc{i}") for i in range(5)]
    store.add(chunks, [np.ones(DIM, dtype=np.float32) for _ in chunks])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="Answer", used_context=True)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=3,
    )

    result = pipeline.run("network question")

    assert len(result["retrieved_documents"]) <= 3
    print("✓ Pipeline top-k limit")


def test_pipeline_runtime_error_on_llm_failure_propagates(tmp_path):
    """LLM failures propagate as RuntimeError for FR-017 handling."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.side_effect = RuntimeError("LLM request timed out after 30s")

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=4,
    )

    import pytest

    with pytest.raises(RuntimeError, match="LLM request"):
        pipeline.run("How do I troubleshoot 5G packet loss?")
    print("✓ Pipeline propagates LLM failure")


class FakeLLM:
    """Deterministic structured-output fake for grounded-path tests (FR-022)."""

    def __init__(self, payload: str):
        self.payload = payload
        self.json_calls = 0
        self.prompts: list[str] = []

    def generate_json(self, prompt: str) -> str:
        self.json_calls += 1
        self.prompts.append(prompt)
        return self.payload

    def generate(self, prompt: str) -> Answer:
        raise AssertionError("free-text path must not run when structured output is available")


VALID_STRUCTURED_PAYLOAD = (
    '{"answer": "Begin by checking the base station cell for RF interference.",'
    ' "citations": [{"document_id": "test", "chunk_id": "test#0001"}],'
    ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
)


def _grounded_pipeline(
    tmp_path, payload: str = VALID_STRUCTURED_PAYLOAD, chunks: list[Chunk] | None = None
):
    store = _empty_store(tmp_path)
    if chunks:
        store.add(chunks, [np.ones(DIM, dtype=np.float32) for _ in chunks])
    fake = FakeLLM(payload)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=fake,  # type: ignore[arg-type]
        top_k=4,
    )
    return pipeline, fake


def test_run_grounded_builds_evidence_and_parses_answer(tmp_path):
    """US1: run_grounded builds Evidence and parses GroundedAnswer (FR-003)."""
    pipeline, fake = _grounded_pipeline(tmp_path, chunks=[_chunk()])

    result = pipeline.run_grounded("How do I troubleshoot 5G packet loss?")

    evidence = result["evidence"]
    assert [e.evidence_id for e in evidence] == ["EVIDENCE-001"]
    assert evidence[0].document_id == "test"
    assert evidence[0].chunk_id == "test#0001"
    assert evidence[0].retrieval_score == 0.0  # zero-vector fake embedder
    assert evidence[0].rank == 1

    grounded = result["grounded_answer"]
    assert isinstance(grounded, GroundedAnswer)
    assert grounded.answer.startswith("Begin by checking")
    assert grounded.citations[0].document_id == "test"
    assert grounded.abstained is False

    # Grounded prompt is evidence-aware and deterministic (contract §1).
    assert fake.json_calls == 1
    assert "QUESTION:" in fake.prompts[0]
    assert "EVIDENCE-001 | test | test#0001" in fake.prompts[0]
    print("✓ run_grounded builds evidence and parses structured answer")


def test_run_delegates_preserving_legacy_keys(tmp_path):
    """run() delegates to run_grounded while keeping ALL legacy dict keys."""
    pipeline, _ = _grounded_pipeline(tmp_path, chunks=[_chunk()])

    result = pipeline.run("How do I troubleshoot 5G packet loss?")

    for key in (
        "question",
        "answer",
        "retrieved_documents",
        "retrieval_scores",
        "used_context",
        "abstention",
    ):
        assert key in result, f"legacy key missing: {key}"
    assert result["used_context"] is True
    assert result["answer"].startswith("Begin by checking")
    assert result["retrieved_documents"] == ["5g_packet_loss.md"]
    assert result["abstention"] == ""
    # Additive grounded extras.
    assert isinstance(result["grounded_answer"], GroundedAnswer)
    assert [v.status for v in result["citation_validation"]] == ["VALID"]
    assert result["evidence_sufficiency"].reason == "SUFFICIENT"
    assert result["abstained"] is False
    print("✓ run() delegates with legacy keys preserved")


def test_run_grounded_malformed_output_raises_structured_output_error(tmp_path):
    """Contract rule 1: malformed structured output is detected, never shown."""
    import pytest

    pipeline, _ = _grounded_pipeline(
        tmp_path,
        payload="Sorry, here is what I think: 5G is fast.",
        chunks=[_chunk()],
    )

    with pytest.raises(StructuredOutputError):
        pipeline.run_grounded("How do I troubleshoot 5G packet loss?")
    print("✓ malformed structured output raises StructuredOutputError")


def test_run_grounded_zero_results_abstains_without_generation(tmp_path):
    """FR-006: zero evidence -> abstention without calling the LLM."""
    pipeline, fake = _grounded_pipeline(tmp_path, chunks=None)

    result = pipeline.run_grounded("what is the meaning of tea?")

    assert fake.json_calls == 0
    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    grounded = result["grounded_answer"]
    assert grounded.abstained is True
    assert grounded.sufficient_evidence is False
    assert result["evidence"] == []
    print("✓ zero results abstain without generation")


def test_run_grounded_structured_abstention_keeps_evidence(tmp_path):
    """Model-reported abstention: evidence retained, abstention key set."""
    payload = (
        '{"answer": "I don\'t have enough information in the knowledge base'
        ' to answer this question.", "citations": [], "abstained": true,'
        ' "sufficient_evidence": false, "conflicts": []}'
    )
    pipeline, _ = _grounded_pipeline(tmp_path, payload=payload, chunks=[_chunk()])

    result = pipeline.run_grounded("How do I troubleshoot 5G packet loss?")

    grounded = result["grounded_answer"]
    assert grounded.abstained is True
    assert result["abstention"] == grounded.answer
    assert len(result["evidence"]) == 1
    print("✓ structured abstention retains evidence")


CONFLICT_PAYLOAD = (
    '{"answer": "Expected 5G speed varies with network load and location.",'
    ' "citations": [{"document_id": "test", "chunk_id": "test#0001"}],'
    ' "abstained": false, "sufficient_evidence": true,'
    ' "conflicts": [{"description": "Marketing doc claims 1 Gbps; reporting'
    ' doc shows 100-300 Mbps.", "positions": [{"document_id": "test",'
    ' "chunk_id": "test#0001"}, {"document_id": "test", "chunk_id": "test#0002"}]}]}'
)


def test_hallucination_scenario_correct_evidence_gives_grounded_answer(tmp_path):
    """R8-1: correct evidence -> correct answer; every claim is cited & valid."""
    pipeline, _ = _grounded_pipeline(tmp_path, chunks=[_chunk()])

    result = pipeline.run_grounded("What can cause 5G packet loss?")

    assert result["evidence"]
    validation = result["citation_validation"]
    assert validation, "a correct answer must carry citations"
    assert all(v.is_valid for v in validation), "cite only retrieved chunks"
    assert not result["abstained"]
    print("✓ scenario: correct evidence -> grounded answer")


def test_hallucination_scenario_unsupported_extra_claim_detected(tmp_path):
    """R8-2: an extra claim absent from evidence is detected as UNSUPPORTED."""
    from evaluation.groundedness import evaluate_claim

    pipeline, _ = _grounded_pipeline(tmp_path, chunks=[_chunk()])
    result = pipeline.run_grounded("What can cause 5G packet loss?")
    evidence = result["evidence"]

    verdict = evaluate_claim("Solar flares disrupt 5G base stations.", evidence)

    assert verdict.status == "UNSUPPORTED"
    print("✓ scenario: unsupported extra claim is detected")


def test_hallucination_scenario_insufficient_evidence_abstains(tmp_path):
    """R8-3: insufficient evidence -> abstention, no fabricated answer."""
    payload = (
        '{"answer": "I don\'t have enough information in the knowledge base'
        ' to answer this question.", "citations": [], "abstained": true,'
        ' "sufficient_evidence": false, "conflicts": []}'
    )
    pipeline, _ = _grounded_pipeline(tmp_path, payload=payload, chunks=[_chunk()])

    result = pipeline.run_grounded("What can cause 5G packet loss?")

    assert result["abstained"] is True
    assert result["grounded_answer"].abstained is True
    assert "don't have enough information" in result["answer"]
    print("✓ scenario: insufficient evidence abstains")


def test_hallucination_scenario_no_evidence_abstains(tmp_path):
    """R8-4: no evidence -> abstain without ever calling the LLM (SC-002)."""
    pipeline, fake = _grounded_pipeline(tmp_path, chunks=None)

    result = pipeline.run("What is the chemical formula of benzene?")

    assert fake.json_calls == 0
    assert result["abstained"] is True
    assert result["answer"].strip()  # abstention text, never a fabricated claim
    print("✓ scenario: no evidence abstains without LLM")


def test_hallucination_scenario_conflicting_evidence_is_reported(tmp_path):
    """R8-5: conflicting evidence -> conflict surfaced, never merged."""
    pipeline, _ = _grounded_pipeline(tmp_path, payload=CONFLICT_PAYLOAD, chunks=[_chunk()])

    result = pipeline.run_grounded("What 5G speed should I quote a customer?")

    assert result["conflicts"], "conflicting evidence must be reported"
    note = result["conflicts"][0]
    assert "Marketing doc claims" in note.description
    assert len(note.positions) >= 2
    # The conflict answer survives verbatim (nothing collapsed into one source).
    assert "varies with network load" in result["answer"]
    print("✓ scenario: conflicting evidence is reported, not merged")


def test_hallucination_scenario_missing_citation_flagged(tmp_path):
    """R8-6: a valid answer with no citations -> INCOMPLETE_CITATIONS."""
    from domain import GroundedEvaluationCase
    from evaluation.answer_metrics import citation_completeness

    payload = (
        '{"answer": "Check the base station cell for RF interference.",'
        ' "citations": [], "abstained": false, "sufficient_evidence": true,'
        ' "conflicts": []}'
    )
    pipeline, _ = _grounded_pipeline(tmp_path, payload=payload, chunks=[_chunk()])

    result = pipeline.run_grounded("What can cause 5G packet loss?")

    assert result["citation_validation"] == []
    case = GroundedEvaluationCase(
        id="h",
        question="q",
        answerable=True,
        case_type="answerable",
        expected_answer="Check the base station cell for RF interference.",
    )
    assert citation_completeness(case, abstained=False, verdicts=[]) == 0.0
    print("✓ scenario: valid answer with missing citation is flagged INCOMPLETE_CITATIONS")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_pipeline_abstention_no_chunks(Path(td))
        test_pipeline_with_mocked_llm(Path(td))
        test_pipeline_abstention_on_empty_answer(Path(td))
        test_pipeline_top_k_limit(Path(td))
        test_pipeline_runtime_error_on_llm_failure_propagates(Path(td))
        test_run_grounded_builds_evidence_and_parses_answer(Path(td))
        test_run_delegates_preserving_legacy_keys(Path(td))
        test_run_grounded_malformed_output_raises_structured_output_error(Path(td))
        test_run_grounded_zero_results_abstains_without_generation(Path(td))
        test_run_grounded_structured_abstention_keeps_evidence(Path(td))
        test_hallucination_scenario_correct_evidence_gives_grounded_answer(Path(td))
        test_hallucination_scenario_unsupported_extra_claim_detected(Path(td))
        test_hallucination_scenario_insufficient_evidence_abstains(Path(td))
        test_hallucination_scenario_no_evidence_abstains(Path(td))
        test_hallucination_scenario_conflicting_evidence_is_reported(Path(td))
        test_hallucination_scenario_missing_citation_flagged(Path(td))
    print("✓ All pipeline tests passed")
