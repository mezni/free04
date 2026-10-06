"""Deterministic tests for prompt building - must pass before implementation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generation.prompt import build_prompt, make_prompt_from_results


def test_build_prompt_with_context():
    """Test prompt building with retrieved context."""
    results = [
        type('obj', (object,), {
            'chunk': type('obj', (object,), {
                'chunk_id': 'doc1#0001',
                'content': '5G packet loss troubleshooting basics',
                'document_id': 'doc1',
                'document_name': '5g_packet_loss.md',
                'source': 'data/documents/5g_packet_loss.md',
            })(),
        })()
    ]

    prompt = build_prompt("How do I troubleshoot 5G packet loss?", results, use_context=True)

    assert "Question:" in prompt
    assert "Context:" in prompt or "Context" in prompt
    assert "5g_packet_loss.md" in prompt or "5G" in prompt
    assert "How do I troubleshoot 5G packet loss?" in prompt
    print("✓ Build prompt with context")


def test_build_prompt_without_context():
    """Test prompt building without retrieved context."""
    results = []

    prompt = build_prompt("How do I troubleshoot 5G packet loss?", results, use_context=False)

    assert "Question:" in prompt
    assert "Answer:" in prompt
    print("✓ Build prompt without context")


def test_make_prompt_from_results():
    """Test convenience function make_prompt_from_results."""
    results = [
        MagicMock(
            chunk=MagicMock(
                chunk_id='doc1#0001',
                content='test chunk content',
                document_id='doc1',
                document_name='5g_packet_loss.md',
                source='data/documents/5g_packet_loss.md',
            )
        )
    ]

    prompt = make_prompt_from_results("How do I troubleshoot 5G packet loss?", results)

    assert "Question:" in prompt
    assert "Context:" in prompt or "5G" in prompt
    assert "Answer:" in prompt
    print("✓ Make prompt from results")


def test_prompt_contains_question_and_context():
    """Test that prompt built from results contains question and context."""
    from unittest.mock import MagicMock

    results = [
        MagicMock(
            chunk=MagicMock(
                content='test context content that is long enough to be used',
                document_name='5g_packet_loss.md',
                source='data/documents/5g_packet_loss.md',
            )
        )
    ]

    prompt = make_prompt_from_results("How do I troubleshoot 5G packet loss?", results)

    assert "How do I troubleshoot 5G packet loss?" in prompt
    assert "test context content" in prompt
    print("✓ Prompt contains question and context")


if __name__ == "__main__":
    test_build_prompt_with_context()
    test_build_prompt_without_context()
    test_make_prompt_from_results()
    test_prompt_contains_question_and_context()
    print("✓ All prompt tests passed")