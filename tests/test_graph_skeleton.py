"""Stage E contract: the stub graph runs end-to-end and emits a trajectory
that passes the FULL schema contract (invariants 1–6 + data hygiene).

The merge-reducer tests encode decision 2b's contract; they (and the e2e
tests, which need a working reducer) skip until the owner implements
`merge_assessments` — the reserved Stage-E design slot.
"""

from pathlib import Path

import pytest

from agent.run import SYNTHETIC_JD, SYNTHETIC_RESUME, run_pair
from agent.state import merge_assessments
from agent.tools import SyntheticSource, document_anomalies, get_rubric
from agent.trajectory_writer import TrajectoryWriter, new_run_id
from agent.types import Assessment, PairRef
from eval.trajectory import load_trajectory, validate_data_hygiene, validate_trajectory


def _assessment(dimension: str = "skills_coverage", score: int = 2) -> Assessment:
    return Assessment(
        dimension=dimension,  # type: ignore[arg-type]
        score=score,
        evidence_spans=[{"doc": "resume", "start": 0, "end": 10}],  # type: ignore[list-item]
    )


def _reducer_implemented() -> bool:
    try:
        merge_assessments({}, {"skills_coverage": _assessment()})
        return True
    except NotImplementedError:
        return False


needs_reducer = pytest.mark.skipif(
    not _reducer_implemented(),
    reason="decision 2b: owner implements merge_assessments (Stage E slot)",
)


# --- reducer contract (decision 2b) ---


@needs_reducer
def test_reducer_merges_disjoint_keys() -> None:
    a, b = _assessment("skills_coverage"), _assessment("experience_level", 3)
    merged = merge_assessments({"skills_coverage": a}, {"experience_level": b})
    assert set(merged) == {"skills_coverage", "experience_level"}


@needs_reducer
def test_reducer_raises_on_duplicate_key() -> None:
    a = _assessment("skills_coverage")
    with pytest.raises(ValueError, match="skills_coverage"):
        merge_assessments({"skills_coverage": a}, {"skills_coverage": a})


# --- deterministic pieces (no reducer needed) ---


def test_anomaly_closed_list() -> None:
    long = "x" * 300
    assert document_anomalies(long, long) == []
    assert any("A1" in a for a in document_anomalies("", long))
    assert any("A2" in a for a in document_anomalies("too short", long))
    # the list is closed: garbled-but-long text does NOT trigger (5b)
    assert document_anomalies("ALL CAPS GARBLE " * 40, long) == []


def test_get_rubric_returns_the_dimension_slice() -> None:
    slice_ = get_rubric("hard_requirements")
    assert slice_["id"] == "hard_requirements"
    assert slice_["weight"] == 0


def test_writer_envelope_monotonic(tmp_path: Path) -> None:
    writer = TrajectoryWriter(tmp_path, run_id=new_run_id())
    writer.emit("run_start", schema_version="0.2")
    writer.emit("error", where="x", kind="other", recovered=True, detail="")
    events = load_trajectory(writer.path)
    assert [e["seq"] for e in events] == [0, 1]
    assert len({e["run_id"] for e in events}) == 1


# --- end to end (the Stage E acceptance) ---


@needs_reducer
def test_skeleton_emits_schema_valid_trajectory(tmp_path: Path) -> None:
    final, writer = run_pair(
        SyntheticSource(SYNTHETIC_RESUME, SYNTHETIC_JD),
        PairRef(split="train", row=0),
        "eval",
        tmp_path,
    )
    events = load_trajectory(writer.path)
    assert validate_trajectory(events) == []
    assert validate_data_hygiene(events, {"resume": SYNTHETIC_RESUME, "jd": SYNTHETIC_JD}) == []
    # stub scores are all 3 -> mean 3.0, veto indeterminate, in-band
    aggregate = final["aggregate"]
    assert aggregate is not None
    assert aggregate.weighted_mean == 3.0 and aggregate.capped == 3.0
    assert aggregate.veto == "indeterminate"
    gate = final["gate"]
    assert gate is not None
    assert set(gate.triggers) == {"hard_indeterminate", "boundary"}
    assert final["recommendation"] == "flagged"


@needs_reducer
def test_skeleton_anomaly_path(tmp_path: Path) -> None:
    final, writer = run_pair(
        SyntheticSource("short resume", SYNTHETIC_JD),
        PairRef(split="train", row=0),
        "eval",
        tmp_path,
    )
    events = load_trajectory(writer.path)
    assert validate_trajectory(events) == []
    gate = final["gate"]
    assert gate is not None and "anomaly" in gate.triggers
