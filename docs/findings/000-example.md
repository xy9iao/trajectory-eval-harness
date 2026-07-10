# 000 — [SYNTHETIC] pass^k instability traced to an unanchored rubric criterion

> **This finding is synthetic.** It was seeded at repo initialization as the format anchor for `docs/findings/` and must never be cited as a real result. The run IDs below do not exist. Real findings start at 001, use this exact five-part structure, and every number must be reproducible from the trajectory JSONL of the cited runs.

## Observation

In a 30-case batch (run `2026-01-01-synthetic-a`), pass^5 stability on the *experience level* dimension was 0.58, while every other dimension sat above 0.85. Same pairs, same model, same prompt — only that dimension's scores flipped between repeats.

## Hypothesis

The rubric criterion for *experience level* ("candidate's experience is adequate for the role") carries no anchor examples, so the model resolves "adequate" differently across runs — the instability is a rubric-design gap, not a sampling artifact.

## Verification

Read the trajectories of the 7 flip-flopping cases: in 6 of 7, the cited evidence spans were identical across repeats while the score differed — the model saw the same facts and judged them inconsistently. That isolates the criterion wording (design), rules out extraction noise (structure), and matches the hypothesis.

## Change

Rubric v1 → v1.1: added two anchor examples to *experience level* (a clear 2/5 and a clear 4/5, each with the reasoning pattern spelled out). Single-variable change; prompt and thresholds untouched.

## Result

Re-run on the same fixed seed set (run `2026-01-02-synthetic-b`): pass^5 on *experience level* 0.58 → 0.87; other dimensions unchanged (±0.02). Before/after regenerable via `eval/reports/` from the two runs' JSONL.
