# 009 — Across five calibration interventions, prose bound process but not judgment

**Status:** closed at P1 scope (owner ruling 2026-07-21: option b); cross-model follow-up
is a pre-committed P2 item. **Date:** 2026-07-21 · **Phase:** P1 (calibration rounds 1–2)

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

## Change (owner ruling, 2026-07-21: option b — stop calibrating; reclassify)

#3/#4 reclassify as **model-limitation, honest P2 numbers**. Rationale, both halves on
record: (1) the semantic prior may be provider-specific — spending mechanism budget on
DeepSeek's reading may fix a problem the delivery model does not have; the cross-model table
(D12) is the instrument that decides. (2) Option (a) would make agent output a composite of
model judgment + mechanical correction: P2's agreement would then measure the corrected
system, not the model — the right choice for a production tool and the wrong one for a
research harness. **The framework's job is to make failure visible, not to make it
disappear**; 596 at 5vs0 — two semantic rounds, zero movement, the prior quotable in its own
justifications — is a complete model-limitation evidence chain, and "fixing" it would burn
the exhibit. Marginal-return account: mechanism gains are banked (ledger 8→2 stable, hygiene
3×30/30 clean); semantic prose is two rounds flat — the evidence-then-fix discipline has a
mirror clause: when the evidence says it won't fix, stop. Cleanest place to stop is here.

**P2 pre-commitment (owner instruction):** the agreement chapter stratifies per-dimension
agreement BY DIVERGENCE ROOT CAUSE — the semantic-prior class (596-class, 0/1 cluster)
reported separately from other divergence, so low headline numbers carry their explanatory
structure instead of being averaged into one unexplained figure.

## Result

At P1 scope the reclassification IS the result: targets left unmoved by design, evidence
chain preserved intact for P2. Scientific-status annotation (owner, recorded): **n is small
— five interventions, one model. This is a working hypothesis, not a law**, until the
cross-model table: if the delivery model lacks the prior, the hypothesis gains its second
data point; if it shares it, that is a finding too. Both directions are content — that is
the shape of a good hypothesis.
