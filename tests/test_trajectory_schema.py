"""Trajectory schema v0.1 contract tests (docs/trajectory-schema.md).

Pattern: build one valid synthetic trajectory, then plant one defect per
invariant and assert the validator names it — the same self-verification
discipline P2 requires of every scorer ("a scorer that can't catch a
planted defect is not done"), applied to the validator itself.
"""

import copy
from typing import Any

from eval.trajectory import DEFAULT_DIMENSIONS, load_trajectory, validate_trajectory

RUN = "r20260716T090000-abc123"


def _ev(seq: int, type_: str, **fields: Any) -> dict[str, Any]:
    return {
        "run_id": RUN,
        "seq": seq,
        "ts": f"2026-07-16T09:00:{seq:02d}.000Z",
        "type": type_,
        **fields,
    }


def valid_trajectory() -> list[dict[str, Any]]:
    events = [
        _ev(
            0,
            "run_start",
            schema_version="0.1",
            pair={"split": "train", "row": 0},
            rubric_version="1.1",
            agent_mode="eval",
            provider="deepseek",
            model="deepseek-chat",
            config_digest="0" * 64,
        ),
        _ev(1, "tool_call", tool="parse_resume", status="ok", latency_ms=12, args_summary={}),
        _ev(2, "tool_call", tool="parse_jd", status="ok", latency_ms=9, args_summary={}),
        _ev(
            3,
            "llm_call",
            node="extract",
            purpose="extraction",
            provider="deepseek",
            model="deepseek-chat",
            tokens_in=1000,
            tokens_out=200,
            latency_ms=800,
            attempt=1,
            status="malformed_output",
        ),
        _ev(
            4,
            "llm_call",
            node="extract",
            purpose="extraction",
            provider="deepseek",
            model="deepseek-chat",
            tokens_in=1000,
            tokens_out=210,
            latency_ms=650,
            attempt=2,
            status="ok",
        ),
    ]
    seq = 5
    scores = {
        "skills_coverage": 1,
        "experience_level": 3,
        "education_domain_fit": 3,
        "hard_requirements": 0,
    }
    for dim in DEFAULT_DIMENSIONS:
        extra: dict[str, Any] = {"veto_state": "unmet"} if dim == "hard_requirements" else {}
        events.append(
            _ev(
                seq,
                "dimension_assessed",
                dimension=dim,
                score=scores[dim],
                evidence_spans=[{"doc": "jd", "start": 10, "end": 40}],
                **extra,
            )
        )
        seq += 1
    events.append(
        _ev(
            seq,
            "gate_event",
            triggers=["hard_unmet"],
            mode="eval",
            action="auto_resume",
            resolution="auto",
        )
    )
    events.append(
        _ev(
            seq + 1,
            "run_end",
            recommendation="flagged",
            aggregate={"weighted_mean": 1.6, "veto": "unmet"},
            gate_fired=True,
            totals={"llm_calls": 2, "tokens_in": 2000, "tokens_out": 410},
        )
    )
    return events


def test_valid_trajectory_passes() -> None:
    assert validate_trajectory(valid_trajectory()) == []


def test_committed_example_passes() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "examples" / "trajectories" / "synthetic.jsonl"
    assert validate_trajectory(load_trajectory(path)) == []


def _planted(mutate: Any) -> list[str]:
    events = copy.deepcopy(valid_trajectory())
    mutate(events)
    return validate_trajectory(events)


def test_catches_seq_gap() -> None:
    problems = _planted(lambda ev: ev[3].update(seq=99))
    assert any("monotonic" in p for p in problems)


def test_catches_missing_run_end() -> None:
    problems = _planted(lambda ev: ev.pop())
    assert any("run_end" in p for p in problems)


def test_catches_missing_dimension() -> None:
    problems = _planted(lambda ev: ev.pop(5))
    assert any("assessed 0 times" in p for p in problems)


def test_catches_duplicate_dimension() -> None:
    def dup(ev: list[dict[str, Any]]) -> None:
        clone = copy.deepcopy(ev[5])
        ev.insert(6, clone)
        for i, e in enumerate(ev):
            e["seq"] = i

    problems = _planted(dup)
    assert any("assessed 2 times" in p for p in problems)


def test_catches_missing_evidence() -> None:
    problems = _planted(lambda ev: ev[5].update(evidence_spans=[]))
    assert any("no evidence spans" in p for p in problems)


def test_catches_gate_flag_mismatch() -> None:
    problems = _planted(lambda ev: ev[-1].update(gate_fired=False))
    assert any("gate_fired" in p for p in problems)


def test_catches_veto_without_gate_trigger() -> None:
    problems = _planted(lambda ev: ev[-2].update(triggers=["boundary"]))
    assert any("hard_unmet" in p for p in problems)


def test_catches_eval_mode_manual_resolution() -> None:
    problems = _planted(lambda ev: ev[-2].update(resolution="approved"))
    assert any("eval-mode" in p for p in problems)


def test_catches_total_mismatch() -> None:
    problems = _planted(lambda ev: ev[-1]["totals"].update(tokens_in=1))
    assert any("totals.tokens_in" in p for p in problems)


def test_catches_silent_retry() -> None:
    problems = _planted(lambda ev: ev[3].update(status="ok"))
    assert any("without a prior non-ok attempt" in p for p in problems)


def test_catches_unknown_event_type() -> None:
    problems = _planted(lambda ev: ev[1].update(type="mystery"))
    assert any("unknown event type" in p for p in problems)
