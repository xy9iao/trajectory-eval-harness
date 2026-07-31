"""Per-dimension agreement vs the human reference, STRATIFIED by divergence
root cause (pre-committed in findings 009/010, p0 report §5b).

Strata come from §5b's first-pass pattern classification — deliberately
reused rather than re-derived: §5b was written so P2 would inherit a
populated ledger, and re-classifying pair by pair now would discard that.

Two guards the design demands:

- **n<5 strata are labelled `insufficient for interpretation`.** Splitting
  30 pairs into five classes yields ~6 per class; comparing those rates is
  reading noise, and finding 011 supplied the error bars that prove it.
  Stratification exists to give low headline numbers an explanatory
  structure — not to manufacture more comparable numbers.
- **`agreement` is scores-vs-human-reference only** — never the model
  against itself (that is self-consistency, finding 011). The two are
  distinct measurements and the cross-validation argument depends on it.
"""

from collections import Counter
from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult, StabilityNote

DIMENSIONS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]
MIN_STRATUM_N = 5

# p0 report §5b, table B — first-pass pattern classification of agent-vs-reference
# divergence. Pairs may appear in more than one pattern; a pair in none is "other".
STRATA: dict[str, set[int]] = {
    "adjacency_axis": {2980, 3559, 3773, 3800, 3978, 4160, 4890, 4928, 5063, 5084, 5798},
    "skills_band_0_1": {175, 901, 935, 1089, 3861, 4928, 6236},
    "relevant_years_prior": {596},
    "experience_proximity": {935, 1050, 3148, 3229, 3590, 3769, 4715, 5063, 5707},
}


def _strata_for(row: int) -> list[str]:
    hit = [name for name, rows in STRATA.items() if row in rows]
    return hit or ["other"]


def agreement_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    groups = corpus.by_pair()
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    stratum_exact: Counter[tuple[str, str]] = Counter()
    stratum_total: Counter[tuple[str, str]] = Counter()
    stratum_pairs: dict[str, set[int]] = {}
    rows: list[dict[str, Any]] = []

    for pair, cases in sorted(groups.items(), key=lambda kv: kv[0][1]):
        ref = reference.get(pair)
        if ref is None:
            continue
        row_id = pair[1]
        strata = _strata_for(row_id)
        for name in strata:
            stratum_pairs.setdefault(name, set()).add(row_id)
        for dim in DIMENSIONS:
            ref_score = ref["dimensions"][dim]["score"]
            agent_scores = [c.dimension_scores().get(dim) for c in cases]
            # one comparison per RUN — the deployed system runs once, so the
            # agreement rate is per-run, not per-majority-vote (the same
            # primary/secondary ruling as gate integrity).
            for score in agent_scores:
                if score is None:  # degraded: no score to compare
                    continue
                total[dim] += 1
                for name in strata:
                    stratum_total[(name, dim)] += 1
                if score == ref_score:
                    exact[dim] += 1
                    for name in strata:
                        stratum_exact[(name, dim)] += 1
            rows.append(
                {
                    "pair": f"{pair[0]}:{row_id}",
                    "dimension": dim,
                    "reference": ref_score,
                    "agent_across_k": agent_scores,
                    "strata": strata,
                }
            )

    overall = [
        {
            "dimension": dim,
            "exact": f"{exact[dim]}/{total[dim]}",
            "rate": round(exact[dim] / total[dim], 3) if total[dim] else None,
        }
        for dim in DIMENSIONS
    ]

    by_stratum: list[dict[str, Any]] = []
    for name in list(STRATA) + ["other"]:
        n_pairs = len(stratum_pairs.get(name, ()))
        entry: dict[str, Any] = {
            "stratum": name,
            "pairs": n_pairs,
            "interpretable": n_pairs >= MIN_STRATUM_N,
        }
        for dim in DIMENSIONS:
            tot = stratum_total[(name, dim)]
            entry[dim] = (
                f"{stratum_exact[(name, dim)]}/{tot}"
                + ("" if n_pairs >= MIN_STRATUM_N else " [insufficient for interpretation]")
                if tot
                else "-"
            )
        by_stratum.append(entry)

    return ScorerResult(
        name="agreement (vs human reference)",
        metrics={
            "comparisons": sum(total.values()),
            "overall_by_dimension": overall,
            "by_stratum": by_stratum,
            "min_stratum_n_for_interpretation": MIN_STRATUM_N,
        },
        rows=rows,
        notes=(
            "Strata are p0 §5b's first-pass classification, inherited not re-derived. Strata "
            f"with fewer than {MIN_STRATUM_N} pairs are marked insufficient for interpretation: "
            "stratification exists to give low numbers an explanatory structure, not to produce "
            "more comparable numbers out of the same 30 pairs. 'Agreement' here always means "
            "agent vs human reference — never the model against itself (self-consistency)."
        ),
        stability=StabilityNote(
            basis="across-k",
            detail=(
                "one comparison per RUN (not per majority vote), so the rate is what the "
                "deployed single-run system achieves; read against finding 011's per-dimension "
                "variance floor — e.g. skills self-consistency 0.400 bounds how much of any "
                "agreement movement can be attributed to anything but variance."
            ),
        ),
    )
