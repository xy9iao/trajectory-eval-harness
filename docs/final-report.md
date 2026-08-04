# Final Report — trajectory-eval-harness

**An evaluation harness for the intermediate behavior of LLM agents**, demonstrated on a
resume–JD matching agent with a human-in-the-loop gate. NUS-ISS capstone, 2026-07-10 → 2026-08-03.

Every number below cites the run manifest whose trajectory JSONL regenerates it. Phase reports
carry the full detail; this document is the executive layer.

---

## 1. The result that justifies the approach

Same agent, same 30 evaluation pairs, two model providers, identical rubric and prompts.

| | `deepseek-chat` | `gpt-4o-mini` |
|---|---|---|
| Gate confusion, per run | TP 139 · FN 6 · FP 5 | **TP 145 · FN 0 · FP 5** |
| Gate decision identical across k=5 | 26/30 | **30/30** |
| **Fired for the reference's stated reason** | **21/28** | **14/29** |
| `hard_requirements` degradations | 1 | **20** |
| Times it scored `hard_requirements` = 5 | 19 | **0** |

The outcome metric says the second model is better: no false negatives, perfectly stable gate. The
trajectory metrics say the opposite, and the third row of the lower block explains why — **a model
that never judges a candidate's requirements fully met can never clear the veto**, so it escalates
every candidate. On a reference set where 29 of 30 genuinely warrant escalation, escalating
everything scores 29/30. **The perfect stability is the stability of a constant function.**

> **If this project reported only the confusion matrix, it would have recommended the model that
> reasons worse.**

This is [finding 004](findings/004-gate-truth-imbalance.md) arriving in concrete form: with a
degenerate positive class, an outcome-level metric cannot distinguish a better agent from a more
indiscriminate one. Trajectory-level metrics can, and here they did.

## 2. What was built

| Component | |
|---|---|
| **Agent** (P1) | LangGraph, 6 nodes, two-mode HITL gate — `interrupt()` + review artifact + CLI resume for interactive; auto-resume with recorded trigger events for batch eval |
| **Trajectory schema** (P1) | 7 event types, 7 validator-enforced invariants, frozen before P2; **requirement ids and evidence offsets only, never document text** |
| **Harness** (P2) | 6 scorers as pure `(corpus, reference) -> ScorerResult` functions over a dumb-pipe runner; one command produces the whole report |
| **Constructed cases** (P2/P3) | fault-injection variants and poisoned-document cases, each materialized at run time from a gitignored corpus |
| **Defenses** (P3) | parse-seam sanitization and per-run nonce document fencing |

**Reproduce any table or figure:**

```bash
uv run python -m eval.report --manifest runs/<batch>.json --out report.md
uv run python -m eval.reports.passk_report runs/<batch>.json
```

### The six scorers, and how far they travel

| Scorer | Question | Portable? |
|---|---|---|
| pass^k | Same input k times — same answer? | schema-generic |
| gate integrity | Is the escalation right, and right *for the stated reason*? | needs your gate vocabulary |
| agreement | How close to a human reference, per dimension and per divergence stratum? | needs your reference labels |
| ledger consistency | Does the run contradict its own earlier findings? | needs your ledger structure |
| tool-call correctness | Structural correctness; does retry → degrade → escalate work? | schema-generic |
| evidence coverage | Which conclusions rest on too little cited evidence? (**sentinel**, not a score) | schema-generic |

Three of six run unchanged elsewhere; three encode this rubric's vocabulary. **The coupling point
is the trajectory schema, not the agent's code.**

## 3. Consolidated metrics

**Live corpus** — 30 pairs, k=5, `deepseek-chat`, `runs/passk-r20260728T035619-2d6bcd.json`:

| | |
|---|---|
| Gate confusion, per run (PRIMARY) | TP 139 · FN 6 · FP 5 |
| Gate confusion, by-pair majority (SECONDARY) | TP 28 · FN 1 · FP 1 |
| Fired for the reference's reason | 21/28 |
| Gate decision stable across k=5 | 26/30 pairs |
| Agreement vs human reference | skills 0.287 · experience 0.570 · education 0.592 · hard 0.799 |
| Self-consistency (pairs stable across k=5) | skills 12/30 · experience 17/30 · education 7/30 · hard 20/30 |
| Self-contradictions within a run | 15, on 8/30 pairs |
| Tool-call structural correctness | 150/150 |
| Human inter-annotator agreement (2 annotators, 10 pairs) | 36/40 dimension scores · **10/10 gate decisions** |

