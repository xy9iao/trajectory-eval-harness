# 004 — Gate ground truth is 29/30 positive — the P2 confusion matrix starts degenerate

**Status:** open — Observation final (P0 labeling complete, 2026-07-16); Change lands in P1
gate design; Result closes in P2. **Date:** 2026-07-16 · **Phase:** P0 → P1/P2

## Observation (P0 labeling complete, 2026-07-16)

Over the 30-pair reference set: `gate_expected` = **29/30**. Drivers: hard-requirements veto
fires on 24/30 (`hard_unmet`), 5 more are `hard_indeterminate`; `anomaly` is flagged on
10/30 (garbled/broken document text in the source corpus); only ONE pair
(`gate_expected: false`) represents the "clean pass" class.
Reproduction: `python eval/reports/label_stats.py`.

## Hypothesis

Two compounding causes: (1) the corpus pairs resumes and JDs loosely, so most pairs
genuinely fail stated musts — real screening corpora are gate-heavy by nature; (2) the soft
veto's strictness (any unmet must → gate) converts that base rate directly into gate ground
truth. Neither is a labeling error — but a confusion matrix with 29 positives and 1 negative
cannot measure false-positive behavior (gate fires when it shouldn't) at all.

## Verification — PENDING (P2 design work)

The imbalance is established; what needs verification is the remedy's effect on
gate-integrity measurement.

## Change — PENDING (P1/P2, recorded intentions)

- P1 gate thresholds must be chosen knowing the base rate (a gate that always fires is
  trivially "correct" on this set).
- P2 gate-integrity reporting stratifies by trigger type (`hard_unmet` vs
  `hard_indeterminate` vs `boundary`/`anomaly`) rather than one aggregate matrix.
- The P2 seed set's planned variants (roadmap: "~30 seed cases = P0 pairs + variants")
  should deliberately include non-gating variants (musts satisfied) to populate the
  negative class.

## Result — PENDING

Closes in P2 with the stratified gate-integrity numbers and the variant-set composition.

**Mechanism supplied (2026-07-31):** [finding 014](014-low-road-negative-is-structurally-unconstructible.md)
shows TN=0 is not a sampling accident. The hard-requirement ledger reuses the determinations
that produce the scoring bands (28/30 ledgers say so in prose), so "meets every must, still
below the advance floor" asks two coupled variables to move in opposite directions — a
region occupying 16/216 band combinations and 0/30 reference pairs. The negative class in
this batch is therefore populated by the **high road only**, and the third bullet above is
amended accordingly: non-gating variants are built by raising a pair to `advance`, not by
holding it at `do_not_advance`.

**Second mechanism (2026-08-02):** the high road is also structurally hard, for an unrelated
reason. Building one means satisfying every item the agent's ledger enumerates — but
[finding 015](015-extraction-ledger-size-is-pair-dependent-unstable.md) shows that on some
pairs the ledger's *size* is a draw (train 3773 ranged from 2 to 12 items on the same JD).
A perturbation cannot be written to clear a bar whose height is sampled per run. Three of
four high-road attempts failed, and the batch closed with **TN=1**.

So TN=0 has two independent structural causes, not one accident: the low road is nearly
empty by score geometry, and the high road is hard to construct against a moving ledger.
That conclusion is worth more than the six true negatives the batch was built to collect.

**Third layer — the one that matters most (2026-08-02):** the missing negative class does
not merely degrade a metric, it makes a whole class of defects **unobservable**. Every one
of the 30 reference pairs deserved a gate, so no live run could ever show the gate firing
for the wrong reason. [Finding 012](012-gate-fires-for-the-wrong-reason.md)'s availability-
requirement defect sat undetected across 150 runs for exactly this reason: both affected
pairs already failed for legitimate reasons, and the spurious trigger hid behind them. It
surfaced only when a variant repaired every real failure and left the boilerplate item
standing alone.

This is the strongest available justification for constructing negatives at all — the batch
returned one true negative and one fully diagnosed defect that 150 live runs could not have
produced.
