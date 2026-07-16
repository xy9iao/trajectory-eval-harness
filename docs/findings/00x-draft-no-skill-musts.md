# [DRAFT — PENDING] A JD with no stated skill musts leaves skills_coverage undefined

> **Status: pending draft — do not cite.** CC-drafted from labeling session 1; owner to
> double-check the characterization. A number is assigned at promotion. The Change is an
> owner rubric decision (v1 → v1.1), to be made **between labeling sessions**, never mid-pair.

## Observation (labeling session 1, 2026-07-16 — train 596, the first sampled pair)

The JD's "You'll need to have" list contains only two items: a degree-OR-experience floor and
a relevant-years floor. Every technology mention (Teradata, Hadoop stack, GCP/BigQuery,
Tableau/Looker) sits in the "Even better if you have" list, which stance A excludes from
banding; the duties section describes data-pipeline work but states no requirements.
`skills_coverage` — the 0.5-weight dimension — operates on *must-have skill requirements*, so
it had **zero inputs**: band geometry undefined (auto-recorded by the cockpit). The owner
scored 0 manually with sound screening logic ("QA/testing resume, data-engineering role,
only overlap is SQL in a QA context") — but that reasoning runs over duties and
preferred-stack content, exactly the material the rubric's own rules exclude. The heaviest
dimension was scored outside its rules on the very first real pair.

## Hypothesis

JDs that state no formal skill musts are common — real postings routinely bury requirements
in duties prose or mark everything as preferred. Without a written rule, handling varies
across pairs and annotators (mentor included): the same situation could get a duties-derived
0 on one pair and a benefit-of-the-doubt mid-band on another. That variance lands directly in
the reference labels, and later in P2 it becomes unattributable noise: rubric-vs-agent
disagreement on such pairs cannot be classified as agent error vs rubric gap.

## Verification — PENDING

- Count affected pairs as labeling proceeds: the cockpit's auto-hesitation ("no skills must
  items; band geometry undefined") makes them enumerable from `labels-v1.jsonl`.
- Optional corpus-level directional scan: unique JDs whose must-language sentences contain no
  skill-like terms (taxonomy patterns give the must-language side; the skill-term side would
  need a defined list — record the method with the count if run).

## Change — PENDING (owner decision, rubric v1 → v1.1, between sessions)

Candidate rules, each with a cost:

- **(a) Duties-derived musts:** when a JD states no skill musts, derive skill requirements
  from the duties section by a defined procedure. Cost: a new judgment surface (which duties
  count?) — the ambiguity stance A existed to avoid.
- **(b) NA + renormalize:** `skills_coverage` is not-applicable for such pairs; weights
  renormalize over the remaining scoring dimensions. Cost: schema change (`score: null`),
  and pairs stop being comparable on the headline dimension.
- **(c) Codified fallback:** keep the manual score but write down what it may consider
  (e.g. duties yes, preferred no) and what the default band is. Cost: smallest change, but
  partially contradicts stance A and must say so explicitly.

Whichever rule lands: already-labeled pairs get re-checked under it (protocol §1), and the
decision is logged as a rubric revision (p0 report §2.2).

## Result — PENDING

Closes when the v1.1 rule is ratified and affected pairs are re-checked; before/after =
labels under fallback vs under the written rule, plus the affected-pair count from
Verification.

Cross-references: train 596 record in `data/reference/labels-v1.jsonl` (hesitations field) ·
labeling protocol §7 rubric map, step 3 · rubric v1 `skills_coverage` design_notes (stance A).
