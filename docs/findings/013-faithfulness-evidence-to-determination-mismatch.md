# 013 — Faithfulness fails by evidence-to-determination mismatch, not by weak quotes

**Status:** closed at P2-measurement scope (2026-07-28). Change candidates recorded, none
taken — P2 measures; the cross-model stage decides whether this is provider-specific.
**Phase:** P2 (semantic tier)

**Reproduction:** `python -m eval.faithfulness --manifest
runs/passk-r20260728T035619-2d6bcd.json --show` over the k=5 corpus (150 runs,
deepseek-v4-flash); verdicts in `data/reference/faithfulness-v1.jsonl`. Corpus-wide ratio
figures recomputed from the same manifest.

## Method, and what it can and cannot say

Ten assessments judged by the owner: does the cited evidence support the score at that band?
Scale: supports / partially supports / does not support, with a mandatory reason on
"partially" (eval-design 3d).

**The sample is STRATIFIED, not random** (3 education · 3 veto-swing · 2
degraded-or-resolution-failure · 2 random). It is a probe of three known weak spots plus a
baseline. **No overall faithfulness rate exists in this finding and none may be derived from
it** — a stratified draw cannot estimate a population.

*Judgment-boundary check (method quality):* the two "partially" verdicts both cite
"quote too weak for the band", and none of the three "does not support" verdicts were about
strength — all three were structural (missing or category-wrong evidence). The two categories
did not bleed: **does-not-support = structural defect, partially = strength shortfall.** The
boundary held across all ten, which is what makes the small sample worth reporting at all.

## Measurement

| dimension | verdicts | independence |
|---|---|---|
| **hard_requirements** | 1 supports · **3 does not support** | **3 distinct pairs / 4 evaluations** — train 5084 was sampled twice (two runs of the same pair), so this is 3 documents, not 4 independent observations |
| education_domain_fit | 2 supports · 1 partially | 3 pairs / 3 evaluations |
| experience_level | 1 supports · 1 partially | 2 pairs / 2 evaluations |
| skills_coverage | 1 supports | 1 pair / 1 evaluation |

Every "does not support" verdict landed on hard_requirements. One of them (train 5798) came
from the **random** stratum — consistent with a dimension-level rather than
veto-swing-subset-level property, **but n=2 in the random stratum cannot establish it**.

## §1 — Disconfirmation: self-consistency and faithfulness are separable (first-tier result)

Finding 011 §2 established education_domain_fit as the least self-consistent dimension
(0.233) and the lowest human-agreement one (8/10), and hypothesised that an under-specified
rubric axis is unstable for humans and models alike. **That hypothesis does not extend to
evidence quality.** Education was among the better-behaved dimensions here (2 supports, 1
partially, 0 failures), while hard_requirements — the *most* self-consistent dimension in
011 (0.667) — produced every faithfulness failure.

**A dimension the model reproduces reliably can be reliably badly evidenced.** The two
properties are separable in this data, so 011 §2's hypothesis is hereby bounded: it concerns
*score stability*, and may not be carried over to *evidence quality* without its own
evidence. A hypothesis that survives this kind of boundary test is falsifiable rather than
all-purpose — which is the more useful thing to own.

## §2 — Mechanism: cardinality mismatch and category mismatch, not weak quotes

All three failures passed D7's existing contract — every quote existed and resolved back to
the document — and still failed to support their conclusions. Two distinct defects:

**(a) Cardinality mismatch.** hard_requirements is a ledger: one determination per must-item.
The failures carry far fewer spans than determinations:

| case | determinations | evidence spans | ratio |
|---|---|---|---|
| train 5084 (run A) | 10 | 1 | 10:1 |
| train 5084 (run B) | 10 | 1 | 10:1 |
| train 5798 | 18 | 6 | 3:1 |

Nine of ten determinations in the 5084 runs have no evidence of their own; they inherit a
shared pointer. This is not weak evidence per determination — it is **most determinations
having none**.

Corpus-wide, the ratio separates the two determination-bearing dimensions cleanly (149–150
assessments each, same manifest):

