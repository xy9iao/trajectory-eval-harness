"""pass^k stability scorer (P2 eval-design decision 1).

Same pair run k times → how stable are the outputs? The primary product is
the **per-dimension run-to-run variance table** — the settlement site for
the "skills 13→7→9: drift or variance?" account (findings 009/010). Rule
written into the design: if a dimension's within-pair variance is wide, its
cross-batch movements fall inside the noise band; if narrow, movement is
real drift.

Gate stability is reported alongside and matters most: an unstable gate
decision on the same pair is the real screening incident (roadmap).

A degraded dimension (score null) counts as its OWN outcome for stability —
a run that degrades a dimension IS a different result, not a missing one.
"""

import statistics
from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult

DIMENSIONS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]


def _all_agree(values: list[Any]) -> bool:
    return len(set(values)) <= 1


def _numeric_stdev(scores: list[int | None]) -> float | None:
    nums = [s for s in scores if s is not None]
    return statistics.pstdev(nums) if len(nums) >= 2 else None


def passk_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    by_pair = {p: cs for p, cs in corpus.by_pair().items() if len(cs) >= 2}
    k_seen = sorted({len(cs) for cs in by_pair.values()})

    # per-dimension run-to-run stability, aggregated over pairs
    dim_rows: list[dict[str, Any]] = []
    for dim in DIMENSIONS:
        agree = 0
        stdevs: list[float] = []
        degraded_pairs = 0
        for cs in by_pair.values():
            scores = [c.dimension_scores().get(dim) for c in cs]
            if _all_agree(scores):
                agree += 1
            sd = _numeric_stdev(scores)
            if sd is not None:
                stdevs.append(sd)
            if any(s is None for s in scores):
                degraded_pairs += 1
        n = len(by_pair)
        dim_rows.append(
            {
                "dimension": dim,
                "all_agree": f"{agree}/{n}",
                "all_agree_rate": round(agree / n, 3) if n else None,
                "mean_within_pair_stdev": round(statistics.mean(stdevs), 3) if stdevs else None,
                "max_within_pair_stdev": round(max(stdevs), 3) if stdevs else None,
                "pairs_with_a_degraded_run": degraded_pairs,
            }
        )

    # gate + recommendation stability (per pair, across the k runs)
    gate_agree = sum(1 for cs in by_pair.values() if _all_agree([c.gate_fired for c in cs]))
    rec_agree = sum(1 for cs in by_pair.values() if _all_agree([c.recommendation for c in cs]))
    n = len(by_pair)

    # the least-stable pairs (surface them by name for inspection)
    unstable: list[dict[str, Any]] = []
    for pair, cs in by_pair.items():
        flips = {
            dim: sorted({str(c.dimension_scores().get(dim)) for c in cs})
            for dim in DIMENSIONS
            if not _all_agree([c.dimension_scores().get(dim) for c in cs])
        }
        gate_flip = not _all_agree([c.gate_fired for c in cs])
        if flips or gate_flip:
            unstable.append(
                {
                    "pair": f"{pair[0]}:{pair[1]}",
                    "runs": len(cs),
                    "dim_flips": flips,
                    "gate_flip": gate_flip,
                }
            )

    return ScorerResult(
        name="pass^k",
        metrics={
            "pairs_scored": n,
            "k_seen": k_seen,
            "gate_all_agree": f"{gate_agree}/{n}",
            "gate_stability_rate": round(gate_agree / n, 3) if n else None,
            "recommendation_all_agree": f"{rec_agree}/{n}",
            "recommendation_stability_rate": round(rec_agree / n, 3) if n else None,
        },
        rows=dim_rows,
        notes=(
            f"{len(unstable)} pair(s) flipped at least one dimension or the gate across runs; "
            f"{len(corpus.excluded)} case(s) excluded at load (validation failures)."
        ),
    )
