"""Ledger-consistency scorer (finding 008): internal coherence, zero annotation.

The hard_requirements ledger claims to reuse the other dimensions'
determinations. Where it references the same requirement id as a prior
dimension, the two values must agree; a contradiction is detectable without
any reference standard — the trajectory testifies against itself.

Scope discipline (finding 008's own caveat, carried here so no reader
misreads the metric): **consistency is not correctness.** A run can leave
this scorer clean by being consistently wrong — P1's 596 did exactly that
after the consistency prompt landed. This scorer measures coherence; the
agreement scorers measure correctness; they are never merged.
"""

from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult, StabilityNote

# The dimensions whose determinations the ledger claims to reuse.
SOURCE_DIMENSIONS = ["skills_coverage"]


def ledger_consistency_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    groups = corpus.by_pair()
    rows: list[dict[str, Any]] = []
    contradictions_total = 0
    pairs_with_contradiction: set[str] = set()
    unstable: list[str] = []

    for pair, cases in sorted(groups.items(), key=lambda kv: kv[0][1]):
        label = f"{pair[0]}:{pair[1]}"
        per_run_counts = []
        for case in cases:
            hard = case.determinations("hard_requirements")
            found = 0
            for source in SOURCE_DIMENSIONS:
                prior = case.determinations(source)
                for rid, value in hard.items():
                    if rid in prior and prior[rid] != value:
                        found += 1
                        rows.append(
                            {
                                "pair": label,
                                "run_id": case.run_id,
                                "requirement": rid,
                                "source_dimension": source,
                                "source_value": prior[rid],
                                "ledger_value": value,
                            }
                        )
            per_run_counts.append(found)
            contradictions_total += found
            if found:
                pairs_with_contradiction.add(label)
        if len(set(per_run_counts)) > 1:
            unstable.append(f"{label} ({per_run_counts})")

    n_pairs = len(groups)
    n_runs = len(corpus.cases)
    return ScorerResult(
        name="ledger consistency",
        metrics={
            "runs_scored": n_runs,
            "pairs_scored": n_pairs,
            "contradictions_total": contradictions_total,
            "pairs_with_any_contradiction": f"{len(pairs_with_contradiction)}/{n_pairs}",
            "contradictions_per_run": (round(contradictions_total / n_runs, 3) if n_runs else None),
        },
        rows=rows,
        notes=(
            "Consistency is not correctness: a run can be clean here by being consistently "
            "wrong (finding 008, train 596 after the consistency prompt). Pair with the "
            "agreement scorers; never merge them. "
            "COMPARABILITY: totals here are over ALL runs in the corpus, while finding 008's "
            "figures (8 contradictions / 7 pairs pre-calibration, 2 / 1 pair post) came from "
            "single 30-run batches — the two are only comparable as per-run rates "
            "(008 post-calibration: 2/30 = 0.067 per run), never as raw counts."
        ),
        stability=StabilityNote(
            basis="across-k",
            detail=(
                f"contradiction counts vary across the k repeats on {len(unstable)}/{n_pairs} "
                "pairs; the headline is the total over all runs, not a single-run snapshot."
            ),
            unstable_pairs=unstable,
        ),
    )
