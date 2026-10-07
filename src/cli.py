"""Telco RAG CLI (Typer; contracts/CLI.md, constitution XII).

Commands:
  ingest   — reset + rebuild the ChromaDB collection from data/documents/
  query    — retrieve + generate a grounded answer (or diagnostics only with
             --debug-retrieval; FR-007 US2)
  evaluate — retrieval metrics (added in US4)

Exit codes: 0 success/abstention, 1 usage/config, 2 runtime failure (FR-017).
"""

import time
import traceback
from pathlib import Path
from typing import Annotated

import typer

from config import settings
from domain import StructuredOutputError
from embeddings.embedder import Embedder
from evaluation.answer_metrics import EvaluationOutcome
from grounding.evidence_builder import build_evidence
from ingestion.chunker import chunk_document
from ingestion.loader import discover_documents
from rag.pipeline import RAGPipeline
from retrieval.vector_store import VectorStore

app = typer.Typer(
    name="telco-rag",
    help="Telco RAG: ask a question and get a grounded answer from your corpus.",
)

ABSTENTION = "I don't have enough information in the knowledge base to answer this question."


def setup_pipeline() -> RAGPipeline:
    """Initialize and return a RAGPipeline instance tied to the ChromaDB store."""
    embedder = Embedder(
        provider=settings.embedding_provider,
        model=settings.embedding_model,
    )

    vector_store = VectorStore(
        persist_directory=settings.vector_db_path,
        collection_name=settings.collection,
        dimension=embedder.dimension(),
    )

    return RAGPipeline(
        vector_store=vector_store,
        embedder=embedder,
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
    )


def _print_retrieved_evidence(results) -> None:
    """Print the Retrieved Evidence block from raw retrieval results (FR-014)."""
    print("Retrieved Evidence:")
    evidence = build_evidence(results)
    if not evidence:
        print("(none — nothing above similarity threshold)")
        return
    for e in evidence:
        text = e.text[:120].replace("\n", " ").strip()
        print(f"{e.evidence_id} | {e.document_id} | {e.chunk_id} | score {e.retrieval_score:.2f}")
        print(f"  {text}")
    print()


def _print_grounding(result: dict) -> None:
    """Print the full grounded pipeline path (contracts/cli-grounded-output.md §3)."""
    evidence = result.get("evidence", [])
    grounded = result.get("grounded_answer")
    validation = result.get("citation_validation", [])
    decision = result.get("evidence_sufficiency")

    print("Retrieved Evidence:")
    if not evidence:
        print("(none — nothing above similarity threshold)")
    else:
        for e in evidence:
            text = e.text[:120].replace("\n", " ").strip()
            print(
                f"{e.evidence_id} | {e.document_id} | {e.chunk_id} | score {e.retrieval_score:.2f}"
            )
            print(f"  {text}")
    print()

    if decision is not None:
        if decision.sufficient:
            print(
                f"Evidence sufficiency: SUFFICIENT "
                f"(count={decision.evidence_count}, mean_score={decision.mean_score:.2f})"
            )
        else:
            print(f"Evidence sufficiency: INSUFFICIENT ({decision.reason})")
    else:
        print("Evidence sufficiency: (not assessed)")
    print()

    print("Generated Answer:")
    print(grounded.answer if grounded is not None else result.get("answer", ""))
    print()

    id_map = {(e.document_id, e.chunk_id): e.evidence_id for e in evidence}
    citations = grounded.citations if grounded is not None else []
    print("Citations:")
    if citations:
        for c in citations:
            eid = id_map.get((c.document_id, c.chunk_id), "?")
            print(f"[{c.document_id}:{c.chunk_id}]  (evidence {eid})")
    else:
        print("(none)")
    print()

    print("Citation Validation:")
    valid = [v for v in validation if v.is_valid]
    if not validation:
        print("PASS — no citations")
    elif len(valid) == len(validation):
        print("PASS")
    else:
        print(f"FAIL ({len(validation) - len(valid)} invalid)")
        for v in validation:
            if not v.is_valid:
                print(f"  [{v.citation.document_id}:{v.citation.chunk_id}] {v.status} — {v.detail}")
    print()

    conflicts = list(result.get("conflicts", []))
    print("Conflicts:")
    if conflicts:
        for note in conflicts:
            print(f"  {note.description}")
            for c in note.positions:
                print(f"    [{c.document_id}:{c.chunk_id}]")
    else:
        print("(none)")
    print()

    print("Groundedness:")
    print("(not evaluated — run `evaluate --answers`)")
    print()

    print("Final Response:")
    print(result.get("answer", ""))


