# 005 — Unbandable case exposed a missing dimension boundary (years → experience_level)

**Status:** closed (P0 arm) — verified over the completed 30-pair labeling; P2 per-dimension
agreement + pass^k remain the stronger instrument. **Date:** 2026-07-13 → 2026-07-16 ·
**Phase:** P0

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

## Verification (P0 labeling complete, 2026-07-16)

Scan over all 30 records' hesitation and notes fields (`labels-v1.jsonl`): **zero**
"which dimension does this belong to?"-shaped hesitations. Years reasoning appears in 18
records — in every case inside experience_level / hard_requirements notes, i.e. exactly where
the boundary sends it. The ledger/proximity double-mention (years pass-fail in
hard_requirements, years proximity in experience_level) was applied across all 30 records
without a recorded conflict.

## Change

Rubric v1 boundary decision (skills_coverage `scope_notes`, design decision 4): skill-attached
years requirements score under experience_level; skills_coverage answers only "is the skill
present and how strong is the evidence."

## Result

The boundary held across the full reference set: the hesitation type that motivated the
decision (row 4699's unbandable strong-evidence/short-years case) did not recur in 30 pairs
of labeling. P0 arm closed; P2's per-dimension agreement and pass^k variance will provide the
quantitative strengthener (cite run IDs there).
