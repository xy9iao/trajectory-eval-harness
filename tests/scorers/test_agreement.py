"""Planted-defect self-verification for the agreement scorer (2b).

Structural defects: a wrong score must lower the rate; degraded scores must
be excluded rather than counted wrong.

Semantic-boundary defect: a stratum with too few pairs must be labelled
`insufficient for interpretation` — a scorer that reports 2/2 = 1.0 for a
one-pair stratum as if it were comparable to a twenty-pair stratum is the
version that manufactures numbers instead of explaining them.
"""

from typing import Any

from eval.scorers import Case, Corpus
from eval.scorers.agreement import MIN_STRATUM_N, agreement_scorer

DIMS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]


def _case(run_id: str, row: int, scores: dict[str, int | None]) -> Case:
    events: list[dict[str, Any]] = [
        {"type": "run_start", "run_id": run_id, "seq": 0, "pair": {"split": "train", "row": row}}
    ]
    for dim in DIMS:
        events.append(
            {
                "type": "dimension_assessed",
                "dimension": dim,
                "score": scores[dim],
                "degraded": scores[dim] is None,
            }
        )
    events.append({"type": "run_end", "gate_fired": True, "recommendation": "flagged"})
    return Case(run_id=run_id, events=events)


def _ref(row: int, scores: dict[str, int]) -> dict[str, Any]:
    return {
        "pair": {"split": "train", "row": row},
        "dimensions": {d: {"score": s} for d, s in scores.items()},
        "gate_expected": True,
        "gate_reasons": ["hard_unmet"],
    }


MATCH = {
    "skills_coverage": 3,
    "experience_level": 3,
    "education_domain_fit": 3,
    "hard_requirements": 0,
}


def test_perfect_agreement() -> None:
    corpus = Corpus(cases=[_case("r1", 175, dict(MATCH))], excluded=[])
    result = agreement_scorer(corpus, {("train", 175): _ref(175, MATCH)})
    for row in result.metrics["overall_by_dimension"]:
        assert row["rate"] == 1.0


def test_catches_score_mismatch() -> None:
    corpus = Corpus(cases=[_case("r1", 175, {**MATCH, "skills_coverage": 1})], excluded=[])
    result = agreement_scorer(corpus, {("train", 175): _ref(175, MATCH)})
    skills = next(
        r for r in result.metrics["overall_by_dimension"] if r["dimension"] == "skills_coverage"
    )
    assert skills["rate"] == 0.0
    exp = next(
        r for r in result.metrics["overall_by_dimension"] if r["dimension"] == "experience_level"
    )
    assert exp["rate"] == 1.0  # other dimensions unaffected


def test_degraded_is_excluded_not_counted_wrong() -> None:
    corpus = Corpus(cases=[_case("r1", 175, {**MATCH, "skills_coverage": None})], excluded=[])
    result = agreement_scorer(corpus, {("train", 175): _ref(175, MATCH)})
    skills = next(
        r for r in result.metrics["overall_by_dimension"] if r["dimension"] == "skills_coverage"
    )
    assert skills["exact"] == "0/0"  # no comparison, not a failed one


def test_small_stratum_is_flagged_insufficient() -> None:
    # SEMANTIC-BOUNDARY: 596 is the only pair in the relevant_years_prior
    # stratum. Its rate is arithmetically computable and statistically
    # meaningless — the scorer must say so rather than emit a clean 1.0.
    corpus = Corpus(cases=[_case("r1", 596, dict(MATCH))], excluded=[])
    result = agreement_scorer(corpus, {("train", 596): _ref(596, MATCH)})
    stratum = next(
        s for s in result.metrics["by_stratum"] if s["stratum"] == "relevant_years_prior"
    )
    assert stratum["pairs"] == 1 and stratum["interpretable"] is False
    assert "insufficient for interpretation" in stratum["skills_coverage"]
    assert MIN_STRATUM_N == 5


def test_pair_can_belong_to_several_strata() -> None:
    # 4928 is in both adjacency_axis and skills_band_0_1 (p0 §5b) — the
    # classification is patterns, not a partition, and both must count it.
    corpus = Corpus(cases=[_case("r1", 4928, dict(MATCH))], excluded=[])
    result = agreement_scorer(corpus, {("train", 4928): _ref(4928, MATCH)})
    names = {s["stratum"] for s in result.metrics["by_stratum"] if s["pairs"] > 0}
    assert {"adjacency_axis", "skills_band_0_1"} <= names


def test_agreement_is_never_self_consistency() -> None:
    # vocabulary discipline (finding 011 §2): this scorer compares against the
    # human reference only; runs are compared to the reference, never to each
    # other. Two runs disagreeing with each other but both matching the
    # reference must read as perfect agreement.
    corpus = Corpus(
        cases=[_case("r1", 175, dict(MATCH)), _case("r2", 175, dict(MATCH))], excluded=[]
    )
    result = agreement_scorer(corpus, {("train", 175): _ref(175, MATCH)})
    assert result.metrics["comparisons"] == 8  # 2 runs x 4 dimensions
    assert all(r["rate"] == 1.0 for r in result.metrics["overall_by_dimension"])
    assert "never the model against itself" in result.notes
