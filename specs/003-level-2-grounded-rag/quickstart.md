# Quickstart Validation: Level 2 Grounded RAG

**Feature**: specs/003-level-2-grounded-rag
**Purpose**: end-to-end validation scenarios proving the grounded pipeline
works. Run from the repository root. This is a run/validate guide —
implementation details live in `tasks.md` (Phase 2).

## Prerequisites

- Python 3.12+, `uv` environment synced (`uv sync`)
- Corpus ingested: `uv run telco-rag ingest` (resets + rebuilds the
  ChromaDB collection from `data/documents/`)
- LLM credentials in `.env` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`)
  for scenarios that generate answers; unit tests need **no** network
- Existing suite green before starting: `uv run pytest`

## Scenario matrix

| # | Scenario | Command | Expected outcome |
|---|----------|---------|------------------|
| V1 | Grounded answer + sources | `uv run telco-rag query "What can cause packet loss on a 5G network?"` | `Answer:` followed by `Sources:` listing `[document_id:chunk_id]` pairs that appear in Retrieved Documents |
| V2 | Full grounding path observable | `uv run telco-rag query "..." --debug-grounding` | Blocks: Retrieved Evidence (EVIDENCE-nnn), Evidence sufficiency, Generated Answer, Citations, Citation Validation `PASS`, Conflicts, Final Response |
| V3 | Retrieval-only diagnostics unchanged | `uv run telco-rag query "..." --debug-retrieval` | Level 1 output only; no evidence/answer/citations blocks; LLM not invoked |
| V4 | Abstention on unknown question | `uv run telco-rag query "What is the average 5G speed in Japan?"` | Abstention message; no `Sources:`; exit 0 |
| V5 | Invalid citation rejected | covered by `uv run pytest tests/test_citations.py -q` | Nonexistent doc / invalid chunk / unretrieved chunk → rejected (SC-002: 100%) |
| V6 | Conflicting evidence surfaced | conflict case in `grounded_answers.jsonl` via evaluate + a manual query over conflict docs | Answer names differing sources; `Conflicts:` block non-empty; nothing silently merged |
| V7 | Retrieval metrics preserved | `uv run telco-rag evaluate` | `Recall@K`, `Precision@K`, `MRR` block present with unchanged meaning |
| V8 | Two-layer evaluation | `uv run telco-rag evaluate --answers` (or `--dataset data/evaluation/grounded_answers.jsonl`) | Separate labeled retrieval block **and** answer block: correctness, abstention accuracy, citation validity, citation completeness, groundedness counts |
| V9 | Full regression | `uv run pytest` | All Level 0/1 tests + 7 new Level 2 test modules pass (FR-022) |
| V10 | Static gates | `uv run ruff check . && uv run ruff format --check . && uv run mypy` | Clean |

## Validation commands (copy-paste)

```bash
# 0. baseline + static checks
uv run pytest -q
uv run ruff check . && uv run mypy

# 1. rebuild knowledge base
uv run telco-rag ingest

# 2. grounded answer with sources (V1)
uv run telco-rag query "What can cause packet loss on a 5G network?"

# 3. full grounding path (V2)
uv run telco-rag query "What can cause packet loss on a 5G network?" --debug-grounding

# 4. Level 1 diagnostics still independent (V3)
uv run telco-rag query "What can cause packet loss on a 5G network?" --debug-retrieval

# 5. abstention (V4)
uv run telco-rag query "What is the average 5G speed in Japan?"

# 6. evaluation: retrieval layer only (V7), then two layers (V8)
uv run telco-rag evaluate
uv run telco-rag evaluate --answers

# 7. targeted Level 2 suites (V5, V9)
uv run pytest tests/test_evidence.py tests/test_answer_schema.py \
  tests/test_citations.py tests/test_abstention.py tests/test_grounding.py \
  tests/test_answer_evaluation.py tests/test_rag_pipeline.py -q