@app.command()
def ingest() -> int:
    """Reset the collection and ingest the document corpus (FR-016)."""
    embedder = Embedder(
        provider=settings.embedding_provider,
        model=settings.embedding_model,
    )

    store = VectorStore(
        persist_directory=settings.vector_db_path,
        collection_name=settings.collection,
        dimension=embedder.dimension(),
    )

    started = time.time()
    docs = discover_documents(str(settings.document_dir))
    print(f"Discovered {len(docs)} documents from {settings.document_dir}")

    # Reset once so the collection reflects only the current configuration.
    store.reset()

    total_chunks = 0
    for doc in docs:
        chunks = chunk_document(
            doc,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        embeddings = embedder.embed_batch([c.content for c in chunks])
        store.add(chunks, embeddings)
        total_chunks += len(chunks)

    elapsed = time.time() - started
    print(
        f"Ingested {total_chunks} chunks into collection '{settings.collection}' in {elapsed:.2f}s"
    )
    return 0


@app.command()
def query(
    question: Annotated[str, typer.Argument(help="Non-empty question")],
    top_k: Annotated[
        int | None,
        typer.Option(help="Override retrieval depth (default from config)"),
    ] = None,
    debug_retrieval: Annotated[
        bool,
        typer.Option(help="Show per-chunk retrieval diagnostics (FR-007)"),
    ] = False,
    debug_grounding: Annotated[
        bool,
        typer.Option(help="Show the full grounded pipeline path (FR-014)"),
    ] = False,
) -> int:
    """Ask a question and get a grounded answer."""
    question = question.strip()
    if not question:
        typer.echo("Error: Question cannot be empty", err=True)
        raise typer.Exit(code=1)

    pipeline = setup_pipeline()

    # Step 1: Retrieve (independent of generation — FR-007/US2).
    try:
        results = pipeline.retrieve(question, top_k=top_k)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2) from e

    print("Question:")
    print(question)
    print()

    # Diagnostic / retrieved-documents block.
    if debug_retrieval:
        if results:
            print("Retrieved Documents:")
            for r in results:
                text = r.chunk.content[:120].replace("\n", " ").strip()
                print(
                    f"{r.chunk.document_id} :: {r.chunk.chunk_id} :: "
                    f"{r.chunk.document_name} (score: {r.score:.2f}) :: {text}"
                )
        else:
            print(
                f"Retrieved Documents: (none — nothing above "
                f"similarity_threshold={settings.similarity_threshold})"
            )
        print()

        # Diagnostics-only mode: retrieval is inspectable without the LLM (US2).
        print("Answer:")
        print("(diagnostics only — LLM not invoked)")
        return 0

    # Debug-grounding mode (FR-014): observe every grounding stage.
    if debug_grounding:
        try:
            result = pipeline.run_grounded(question, top_k=top_k)
        except StructuredOutputError as e:
            _print_retrieved_evidence(results)
            typer.echo(f"Error: structured output invalid: {e}", err=True)
            raise typer.Exit(code=2) from e
        except RuntimeError as e:
            # Contract §3: evidence is exposed before the error.
            _print_retrieved_evidence(results)
            typer.echo(f"Error: generation backend unavailable: {e}", err=True)
            raise typer.Exit(code=2) from e
        _print_grounding(result)
        return 0

    # Normal query: print retrieved docs after generation, or via fallback
    # retrieve on LLM failure (FR-017) so results are shown before the error.
    try:
        result = pipeline.run(question, top_k=top_k)
    except StructuredOutputError as e:
        # Contract §5: malformed structured output is reported, never shown
        # as an answer (grounded-answer-schema rule 1).
        if results:
            print("Retrieved Documents:")
            for i, r in enumerate(results, start=1):
                print(f"{i}. {r.chunk.document_name}  (score: {r.score:.2f})")
        else:
            print("Retrieved Documents:")
            print("(none)")
        print()
        typer.echo(f"Error: structured output invalid: {e}", err=True)
        raise typer.Exit(code=2) from e
    except RuntimeError as e:
        fallback = pipeline.retrieve(question, top_k=top_k)
        if fallback:
            print("Retrieved Documents:")
            for i, r in enumerate(fallback, start=1):
                print(f"{i}. {r.chunk.document_name}  (score: {r.score:.2f})")
        else:
            print("Retrieved Documents:")
            print("(none)")
        print()
        typer.echo(f"Error: generation backend unavailable: {e}", err=True)
        raise typer.Exit(code=2) from e

    if result["retrieved_documents"]:
        print("Retrieved Documents:")
        for i, (doc, score) in enumerate(
            zip(result["retrieved_documents"], result["retrieval_scores"], strict=True), start=1
        ):
            print(f"{i}. {doc}  (score: {score:.2f})")
    else:
        print("Retrieved Documents:")
        print("(none)")
    print()

    grounded = result.get("grounded_answer")
    abstained = result.get("abstained", bool(grounded and grounded.abstained))

    # Citation validation banner (contract §1): invalid citations are
    # reported before the answer, never silently dropped. Abstention takes
    # precedence over citations (US3, T022).
    validation = result.get("citation_validation") or []
    invalid = [v for v in validation if not v.is_valid]
    if invalid and not abstained:
        print(f"Citation validation: FAIL ({len(invalid)} invalid)")
        for v in invalid:
            print(f"  [{v.citation.document_id}:{v.citation.chunk_id}] {v.status}")
        print()

    print("Answer:")
    print(result["answer"])

    # Sources block (FR-013, contracts/cli-grounded-output.md §1): only
    # VALID citations; abstained answers print no Sources (T022).
    if not abstained:
        valid = [v.citation for v in validation if v.is_valid]
        if valid:
            print()
            print("Sources:")
            for c in valid:
                print(f"[{c.document_id}:{c.chunk_id}]")

    # Conflicts surfaced, never merged (FR-019, Principle XXIII).
    conflicts = list(result.get("conflicts", []))
    if conflicts and not abstained:
        print()
        for note in conflicts:
            positions = ", ".join(f"[{c.document_id}:{c.chunk_id}]" for c in note.positions)
            print(f"Conflicts: {note.description} ({positions})")
    return 0


