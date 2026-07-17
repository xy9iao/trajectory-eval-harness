"""Trajectory schema v0.2 contract tests (docs/trajectory-schema.md).

Pattern: build valid synthetic trajectories, then plant one defect per
invariant and assert the validator names it — the P2 self-verification
rule ("a scorer that can't catch a planted defect is not done") applied
to the validator itself. Two fixtures: a clean gated run, and a degraded
run exercising decision 3-ii's escalation chain.
"""

import copy
from pathlib import Path
from typing import Any

from eval.trajectory import (
    DEFAULT_DIMENSIONS,
    load_trajectory,
    validate_data_hygiene,
    validate_trajectory,
)

RUN = "r20260717T090000-abc123"
SCORES = {
    "skills_coverage": 1,
    "experience_level": 3,
    "education_domain_fit": 3,
    "hard_requirements": 0,
}


def _ev(seq: int, type_: str, **fields: Any) -> dict[str, Any]:
    return {
        "run_id": RUN,
        "seq": seq,
        "ts": f"2026-07-17T09:00:{seq:02d}.000Z",
        "type": type_,
        **fields,
    }


def _header() -> list[dict[str, Any]]:
    return [
        _ev(
            0,
            "run_start",
            schema_version="0.2",
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


def valid_trajectory() -> list[dict[str, Any]]:
    """Clean gated run: all four dimensions assessed, veto unmet, gate fires."""
    events = _header()
    seq = len(events)
    for dim in DEFAULT_DIMENSIONS:
        extra: dict[str, Any] = {"veto_state": "unmet"} if dim == "hard_requirements" else {}
        events.append(
            _ev(
                seq,
                "dimension_assessed",
                dimension=dim,
                score=SCORES[dim],
                degraded=False,
                resolution_failures=0,
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
            aggregate={
                "weighted_mean": 1.6,
                "capped": 1.6,
                "veto": "unmet",
                "partial": False,
                "missing": [],
            },
            gate_fired=True,
            totals={"llm_calls": 2, "tokens_in": 2000, "tokens_out": 410},
        )
    )
    return events


def degraded_trajectory() -> list[dict[str, Any]]:
    """Decision 3-ii chain: skills degraded after retry -> null score ->
    partial aggregate -> insufficient_evidence gate."""
    events = _header()
    seq = len(events)
    for dim in DEFAULT_DIMENSIONS:
        degraded = dim == "skills_coverage"
        extra: dict[str, Any] = {"veto_state": "met"} if dim == "hard_requirements" else {}
        events.append(
            _ev(
                seq,
                "dimension_assessed",
                dimension=dim,
                score=None if degraded else SCORES[dim] or 5,
                degraded=degraded,
                resolution_failures=3 if degraded else 0,
                evidence_spans=[] if degraded else [{"doc": "resume", "start": 5, "end": 30}],
                **extra,
            )
        )
        seq += 1
    events.append(
        _ev(
            seq,
            "gate_event",
            triggers=["insufficient_evidence"],
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
            aggregate={
                "weighted_mean": None,
                "capped": None,
                "veto": "met",
                "partial": True,
                "missing": ["skills_coverage"],
            },
            gate_fired=True,
            totals={"llm_calls": 2, "tokens_in": 2000, "tokens_out": 410},
        )
    )
    return events


def test_valid_trajectory_passes() -> None:
    assert validate_trajectory(valid_trajectory()) == []


def test_degraded_trajectory_passes() -> None:
    assert validate_trajectory(degraded_trajectory()) == []


def test_committed_example_passes() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "trajectories" / "synthetic.jsonl"
    assert validate_trajectory(load_trajectory(path)) == []


def _planted(base: list[dict[str, Any]], mutate: Any) -> list[str]:
    events = copy.deepcopy(base)
    mutate(events)
    return validate_trajectory(events)


# --- invariant 1: envelope ---


def test_catches_seq_gap() -> None:
    assert any(
        "monotonic" in p for p in _planted(valid_trajectory(), lambda ev: ev[3].update(seq=99))
    )


def test_catches_missing_run_end() -> None:
    assert any("run_end" in p for p in _planted(valid_trajectory(), lambda ev: ev.pop()))


def test_catches_wrong_schema_version() -> None:
    assert any(
        "schema_version" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[0].update(schema_version="0.1"))
    )


def test_catches_unknown_event_type() -> None:
    assert any(
        "unknown event type" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[1].update(type="mystery"))
    )


