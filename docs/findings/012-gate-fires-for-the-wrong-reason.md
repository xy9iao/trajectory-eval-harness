# 012 — [STUB] The gate fires for the wrong reason on 7/28 true positives

**Status:** stub — Observation only (2026-07-28). Verification and Change deliberately empty:
root-causing waits for the cross-model stage, because the suspected driver overlaps finding
011 §3's veto instability and may be provider-specific. Opening a numbered record now so this
stops being a footnote — P1 raised it qualitatively (train 596, "fired right for the wrong
reason"), and this is its first quantification.

**Reproduction:** `gate_integrity_scorer` over the k=5 pass^k corpus
(`runs/passk-r20260728T035619-2d6bcd.json`, 150 runs, deepseek-chat), reference =
`data/reference/labels-v1.jsonl`.

## Observation

Of the 28 pairs the confusion matrix counts as true positives, **21 fired for a reason the
reference lists; 7 did not** (`trigger_attribution_ok: 21/28`). Those 7 are scored as perfect
successes by any binary should-gate × did-gate matrix: the gate fired, the reference said it
should, cell = TP. The disagreement is entirely in *why*.

Example — train 400: reference reason `hard_unmet`; the agent fired with
`hard_indeterminate`, `hard_unmet`, `insufficient_evidence` across its runs. The pair is
gated either way, but the stated cause differs between runs and from the reference.

This is a **capability-boundary statement about the gate-integrity scorer itself**: the binary
matrix measures *whether* the gate fires; trigger attribution measures *why*. They are two
distinct measurements of the same event and must never be collapsed into one number — the
same vocabulary discipline as *self-consistency* vs *agreement* (finding 011 §2). Reporting
28/30 alone is misleading; the report presents the two figures side by side, always.

## Hypothesis (not yet tested)

The wrong-reason firings likely overlap finding 011 §3's veto instability: `hard_indeterminate`
is itself the product of an unstable ledger determination, so a pair whose veto state swings
between runs will also swing its stated trigger. If so, this is a symptom of the same
bimodality, not an independent defect — and possibly provider-specific.

## Verification — PENDING (cross-model stage)

Deliberately empty. Chasing the root cause before the delivery-model run would risk opening a
case on a provider-specific phenomenon — the same reasoning that left 596's semantic-prior
divergence unfixed in P1 (finding 009).

## Change — PENDING

None taken. The structural-scorer stage's job is to build the instrument and let it surface
the problem; fixing is a later decision with its own attribution discipline.
