# trajectory-eval-harness

An evaluation framework for AI-agent reliability — trajectory-level scoring of intermediate agent behavior — demonstrated on a resume–JD matching agent with a human-in-the-loop gate.

The eval framework is the protagonist; the resume–JD matching agent is its host. This is a research project (NUS-ISS capstone), not a demo build: its value is proven by documented findings — evaluation surfaced a problem → the design was revised → metrics improved. Findings live in [docs/findings/](docs/findings/), one file each in a fixed five-part format; every phase closes with a public report in [docs/phase-reports/](docs/phase-reports/).

## Status

**P0 — data + rubric foundation (open).** Phases and acceptance criteria: [docs/roadmap.md](docs/roadmap.md). Locked design decisions and their rationale: [docs/decisions.md](docs/decisions.md).

## Layout

| Path | Purpose |
|---|---|
| `agent/` | Host: LangGraph graph, HITL gate logic, tools (P1) |
| `eval/` | Protagonist: trajectory scorers, cases, runners (P2) |
| `eval/reports/` | Report/figure generation scripts — every figure regenerable from trajectory JSONL |
| `rubrics/` | Versioned YAML rubrics: dimensions, weights, criteria, anchor examples |
| `data/` | License-cleared datasets, or download scripts + checksums |
| `examples/` | Walkthrough resume–JD pairs for the README/demo |
| `docs/` | Roadmap, decision log, findings, phase reports, project handoff |

## Data handling

Public resume–JD datasets only; a dataset is committed only when its license permits use and redistribution — otherwise the repo carries a download script plus checksum. Resumes of real people personally known to the owner are never committed and never sent to an API without explicit consent. API keys live in `.env` (gitignored; template in `.env.example`), and CI runs a secrets scan on every push.

## Stack

Python 3.12 + uv · LangGraph (real HITL need: interrupts + checkpointing) · typer CLI · filesystem-only storage (JSON / JSONL / YAML) · OpenAI-compatible client with provider chosen by env config (dev: DeepSeek, delivery: OpenAI) · pytest + hand-written trajectory scorers.
