# Quickstart: Validating Level 0 — Naive RAG Baseline

**Date**: 2026-10-06
**Purpose**: Runnable validation guide proving the feature works end to end.
It references the contracts (behaviour) and data model (entities) instead of
duplicating them. Implementation details live in `tasks.md` (created by
`/speckit.tasks`).

## Prerequisites

- Python 3.12+ on the local machine.
- Network access once to download the embedding model
  (`all-MiniLM-L6-v2`, ~91 MB); offline afterwards.
- Access to an OpenAI-compatible chat-completions endpoint
  (`LLM_BASE_URL` + optional `LLM_API_KEY`). Any compatible local or hosted
  server works; see `contracts/config.md` provider contract.

## Setup

```bash
git clone <repo> && cd telco-rag
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env       # then edit .env with LLM_BASE_URL / LLM_MODEL / LLM_API_KEY
python -m telco_rag --help
```

Expected outcome: `--help` prints the CLI usage (see `contracts/cli.md`),
proving the package, config loader, and CLI entry point are installed.

## Run the test suite

```bash
pytest
```

Expected outcome: all tests pass. The suite covers the five component areas
required by the spec (loader, chunker, retriever, prompt builder,
end-to-end pipeline) — 100% green on a fresh checkout (spec SC-005). The
end-to-end test uses mocked embedding and LLM clients (no network, no real
model) as required by FR-012.

## Ask a covered question

```bash
python -m telco_rag "How do I troubleshoot 5G packet loss?"
```

Expected outcome (spec SC-001 / SC-003): within 10 seconds the CLI prints
the Question, at least one `Retrieved Documents` line with a source name and
score (`5g_packet_loss.md` expected for this question given the corpus in
section 6 of the Level 0 plan), and a grounded `Answer`. Retrieval is always
inspectable.

## Ask an unknown question (abstention)

```bash
python -m telco_rag "What is the procedure for satellite network handover?"
```

Expected outcome (spec SC-002): the response explicitly states there is not
enough information — no fabricated satellite procedure. Repeat this query a
few times; at least 9 of 10 attempts must abstain to meet SC-002.

## Call matrix (spec edge cases → validation scenario)

| Case | Command / action | Expected outcome |
|------|------------------|------------------|
| Empty question | `python -m telco_rag ""` | Exit 1, usage error (cli contract) |
| Missing setting | unset `LLM_BASE_URL`, then query | Exit 1, error names the variable (config contract) |
| Empty/nonexistent corpus | `DOCUMENT_DIR=/tmp/nope` then query | Exit 1, error names the directory |
| Synonym/ambiguous query | "What to do when my phone loses signal at work?" | Runs; observe retrieval, scores, and answer; record in baseline |
| Noisy/irrelevant query | any question with extra filler | Runs; answer stays corpus-grounded |
| Multi-doc relevance | "How do I handle a network incident that may breach SLA?" | Multiple sources + scores shown |
| Repeated question | run twice | Same retrieved documents, scores stable within tolerance |

## Baseline experiments

Per the Level 0 plan (§19, §20), run this fixed set and record each outcome
as a Baseline Record (fields in `data-model.md`) into
`docs/levels/level-00-naive-rag/baseline.md`:

```text
Q1  How do I troubleshoot 5G packet loss?
Q2  What are the common causes of high latency?
Q3  How do I activate a SIM?
Q4  What is the enterprise SLA for broadband?
Q5  How do I escalate a network incident?
Q6  What is the procedure for something that does not exist
    in the knowledge base?
Q7  What is the procedure for satellite network handover?   (deliberate failure)
```

For each: record question, retrieved documents, retrieval scores, answer,
observations (good/bad retrieval, hallucination, abstention). Finish with
the known-limitations list (plan §21) — this is the Level 1 input
(FR-016).

## Definition of Done (quick check)

The single command `python -m telco_rag "How do I troubleshoot 5G packet loss?"`
works end to end (plan §23), all the rows above behave as expected, tests
pass, and `docs/levels/level-00-naive-rag/baseline.md` contains Q1–Q7 with
observations and the limitations list.