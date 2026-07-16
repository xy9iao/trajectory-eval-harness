# [DRAFT — PENDING] A JD with no stated skill musts leaves skills_coverage undefined

> **Status: Change recorded (rubric v1.1, 2026-07-16); Result pending.** A number is
> assigned at promotion. The rule decision was made under the rubric-maintenance delegation
> (decisions.md log 2026-07-16): option (a), derived musts.

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

## Change — recorded (rubric v1.1, 2026-07-16)

**Option (a) adopted — derived musts** (CC decision under the rubric-maintenance delegation,
decisions.md log 2026-07-16): when a JD states no must-have skill requirements, skill
requirements are derived from the duties/responsibilities section (one requirement per duties
sentence naming concrete tools/technologies/skills, bundled per sentence), determined and
banded exactly like stated musts, provenance noted. Preferred-only skills stay excluded
(stance A unchanged). Options considered and set aside: (b) NA + weight renormalization
(schema change; headline dimension stops being comparable across pairs), (c) codified manual
fallback (smallest change but leaves the judgment surface unwritten).

## Result — PENDING

Closes with: (1) the train 596 skills determinations re-checked under the v1.1 rule at the
next labeling session (~2 min; the current 0 stands if all derived items are absent — the
recorded SQL-adjacency note may move it to 1 via any-absent geometry, which is exactly the
before/after this finding needs); (2) the affected-pair count over the 30 as labeling
proceeds (cockpit auto-hesitations make these enumerable).

Cross-references: train 596 record in `data/reference/labels-v1.jsonl` (hesitations field) ·
labeling protocol §7 rubric map, step 3 · rubric v1 `skills_coverage` design_notes (stance A).
