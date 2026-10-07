from config import settings
from domain import (
    EvidenceSufficiencyDecision,
    GroundedAnswer,
    RetrievalQuery,
    RetrievalResult,
)
from generation.generator import parse_grounded_answer
from generation.llm import LLMClient
from generation.prompt import build_grounded_prompt, build_prompt
from grounding.abstention import decide
from grounding.citation_validator import validate_citations
from grounding.evidence_builder import build_evidence
from retrieval.retriever import Retriever
from retrieval.vector_store import VectorStore

ABSTENTION_TEXT = "I don't have enough information in the knowledge base to answer this question."


class RAGPipeline:
    """Orchestrate retrieve → prompt → generate → answer.

    Returns answer + retrieval record; abstention ("I don't have enough
    information in the knowledge base to answer this question.") when no
    context, without calling the LLM.
    """

    def __init__(
        self,
        vector_store: "VectorStore",
        embedder,
        retriever: Retriever | None = None,
        llm_client: LLMClient | None = None,
        top_k: int = 4,
        similarity_threshold: float = 0.0,
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        if retriever is None:
            self.retriever = Retriever(vector_store, embedder)
        else:
            self.retriever = retriever

        if llm_client is None:
            self.llm_client = LLMClient(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
        else:
            self.llm_client = llm_client

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievalResult]:
        """Retrieve relevant chunks for a question (no LLM; FR-007/US2)."""
        k = top_k if top_k is not None else self.top_k
        query = RetrievalQuery(
            question=question,
            top_k=max(k, 1),
            similarity_threshold=self.similarity_threshold,
        )
        return self.retriever.retrieve(query)

    def run(self, question: str, top_k: int | None = None) -> dict:
        """Run the full RAG pipeline for a given question.

        Delegates to run_grounded() (research R7) while preserving ALL
        legacy dict keys:
        - "question": the user question
        - "answer": the generated answer or abstention text
        - "retrieved_documents": list of source document names
        - "retrieval_scores": list of similarity scores
        - "used_context": whether retrieval produced chunks
        - "abstention": abstention text if no context

        Grounded extras ("evidence", "grounded_answer", ...) are additive.
        """
        return self.run_grounded(question, top_k=top_k)

    def run_grounded(self, question: str, top_k: int | None = None) -> dict:
        """Canonical Level 2 entry point (FR-003, research R7).

        retrieve -> build_evidence -> grounded prompt -> structured
        generation -> GroundedAnswer. Raises StructuredOutputError on
        malformed structured output (contract rule 1); RuntimeError on
        transport/LLM failures propagates as in Level 1 (FR-017).
        """
        results = self.retrieve(question, top_k=top_k)
        retrieved_docs = [r.chunk.document_name for r in results]
        retrieval_scores = [r.score for r in results]

        if not results:
            # Zero evidence: abstain without generation (FR-006).
            grounded = GroundedAnswer(
                answer=ABSTENTION_TEXT, abstained=True, sufficient_evidence=False
            )
            decision = decide([])
            return self._pack(
                question=question,
                answer_text=ABSTENTION_TEXT,
                retrieved_docs=retrieved_docs,
                retrieval_scores=retrieval_scores,
                used_context=False,
                abstention=ABSTENTION_TEXT,
                evidence=[],
                grounded=grounded,
                abstained=True,
                decision=decision,
            )

        evidence = build_evidence(results)
        prompt = build_grounded_prompt(question, evidence)
        raw = self.llm_client.generate_json(prompt)

        if not isinstance(raw, str):
            # Level 1 free-text client (no structured mode): legacy path.
            answer_obj = self.llm_client.generate(build_prompt(question, results, use_context=True))
            decision = decide(evidence)
            if not decision.sufficient:
                # Config layers 1-2 still apply (FR-011).
                return self._pack(
                    question=question,
                    answer_text=ABSTENTION_TEXT,
                    retrieved_docs=retrieved_docs,
                    retrieval_scores=retrieval_scores,
                    used_context=False,
                    abstention=ABSTENTION_TEXT,
                    evidence=evidence,
                    grounded=None,
                    abstained=True,
                    decision=decision,
                )
            if not answer_obj.used_context or not answer_obj.text.strip():
                return self._pack(
                    question=question,
                    answer_text=ABSTENTION_TEXT,
                    retrieved_docs=retrieved_docs,
                    retrieval_scores=retrieval_scores,
                    used_context=False,
                    abstention=ABSTENTION_TEXT,
                    evidence=evidence,
                    grounded=None,
                    abstained=True,
                    decision=decision,
                )
            return self._pack(
                question=question,
                answer_text=answer_obj.text,
                retrieved_docs=retrieved_docs,
                retrieval_scores=retrieval_scores,
                used_context=True,
                abstention="",
                evidence=evidence,
                grounded=None,
                abstained=False,
                decision=decision,
            )

        grounded = parse_grounded_answer(raw)
        verdicts = validate_citations(evidence, grounded.citations)
        decision = decide(evidence, model_answer=grounded)

        if grounded.abstained:
            # Model-authored abstention: keep its wording (T022 precedence).
            answer_text = grounded.answer
            abstention = grounded.answer
            used_context = False
        elif not decision.sufficient:
            # Sufficiency layers 1-3 override a substantive model answer.
            answer_text = ABSTENTION_TEXT
            abstention = ABSTENTION_TEXT
            used_context = False
        else:
            answer_text = grounded.answer
            abstention = ""
            used_context = True

        return self._pack(
            question=question,
            answer_text=answer_text,
            retrieved_docs=retrieved_docs,
            retrieval_scores=retrieval_scores,
            used_context=used_context,
            abstention=abstention,
            evidence=evidence,
            grounded=grounded,
            abstained=grounded.abstained or not decision.sufficient,
            decision=decision,
            citation_validation=verdicts,
        )

    @staticmethod
    def _pack(
        *,
        question: str,
        answer_text: str,
        retrieved_docs: list[str],
        retrieval_scores: list[float],
        used_context: bool,
        abstention: str,
        evidence: list,
        grounded: GroundedAnswer | None,
        abstained: bool,
        decision: EvidenceSufficiencyDecision,
        citation_validation: list | None = None,
    ) -> dict:
        """Legacy keys + additive grounded extras (research R7, T021)."""
        return {
            "question": question,
            "answer": answer_text,
            "retrieved_documents": retrieved_docs,
            "retrieval_scores": retrieval_scores,
            "used_context": used_context,
            "abstention": abstention,
            "abstained": abstained,
            "sufficient_evidence": decision.sufficient,
            "evidence_sufficiency": decision,
            "evidence": evidence,
            "grounded_answer": grounded,
            "citation_validation": list(citation_validation or []),
            "conflicts": list(grounded.conflicts) if grounded else [],
        }