```

## Expected results checklist

- [x] V1: every displayed source maps to a actually-retrieved chunk — covered by `test_run_grounded_builds_evidence_and_parses_answer` / CLI Sources filter (`VALID` only); live run needs LLM creds (recorded as blocked in T039 note below)
- [ ] V1 live: `uv run telco-rag query "What can cause packet loss on a 5G network?"` — requires `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` in `.env`
- [x] V2: every grounding block present; `Citation Validation: PASS` — `test_debug_grounding_prints_full_path`; live run needs LLM creds
- [ ] V2 live: `uv run telco-rag query "..." --debug-grounding` — requires LLM creds
- [x] V3: byte-level behavior of Level 1 diagnostics preserved (LLM not called) — executed for real on the rebuilt index: `--debug-retrieval` returned retrieved documents + `(diagnostics only — LLM not invoked)`
- [x] V4: abstains without fabricating an answer — `test_unknown_question_abstains` + `test_run_grounded_zero_results_abstains_without_generation`; live run needs LLM creds
- [ ] V4 live: `uv run telco-rag query "What is the average 5G speed in Japan?"` — requires LLM creds
- [x] V5: 100% of fabricated citations rejected (SC-002) — `uv run pytest tests/test_citations.py -q` → 11 passed
- [x] V6: conflict acknowledged, sources named, not merged (SC-008) — `test_hallucination_scenario_conflicting_evidence_is_reported` + `test_conflicting_evidence_is_reported`; live run needs LLM creds
- [ ] V6 live: manual query over the speed-conflict docs — requires LLM creds
- [x] V7: Recall@K / Precision@K / MRR still reported (SC-005) — executed for real over the rebuilt index: Recall@5 1.00, Precision@5 0.20, MRR 1.00
- [x] V8: five answer metrics reported for every case, separate layer (SC-004) — `test_evaluate_answers_cli_prints_answer_layer` + `test_evaluate_routes_grounded_dataset_to_answer_layer`; real answer layer exercised deterministically via `scripts/run_grounded_experiments.py --retriever store` (see experiments.md); live `evaluate --answers` needs LLM creds
- [ ] V8 live: `uv run telco-rag evaluate --answers` — requires LLM creds
- [x] V9: full suite green incl. Level 0/1 regression (SC-006) — `uv run pytest -q` → 155 passed
- [x] V10: ruff + mypy clean — `uv run ruff check .` + `uv run mypy src` clean

> T039 validation-run note (2026-10-07): the deterministic/live-free scenarios
> (V3, V5, V7, V9, V10 and the answer-layer V8/V6 paths) were executed end-to-end
> against a freshly rebuilt Chroma index (`uv run telco-rag ingest`, 10 docs,
> 20 chunks, `BAAI/bge-small-en-v1.5`) and confirmed. Scenarios marked
> "requires LLM creds" (V1/V2/V4/V6/V8 live variants) could not be confirmed in
> this environment (no `LLM_BASE_URL`/`LLM_API_KEY`); their behavior is pinned
> by the named deterministic tests above and the recorded experiments in
> `experiments.md`. Re-run the marked commands with credentials in `.env` to
> complete the live confirmation.

## Experiments (manual, recorded — not part of the automated suite)

Per FR-023/SC-009, after the pipeline is green:

1. Run prompt strategies A (simple RAG), B (evidence-only),
   C (evidence-only + citations), D (evidence-only + citations +
   abstention) over `grounded_answers.jsonl`.
2. Record per-strategy: correctness, groundedness, citation validity,
   citation completeness, abstention accuracy in
   `docs/levels/level-02-grounded-rag/experiments.md`.
3. Answer the lessons-learned questions in
   `docs/levels/level-02-grounded-rag/lessons-learned.md`
   (unsupported-answer causes, high-score ≠ grounded, citation-invention
   rate, prompt-only effectiveness, false abstentions, incomplete
   citations, retrieval-vs-generation failure attribution).

## References

- Wire schema & validation rules: [`contracts/grounded-answer-schema.md`](./contracts/grounded-answer-schema.md)
- CLI output formats & exit codes: [`contracts/cli-grounded-output.md`](./contracts/cli-grounded-output.md)
- Entities & invariants: [`data-model.md`](./data-model.md)
- Decisions behind this design: [`research.md`](./research.md)