# --- invariant 2: dimension completeness + score consistency ---


def test_catches_missing_dimension() -> None:
    assert any("assessed 0 times" in p for p in _planted(valid_trajectory(), lambda ev: ev.pop(5)))


def test_catches_duplicate_dimension() -> None:
    def dup(ev: list[dict[str, Any]]) -> None:
        ev.insert(6, copy.deepcopy(ev[5]))
        for i, e in enumerate(ev):
            e["seq"] = i

    assert any("assessed 2 times" in p for p in _planted(valid_trajectory(), dup))


def test_catches_degraded_with_score() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[5].update(degraded=True, score=3)

    assert any("must be null" in p for p in _planted(degraded_trajectory(), mutate))


def test_catches_null_score_without_degraded() -> None:
    assert any(
        "not an int in 0..5" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[5].update(score=None))
    )


# --- invariant 3: evidence (forked) ---


def test_catches_missing_evidence_on_non_degraded() -> None:
    assert any(
        "no evidence spans" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[5].update(evidence_spans=[]))
    )


def test_degraded_zero_spans_allowed() -> None:
    assert validate_trajectory(degraded_trajectory()) == []  # skills has 0 spans by fixture


def test_catches_malformed_span() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[5]["evidence_spans"] = [{"doc": "jd", "start": 40, "end": 10}]

    assert any("malformed span" in p for p in _planted(valid_trajectory(), mutate))


# --- invariant 4: gate consistency ---


def test_catches_gate_flag_mismatch() -> None:
    assert any(
        "gate_fired" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[-1].update(gate_fired=False))
    )


def test_catches_veto_without_gate_trigger() -> None:
    assert any(
        "hard_unmet" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[-2].update(triggers=["boundary"]))
    )


def test_catches_eval_mode_manual_resolution() -> None:
    assert any(
        "eval-mode" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[-2].update(resolution="approved"))
    )


def test_catches_degraded_without_insufficient_evidence_gate() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[-2].update(triggers=["boundary"])

    assert any("insufficient_evidence" in p for p in _planted(degraded_trajectory(), mutate))


def test_catches_aggregate_veto_mismatch() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[-1]["aggregate"]["veto"] = "met"

    assert any("aggregate.veto" in p for p in _planted(valid_trajectory(), mutate))


def test_catches_partial_incoherence() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[-1]["aggregate"].update(weighted_mean=2.0)  # partial=True but mean present

    assert any("incoherent" in p for p in _planted(degraded_trajectory(), mutate))


# --- invariants 5-6: totals + retry visibility ---


def test_catches_total_mismatch() -> None:
    def mutate(ev: list[dict[str, Any]]) -> None:
        ev[-1]["totals"].update(tokens_in=1)

    assert any("totals.tokens_in" in p for p in _planted(valid_trajectory(), mutate))


def test_catches_silent_retry() -> None:
    assert any(
        "without a prior non-ok attempt" in p
        for p in _planted(valid_trajectory(), lambda ev: ev[3].update(status="ok"))
    )


# --- invariant 7: data hygiene (no raw data needed here: synthetic docs) ---

DOCS = {
    "resume": "Seasoned data engineer with ten years of Spark and Kafka pipelines at scale.",
    "jd": "We need a senior engineer to build streaming data platforms with Kafka and Flink.",
}


def test_hygiene_clean_trajectory_passes() -> None:
    assert validate_data_hygiene(valid_trajectory(), DOCS) == []


def test_hygiene_catches_quote_in_error_detail() -> None:
    events = copy.deepcopy(valid_trajectory())
    leak = _ev(
        0,
        "error",
        where="assess_dimension",
        kind="validation",
        recovered=True,
        detail="quote not found: 'ten years of Spark and Kafka pipelines'",
    )
    events.insert(5, leak)
    for i, e in enumerate(events):
        e["seq"] = i
    problems = validate_data_hygiene(events, DOCS)
    assert any("shares a 20-char substring with resume" in p for p in problems)


def test_hygiene_allows_counts_and_short_overlap() -> None:
    events = copy.deepcopy(valid_trajectory())
    ok = _ev(
        0,
        "error",
        where="assess_dimension",
        kind="validation",
        recovered=True,
        detail="2 quotes failed resolution (skills_coverage)",  # counts yes, text no
    )
    events.insert(5, ok)
    for i, e in enumerate(events):
        e["seq"] = i
    assert validate_data_hygiene(events, DOCS) == []
