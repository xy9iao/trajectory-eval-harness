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
