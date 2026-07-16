# 003 — Dataset labels diverge from rubric judgments on 6/30 pairs; "Good Fit" is the unreliable class

**Status:** closed — Change recorded (reference standard = rubric labels; dataset labels are
stratification devices only). **Date:** 2026-07-16 · **Phase:** P0 (labeling)

**Reproduction:** `python eval/reports/label_stats.py` over
`data/reference/labels-v1.jsonl` (30 records, committed) — divergence operationalization
recorded in the script docstring (Good Fit & mean < 2.5, or No Fit & mean ≥ 3.5).

## Observation

Owner labeled all 30 sampled pairs against rubric v1.1. 6/30 (20%) diverge from the dataset's
own labels: five pairs the dataset calls **Good Fit** score 0.5–2.4 on the rubric with the
hard-requirements veto firing (train 5798, 5699, 4928, 5707, 6236), and one **No Fit** pair
scores 4.0 (train 970, veto indeterminate). The first observed case predates the sample: the
rubric anchor pair train 4699 ("Good Fit"; rubric skills_coverage = 1, veto unmet) — recorded
as disagreement sample #1 during rubric authoring.

## Hypothesis

The dataset's labels were not produced by requirement-ledger screening logic — "Good Fit"
tolerates unmet stated musts (missing years, missing hard skills). Divergence therefore
concentrates in the Good Fit class, and the dataset label is usable as a *difficulty/stratum
signal* but not as ground truth for a screening agent.

## Verification

`label_stats.py` (2026-07-16): 5/10 sampled Good Fit pairs carry veto `unmet`; divergent
pairs 6/30 with 5/6 in Good Fit; dataset-label × owner-veto crosstab shows veto `unmet`
across all three classes (9/8/7), i.e. the dataset classes barely separate on the rubric's
strictest signal.

## Change

Already structural, now recorded with numbers: the project's reference standard is the
owner's rubric labels (`labels-v1.jsonl`), not the dataset labels. Dataset labels serve
exactly two purposes — sampling stratification (protocol §2) and this divergence analysis.
P2 agreement metrics are computed against the rubric labels only.

## Result

The 30-pair reference set is built on rubric labels; the 20% divergence rate (and its
Good-Fit concentration) is the recorded justification. Interview-ready formulation: "we
measured our reference standard against the dataset's labels and kept the one that has a
written, reproducible procedure behind it."
