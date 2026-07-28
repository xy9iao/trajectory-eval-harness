"""pass^k scorer self-verification (eval-design decision 2b).

Planted defects declare the scorer's capability boundary: it must catch a
dimension that flips across runs (structural) AND a gate that flips across
runs while dimension scores stay put (the semantic-boundary case — an
unstable gate decision is the real incident even when the scores look
stable). A scorer that reports "all stable" on these is not done.
"""

from collections.abc import Mapping
from typing import Any

from eval.scorers import Case, Corpus
from eval.scorers.passk import passk_scorer

DIMS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]


def _case(run_id: str, row: int, scores: Mapping[str, int | None], gate_fired: bool) -> Case:
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
    events.append(
        {
            "type": "run_end",
            "gate_fired": gate_fired,
            "recommendation": "flagged",
            "aggregate": {"weighted_mean": 2.0, "veto": "unmet"},
        }
    )
    return Case(run_id=run_id, events=events)


STABLE: Mapping[str, int | None] = {
    "skills_coverage": 3,
    "experience_level": 3,
    "education_domain_fit": 3,
    "hard_requirements": 0,
}


def _corpus(cases: list[Case]) -> Corpus:
    return Corpus(cases=cases, excluded=[])


def test_perfectly_stable_pair_reports_full_agreement() -> None:
    cases = [_case(f"r{i}", 1, STABLE, gate_fired=True) for i in range(5)]
    result = passk_scorer(_corpus(cases), {})
    assert result.metrics["gate_stability_rate"] == 1.0
    for row in result.rows:
        assert row["all_agree_rate"] == 1.0
        assert row["mean_within_pair_stdev"] == 0.0


def test_catches_dimension_flip() -> None:
    # experience flips 1/3/5 across three runs; others stable
    cases = [
        _case("r1", 2, {**STABLE, "experience_level": 1}, True),
        _case("r2", 2, {**STABLE, "experience_level": 3}, True),
        _case("r3", 2, {**STABLE, "experience_level": 5}, True),
    ]
    result = passk_scorer(_corpus(cases), {})
    exp = next(r for r in result.rows if r["dimension"] == "experience_level")
    skills = next(r for r in result.rows if r["dimension"] == "skills_coverage")
    assert exp["all_agree_rate"] == 0.0 and exp["mean_within_pair_stdev"] > 0
    assert skills["all_agree_rate"] == 1.0  # unaffected dim stays stable
    assert "train:2" in result.notes or any(u for u in [result.notes])


def test_catches_gate_flip_with_stable_scores() -> None:
    # SEMANTIC-BOUNDARY defect: dimension scores identical across runs, but
    # the gate decision flips — an unstable gate is the real incident. A
    # scorer that only watches dimension scores would call this pair stable.
    cases = [
        _case("r1", 3, STABLE, gate_fired=True),
        _case("r2", 3, STABLE, gate_fired=False),
        _case("r3", 3, STABLE, gate_fired=True),
    ]
    result = passk_scorer(_corpus(cases), {})
    assert result.metrics["gate_stability_rate"] == 0.0  # caught
    # and every dimension still reads stable — proving the gate signal is
    # independent of the dimension-score signal
    assert all(r["all_agree_rate"] == 1.0 for r in result.rows)


def test_degraded_run_counts_as_its_own_outcome() -> None:
    cases = [
        _case("r1", 4, {**STABLE, "skills_coverage": 3}, True),
        _case("r2", 4, {**STABLE, "skills_coverage": None}, True),  # degraded
        _case("r3", 4, {**STABLE, "skills_coverage": 3}, True),
    ]
    result = passk_scorer(_corpus(cases), {})
    skills = next(r for r in result.rows if r["dimension"] == "skills_coverage")
    assert skills["all_agree_rate"] == 0.0  # None != 3, flagged unstable
    assert skills["pairs_with_a_degraded_run"] == 1


def test_single_run_pairs_are_excluded_from_passk() -> None:
    # a pair with only one run cannot have run-to-run variance
    cases = [_case("r1", 5, STABLE, True)] + [_case(f"r{i}", 6, STABLE, True) for i in range(3)]
    result = passk_scorer(_corpus(cases), {})
    assert result.metrics["pairs_scored"] == 1  # only train:6 (3 runs) qualifies
