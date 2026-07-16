# 002 — A JD with no stated skill musts leaves skills_coverage undefined

> **Status: closed** (promoted 2026-07-16). Rule decision made under the rubric-maintenance
> delegation (decisions.md log 2026-07-16): option (a), derived musts.

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

## Verification (P0 labeling complete, 2026-07-16)

Affected pairs over the full 30: **1/30** (train 596 only), enumerable via the cockpit's
auto-hesitation ("band geometry undefined") — `python eval/reports/label_stats.py`. The
hypothesis "such JDs are common" did NOT hold on this sample; the gap is real but rare here.
Recorded honestly: the rule's value is consistency insurance (and agent-parity — the P1 agent
reads whole JDs), not high frequency.

## Change — recorded (rubric v1.1, 2026-07-16)

**Option (a) adopted — derived musts** (CC decision under the rubric-maintenance delegation,
decisions.md log 2026-07-16): when a JD states no must-have skill requirements, skill
requirements are derived from the duties/responsibilities section (one requirement per duties
sentence naming concrete tools/technologies/skills, bundled per sentence), determined and
banded exactly like stated musts, provenance noted. Preferred-only skills stay excluded
(stance A unchanged). Options considered and set aside: (b) NA + weight renormalization
(schema change; headline dimension stops being comparable across pairs), (c) codified manual
fallback (smallest change but leaves the judgment surface unwritten).

## Result

Train 596 re-labeled under v1.1 (owner, 2026-07-16): **skills_coverage 0 → 1** via six
derived determinations (any-absent geometry; the recorded SQL adjacency makes one derived
item covered-adjacent, blocking the all-absent 0). Before/after: v1.0 manual fallback 0
(un-ruled judgment) → v1.1 ruled 1 — the score moved BECAUSE the rule was written, which is
the eval-informs-design loop in miniature. Affected-pair count: 1/30 (Verification).

Cross-references: train 596 record in `data/reference/labels-v1.jsonl` (hesitations field) ·
labeling protocol §7 rubric map, step 3 · rubric v1 `skills_coverage` design_notes (stance A).
