# Contract: CLI

**Silent**: `telco-rag` —`goose`— UT about Level 1 querying and diagnostics.

**Implementation**: Typer CLI migrating the current `argparse` in `src/cli.py`.
Entry point `telco-rag = "src.cli:main"` in `pyproject.toml` is preserved so
`uv run telco-rag ...` works.

## Commands

### `telco-rag query "QUESTION" [OPTIONS]`

Ask a question and get a grounded answer. Replaces current positional-arg
CLI; the existing four-block output protocol is preserved (FR-013 / US-5).

Options:

| Flag | Type | Default | Meaning |
|------|------|---------|---------|
| `--top-k INT` | int | from config | Overrides retrieval depth for this run (current CLI stub; now actually honored). |
| `--debug-retrieval` | flag | off | Prints per-chunk diagnostics BEFORE generation (FR-007, US-2 / SC-003). |
| `--config PATH` | str | `config/settings.yaml` | Alternate settings file. |

Exit codes (kept from current implementation):

- `0` — success, or abstention (no context above threshold).
- `1` — usage/config error (empty question, invalid setting, missing corpus).
- `2` — runtime failure (embedding load failure, LLM unreachable — FR-017).

**Abstention**: when retrieval yields zero results above
`similarity_threshold`, print the Level 0 abstention message and exit `0`
(regression US-5). Debug mode still shows "zero results above threshold".

### `telco-rag ingest [OPTIONS]`

Ingest `data/documents/` → chunk → embed → store. **Resets the collection
first** (FR-016). Reports document count, chunk count, elapsed time.

| Flag | Type | Default | Meaning |
|------|------|---------|---------|
| `--config PATH` | str | `config/settings.yaml` | Alternate settings file. |

Exit codes: `0` success; `1` config error; `2` runtime failure. Corpus
missing/empty is a config error (exit `1`).

### `telco-rag evaluate [OPTIONS]`

Run retrieval over `data/evaluation/retrieval_questions.jsonl`, print
Recall@5, Precision@5, MRR for answerable questions plus the true-negative
count for unanswerable ones (FR-009 / FR-009a / SC-006).

| Flag | Type | Default | Meaning |
|------|------|---------|---------|
| `--k INT` | int | `5` | Evaluation depth for Recall@K / Precision@K. |
| `--dataset PATH` | str | `data/evaluation/retrieval_questions.jsonl` | Dataset override. |
| `--config PATH` | str | `config/settings.yaml` | Alternate settings file. |

Exit codes: `0` evaluation completed (regardless of scores); `1` config/
dataset error; `2` runtime failure.

## Output Protocol — Query Block Order

1. `Question:` block (unchanged).
2. `Retrieved Documents:` block — document name + `(score: 0.XX)` per result,
   or `(none)` (unchanged). In `--debug-retrieval` mode this block is
   expanded to print one line per chunk:
   `document_id :: chunk_id :: filename :: score`, e.g.
   `5g_packet_loss :: 5g_packet_loss#0008 :: 5g_packet_loss.md :: 0.84`
   (SC-003, FR-007).
3. `Answer:` block (unchanged; abstention text unless grounded).

Debug block is printed before any generation/LLM attempt (US-2).