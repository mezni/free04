"""Run all custom tests to verify implementation."""

import sys
import os

# Set required env vars FIRST
os.environ.setdefault("LLM_BASE_URL", "http://localhost.test")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("CHUNK_SIZE", "500")
os.environ.setdefault("CHUNK_OVERLAP", "50")
os.environ.setdefault("TOP_K", "4")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tests"))


def run_vector_store_tests():
    """Run vector store tests."""
    from tests.test_vector_store import (
        test_vector_store_add_and_search,
        test_vector_store_top_k_limit,
        test_vector_store_empty,
        test_vector_store_descending_order,
        test_vector_store_dimension_required,
        test_vector_store_single_chunk,
    )
    print("Vector store tests:")
    test_vector_store_add_and_search()
    print("  add_search: PASS")
    test_vector_store_top_k_limit()
    print("  top_k: PASS")
    test_vector_store_empty()
    print("  empty: PASS")
    test_vector_store_descending_order()
    print("  descending: PASS")
    test_vector_store_dimension_required()
    print("  dimension: PASS")
    test_vector_store_single_chunk()
    print("  single: PASS")


def run_retriever_tests():
    """Run retriever tests."""
    from tests.test_retriever import (
        test_retriever_basic,
        test_retriever_top_k,
        test_retriever_result_types,
        test_retriever_descending_scores,
        test_retriever_rank_assignment,
    )
    print("Retriever tests:")
    test_retriever_basic()
    print("  basic: PASS")
    test_retriever_top_k()
    print("  top_k: PASS")
    test_retriever_result_types()
    print("  result_types: PASS")
    test_retriever_descending_scores()
    print("  descending: PASS")
    test_retriever_rank_assignment()
    print("  rank: PASS")


def run_prompt_tests():
    """Run prompt tests."""
    from tests.test_prompt import (
        test_build_prompt_with_context,
        test_build_prompt_without_context,
        test_make_prompt_from_results,
        test_prompt_system_instruction,
    )
    print("Prompt tests:")
    test_build_prompt_with_context()
    print("  with_context: PASS")
    test_build_prompt_without_context()
    print("  without_context: PASS")
    test_make_prompt_from_results()
    print("  make_prompt: PASS")
    test_prompt_system_instruction()
    print("  system_instruction: PASS")


def run_pipeline_tests():
    """Run pipeline tests."""
    from tests.test_rag_pipeline import (
        test_pipeline_abstention_no_chunks,
        test_pipeline_with_mocked_llm,
        test_pipeline_abstention_on_empty_answer,
        test_pipeline_top_k_limit,
    )
    print("Pipeline tests:")
    test_pipeline_abstention_no_chunks()
    print("  abstention_no_chunks: PASS")
    test_pipeline_with_mocked_llm()
    print("  mocked_llm: PASS")
    test_pipeline_abstention_on_empty_answer()
    print("  empty_answer: PASS")
    test_pipeline_top_k_limit()
    print("  top_k: PASS")


def run_cli_output_tests():
    """Run CLI output tests."""
    from tests.test_cli_output import (
        test_cli_protocol_four_blocks,
        test_cli_retrieved_doc_format,
        test_cli_abstention_format,
    )
    print("CLI output tests:")
    test_cli_protocol_four_blocks()
    print("  protocol: PASS")
    test_cli_retrieved_doc_format()
    print("  format: PASS")
    test_cli_abstention_format()
    print("  abstention: PASS")


if __name__ == "__main__":
    run_vector_store_tests()
    print()
    run_retriever_tests()
    print()
    run_prompt_tests()
    print()
    run_pipeline_tests()
    print()
    run_cli_output_tests()
    print()
    print("=" * 40)
    print("ALL TESTS PASSED SUCCESSFULLY")