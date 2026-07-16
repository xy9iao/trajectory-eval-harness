# 006 — Proportional bundle scoring retracted as a granularity self-contradiction

**Status:** open — P0 interim check passed (2026-07-16); Result awaits the P2
Plan-A-vs-Plan-B contrast run. **Date:** 2026-07-13 → 2026-07-16 · **Phase:** P0 → P2

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

## Verification — P0 interim check passed (2026-07-16)

Scan over the completed 30-record reference set: every recorded determination uses strictly
{covered, partial, absent} (no other values appear), and no fraction-based scoring language
occurs in any notes field (regex scan for ratio/percentage phrasing; all numeric-ratio matches
were dates, GPAs, and decimal year figures). Plan A stayed pure through labeling. The P2
contrast run remains the full verification: it requires the two plans cleanly separated, and
the retraction is what makes that experiment valid.

## Change

Bundled requirements use a **discrete three-value determination** (covered / partial / absent):
majority-absent → low band; any partial caps the band at 2; no ratios (design decision 6,
recorded in rubric v1 `coverage_determination`).

## Result — PENDING

Awaits the P2 Plan-A-vs-Plan-B contrast run (cite run IDs when available).
