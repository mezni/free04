from domain import Document, Chunk, RetrievalResult, Answer
from retrieval.retriever import Retriever
from generation.prompt import build_prompt, make_prompt_from_results
from generation.llm import LLMClient
from config import settings


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
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k

        if retriever is None:
            self.retriever = Retriever(vector_store, embedder, top_k=top_k)
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

    def run(self, question: str) -> dict:
        """Run the full RAG pipeline for a given question.

        Returns a dict with:
        - "question": the user question
        - "answer": the generated answer or abstention text
        - "retrieved_documents": list of source document names
        - "retrieval_scores": list of similarity scores
        - "used_context": whether retrieval produced chunks
        - "abstention": abstention text if no context
        """
        # Step 1: Retrieve
        results = self.retriever.retrieve(question)

        if not results:
            # No chunks found - abstention
            abstention = "I don't have enough information in the knowledge base to answer this question."
            return {
                "question": question,
                "answer": abstention,
                "retrieved_documents": [],
                "retrieval_scores": [],
                "used_context": False,
                "abstention": abstention,
            }

        # Step 2: Build prompt
        prompt = build_prompt(question, results, use_context=True)

        # Step 3: Generate answer
        answer_obj = self.llm_client.generate(prompt)

        # Step 4: Collect retrieval record
        retrieved_docs = [r.chunk.document_name for r in results]
        retrieval_scores = [r.score for r in results]

        used_context = answer_obj.used_context

        # If LLM returned empty answer without context, use abstention
        if not used_context or not answer_obj.text.strip():
            abstention = "I don't have enough information in the knowledge base to answer this question."
            answer_text = abstention
        else:
            answer_text = answer_obj.text

        return {
            "question": question,
            "answer": answer_text,
            "retrieved_documents": retrieved_docs,
            "retrieval_scores": retrieval_scores,
            "used_context": used_context,
            "abstention": "I don't have enough information in the knowledge base to answer this question." if not used_context else "",
        }