**PRIMARY is the per-run figure.** The deployed system runs once, so reporting a k=5 majority as
the headline would describe a configuration that does not exist. Whether the gate fires and why it
fires are reported side by side, always — they are distinct measurements.

**Constructed cases** — never merged with the numbers above:

| batch | result |
|---|---|
| Fault injection (5 cases, 2 independent batches) | **5/5 both times** — anomaly rules fire, one malformed response recovers via retry with no degradation, two exhaust it and escalate |
| Gate negatives (6 attempted) | **1–2 succeeded**; 3 retired as construction errors rather than counted — see §5 |
| Injection (7 cases × 3 defense rounds) | 1 attack class ever worked; **21 attempts, 0 moved the final decision** |

## 4. Key findings

Fifteen archived, in `docs/findings/`. The four that carry the project:

**[009](findings/009-prose-binds-process-not-judgment.md) — Mechanism binds; prose does not.**
Seven interventions across two problem domains (calibration and injection defense): **mechanism
4/4, prose 0/3**. Changing a *structure* — a schema, a tool contract, a state reducer, a document
fence — moved the measurements every time. Adding a sentence to a prompt moved nothing, three
times. *Its own stated limit: every intervention was designed by someone who by then expected
prose to fail, and that bias is not controlled for.*

**[011](findings/011-passk-variance-floor.md) — A measured variance floor bounds every improvement
claim.** The same input re-run gives a different answer often enough that any improvement smaller
than the noise band is unprovable. Measured per dimension *before* any tuning claim was made, and
subsequently used as the decision criterion in a different phase — an injection counts as having
had an effect only if it moves a score beyond that dimension's floor.

**[013](findings/013-faithfulness-evidence-to-determination-mismatch.md) — Self-consistency and
faithfulness are separable.** The *most* self-consistent dimension produced *every* evidence
failure, and the mechanism is structural rather than verbal: ten conclusions citing one quote, and
JD text cited to prove what the résumé contains. This disconfirmed an extension of 011's own
hypothesis — a hypothesis that could be bounded was one that could have been falsified.

**P3's layered conclusion — two injection paths, two defenses.**
An injection has two routes into a judgment: **role forgery** (the model reads text as an
*instruction*) and **content contamination** (it reads text as *evidence*). **Structural
demarcation closes the first; item-by-item ledger reconciliation closes the second. A dimension
with neither is open to both.** `hard_requirements` never moved across 21 attempts because its
ledger is derived from the *other* document — a résumé-side attacker would have to forge the JD's
list, not merely persuade the model. `education_domain_fit`, which carries no determinations at
all, fell to both.

### The framework diagnosed two structural defects in the design it was built on

- **The veto's gain is mismatched to its input noise.** Single-point veto — any one of ~9.7 ledger
  items absent zeroes the dimension — sits on a ledger whose *size* is itself stochastic
  ([015](findings/015-extraction-ledger-size-is-pair-dependent-unstable.md): 2–12 items on one
  input), admits categories the rubric excludes
  ([012](findings/012-gate-fires-for-the-wrong-reason.md)), and reuses the determinations that
  produce the scores it overrides
  ([014](findings/014-low-road-negative-is-structurally-unconstructible.md)). Largest authority,
  least independent information, noisiest input.
- **`education_domain_fit` has no determination ledger, and five independent measurements found
  it.** Least self-consistent on the dev model (011), lowest human agreement (010), ranking
  inverts across providers (P2), driven 1 → 5 by injection (P3 baseline), the only dimension the
  structural defense failed to protect (P3 mechanism). **A dimension with no ledger is both the
  least stable and the least safe — one missing structure seen from two directions.**