| dimension | median det/span | max | assessments with >3 determinations per span |
|---|---|---|---|
| skills_coverage | 1.2 | 8.0 | 11/150 |
| **hard_requirements** | **2.0** | **14.0** | **32/149** |

So the three sampled failures are not anecdotes: the dimension they came from is
systematically the one where determinations outnumber their evidence.

**What the distribution does and does not show.** It establishes that cardinality
mismatch is *prevalent in hard_requirements*. It does NOT establish that the
high-ratio assessments are unfaithful — only three assessments have been verified by a
human, and a high ratio can be legitimate (one substantive passage genuinely covering
many must-items). Prevalence of the structural condition and incidence of actual
unfaithfulness are two claims; only the first has corpus-wide support.

**(b) Category mismatch.** Two failures cite material that cannot serve as evidence for the
claim being made:

- *train 5084 run A* — the single span is JD text ("Experience in customer-facing pre-sales,
  technical architecture guidance, or consulting") used to support ten `covered`
  determinations. `covered` asserts something about the RESUME; JD text is the proposition to
  be proven, not evidence for it. **The literal form of circular argument.**
- *train 5084 run B* — the single span is the resume's Summary self-claim ("around 7 years of
  experience as a Big Data Engineer"). The rubric explicitly excludes Summary self-claims from
  evidenced years (`experience_level` scope_notes). Material barred by rule is not weak
  evidence; it is **non-evidence** — which is why this is category, not strength.

**Citing the JD is not itself the defect.** train 5798's six spans are all JD must-clauses,
and that is correct usage: identifying *what is required* is exactly what JD text establishes.
The defect in 5084 run A is using JD text to establish *what the resume contains*. The
distinction is between defining the requirement (legitimate) and proving its satisfaction
(illegitimate).

## §3 — Cross-reference: the same failure family as finding 009

The rubric's exclusion of Summary self-claims is in the prompt — the full rubric slice is
supplied at assessment time — and the model used the excluded material anyway. Finding 009
recorded that a written *definition* is read and then overridden by a prior at application
time; this is the same shape with an *exclusion rule*: **rationalization overrides the rule
that forbids it.** Both are instruction binding form but not judgment (009's hypothesis),
which is why the change candidates below are mechanisms rather than prose.

## Change candidates — RECORDED, NOT TAKEN

D7's contract currently verifies that a quote exists and resolves. It does not verify any
correspondence between quotes and the determinations they are supposed to support. That hole
is structural and mechanically closable:

1. **Per-determination spans (schema-level).** Require each determination to carry its own
   span rather than sharing a dimension-level `evidence_spans` list. Under finding 009's
   taxonomy this is a mechanism fix — the class with a 3/3 record on this project, against
   0/2 for prose.
2. **`determinations / evidence_spans` ratio as a standing sentinel.** — **ADOPTED**
   (owner ruling 2026-07-28, decisions.md; `eval/scorers/evidence_coverage.py`). A
   measurement rather than a repair, so it is P2-legal, and it converts a 20-minute manual
   probe into a permanent automatic pointer — the role `resolution_failures` plays for
   degradation. Threshold 5x; on this corpus it flags **12/299 assessments, 10 of them
   hard_requirements**.

   **Binding semantics, and a known miss.** The sentinel says "this warrants human
   inspection", never "this is unfaithful": a high ratio may be legitimate, and a normal
   ratio guarantees nothing (5084 run A's category error would have been just as wrong at
   1:1). Concretely, **it does not catch train 5798** — 18 determinations over 6 spans is
   3.0, below threshold, yet a human judged it unsupported. Two of three verified failures
   are inside its pool; one is not. That is the exact sense in which it is a sampling aid,
   not a detector, and it is why the raw ratio is never reported as a score — only the flag
   count and where the flags cluster.

Change 1 is not applied now: the cross-model stage must first show whether the pattern is
provider-specific (the standing reason, cf. findings 009 and 012).

## Result

Faithfulness on this corpus fails structurally, not gradually: the failures are determinations
without evidence and evidence of the wrong category, both of which pass the current contract.
The finding also bounds finding 011 §2's hypothesis to score stability. Sample discipline
stands: ten stratified probes on known weak spots, 3 distinct pairs behind the
hard_requirements failures, and no population rate claimed anywhere.
