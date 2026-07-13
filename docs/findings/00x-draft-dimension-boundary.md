# [DRAFT — PENDING] Unbandable case exposed a missing dimension boundary (years → experience_level)

> **Status: pending draft — do not cite.** A number is assigned at promotion (001 is reserved
> for owner-vs-dataset disagreement, owner note 2026-07-13). Verification and Result await P0
> labeling (does cross-dimension annotation hesitation drop?) or P2 numbers.

## Observation (owner, 2026-07-13)

While stress-testing skills_coverage criteria against train row 4699: the JD's Java requirement
(5+ years) meets a resume showing ~2.5 years of hands-on Hibernate/Spring work. The case fit
none of the 5/3/1 band definitions — evidence *strength* said high band, evidence *quantity*
said low band. Two annotators could defensibly assign different bands.

## Hypothesis

The criteria were not vague — a **dimension boundary was missing**. skills_coverage was
absorbing a quantity judgment ("enough years?") that belongs to experience_level. Ambiguity of
this shape is a rubric-design gap, not annotator noise, and would surface later as
inter-annotator disagreement and pass^k instability on this dimension.

## Verification — PENDING

- P0 labeling: track whether "which dimension does this belong to?" hesitation recurs across
  the 30 pairs after the boundary decision (owner logs hesitations during labeling).
- P2 (stronger): per-dimension agreement and pass^k variance for skills_coverage vs
  experience_level under the boundaried rubric.

## Change

Rubric v1 boundary decision (skills_coverage `scope_notes`, design decision 4): skill-attached
years requirements score under experience_level; skills_coverage answers only "is the skill
present and how strong is the evidence."

## Result — PENDING

Before/after comparison requires P0 labeling records or P2 runs (cite run IDs when available).
