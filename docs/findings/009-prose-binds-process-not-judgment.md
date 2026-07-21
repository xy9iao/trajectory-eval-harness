# 009 — Across five calibration interventions, prose bound process but not judgment

**Status:** draft-for-owner-review — Observation and Verification complete; Change is the
owner's escalation decision (mechanism round vs honest-numbers reclassification); Result
follows that decision. **Date:** 2026-07-21 · **Phase:** P1 (calibration rounds 1–2)

**Reproduction:** batches of 2026-07-20/21 (`eval/reports/batch_vs_reference.py`); rounds
recorded in p1-design.md (calibration section, 表一/表二).

## Observation

Five interventions this week, split by kind:

| intervention | kind | target metric | held? |
|---|---|---|---|
| id carrier contract (dets = R-ids) | mechanism (wire schema + post_validate) | hygiene violations, det degradations | ✅ 10→0, stable 3 batches |
| symmetric substring rule | mechanism (post_validate) | dataset text in events | ✅ 30/30 clean ×3 |
| ledger consistency instruction | prompt, PROCESS-level ("agree with prior or explain") | contradictions | ✅ 8 → 2, stable across 2 batches |
| v1.2 "relevant = role-matching" definition | rubric prose, SEMANTIC redefinition | 596-class hard reading | ❌ unmoved |
| v1.3 worked negative example + band-0 discriminant | rubric prose, SEMANTIC | 596-class · 0/1 cluster | ❌ both unmoved |

The one prompt intervention that held regulated PROCESS (how to reconcile two of its own
outputs); the two that failed tried to re-bind JUDGMENT SEMANTICS (what "relevant" means;
where the 0/1 boundary sits). 596's hard reading survived an abstract definition AND a
worked negative example sitting directly in its prompt context — the model's justification
cites the surface phrase ("14 years of IT ... clearly meets the threshold") both times.

## Hypothesis

Instruction reliably binds form and process because compliance is checkable by the model
itself at generation time. Semantic re-binding fails where the model's prior reading of a
term ("relevant experience" ≈ any tenure) is strong: the definition is read, then the prior
wins at application time. If this holds, the fix ladder for semantic misreadings is
mechanism (structural cross-checks) or model change — more prose is spend without effect.

## Verification

表一/表二 in p1-design.md; runs 2026-07-20/21. Two consecutive rubric-prose rounds on the
same target with clean attribution (rubric-only round) and zero movement; three mechanism
interventions stable across all batches.

## Change — PENDING (owner escalation decision)

(a) mechanism round 3: cross-dimension structural rule (years-item cannot be `covered` when
experience_level evidences no role-matching segments) — note the tension: it converts
finding 008's scorer logic from measurement into enforcement, changing the object P2
measures; or (b) reclassify #3/#4 as honest P2 numbers (model-limitation class) and stop.
CC recommends (b); the dev model's semantic priors become part of what the cross-model
table measures (D12 — the delivery model may simply differ).

## Result — PENDING

Follows the owner's Change decision.