def _run_answer_outcome(case, pipeline, judge, top_k: int) -> EvaluationOutcome:
    """Run one grounded case through the pipeline and produce its outcome.

    Citation validity comes from the pipeline's citation_validation; claim
    support comes the judge (lexical when judge is None) — no extra network.
    """
    from evaluation.groundedness import evaluate_claim, extract_claims

    result = pipeline.run_grounded(case.question, top_k=top_k)
    answer = str(result.get("answer", ""))
    abstained = bool(result.get("abstained", False))
    # Abstained answers carry no factual claims to ground (US6/T036).
    claims = extract_claims(answer) if not abstained else []
    verdicts = [
        evaluate_claim(claim, list(result.get("evidence", [])), judge=judge) for claim in claims
    ]
    return EvaluationOutcome(
        case=case,
        answer=answer,
        abstained=abstained,
        citation_validation=list(result.get("citation_validation", [])),
        grounding_verdicts=verdicts,
    )


def evaluate_answers_cli(
    cases,
    pipeline,
    judge,
    top_k: int,
    path,
) -> int:
    """Run the answer evaluation layer (contracts/cli-grounded-output.md §4).

    Deterministic aside from pipeline LLM/embedding calls; retrieval and
    answer layers remain separately labeled (Principle XXII).
    """
    from evaluation.answer_metrics import evaluate_answers
    from evaluation.dataset import grounded_missing_docs

    missing = grounded_missing_docs(cases)
    if missing:
        print(f"! corpus missing docs referenced by dataset: {', '.join(missing)}")

    outcomes = [_run_answer_outcome(case, pipeline, judge, top_k) for case in cases]
    report = evaluate_answers(outcomes)
    # The answer layer header carries its own counts; '(dataset: ...)' keeps
    # the run reproducible without mixing into the retrieval-same line.
    print("(dataset: " + str(path) + ")")
    for line in report.lines():
        print(line)
    return 0


