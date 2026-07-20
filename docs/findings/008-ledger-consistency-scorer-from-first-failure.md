# 008 — The first live gate miss donated a new scorer class: internal ledger consistency

**Status:** open — Observation final; Verification pending the 30-pair dev batch; Change
(scorer implementation) and Result land in P2. **Date:** 2026-07-20 · **Phase:** P1 → P2

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

## Verification / Result — PENDING

Verification: the 30-pair dev batch counts ledger contradictions (plus gate misses and
semantic divergences) for the single calibration pass (stop-loss discipline: classify →
one decision round — prompt debt vs rubric debt vs honest P2 numbers → dev-model rerun
before/after). Result: P2 scorer implementation + its numbers.