Neither is repaired. Both are diagnosed, costed, and frozen in
[issue #26](https://github.com/xy9iao/trajectory-eval-harness/issues/26) — the cheap half is a
twenty-line change (derive the veto score from the ledger in code instead of asking the model to
apply a computable rule, which both models violate: 9% and 5% of assessments); the expensive half
would invalidate all 30 reference labels and every number recorded since P0.

## 5. Method, and what it cost

The discipline is the deliverable as much as the code is. Four rules, each adopted because
skipping it produced a real wrong number:

- **Explicit batch scope.** Run sets are named by manifest, never by scanning a directory. A
  directory scan once mixed 114 stale runs into a 150-run batch — the output had no error and was
  wrong.
- **Baseline before change; one variable per round.** The cross-model comparison spent its single
  permitted calibration round on request-shape compatibility and never on semantics; P3's three
  rounds changed exactly one thing each, and round 3 *removed* round 2's sentence so the mechanism
  stayed attributable.
- **Pre-registration, with a standing commitment not to explain results away.** Three predictions
  were dated and recorded before the delivery-model run; **two were disconfirmed**, and the record
  says which part of the earlier finding fell (the per-dimension ranking, which is
  provider-specific) and which survived (the structural claim). A third was marked **not tested**
  rather than answered with the nearest available number.
- **Divergence defaults to "my construction is wrong."** A constructed case whose result
  contradicts its expectation is a broken construction until diagnosed otherwise. **Six
  constructions were retired rather than counted** — including one injection case that "passed"
  only because its obfuscation had destroyed its own payload. Admitting them would have
  manufactured phantom true negatives in the exact metric they existed to repair.

**What it cost:** the gate-negative class was left at 1–2 cases instead of the 6 the design asked
for, because padding it would have required admitting broken constructions. The report says so.

## 6. Known limitations

- **n = 30 pairs, one rubric, two models.** A fixed instrument for detecting change in one agent —
  not a benchmark, not comparable across projects.
- **Constructed cases are measured at k=1** while the system has a quantified variance floor. They
  are **existence proofs — "this happened at least once" — never rates.** This is an internal
  inconsistency in the method, caught when the same constructed case flipped between two batches.
- **True negatives are scarce for three independent structural reasons** (014, 015, k=1), not by
  sampling accident; drawing more pairs would not fix it.
- **The faithfulness probe was a stratified sample of known weak spots** — 10 hand-judged cases
  drawn deliberately from the likeliest failures. **No overall faithfulness rate exists in this
  work and none can be derived from it.**
- **The injection results stand on one substrate**, chosen for having zero control noise — a
  property itself established at k=5, and a sixth draw fell outside it. The "21 attempts, veto
  never moved" result is real and consistent across three rounds, but that substrate's veto was
  already firm; **it is not evidence the veto is safe in general.**
- **Rendering-layer attacks (white text, 1pt fonts, CSS hiding) are not representable on a
  plain-text corpus.** They remain live for PDF/DOCX ingestion in production. **This is the
  boundary of this work, not the boundary of the problem.**

## 7. Phase index

| Phase | Report | Outcome |
|---|---|---|
| P0 — data + rubric foundation | [p0.md](phase-reports/p0.md) | 30-pair human reference set, rubric v1.3, mentor touchpoint at 90% agreement |
| P1 — agent + HITL gate | [p1.md](phase-reports/p1.md) | LangGraph agent, two-mode gate, frozen trajectory schema |
| P2 — the evaluation harness | [p2.md](phase-reports/p2.md) · [cross-model](phase-reports/p2-cross-model.md) | 6 scorers, one-command report, the cross-model reversal |
| P3 — adversarial cases | [p3.md](phase-reports/p3.md) | Three defense rounds, the layered conclusion |

Design records: [eval-design.md](eval-design.md) · [adversarial-design.md](adversarial-design.md) ·
[trajectory-schema.md](trajectory-schema.md) · [decisions.md](decisions.md) ·
[roadmap.md](roadmap.md)

## 8. Deliberately not built

RAG · MCP (the owner's other project owns that story) · fine-tuning · a frontend · a database
service · any third-party eval framework. Each is a recorded decision in
[decisions.md](decisions.md) rather than an omission — the scorers are a few hundred lines of pure
functions, and **the expense in this project was annotation, not engineering**.
