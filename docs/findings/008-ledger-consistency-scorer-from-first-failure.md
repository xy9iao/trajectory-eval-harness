# 008 — The first live gate miss donated a new scorer class: internal ledger consistency

**Status:** open — Observation final; **Verification complete (30-pair dev batch,
2026-07-21)**; Change (scorer implementation) and Result land in P2. **Date:** 2026-07-20/21
· **Phase:** P1 → P2

**Reproduction:** run `r20260720T094231-3ae875` (train 596, DeepSeek dev, first live run).

## Observation

The agent matched the owner's reference labels EXACTLY on all three scoring dimensions
(skills 1 — correctly applying the v1.1 derived-musts rule; experience 1; education 3;
aggregate 1.4 = the relabeled reference) — and produced a gate miss anyway:
hard_requirements = 5 (veto met) vs the reference's 0 (unmet, `gate_expected: true`). The
trajectory shows WHY, and it is not just semantic ambiguity: the run contradicts itself.
Its experience_level determination reads "**absent** — Four or more years of relevant work
experience (Data Engineering/AI)"; its hard_requirements ledger, four events later, marks
the same requirement "**covered**" — despite the hard prompt explicitly reusing prior
determinations. First gate-integrity false-negative specimen, with its pathology in the log.

## Hypothesis

Two separable components: (1) genuine ambiguity of the JD's "relevant" (rubric debt — the
reference reading "relevant = role-matching" lives in the owner's notes, not in rubric
text); (2) an agent-error class that needs NO ground truth to detect: intra-run
contradiction between the ledger and the dimensions it claims to reuse.

## Change — a third scorer class for P2 (recorded in p1-design.md)

Existing scorer families either compare against external reference (agreement,
faithfulness) or check execution contracts (tool-call correctness, gate integrity). Ledger
consistency is a third kind: **internal coherence of the agent's own outputs** — zero
annotation cost, the trajectory testifies against itself. Structural rule: every
hard_requirements ledger determination that references a requirement judged by a prior
dimension must agree with that dimension's determination; disagreement = flag. Implemented
in P2 with the planted-defect discipline; this run is the first known-positive test case.

## Verification (30-pair dev batch, 2026-07-21 — `eval/reports/batch_vs_reference.py`)

The contradiction class is real and frequent: **8 contradictions across 7/30 pairs (23%)**,
dominant pattern `skills=absent` vs `hard=covered` on the same item id — the train-596
pathology recurring at scale (pairs 935, 3148, 3773, 4715, 5063, 5707, 5798). Carrier
contract v2's id labels made detection exact (no fuzzy text matching). Same batch, adjacent
evidence: gate confusion vs reference = TP 27 · FN 2 (596, 5084) · FP 1 (4715) · **TN 0** —
the reference set's single negative pair drew a false alarm, finding 004's degeneracy
prediction observed in vivo.

## Result — PENDING

P2 scorer implementation (this batch is its known-positive test set) + the post-calibration
delta.
