# trajectory-eval-harness

Same agent, same 30 evaluation pairs, two model providers. The output-level metric says the second
one is better: **zero false negatives, and a gate decision that is identical across all five
repeats of every pair.** The trajectory-level metrics say something else — that model **never once
judged a candidate's hard requirements fully met**, so it can never clear the veto, so it escalates
*every* candidate to a human. On a reference set where 29 of 30 cases genuinely warrant escalation,
escalating everything scores 29/30. The perfect stability was the stability of a constant function.

**If this project reported only the confusion matrix, it would have recommended the model that
reasons worse.** That is what this harness is for.
→ [the full comparison](docs/phase-reports/p2-cross-model.md)

**An evaluation harness for the *intermediate* behavior of LLM agents.** Most agent evals score the
final answer. This one scores the trajectory: every tool call, every intermediate judgment, every
human-in-the-loop gate decision — and reports how much of it survives being run again.

It is demonstrated on a resume–JD matching agent (LangGraph, with a real HITL gate), but the agent
is the host, not the point. **The coupling point is a trajectory JSONL schema, not the agent's
code** — anything that emits conforming events can be scored by the same six scorers.

```bash
git clone https://github.com/xy9iao/trajectory-eval-harness && cd trajectory-eval-harness
uv sync
uv run python -m eval.report --manifest examples/sample-batch/manifest.json
```

One command, one markdown report, every metric below. **No API key and no dataset needed** — a
3-pair slice of the real batch (15 runs) is committed, which is possible only because trajectories
carry requirement ids and character offsets and never document text (the reference labels do
quote the corpus — see Data handling). No database, no service, no
notebook. The full 30-pair batch lives in the gitignored `runs/` and is what every number in the
reports cites.

## What it measures

| Scorer | Question it answers | Portable? |
|---|---|---|
| **pass^k** | Run the same input k times — do you get the same answer? | schema-generic |
| **gate integrity** | When the agent escalates to a human, is it right — and does it escalate *for the reason it claims*? | needs your gate vocabulary |
| **agreement** | How close are the agent's judgments to a human reference, per dimension and per failure stratum? | needs your reference labels |
| **ledger consistency** | Does the agent contradict its own earlier findings later in the same run? | needs your ledger structure |
| **tool-call correctness** | Are tool calls structurally correct? (The retry → degrade → escalate path has its own `error_recovery_scorer`, unit-tested but not in the report registry — see the P2 report.) | schema-generic |
| **evidence coverage** | Which conclusions rest on too little cited evidence to be worth trusting? (a *sentinel*, not a score) | schema-generic |

Three are portable as-is; three encode this project's rubric vocabulary and need their reference
swapped. That split is stated rather than glossed — a harness that claims to measure anything
usually measures nothing.

**What this is not:** not a benchmark, not a leaderboard, not a hiring tool. The 30-pair reference
set is a fixed instrument for detecting change in one agent, not a score anyone should compare
across projects — and the host agent exists to give the harness something to measure, not to be
deployed on real applicants.

**Known limitation, stated up front:** the constructed negative class is measured at k=1 while the
system under test has a quantified variance floor ([finding 011](docs/findings/011-passk-variance-floor.md)).
Negative-class results are therefore existence proofs — "at least N pairs can produce this" — never
rates. The live corpus is measured at k=5 and does carry rates.

## Design decisions you can steal

- **Trajectory JSONL is the source of truth.** Every figure in every report regenerates from it.
  Numbers that cannot cite a run ID do not enter documents.
- **Scorers are pure functions**, `(corpus, reference) -> ScorerResult`. The runner is a dumb pipe
  (`for scorer in REGISTRY`). Adding a scorer is one line; no dispatch, no plugin system.
- **Every metric computed over runs must declare its stability.** A single-run number without a
  statement about run-to-run movement is a number without an error bar, and the report runner
  prints a warning when a scorer omits it.
- **Explicit batch scope.** A run set is named by a run-id manifest, never by scanning a directory.
  A directory scan once silently mixed 114 stale runs into a 150-run batch — the output had no
  error and was wrong.
- **Validation exclusion is surfaced, never swallowed.** Invalid trajectories are dropped from all
  scorers *and* listed in the report header with their run IDs.
- **Constructed test cases never share a table with observed results.** Hand-built variants carry a
  banner and a separate manifest kind, enforced in code.

## Results on the host agent

30 human-labeled reference pairs, k=5 repeats, 150 runs, `deepseek-chat`
(`runs/passk-r20260728T035619-2d6bcd.json`):

| | |
|---|---|
| Gate decision accuracy (per run) | **139 TP / 6 FN / 5 FP over 150 runs** |
| Gate fired for the reference's stated reason | **21/28** |
| Gate decision identical across all 5 repeats | **26/30 pairs** |
| Per-dimension agreement vs human reference | skills 0.29 · experience 0.57 · education 0.59 · hard requirements 0.80 |
| Self-contradictions within a run | 15 total, on 8/30 pairs |
| Tool-call structural correctness | 150/150 |

