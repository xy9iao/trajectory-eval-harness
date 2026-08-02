# P2 — Cross-model comparison (section draft for the phase report)

**Dev model:** `deepseek-chat` · `runs/passk-r20260728T035619-2d6bcd.json` · 150 runs, 0 invalid
**Delivery model:** `gpt-4o-mini` · `runs/passk-r20260802T144149-e8d83a.json` · 150 runs, 0 invalid
Same 30 reference pairs, k=5, identical rubric (v1.3), identical prompts.

**Calibration discipline.** One calibration round was spent, entirely on request-shape
compatibility, never on semantics (eval-design §4). It was needed only for the
briefly-considered `gpt-5.6-luna`, which rejects function tools unless `reasoning_effort` is
pinned to `none`; the delivery model reverted to `gpt-4o-mini` and required no change at all.
**No prompt, rubric, or threshold differs between these two columns.** That is the precondition
that makes the pre-registered predictions below testable.

## The table

| | deepseek-chat | gpt-4o-mini |
|---|---|---|
| Gate confusion, per run (PRIMARY) | TP 139 · FN 6 · FP 5 | **TP 145 · FN 0 · FP 5** |
| Gate confusion, by-pair majority (SECONDARY) | TP 28 · FN 1 · FP 1 | TP 29 · FN 0 · FP 1 |
| Gate decision identical across k=5 | 26/30 | **30/30** |
| **Fired for the reference's stated reason** | **21/28** | **14/29** |
| Self-consistency — skills | 12/30 (σ̄ 0.445) | 18/30 (σ̄ 0.252) |
| Self-consistency — experience | 17/30 (σ̄ 0.345) | 25/30 (σ̄ 0.113) |
| Self-consistency — education | **7/30 (σ̄ 0.643)** | 23/30 (σ̄ 0.107) |
| Self-consistency — hard requirements | 20/30 (σ̄ 0.592) | **13/30 (σ̄ 0.310)** |
| Agreement vs human — skills | 0.287 | 0.523 |
| Agreement vs human — experience | 0.570 | 0.570 |
| Agreement vs human — education | 0.592 | 0.469 |
| Agreement vs human — hard requirements | 0.799 (n=149) | 0.846 (n=130) |
| Degraded `hard_requirements` assessments | 1 | **20** |
| Self-contradictions within a run | 15, on 8/30 pairs | 7, on 6/30 pairs |
| Tool-call structural correctness | 150/150 | 150/150 |

## The headline result: the outcome metric improved while the reasoning got worse

`gpt-4o-mini` looks strictly better on the number a conventional eval would report. It has **no
false negatives at all**, and its gate decision is **perfectly stable across all 30 pairs**.

The trajectory-level metrics disagree, and they disagree in the same direction on three
independent measures:

1. **Trigger attribution fell from 21/28 to 14/29.** More than half the delivery model's correct
   escalations cite a reason the human reference does not.
2. **`hard_requirements` degradations rose from 1 to 20.** The dimension that drives the veto
   fails to produce a usable answer in 20 of 150 runs.
3. **`gpt-4o-mini` never once scored `hard_requirements` = 5.** Its entire distribution is
   {0: 112, 3: 18}. The dev model's is {0: 125, 3: 5, 5: 19}.

That third fact explains the first two and undercuts the headline. **A model that never judges a
ledger fully met can never clear the veto**, so it escalates everything — and on a reference set
that is 29/30 gate-positive, escalating everything scores 29 TP and 1 FP. The perfect stability
is the stability of a constant function.

This is [finding 004](../findings/004-gate-truth-imbalance.md)'s warning arriving in concrete
form: with a degenerate positive class, the outcome metric cannot distinguish a better agent from
a more indiscriminate one. **The trajectory metrics can, and here they did.** If this project
reported only the confusion matrix, it would have recommended the model that reasons worse.

## Pre-registered predictions

Three predictions were recorded before this run, in findings 011 and 013, precisely so the
delivery model would be an uncontaminated test rather than a post-hoc story.

### 1. "Education is the least self-consistent dimension." — **DISCONFIRMED**

On `deepseek-chat`, education was the worst dimension by a wide margin: 7/30 pairs stable,
mean within-pair σ 0.643. On `gpt-4o-mini` it is among the *best*: 23/30, σ 0.107 — a
six-fold reduction in spread. `hard_requirements` is now the least stable dimension (13/30).

**Consequence for finding 011:** its per-dimension ranking is **provider-specific and not a
property of the rubric.** The rubric's education criteria are not inherently harder to apply;
one model applied them inconsistently. What survives is 011's *structural* claim — that a
variance floor exists and bounds every improvement claim — which holds on both models with
different shapes.

### 2. "The veto is bistable, swinging 0↔5." — **DISCONFIRMED, with a mechanism**

On `deepseek-chat` the prediction held: of 9 pairs whose veto moved across k, **5 swing 0↔5** —
"every item covered" versus "some item absent", with nothing in between.

On `gpt-4o-mini` there is no bistability, because **one of the two states never occurs.** The
score 5 is entirely absent from 130 assessments; all 7 moving pairs move 0↔3, i.e. between
*unmet* and *indeterminate*. The failure mode changed character: the dev model oscillates between
confident opposites, the delivery model hedges and degrades.

**Consequence:** the phenomenon 011 §3 described is real but not universal, and the two models
fail differently enough that a fix tuned to one would not address the other.

### 3. "Faithfulness failures concentrate in `hard_requirements`." — **NOT TESTED**

Stated plainly rather than answered with the nearest available number. Finding 013's result came
from ten **hand-judged** samples; no hand-judging was done on the delivery model, so the
prediction stands untested.

What *can* be reported is that the evidence-coverage **sentinel** — which flags assessments
warranting inspection and is explicitly not a faithfulness measure — inverted its concentration:
`hard_requirements` 10 → 7 flags, `skills_coverage` 2 → 15. That is a reason to look, not a
result. Reporting it as a refutation of 013 would be exactly the sentinel-as-metric error that
finding's own documentation warns against.

## What this section does not claim

- **No claim that either model is "better".** The two columns differ on one variable (the model)
  and the comparison is 30 pairs at k=5 on one rubric. The interesting content is *where* they
  differ, not which wins.
- **`hard_requirements` agreement is not comparable at face value.** The delivery model's 0.846
  is computed over n=130 rather than 149, because 20 assessments degraded and are excluded. A
  rate over a smaller, non-random denominator is not the same measurement.
- **Agreement gains on `skills_coverage` (0.287 → 0.523) are real but unattributed.** Whether
  they reflect better judgment or a different prior on band assignment is not established here.
