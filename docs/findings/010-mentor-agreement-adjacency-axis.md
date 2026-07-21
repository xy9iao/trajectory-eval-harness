# 010 — Mentor agreement: 90% exact, and every disagreement is on the adjacency axis

**Status:** closed (P0 touchpoint 1, 2026-07-21). **Date:** 2026-07-21 · **Phase:** P0

**Reproduction:** `python eval/reports/label_stats.py` over `data/reference/labels-v1.jsonl`
(owner) and `labels-v1-mentor.jsonl` (mentor, blind, rubric v1.3).

## Observation

The mentor blind-labeled 10 flagged pairs. Exact per-dimension agreement: experience 10/10,
skills 9/10, hard 9/10, education 8/10 — **36/40 (90%)**. gate_expected: **10/10**. All four
disagreements localize to a single axis — *adjacency / occupation-boundary strictness*:
596 & 4890 education (how a degree's field maps to an occupation when no field is stated-
required; the two diverge in OPPOSITE directions), and 5798 skills+hard (whether an EE
degree + reliability experience transfers as adjacent coverage of electrical-testing musts).
No disagreement touched evidence presence, band geometry, or veto wiring.

## Hypothesis

The rubric's mechanical layer (three-value determination, band geometry, veto) is
reproducible across annotators; its *judgment* layer — how strictly "related field,"
"adjacent skill," and "occupation match" are read — is not, and is its least-specified axis.
If so, this is exactly where P2's agent-vs-reference agreement will also be weakest, and
education_domain_fit (lowest human-human agreement, 8/10) is the dimension to watch.

## Verification

Two independent annotators, blind, same rubric (v1.3 — confirmed; the packet's printed "v1.1"
was a stale hardcode, fixed PR #18). Disagreements 4/40, 100% on the adjacency axis, education
diverging in both directions across pairs. The mentor *predicted* the 5798 split in her notes
and still gated it.

## Change

The disagreements are **classified, not resolved** (a disagreement is a signal to route, not
an error to eliminate — D4). Three-class discriminant + first-pass tables in p0 report §5b:
the 4 inter-annotator rows are rubric-gap (596, 4890) / ambiguous-label (5798); the broader
agent-vs-reference set is pattern-classified so P2 inherits a populated ledger. Disposition
per class: rubric-gap → changelog candidate; ambiguous-label → protocol limitation + second-
annotator signal; agent-error/model-limitation → counts against the agent in P2. No score
adjudicated, no rubric revised now.

## Result

**The phase's sharpest result: dimension-score disagreement (4/40) produced zero gate
disagreement (0/10).** The veto + boundary structure absorbed sub-dimension noise — including
on 5798, the pair the mentor herself judged closest to "advance without review." The gate
ground truth is robust to inter-annotator variance that the raw scores are not. Interview
formulation: "two annotators disagreed on 4 of 40 dimension scores and on 0 of 10 gate
decisions — the gate is the stable unit, which is the unit that matters."
