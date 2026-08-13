# 011 — pass^k sets the variance floor: three readings from one measurement

**Status:** closed (P2, pass^k stage, 2026-07-28). Settles the accounts left open by findings
009 and 010; §3's mechanism observation is recorded, not acted on. **Phase:** P2

**Reproduction:** `python eval/reports/passk_report.py runs/passk-r20260728T035619-2d6bcd.json`
— k=5 × 30 reference pairs, deepseek-v4-flash, 150/150 runs structurally valid, 0 excluded.
Figure: `docs/phase-reports/figures/passk-deepseek-v4-flash.png`.

Three sections, three certainty levels: §1 settles an open account (high), §2 reports a
cross-validation (medium — correlation, explicitly not causation), §3 describes a mechanism
with retrospective value (descriptive).

## Measurement

| dimension | all k runs identical | self-consistency rate | mean within-pair stdev | max |
|---|---|---|---|---|
| education_domain_fit | 7/30 | 0.233 | 0.643 | 1.0 |
| skills_coverage | 12/30 | 0.400 | 0.445 | 1.2 |
| experience_level | 17/30 | 0.567 | 0.345 | 1.6 |
| hard_requirements | 20/30 | 0.667 | 0.592 | 2.449 |

Gate decision identical across all 5 runs: **26/30 (0.867)**; recommendation likewise 26/30.
28/30 pairs flipped at least one dimension or the gate. *Self-consistency* here means the
model versus itself under fixed inputs — it is not the same measurement as *agreement*
(scores versus the human reference), and §2 depends on the distinction.

## §1 — Main result (settles findings 009 and 010's open account)

skills_coverage moved 13→7→9 exact-agreement across three single-run batches during P1
calibration, and it was unclear whether those moves were calibration drift or noise. Its
run-to-run self-consistency under fixed inputs is **0.400 with a mean within-pair stdev of
0.445** — the observed cross-batch movement sits inside that band.

**Single-round agreement fluctuation cannot be attributed to calibration; pass^k has
quantified it as model variance.** The account carried by findings 009 and 010 is settled: no
claim about calibration effect on skills survives its own error bar, and future single-run
agreement figures must be read against this floor.

## §2 — Cross-validation: education_domain_fit is lowest on two methodologically independent paths

education_domain_fit is bottom-ranked by both of the project's stability measurements:

| path | measurement | education result | what it uses |
|---|---|---|---|
| human reference (P0 touchpoint 1, finding 010) | owner vs mentor exact agreement | **8/10** (lowest of four dimensions) | human labels, a fixed reference, two annotators |
| zero-reference (this finding) | model self-consistency across k=5 | **0.233** (lowest of four dimensions) | no labels, no reference, one model against itself |

The two share only the rubric dimension they measure; the measurement machinery does not
overlap at all — one needs two humans and a reference standard, the other needs neither. Their
coincidence is therefore not a tautology: **the same rubric axis was independently identified
as the least reproducible by two instruments that have no common failure mode.** This is where
finding 010's prediction ("the adjacency axis is where P2's agreement will be weakest") meets
its first test, from a direction 010 could not have used.

Sharper than the rate: on the strip plot, **education has almost no pairs at stdev 0.0**,
while hard_requirements has ~20. Low self-consistency on education is not a few hard pairs
lifting the mean — there is almost no pair in the reference set that the model reproduces
identically across runs. The property is distribution-wide, not tail-driven.

**Bounded by finding 013 (2026-07-28):** the hypothesis below concerns SCORE
STABILITY only. Faithfulness data separated the two properties — education was among
the better-evidenced dimensions while hard_requirements, the most self-consistent one,
produced every evidence failure. A dimension the model reproduces reliably can be
reliably badly evidenced; do not carry this hypothesis over to evidence quality.

*Hypothesis for future work (explicitly not a conclusion):* one reading is that a rubric axis
that is under-specified for humans is also under-determined for a model, so both instruments
register it as unstable. The data here support only the correlation — both measurements are
lowest on the same dimension — not the mechanism. The cross-model stage is the next
opportunity to test it: if education is also bottom-ranked on the delivery model, the property
belongs to the rubric axis; if not, it is provider-specific.

## §3 — Mechanism observation: hard_requirements is bimodal, and gate instability is its strict subset

hard_requirements has the **highest** self-consistency (0.667) and the **largest** maximum
within-pair stdev (2.449). The strip plot shows why these coexist: roughly 20 pairs sit at
exactly 0.0, then a visible gap, then 5–6 pairs at 1.2–2.45. **Bimodality is defined by the
absence of a middle** — the gap in the strip is the direct reading that intermediate states do
not occur: the score does not drift continuously, it jumps between attractors.

Numerators (from the same batch):

| quantity | count |
|---|---|
| pairs where hard_requirements flips at all | 10/30 |
| pairs swinging between **0 and 5** (the two veto poles) | **7/30** |
| pairs whose gate decision is not constant | **4/30** |
| **overlap: gate-unstable ∩ veto-swinging** | **4/4 — every gate-unstable pair is a veto-swinging pair** |

The four: train 596 `hard=[0,3,5,0,5]`, 970 `[5,3,5,0,5]`, 5084 `[0,0,5,5,5]`,
6220 `[0,0,0,0,5]`. The inclusion is strict in one direction only: 3 of the 7 veto-swinging
pairs (3148, 4715, 5798) kept a constant gate decision because other triggers
(boundary/anomaly) fired regardless — **the multi-trigger design absorbed the swing in 3 of 7
cases**, which is the first quantified evidence that trigger redundancy does work.

Retrospective value: P1 decision 5c (veto cap 2.4, hard_requirements as a one-vote veto) was
designed on the assumption that the veto determination is stable. Under fixed inputs it is
not, on 7/30 pairs. This is the second time evaluation has fed back into gate design (the
first was calibration round 1) — but it is **recorded, not acted on**: P2's job is
measurement, threshold revision is a later decision, and the cross-model stage must first show
whether the bimodality is provider-specific.

## Result

The variance floor is established and is now a required denominator for every downstream
single-run metric in P2 (gate integrity, agreement). Findings 009 and 010's open account is
closed by §1. §2's cross-validation and §3's mechanism observation carry into the cross-model
stage as pre-registered checks: does education stay bottom-ranked, and does the veto
bimodality persist?