The two gate numbers are reported side by side on purpose: *whether* it escalates and *why* it
escalates are different measurements, and 7 of 28 correct escalations cite a reason the human
reference does not.

## Key findings

The point of the harness is what it surfaced. Fifteen records in [docs/findings/](docs/findings/),
consolidated in the [final report](docs/final-report.md); the four that carry the project:

- **Mechanism binds; prose does not.** Across seven interventions in two different problem domains
  — agent calibration and injection defense — changing a *structure* (a schema, a tool contract, a
  state reducer, a document fence) moved the measurements **4/4**; adding a sentence to a prompt
  moved nothing, **0/3**. → [009](docs/findings/009-prose-binds-process-not-judgment.md)
- **A variance floor bounds every other claim.** The same input re-run gives a different answer
  often enough that any improvement smaller than the noise band is unprovable — measured per
  dimension before any tuning claim was made. → [011](docs/findings/011-passk-variance-floor.md)
- **Self-consistency and faithfulness are separable.** The *most* self-consistent dimension
  produced *every* evidence-faithfulness failure; the mechanism is structural (10 conclusions
  citing 1 quote), not weak wording.
  → [013](docs/findings/013-faithfulness-evidence-to-determination-mismatch.md)
- **Injection has two routes, and each needs its own defense.** Role forgery — the text is read as
  an *instruction* — is closed by structural demarcation. Content contamination — the text is read
  as *evidence* — is closed by reconciling item by item against a list that lives in a **different
  document**. A dimension with neither is open to both: across 21 injection attempts the
  ledger-backed dimension never moved and no candidate was ever advanced, while the one dimension
  with no ledger was driven from 1 to 5. → [P3 report](docs/phase-reports/p3.md)

**The framework also diagnosed two structural defects in the design it was built on** — a veto whose
authority is mismatched to its input noise, and one dimension indicted five times by five different
methods before the common cause was visible. Both are diagnosed, costed, and deliberately unfixed;
the [final report](docs/final-report.md) says which fix costs twenty lines and which costs the whole
reference set.

## Running it on your own agent

1. Emit trajectory JSONL per [docs/trajectory-schema.md](docs/trajectory-schema.md) — 7 event
   types, 7 validator-enforced invariants.
2. Record a run-id manifest per batch: `{"kind": ..., "provider": ..., "model": ..., "run_ids": [...]}`.
3. Supply reference labels for the agreement and gate scorers, or run the three schema-generic
   scorers alone.
4. `uv run python -m eval.report --manifest <your-manifest>.json --out report.md`

## Local setup

```bash
uv sync
cp .env.example .env          # add your key; .env is gitignored
uv run pytest -q              # no API calls, no key needed
uv run python -m agent.run --synthetic          # one run, no dataset, no key
uv run python -m agent.run --pair train:596 --live
```

## Layout

| Path | Purpose |
|---|---|
| `eval/` | The harness: scorers, corpus loading, trajectory validator, report runner |
| `eval/scorers/` | One file per scorer, each a pure function with planted-defect tests |
| `agent/` | The host agent: LangGraph graph, HITL gate, tools |
| `rubrics/` | Versioned YAML rubric: dimensions, weights, criteria, anchors |
| `data/` | Reference labels, variant specs, dataset loader (raw data is gitignored) |
| `docs/` | Findings, phase reports, eval design, decisions, roadmap |

## Data handling

Public resume–JD datasets only, committed only when the license permits redistribution — otherwise
a download script plus checksum. Résumés of real people known to the author are never committed and
never sent to an API. API keys live in `.env` (gitignored; template in `.env.example`), and CI runs
a secrets scan on every push. Trajectories carry requirement **ids and evidence offsets, never document text**, so a committed
trajectory cannot leak the corpus.

**Reference labels are not text-free.** They store row indices, scores and character offsets, and ALSO verbatim requirement strings plus annotator notes that quote the source corpus. The source dataset declares no license; these fragments are retained for research reproducibility, and this repository is not a redistribution of the dataset. Trajectories are text-free — that claim holds and is validator-enforced. Reference labels store row indices, scores, character offsets **and** verbatim requirement strings plus annotator notes that quote the source corpus. The source dataset declares no license; these fragments are retained for research reproducibility, and this repository is not a redistribution of the dataset.

## Stack

Python 3.12 + uv · LangGraph (chosen for a real HITL need: `interrupt()` + checkpointing) ·
filesystem-only storage (JSON / JSONL / YAML), no database service · OpenAI-compatible client with
the provider selected by env config · pytest + hand-written scorers, no eval framework dependency.

## Project status

NUS-ISS capstone, complete. P0 (rubric + reference set), P1 (agent + HITL gate), P2 (the eval
framework) and P3 (adversarial cases) are closed; the [final report](docs/final-report.md) is the
executive layer over all four. Phases and acceptance criteria live in
[docs/roadmap.md](docs/roadmap.md), locked design decisions in
[docs/decisions.md](docs/decisions.md), and each phase closes with a public report in
[docs/phase-reports/](docs/phase-reports/).
