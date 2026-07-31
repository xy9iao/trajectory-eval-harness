"""Evidence-coverage SENTINEL: determinations per evidence span (finding 013).

**This is a sentinel, not a faithfulness metric.** It flags assessments that
*warrant human inspection*; it does not measure whether evidence supports a
conclusion. Both directions of the inference fail:

- a high ratio need NOT be unfaithful — one substantive passage can legitimately
  cover ten must-items;
- a normal ratio does NOT guarantee faithfulness — a 1:1 assessment can cite
  the wrong category of evidence entirely (finding 013's train 5084 run A
  cited JD requirement text to prove resume content).

Reporting rule that follows: **the ratio itself never appears as a headline
number** (2.0 means nothing without a baseline), only the count and location
of over-threshold assessments. Anyone reporting this as a faithfulness score
is producing exactly the plausible-looking wrong number this project keeps
guarding against.

Its real payoff is sampling: faithfulness spot-checks draw from the
over-threshold pool instead of guessing where to look, so the scarce human
minutes land on the likeliest failures (eval-design 3d) — the same role
`resolution_failures` played as the diagnostic entry point for degradation.

Threshold: 5x (owner ruling 2026-07-28, recorded in decisions.md). Rationale:
the corpus medians are 1.2 (skills) and 2.0 (hard), so 3x still sits inside
the normal tail (32/149 hard assessments) and would drown the signal; 5x
targets the 10:1 / 14:1 structural mismatches.
"""

from collections import Counter
from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult, StabilityNote

RATIO_THRESHOLD = 5.0


def evidence_coverage_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    flagged: list[dict[str, Any]] = []
    by_dimension: Counter[str] = Counter()
    assessments = 0
    no_span = 0

    for case in corpus.cases:
        for event in case.events:
            if event.get("type") != "dimension_assessed":
                continue
            determinations = event.get("determinations") or []
            if not determinations:
                continue
            assessments += 1
            spans = len(event.get("evidence_spans") or [])
            if spans == 0:
                no_span += 1
                ratio = float("inf")
            else:
                ratio = len(determinations) / spans
            if ratio > RATIO_THRESHOLD:
                by_dimension[str(event["dimension"])] += 1
                flagged.append(
                    {
                        "run_id": case.run_id,
                        "pair": f"{case.pair[0]}:{case.pair[1]}",
                        "dimension": event["dimension"],
                        "determinations": len(determinations),
                        "evidence_spans": spans,
                        "ratio": round(ratio, 1) if spans else "inf",
                    }
                )

    return ScorerResult(
        name="evidence coverage (sentinel)",
        metrics={
            "assessments_with_determinations": assessments,
            "over_threshold": f"{len(flagged)}/{assessments}",
            "threshold": f"{RATIO_THRESHOLD}x determinations per evidence span",
            "over_threshold_by_dimension": dict(by_dimension),
            "assessments_with_zero_spans": no_span,
        },
        rows=flagged,
        notes=(
            "SENTINEL, NOT A FAITHFULNESS METRIC: a flag means 'this assessment warrants human "
            "inspection', never 'this assessment is unfaithful'. A high ratio can be legitimate "
            "(one passage genuinely covering many must-items) and a normal ratio can still be "
            "unfaithful (right count, wrong category of evidence — finding 013). Report the "
            "flag count and where they cluster; never report the raw ratio as a score. Primary "
            "use: the sampling pool for faithfulness spot-checks (eval-design 3d)."
        ),
        stability=StabilityNote(
            basis="across-k",
            detail=(
                "computed per assessment over all repeats; a pair may be flagged in some runs "
                "and not others, which is itself informative — the flag list carries run_ids."
            ),
        ),
    )
