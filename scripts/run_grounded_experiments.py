"""Run the US6 prompt-strategy experiments (T036; research R8, FR-023).

Usage (from repo root):
  uv run python scripts/run_grounded_experiments.py
    [--dataset data/evaluation/grounded_answers.jsonl]
    [--oracle copy|llm]          (copy = deterministic extractive, FR-022)
    [--retriever ground-truth|store]
    [--out docs/levels/level-02-grounded-rag/experiments.md]

- `--oracle copy` (default) uses CopyOracle: deterministic, no LLM, CI-safe.
- `--oracle llm` swaps in the settings-configured LLM + StructuredJudge and
  needs LLM_BASE_URL/LLM_API_KEY/LLM_MODEL (see quickstart.md).
- `--retriever ground-truth` (default) fetches each case's relevant chunks
  from data/documents; `--retriever store` uses the live Chroma index.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from domain import Evidence  # noqa: E402


def load_cases(dataset: Path):
    from evaluation.dataset import load_grounded_cases

    return load_grounded_cases(dataset)


def ground_truth_evidence_factory():
    """A case -> evidence mapper from the corpus (no embeddings, no store)."""
    from config import settings
    from grounding.evidence_builder import build_evidence
    from ingestion.chunker import chunk_document
    from ingestion.loader import discover_documents

    docs = {d.document_id: d for d in discover_documents(settings.document_dir)}
    cs = int(getattr(settings, "chunk_size", 500))
    co = int(getattr(settings, "chunk_overlap", 50))
    chunk_index: dict[str, str] = {}
    for document in docs.values():
        for c in chunk_document(document, cs, co):
            chunk_index[c.chunk_id] = c.content

    def evidence_for(case):
        target_ids = case.relevant_chunks or []
        if not target_ids and case.relevant_documents:
            for doc in case.relevant_documents:
                target_ids += [cid for cid in chunk_index if cid.startswith(doc + "#")]
        if not target_ids:
            return []
        from domain import Chunk, RetrievalResult

        results = [
            RetrievalResult(
                chunk=Chunk(
                    chunk_id=cid,
                    content=chunk_index[cid],
                    document_id=cid.split("#")[0],
                    document_name=cid.split("#")[0] + ".md",
                    source=f"data/documents/{cid.split('#')[0]}.md",
                    chunk_index=int(cid.split("#")[1]),
                ),
                score=0.9,
                rank=rank,
            )
            for rank, cid in enumerate(sorted(target_ids), start=1)
            if cid in chunk_index
        ]
        return build_evidence(results)

    return evidence_for


def store_evidence_factory():
    """A case -> evidence mapper through the real retrieval index."""
    from cli import setup_pipeline
    from grounding.evidence_builder import build_evidence

    pipeline = setup_pipeline()

    def evidence_for(case):
        results = pipeline.retrieve(case.question, top_k=getattr(pipeline, "top_k", 4))
        return build_evidence(results)

    return evidence_for


class PromptOracle:
    """LLM-backed generator for live experiment runs (isolated; FR-022)."""

    def __init__(self, strategy: str) -> None:
        from config import settings
        from generation.llm import LLMClient

        self.strategy = strategy
        self.llm = LLMClient(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )

    def generate(self, question: str, evidence: list[Evidence]):
        from generation.generator import parse_grounded_answer
        from generation.prompt import build_strategy_prompt

        prompt = build_strategy_prompt(self.strategy, question, evidence)
        raw = self.llm.generate_json(prompt)
        return parse_grounded_answer(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/evaluation/grounded_answers.jsonl")
    parser.add_argument("--oracle", choices=("copy", "llm"), default="copy")
    parser.add_argument("--retriever", choices=("ground-truth", "store"), default="ground-truth")
    parser.add_argument("--out", default="docs/levels/level-02-grounded-rag/experiments.md")
    args = parser.parse_args()

    from evaluation.experiments import (
        AllStrategies,
        CopyOracle,
        format_run,
        run_strategy,
    )
    from evaluation.groundedness import StructuredJudge

    dataset = Path(args.dataset)
    cases = load_cases(dataset)
    evidence_for = (
        store_evidence_factory() if args.retriever == "store" else ground_truth_evidence_factory()
    )

    oracle = CopyOracle() if args.oracle == "copy" else None
    judge = None
    if args.oracle == "llm":
        oracle = PromptOracle("D")  # replaced per-strategy below
        judge = StructuredJudge(
            llm_client=oracle.llm,
        )
        # For live runs each strategy needs its own builder: scope judge+oracle
        # per strategy below.
        oracle = None

    lines = [
        "# Level 2 Prompt-Strategy Experiments (US6, T036)",
        "",
        "Method: strategies A-D scored over `data/evaluation/grounded_answers.jsonl` "
        "with the five answer metrics (SC-009). Deterministic run = `CopyOracle` "
        "(extractive, no LLM; FR-022). Live run = settings LLM + StructuredJudge.",
        "",
        f"- dataset: `{args.dataset}`",
        f"- retriever: `{args.retriever}` (ground-truth = the case's own relevant chunks)",
        f"- oracle: `{'copy (deterministic, FR-022)' if args.oracle == 'copy' else 'llm (live)'}`",
        "",
    ]

    for strategy in AllStrategies:
        if args.oracle == "llm":
            run = run_strategy(strategy, cases, evidence_for, PromptOracle(strategy), judge)
        else:
            run = run_strategy(strategy, cases, evidence_for, oracle)
        block = format_run(strategy, run, str(dataset))
        lines.append(block[0])
        lines.extend(block[1:])
        lines.append("")
        print("\n".join(block))
        print()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
