# trajectory-eval-harness

[![CI](https://github.com/xy9iao/trajectory-eval-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/xy9iao/trajectory-eval-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C?logo=langchain&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![Tests](https://img.shields.io/badge/tests-124-success)
![Findings](https://img.shields.io/badge/archived%20findings-15-blue)

An **evaluation framework for LLM-agent reliability** that scores *intermediate reasoning steps*, not
just final outputs. Six trajectory-level scorers over a frozen JSONL schema, pass^k stability
measurement, constructed fault and injection cases, and a cross-provider comparison — all behind one
reproducible command. Demonstrated on a resume–JD screening agent with a human-in-the-loop gate.

> **Scope:** this is a research instrument, **not a benchmark, leaderboard, or hiring tool.** The
> 30-pair reference set is a fixed instrument for detecting change in *one* agent, not a score to
> compare across projects. The host agent exists to give the harness something to measure — it is
> not intended for use on real applicants.

## The result that motivates the whole approach

Same agent, same 30 evaluation pairs, two model providers, identical rubric and prompts.

| | `deepseek-v4-flash` | `gpt-4o-mini` |
|---|---|---|
| Gate confusion, per run | TP 139 · FN 6 · FP 5 | **TP 145 · FN 0 · FP 5** |
| Gate decision identical across k=5 | 26/30 | **30/30** |
| **Fired for the reference's stated reason** | **21/28** | **14/29** |
| Times it scored `hard_requirements` = 5 | 19 | **0** |

The outcome metric says the second model is better — no false negatives, a perfectly stable gate.
The trajectory metrics say the opposite, and the last row explains why: **a model that never judges
a candidate's requirements fully met can never clear the veto**, so it escalates *every* candidate.
On a reference set where 29 of 30 genuinely warrant escalation, escalating everything scores 29/30.
The perfect stability was the stability of a constant function.

> **If this project reported only the confusion matrix, it would have recommended the model that
> reasons worse.** → [full comparison](docs/phase-reports/p2-cross-model.md)

## Architecture

**The harness is the product; the agent is its host.** The coupling point between them is a
trajectory JSONL schema — not the agent's code — so anything that emits conforming events can be
scored by the same scorers.

```mermaid
graph LR
  CLI["agent.run<br/>--pair · --passk · --variants · --poisoned"] --> GRAPH
  GRAPH["LangGraph agent (6 nodes)<br/>parse → extract → assess⟲ → aggregate → gate → recommend"] --> W[["trajectory JSONL<br/>7 event types · 7 invariants<br/>ids + offsets, never document text"]]
  GRAPH --> GATE["HITL gate<br/>interactive: interrupt() + review file + resume<br/>eval: auto-resume, triggers recorded"]
  GRAPH -->|"one gateway"| LLM["OpenAI-compatible client<br/>provider by env · CI-asserted isolation"]
  W --> VAL{{"validator<br/>invalid runs excluded AND surfaced"}}
  VAL --> CORP["Corpus<br/>scoped by run-id manifest"]
  CORP --> REG["eval.report — dumb-pipe runner<br/>for scorer in REGISTRY"]
  REG --> S1["pass^k · gate integrity · agreement"]
  REG --> S2["ledger consistency · tool calls · evidence sentinel"]
  S1 --> OUT["one markdown report<br/>every figure regenerable"]
  S2 --> OUT
  REF[("30-pair human reference<br/>rubric v1.3 · 2 annotators")] --> REG
```

Iteration and I/O live in the runner; **all judgment lives in pure `(corpus, reference) -> ScorerResult`
functions**, so a scorer is independently testable and adding one is a single registry line.

## By the numbers (measured)

30 pairs · k=5 · 150 runs per model · `deepseek-v4-flash` unless noted.

| Metric | Value | Source |
| --- | --- | --- |
| Gate accuracy, per run | **TP 139 · FN 6 · FP 5** | `runs/passk-r20260728T035619-2d6bcd.json` |
| Fired for the reference's stated reason | **21/28** — reported beside accuracy, always | `gate_integrity_scorer` |
| Gate decision stable across k=5 | **26/30 pairs** | `passk_scorer` |
| Agreement vs human reference | skills 0.287 · exp 0.570 · edu 0.592 · hard 0.799 | `agreement_scorer` |
| Human inter-annotator agreement | 36/40 dimensions · **10/10 gate decisions** | 2 blind annotators, 10 pairs ([010](docs/findings/010-mentor-agreement-adjacency-axis.md)) |
| Self-contradictions within a run | 15, on 8/30 pairs | `ledger_consistency_scorer` |
| Fault-injection cases | **5/5, reproduced across 2 batches** | `runs/variants-*.json` |
| Injection defense | 1 attack class ever worked; **21 attempts, 0 moved the decision** | [p3 report](docs/phase-reports/p3.md) |
| Injection effect once documents were fenced | **+3.3 → +0.8** over control | p3 §1 |
| Trajectory validity | **300/300 runs schema-clean** across both models | `eval/trajectory.py` |
| Automated tests | **124**, CI-gated (ruff · ruff format · mypy strict · pytest) | `.github/workflows/ci.yml` |

**PRIMARY is the per-run figure, never a k=5 majority vote** — the deployed system runs once, so
reporting the majority would describe a configuration that does not exist.

## What it measures

| Scorer | Question it answers | Portable? |
|---|---|---|
| **pass^k** | Run the same input k times — do you get the same answer? | schema-generic |
| **gate integrity** | When the agent escalates, is it right — and does it escalate *for the reason it claims*? | needs your gate vocabulary |
| **agreement** | How close to a human reference, per dimension and per divergence stratum? | needs your reference labels |
| **ledger consistency** | Does the run contradict its own earlier findings? | needs your ledger structure |
| **tool-call correctness** | Are calls structurally correct? | schema-generic |
| **evidence coverage** | Which conclusions rest on too little cited evidence? (a *sentinel*, not a score) | schema-generic |

Three run unchanged elsewhere; three encode this rubric's vocabulary. That split is stated rather
than glossed — **a harness that claims to measure anything usually measures nothing.**

## Key findings

Fifteen archived in [docs/findings/](docs/findings/), consolidated in the
[final report](docs/final-report.md). The four that carry the project:

- **Mechanism binds; prose does not.** Across seven interventions in two problem domains — agent
  calibration and injection defense — changing a *structure* (a schema, a tool contract, a state
  reducer, a document fence) moved the measurements **4/4**; adding a sentence to a prompt moved
  nothing, **0/3**. → [009](docs/findings/009-prose-binds-process-not-judgment.md)
- **A variance floor bounds every other claim.** The same input re-run gives a different answer often
  enough that any improvement smaller than the noise band is unprovable — measured per dimension
  *before* any tuning claim, then reused as the decision criterion in a later phase.
  → [011](docs/findings/011-passk-variance-floor.md)
- **Self-consistency and faithfulness are separable.** The *most* self-consistent dimension produced
  *every* evidence failure; the mechanism is structural (ten conclusions citing one quote), not weak
  wording. → [013](docs/findings/013-faithfulness-evidence-to-determination-mismatch.md)
- **Injection has two routes, and each needs its own defense.** Role forgery (text read as an
  *instruction*) is closed by structural demarcation; content contamination (text read as *evidence*)
  is closed by reconciling item by item against a list living in a **different document**. A
  dimension with neither is open to both. → [p3 report](docs/phase-reports/p3.md)

**The framework also diagnosed two structural defects in the design it was built on** — a veto whose
authority is mismatched to its input noise, and one dimension indicted five times by five different
methods before the common cause was visible. Both are diagnosed, costed, and deliberately unfixed;
the final report says which fix costs twenty lines and which costs the whole reference set.

## Design decisions you can steal

- **Trajectory JSONL is the source of truth.** Every figure regenerates from it; numbers that cannot
  cite a run ID do not enter documents.
- **Explicit batch scope.** A run set is named by a run-id manifest, never by scanning a directory —
  a directory scan once silently mixed 114 stale runs into a 150-run batch, and the output had no
  error and was wrong.
- **Every metric computed over runs declares its stability.** A number without a statement about
  run-to-run movement is a number without an error bar; the runner warns when a scorer omits it.
- **Validation exclusion is surfaced, never swallowed** — invalid trajectories are dropped from all
  scorers *and* listed in the report header with their run IDs.
- **Constructed cases never share a table with observed results**, enforced in code.
- **Divergence defaults to "my construction is wrong."** Six constructed cases were retired rather
  than counted — admitting them would have manufactured phantom true negatives in the exact metric
  they existed to repair.

## Quick start

No API key and no dataset needed — a 3-pair, 15-run slice of the real batch is committed, which is
possible only because trajectories carry ids and offsets and never document text.

```bash
git clone https://github.com/xy9iao/trajectory-eval-harness.git
cd trajectory-eval-harness
uv sync
uv run python -m eval.report --manifest examples/sample-batch/manifest.json
```

One command, one markdown report, every metric above. No database, no service, no notebook.

```bash
uv run pytest -q                                   # no API calls, no key
uv run python -m agent.run --synthetic             # one agent run, no dataset, no key
```

Live runs need a key and the dataset — see [SETUP.md](SETUP.md), which states plainly what cannot be
done unkeyed.

```bash
uv run python -m agent.run --passk 5 --smoke --live   # 2 pairs × 5 — the cost/compat check
uv run python -m agent.run --passk 5 --live           # the full 30-pair batch
```

**Run the smoke first.** It is two pairs and a few cents, and it has caught a provider
incompatibility, a scorer scoping bug, and a wall-clock estimate wrong by 4× — each of which would
otherwise have cost a full batch to discover.

## Development

```bash
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run mypy .                                        # strict, 53 source files
uv run pytest -q                                     # 124 tests
```

CI (GitHub Actions) enforces exactly these gates on every push/PR, plus a gitleaks secrets scan.

## Running it on your own agent

1. Emit trajectory JSONL per [docs/trajectory-schema.md](docs/trajectory-schema.md) — 7 event types,
   7 validator-enforced invariants.
2. Record a run-id manifest per batch: `{"kind", "provider", "model", "run_ids": [...]}`.
3. Supply reference labels for the agreement and gate scorers, or run the three schema-generic
   scorers alone.
4. `uv run python -m eval.report --manifest <your-manifest>.json --out report.md`

The methodology transfers completely; the structural layer mostly reuses; the semantic layer must be
rebuilt. **The expense is in annotation, not engineering** — the scorers are a few hundred lines of
pure functions, while the 30-pair reference set took an entire phase.

## Project structure

```
├── eval/                 # the harness
│   ├── scorers/          # one file per scorer, each a pure function with planted-defect tests
│   ├── report.py         # dumb-pipe runner: manifest scope, validation exclusion, isolation banner
│   ├── trajectory.py     # schema validator + data-hygiene invariants
│   ├── variants.py       # constructed fault/gate cases
│   └── adversarial.py    # poisoned-case materialization + effect classification
├── agent/                # the host agent
│   ├── graph.py          # LangGraph: 6 nodes, conditional gate edge
│   ├── hitl.py           # interrupt() gate; review.py for the human artifact
│   ├── client.py         # THE only module that knows providers exist (CI-asserted)
│   └── sanitize.py       # parse-seam defense: carrier stripping + role-marker neutralization
├── rubrics/              # versioned YAML rubric (v1.3): dimensions, weights, anchors, veto
├── data/                 # reference labels, constructed-case specs, dataset loader
├── examples/sample-batch # committed 15-run slice so the quick start works from a fresh clone
├── docs/
│   ├── final-report.md   # executive layer over all four phases
│   ├── findings/         # 15 archived findings, five-part format
│   └── phase-reports/    # p0–p3 + the cross-model comparison
└── runs/                 # trajectories and manifests (gitignored)
```

## Known limitations

Stated here rather than left for a reader to discover.

- **n = 30 pairs, one rubric, two models.** A fixed instrument for detecting change in one agent.
- **Constructed cases are measured at k=1** while the system has a quantified variance floor — they
  are **existence proofs, never rates.** This is an internal inconsistency in the method, caught when
  the same constructed case flipped between two batches.
- **True negatives are scarce for three independent structural reasons**, not by sampling accident;
  drawing more pairs would not fix it.
- **The faithfulness probe was a stratified sample of known weak spots** — 10 hand-judged cases.
  **No overall faithfulness rate exists in this work and none can be derived from it.**
- **Injection results stand on one substrate**, chosen for zero control noise — itself only a k=5
  property, and a sixth draw fell outside it.
- **Rendering-layer attacks are not representable on a plain-text corpus.** They stay live for
  PDF/DOCX ingestion in production. **This is the boundary of this work, not of the problem.**

## Data handling

Public resume–JD data only. The source dataset declares **no license** (re-verified 2026-08-04 via
the HuggingFace API), so the corpus itself is gitignored and reachable only through a pinned
download script plus checksum — **this repository is not a redistribution of the dataset.**
Trajectories carry requirement ids and character offsets and **never document text**, enforced by
the validator. The reference labels are a separate artifact and *do* quote the corpus; see
[data/README.md](data/README.md) for the accuracy note. API keys live in `.env` (gitignored), and CI
runs a secrets scan on every push.

## Status

NUS-ISS capstone, **complete**. P0 (rubric + reference set), P1 (agent + HITL gate), P2 (the eval
framework) and P3 (adversarial cases) are closed, each with a public report; P4 delivered the
[final report](docs/final-report.md). Phases and acceptance criteria in
[docs/roadmap.md](docs/roadmap.md), locked design decisions in [docs/decisions.md](docs/decisions.md).

Three issues are open **on purpose** — each records something diagnosed but deliberately not built,
with its cost: [#26](https://github.com/xy9iao/trajectory-eval-harness/issues/26) extractor fixes ·
[#31](https://github.com/xy9iao/trajectory-eval-harness/issues/31) experimental conditions in the
manifest · [#33](https://github.com/xy9iao/trajectory-eval-harness/issues/33) component ablation for
the injection defenses.

## License

**MIT** — see [LICENSE](LICENSE). It covers the code, tests, rubric and documentation authored here.

It deliberately does **not** relicense material derived from the source dataset, which declares no
license of its own: the reference labels quote that corpus, as do shorter fragments in the variant
specs and three findings. Those are retained for research reproducibility, not relicensed — the
scope note in `LICENSE` says exactly which files, and [data/README.md](data/README.md) explains why
they are kept.

© 2026 Xinyang Qiao — sole author.