def _answer_judge(pipeline):
    """Groundedness judge wired to the pipeline's LLM (isolated FR-022)."""
    from evaluation.groundedness import StructuredJudge

    return StructuredJudge(llm_client=pipeline.llm_client)


@app.command()
def evaluate(
    k: Annotated[
        int | None,
        typer.Option(help="Evaluation depth (Recall@K/Precision@K)"),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option(
            help="Path to the evaluation questions (or grounded-answers with --answers) dataset"
        ),
    ] = None,
    threshold: Annotated[
        float | None,
        typer.Option(help="Overrides retrieval similarity_threshold (FR-006)"),
    ] = None,
    answers: Annotated[
        bool,
        typer.Option(help="Evaluate grounded answers over the grounded dataset (FR-015)"),
    ] = False,
    answers_dataset: Annotated[
        str | None,
        typer.Option(help="Path to the grounded-answers dataset (with --answers)"),
    ] = None,
) -> int:
    """Run retrieval evaluation (US4) and answer evaluation with --answers (FR-015)."""
    from evaluation.dataset import is_grounded_dataset

    effective = answers_dataset if answers_dataset else dataset
    ground_path = Path(answers_dataset) if answers_dataset else None
    answer_layer = answers or (effective is not None and is_grounded_dataset(Path(effective)))

    path = (
        ground_path
        if ground_path is not None
        else (Path(effective) if effective is not None else Path(settings.eval_dataset_path))
    )
    k_val = k or settings.eval_k
    threshold_val = threshold if threshold is not None else settings.similarity_threshold

    if answer_layer:
        from evaluation.dataset import load_grounded_cases

        answer_path = path or Path(settings.grounded_dataset_path)
        try:
            cases = load_grounded_cases(answer_path)
        except FileNotFoundError:
            typer.echo(f"Error: evaluation dataset not found: {answer_path}", err=True)
            raise typer.Exit(code=1) from None

        from evaluation.groundedness import StructuredJudge

        pipeline = setup_pipeline()
        return evaluate_answers_cli(
            cases,
            pipeline,
            StructuredJudge(llm_client=pipeline.llm_client),
            k_val,
            answer_path,
        )

    from evaluation.dataset import load_questions, missing_docs
    from evaluation.metrics import evaluate_retrieval

    try:
        questions = load_questions(path)
    except FileNotFoundError:
        typer.echo(f"Error: evaluation dataset not found: {path}", err=True)
        raise typer.Exit(code=1) from None

    embedder = Embedder(
        provider=settings.embedding_provider,
        model=settings.embedding_model,
    )
    store = VectorStore(
        persist_directory=settings.vector_db_path,
        collection_name=settings.collection,
        dimension=embedder.dimension(),
    )
    from retrieval.retriever import Retriever

    retriever = Retriever(store, embedder)

    report = evaluate_retrieval(questions, retriever, k_val, similarity_threshold=threshold_val)

    answerable = [q for q in questions if not q.is_unanswerable]
    unanswerable = [q for q in questions if q.is_unanswerable]

    # Docs referenced by the dataset but absent from the corpus => reported
    # as misses, never a crash (Edge Case, evaluation contract).
    missing = missing_docs(questions)
    if missing:
        print(f"! corpus missing docs referenced by dataset: {', '.join(missing)}")
    print(
        f"Evaluation: {len(answerable)} answerable, {len(unanswerable)} unanswerable (dataset: {path})"
    )
    print(f"Recall@{k_val}:   {report['recall_at_k']:.2f}")
    print(f"Precision@{k_val}: {report['precision_at_k']:.2f}")
    print(f"MRR:         {report['mrr']:.2f}")
    print(
        f"Unanswerable: {len(unanswerable)} questions · "
        f"true-negatives {report['true_negatives']} · false-positives {report['false_positives']}"
    )
    print(
        "Per-question: "
        + " · ".join(
            f"{pid} (r={pv['recall']:.2f}/p={pv['precision']:.2f}/rr={pv['rr']:.2f})"
            for pid, pv in report["per_question"].items()
        )
    )
    return 0


def main():
    """Entry point for the `telco-rag` console script (exit code protocol)."""
    try:
        app()
    except typer.Exit as e:
        raise SystemExit(e.exit_code) from None
    except Exception:
        traceback.print_exc()
        raise SystemExit(2) from None
