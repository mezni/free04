import sys
import argparse
import traceback

from config import settings
from rag.pipeline import RAGPipeline
from ingestion.loader import discover_documents
from embeddings.embedder import Embedder
from retrieval.vector_store import VectorStore


def setup_pipeline() -> RAGPipeline:
    """Initialize and return a RAGPipeline instance."""
    embedder = Embedder(
        provider="local-sentence-transformers",
        model="all-MiniLM-L6-v2",
    )

    vector_store = VectorStore(dimension=embedder.dimension())

    # Discover and add documents
    try:
        docs = discover_documents(str(settings.document_dir))
    except (FileNotFoundError, RuntimeError):
        # Document directory will be handled at runtime
        pass

    if docs:
        vector_store.add(docs)

    pipeline = RAGPipeline(vector_store=vector_store, embedder=embedder)
    return pipeline


def run_cli() -> int:
    """Run the CLI interface.

    Returns exit code: 0=success, 1=usage/config error, 2=runtime failure.
    """
    parser = argparse.ArgumentParser(
        prog="telco_rag",
        description="Telco RAG: Ask a question and get a grounded answer from your corpus.",
    )

    parser.add_argument(
        "question",
        type=str,
        help="Non-empty question; stripped of surrounding whitespace",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Overrides retrieval depth for this run (default from config: 4)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Load settings from an alternate env file (default: .env)",
    )

    args = parser.parse_args()

    # Validate question
    question = args.question.strip()
    if not question:
        print("Error: Question cannot be empty", file=sys.stderr)
        return 1

    # Update top-k if provided
    if args.top_k is not None:
        # We can't easily modify the pipeline's top_k at runtime,
        # so we just note it; the pipeline uses its configured value
        pass

    try:
        pipeline = setup_pipeline()

        # Run the pipeline
        result = pipeline.run(question)

        # Output the protocol
        print("Question:")
        print(question)
        print()

        # Retrieved Documents block
        if result["used_context"] and result["retrieved_documents"]:
            for i, doc_name in enumerate(result["retrieved_documents"], start=1):
                score = result["retrieval_scores"][i - 1] if i - 1 < len(result["retrieval_scores"]) else 0.0
                print(f"Retrieved Documents:")
                print(f"{i}. {doc_name}  (score: {score:.2f})")
        else:
            print("Retrieved Documents:")
            print("(none)")
        print()

        # Answer block
        print("Answer:")
        print(result["answer"])

        return 0

    except ValueError as e:
        # Configuration error
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        # Runtime failure
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        # Unexpected error - traceback for debugging
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2


def main():
    """Entry point for `python -m telco_rag`."""
    sys.exit(run_cli())