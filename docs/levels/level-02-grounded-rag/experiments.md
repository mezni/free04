# Level 2 Prompt-Strategy Experiments (US6, T036)

Method: strategies A-D scored over `data/evaluation/grounded_answers.jsonl` with the five answer metrics (SC-009). Determinism: `CopyOracle` (extractive, no LLM; FR-022) so the measurement path is exercised reproducibly; a live-LLM rerun only swaps the oracle (`--oracle llm` in `scripts/run_grounded_experiments.py`).

Two retrieval backends are recorded:

- **hermetic baseline**: `--retriever ground-truth` — each case feeds its own
  `relevant_chunks` from `data/documents/` (no embeddings, no store). This is
  the CI-runnable, byte-reproducible record.
- **live-index run**: `--retriever store` — real Chroma index over
  `data/documents/` (10 docs, 20 chunks) with `BAAI/bge-small-en-v1.5`.
  Recorded 2026-10-07 after `uv run telco-rag ingest`.

## Summary

| Strategy | Retrieval | Correctness | Abstention acc | Citation validity | Citation completeness | S/U/P |
|----------|-----------|-------------|----------------|-------------------|------------------------|-------|
| A | ground-truth | 0.84 | 1.00 | 1.00 | 1.00 | 19/0/0 |
| B | ground-truth | 0.84 | 1.00 | 1.00 | 1.00 | 19/0/0 |
| C | ground-truth | 0.84 | 1.00 | 1.00 | 1.00 | 19/0/0 |
| D | ground-truth | 0.84 | 1.00 | 1.00 | 1.00 | 19/0/0 |
| A | store | 0.64 | 0.75 | 1.00 | 1.00 | 29/0/0 |
| B | store | 0.64 | 0.75 | 1.00 | 1.00 | 29/0/0 |
| C | store | 0.64 | 0.75 | 1.00 | 1.00 | 29/0/0 |
| D | store | 0.64 | 0.75 | 1.00 | 1.00 | 29/0/0 |

**Winning strategy: none — all four strategies tie.** Strategy deltas are
0.00 on every measure in both runs, which is the expected reproducibility
result: A-D differ only in LLF-facing instruction emphasis, which a scripted
generator cannot exercise. The score differences that *do* appear come from
retrieval/case content, not the prompt — the exact separation the two-layer
evaluation enforces (Principle XXII). Any real A vs D delta must be measured
with `--oracle llm` and recorded here as evidence, never asserted (R8).

**Retrieval beats prompt.** The store run drops correctness 0.84 → 0.64 and
abstention accuracy 1.00 → 0.75 purely because the index returns the 5G-speed
chunks for the unanswerable Japan case (`average_5g_speed_japan`): the
semantic neighbors exist in the corpus even though no Japan figure does. That
is a retrieval-vs-answer-layer distinction, not a prompt effect (FR-018;
see `lessons-learned.md` §7).

**Hallucination-test outcomes:** 0 unsupported claims in every run —
CopyOracle emits only evidence-derived sentences, so the lexical jury finds
them supported. Anti-hallucination guarantees (unknown-doc / unretrieved
chunk / missing-citation rejection, abstention on no/insufficient evidence)
live in `test_citations.py`, `test_regressions_level2.py` and
`test_rag_pipeline.py` (green).

**Conflict-test outcomes:** the `expected_5g_speed_conflict` case was answered
with both conflicting chunks cited verbatim (2/2 VALID; correctness 0.8
ground-truth / 0.7 store, see per-strategy detail). Conflict *reporting* is a
generation-time behavior covered by FakeLLM scenarios (`CONFLICT_PAYLOAD` in
`test_rag_pipeline.py`, `test_conflicting_evidence_is_reported`); a live model
is required to measure how often strategy D actually emits a `conflicts`
block.

## How to rerun

```bash
uv run telco-rag ingest                                   # needs embedding model download once
uv run python scripts/run_grounded_experiments.py          # hermetic baseline (ground-truth)
uv run python scripts/run_grounded_experiments.py --retriever store
uv run python scripts/run_grounded_experiments.py --oracle llm --retriever store  # live, overwrites this file
```

`experiments.md` is overwritten by the last run; keep the two recorded runs by
re-running the commands above. Treat a live run as the authoritative SC-009
record and update `Summary` accordingly.

## Per-strategy detail — hermetic baseline (ground-truth retrieval)

### Strategy A
- correctness=0.84 abstention_acc=1.00 citation_validity=1.00 citation_completeness=1.00
- groundedness: supported 19 / unsupported 0 / partially 0
- packet_loss_steps: 1.0 correct, citations 2/2 valid, grounded 7/0/0
- average_5g_speed_japan: 1.0 (abstain), no citations, no claims
- lte_slow_troubleshooting: 0.6 correct, citations 2/2 valid, grounded 7/0/0
- expected_5g_speed_conflict: 0.8 correct, citations 2/2 valid, grounded 5/0/0

### Strategies B, C, D
Identical to A (all measures match to 2dp) — see Summary table.

## Per-strategy detail — live-index run (store retrieval, 2026-10-07)

### Strategy A
- correctness=0.64 abstention_acc=0.75 citation_validity=1.00 citation_completeness=1.00
- groundedness: supported 29 / unsupported 0 / partially 0
- packet_loss_steps: 1.0 correct, citations 2/2 valid, grounded 9/0/0
- average_5g_speed_japan: 0.0 correct, answered instead of abstaining, 2/2 valid, grounded 5/0/0
- lte_slow_troubleshooting: 0.8 correct, citations 2/2 valid, grounded 10/0/0
- expected_5g_speed_conflict: 0.7 correct, citations 2/2 valid, grounded 5/0/0

### Strategies B, C, D
Identical to A (all measures match to 2dp) — see Summary table.