# [DRAFT — PENDING] Proportional bundle scoring retracted as a granularity self-contradiction

> **Status: pending draft — do not cite.** A number is assigned at promotion (001 is taken by
> the cross-occupation corpus finding; the owner-vs-dataset disagreement finding takes the next
> free number when it opens). Result awaits the P2 Plan-A-vs-Plan-B contrast run.

## Observation (owner, 2026-07-13)

During skills_coverage design, the owner proposed scoring bundled requirements (e.g.
"Microservices, Docker, Kubernetes") by the *fraction* of components covered. One exchange
earlier, the same session had decided **whole-dimension banding (Plan A)** and deferred
per-item arithmetic aggregation (Plan B) to P2 as a contrast experiment. The proportional
proposal quietly reintroduced Plan B inside a single determination — a self-contradiction.

## Hypothesis

Granularity decisions are easy to violate locally while holding them globally: per-item
arithmetic re-enters through innocuous-looking sub-rules. Catching such contradictions in
design review — before any labeling — is the cheapest possible catch point; uncaught, this one
would have contaminated the P2 Plan-A-vs-Plan-B comparison (Plan A would secretly contain
Plan B).

## Verification — PENDING

The P2 contrast run requires the two plans to be cleanly separated; the retraction is what
makes that experiment valid. Interim check at P0 labeling: bundled requirements are labeled
with the discrete three-value determination without fraction-talk appearing in reasoning notes.

## Change

Bundled requirements use a **discrete three-value determination** (covered / partial / absent):
majority-absent → low band; any partial caps the band at 2; no ratios (design decision 6,
recorded in rubric v1 `coverage_determination`).

## Result — PENDING

Awaits the P2 Plan-A-vs-Plan-B contrast run (cite run IDs when available).
