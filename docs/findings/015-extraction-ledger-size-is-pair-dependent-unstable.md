# 015 — The requirement ledger's SIZE is unstable on some pairs, and every hard verdict rests on it

**Status:** open (hypothesis stated, upstream link unverified) · **Phase:** P2 (variant stage)
**Date:** 2026-08-02 · **Not repaired — FROZEN (2026-08-04), issue #26.** Deferred past the cross-model stage and then
closed out with the research surface; the verification procedure below is written down so it stays
runnable, not because it is queued.

Distinct from [finding 006](006-granularity-consistency.md), which is about the human and the
agent bundling requirements differently. This one is the agent disagreeing **with itself**:
same input, same model, different number of ledger items.

## Observation

Diagnosing the variant batch required resolving the trajectory's opaque requirement ids
(`R1`…`Rn`) by re-running extraction. On `gn-02` that failed: the recorded run held a
**12-item** ledger, the re-extraction returned **2 items**, and no id could be mapped. That
prompted a direct measurement.

Repeated extraction, same model (`deepseek-chat`), identical input, item counts observed:

| pair | draws observed | range | verdict |
|---|---|---|---|
| train 5063 | 9, 9, 9, 9, 9 + run 9 | **0** | stable |
| train 3978 | 13, 13, 13 + run 13 | **0** | stable |
| train 6220 | 6, 6, 6 + run 6 | **0** | stable |
| train 4160 | 8, 9, 8, 9, 9, 8 + run 9 | 1 | near-stable |
| train 5798 | 7, 12, 9 + run 9 | 5 | **unstable** |
| train 3773 | 5, 5, 5, 2, 5, 4, 5 + run 12 | **10** | **unstable** |

**Instability is pair-dependent, not general.** Three of six pairs are perfectly stable
across every draw taken. Two are not, and train 3773 spans 2 to 12 items on the same JD.

Two claims made earlier in this investigation and **withdrawn against this data**: that
extraction is broadly unstable (it is not — most pairs are exact), and that the perturbed
resume was driving the variation (a single-variable check with the JD held constant showed
5063 at 9/9 both ways and 4160 at 9,9 vs 8,9 — no perturbation effect; 3773 is simply
unstable in both conditions).

## Hypothesis

**Stated as hypothesis, not conclusion.** `hard_requirements` is scored by ledger: an item
`absent` forces the veto to unmet (score 0), an item `partial` forces indeterminate (3), all
covered gives 5. If the denominator — how many items exist — is itself a draw, then the same
resume against the same JD faces a different bar on different runs. A 2-item ledger is far
easier to clear than a 12-item one.

That makes ledger-size instability a **candidate upstream cause** of the variance floor
measured in [finding 011](011-passk-variance-floor.md), and specifically of the veto
bistability recorded in its §3, where `hard_requirements` swings 0↔5 rather than drifting:
0↔5 is exactly "some item absent" versus "every item covered", and the item set is moving.

**This is unverified.** 011 measured that scores are unstable; it did not measure why. The
link is plausible and mechanically coherent, and that is all it is right now.

### How to verify (written down so it is testable, not just suggestive)

Pin the ledger and re-measure. Extract once per pair, cache the item set, and re-run the
assessment k times against the **frozen** ledger. If `hard_requirements` variance collapses
toward zero while the other three dimensions keep their 011 variance, ledger size is
confirmed as the driver. If hard stays as unstable as before, it is not, and the cause is in
the assessment step rather than the extraction step. Either outcome is informative, which is
what makes it worth running.

## Change

**None — deliberately.** The extractor is upstream of every `hard_requirements` verdict in
the project, so changing it invalidates every hard-related baseline recorded in P0, P1 and
P2 at once. It is queued behind the cross-model stage as a standalone single-variable
calibration with before/after, alongside the extraction-scope fix from
[finding 012](012-gate-fires-for-the-wrong-reason.md).

## Result

**Consequences already paid, recorded here so they are not re-discovered:**

1. **`gn-02` is undiagnosable** (eval-design 3c gate 5, state 3) — recorded against neither
   the construction nor the agent. After-the-fact id resolution only works while the
   extractor is stable, and on this pair it is not. The undiagnosable entry names this
   finding as its cause.
2. **The variant rebuild was declined partly on this basis.** Rewriting perturbations to
   satisfy the agent's own enumeration requires the enumeration to be a fixed target. On
   train 3773 it ranges from 2 to 12 items, so a perturbation written to satisfy 12 would
   face a different bar on the next run. This is why the negative set was left
   under-populated rather than repaired (see `rebuild_declined` in the variant spec).
3. **It supplies a second, independent mechanism for finding 004's TN=0** — see that
   finding's amended Result section.

## Scope limits, stated plainly

n = 6 pairs, 3–7 draws each, one model, one provider. Enough to establish that the
instability is real and pair-dependent; **not** enough to estimate a corpus-wide rate, and
not enough to say which JD properties predict it. The obvious candidate — that longer or
less structured requirement sections extract less consistently — was not tested.
