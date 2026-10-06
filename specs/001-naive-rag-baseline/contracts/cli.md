# Contract: CLI (User Interface)

**Feature**: Level 0 — Naive RAG Baseline
**Date**: 2026-10-06
**Constitution**: v1.0.0 (P XII CLI First)

The command-line interface is the only user-facing contract of Level 0. It
consumes a question and returns the inspection record defined by P VIII
(question, retrieved sources, scores, answer).

## Invocation

```bash
python -m telco_rag "How do I troubleshoot 5G packet loss?"
```

### Arguments

| Argument | Kind | Required | Default | Notes |
|----------|------|----------|---------|-------|
| `question` | positional text | yes | — | Non-empty question; stripped of surrounding whitespace |
| `--top-k` | int | no | from config (4) | Overrides retrieval depth for this run |
| `--config` | path | no | `.env` | Loads settings from an alternate env file |

`--help` and `--version` flags are supported.

## Stdout Protocol (text)

Successful run prints exactly four labelled blocks, in order:

```text
Question:
How do I troubleshoot 5G packet loss?

Retrieved Documents:
1. 5g_packet_loss.md  (score: 0.81)
2. noc_incident_procedure.md  (score: 0.64)

Answer:
...
```

Rules:

- `Retrieved Documents` block: one line per source, ranked, `name  (score: <0.00>)`.
- If fewer than K chunks exist, only the available sources are listed.
- `Answer` block: the model's answer text; trailing whitespace trimmed.
- Abstention (no retrieved context): the `Answer` block contains the exact
  insufficient-information sentence (see `contracts/config.md` prompt rules)
  and `Retrieved Documents` shows `(none)`.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success: answer (grounded or abstention) printed |
| 1 | Usage or configuration error (empty question, missing required setting, bad value, missing document directory) |
| 2 | Runtime failure during retrieval or generation (network timeout, provider error, embedding failure) |

Errors are written to stderr with a one-line message and exit code per the
table; the process never crashes with an unhandled traceback.

## Example: covered question

```text
$ python -m telco_rag "How do I troubleshoot 5G packet loss?"
Question:
How do I troubleshoot 5G packet loss?

Retrieved Documents:
1. 5g_packet_loss.md  (score: 0.81)

Answer:
Begin by checking the base station cell for RF interference...
```

## Example: unknown question (abstention)

```text
$ python -m telco_rag "What is the procedure for satellite network handover?"
Question:
What is the procedure for satellite network handover?

Retrieved Documents:
(none)

Answer:
I don't have enough information in the knowledge base to answer this question.
```

## Example: missing setting

```text
$ python -m telco_rag "What is 5G?"
Error: LLM_BASE_URL is not set. See .env.example.
$ echo $?
1
```

## Notes

- Full runnable setup and expected outcomes: see `../quickstart.md`.
- CLI details (output formatting) are implementation concerns left to
  `/speckit.tasks`; this contract fixes the observable behaviour.
- A web UI is NOT part of Level 0 (P XII).