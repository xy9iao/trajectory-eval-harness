# 007 — First live run tripped the data-hygiene invariant: model-authored labels quoted the JD

**Status:** open — Change landed (symmetric carrier contract); Result closes with the
post-fix rerun + clean 30-pair batch. **Date:** 2026-07-20 · **Phase:** P1 (Stage F live)

**Reproduction:** run `r20260720T094231-3ae875` (train 596, DeepSeek dev, first live run) —
`validate_data_hygiene` reports 10 violations; structural validation (invariants 1–6) CLEAN.

## Observation

The very first live trajectory passed every structural invariant but tripped invariant 7 ten
times: the model wrote `determination.requirement` labels by copying JD sentences verbatim
("Bachelor's degree or four or more years of work experience (stated must)" — a ≥20-char
document substring inside a trajectory event). The mocked tests never caught this: scripted
determinations used short labels. Real model behavior differs from scripted behavior in
exactly the dimension the invariant guards.

## Hypothesis

Any model-authored free-text field is a leak channel for document text unless mechanically
constrained; instructions alone won't hold (same reasoning as D7's upgrade from prompt to
schema). Trajectories are future-public material (findings cite them, reports embed them) —
every additional run before the fix is one more artifact to launder later.

## Change (this PR — the symmetric carrier contract)

Quotes are the ONLY sanctioned carrier of document text (and they are resolved to offsets,
never logged). Therefore two complementary assertions pin down the complete contract:
`evidence_quotes` MUST be verbatim document substrings (existing resolution check); every
other model-authored string — determination labels — MUST NOT share a ≥20-char substring
with either document. Three layers: post_validate check joining the malformed/retry chain
(mechanism) · prompt instruction to paraphrase (guidance) · `max_length=80` on the wire
schema (cap). Single-source check: `eval.trajectory.shares_doc_substring` serves both the
validator and the agent. Also recorded as a standing CLAUDE.md rule: data-boundary holes are
fixed on discovery, never queued.

## Result — PENDING

Closes with: post-fix rerun of train 596 hygiene-clean, and the 30-pair batch reporting zero
invariant-7 violations.
