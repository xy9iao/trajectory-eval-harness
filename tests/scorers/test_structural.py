"""Planted-defect self-verification for the structural scorers (2b).

Each scorer gets structural defects AND a semantic-boundary defect — the
case that a naive version of the scorer would score as clean:

- gate integrity: a pair that fires on the WRONG trigger (the synthetic form
  of P1's train 596, which the binary matrix counted as a true positive)
- ledger consistency: a run that is internally consistent but wrong against
  the reference (consistency is not correctness — must NOT be flagged here)
- tool-call correctness: right tool multiset, wrong ORDER
- error recovery: a degraded dimension that never reaches the gate

Ledger positive-sample provenance: the known-positive pattern
(`skills=absent` vs `hard=covered` on a shared requirement id) is taken from
the PRE-v1.2 batch of 2026-07-20 (8 contradictions across 7/30 pairs,
finding 008). That batch predates the round-1 consistency instruction, which
cut live contradictions to 2/1 pair — the older data is used because its
positives are dense and the pattern is unambiguous. It is a fixture of a
past prompt version, deliberately, and is not expected to match current
system behavior.
"""

from typing import Any

from eval.scorers import Case, Corpus
from eval.scorers.gate_integrity import gate_integrity_scorer
from eval.scorers.ledger_consistency import ledger_consistency_scorer
from eval.scorers.tool_calls import error_recovery_scorer, tool_call_correctness_scorer

DIMS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]


def _run(
    run_id: str,
    row: int,
    *,
    gate_fired: bool = True,
    triggers: list[str] | None = None,
    dets: dict[str, dict[str, str]] | None = None,
    degraded: list[str] | None = None,
    tools: list[str] | None = None,
    attempts: list[int] | None = None,
) -> Case:
    degraded = degraded or []
    events: list[dict[str, Any]] = [
        {"type": "run_start", "run_id": run_id, "seq": 0, "pair": {"split": "train", "row": row}}
    ]
    for name in (
        tools
        if tools is not None
        else ["parse_resume", "parse_jd", *["get_rubric", "assess_dimension"] * 4]
    ):
        events.append({"type": "tool_call", "tool": name, "status": "ok", "args_summary": {}})
    for attempt in attempts or [1]:
        events.append(
            {
                "type": "llm_call",
                "node": "assess",
                "attempt": attempt,
                "status": "ok" if attempt == 1 else "ok",
                "tokens_in": 1,
                "tokens_out": 1,
            }
        )
    for dim in DIMS:
        event: dict[str, Any] = {
            "type": "dimension_assessed",
            "dimension": dim,
            "score": None if dim in degraded else 3,
            "degraded": dim in degraded,
        }
        if dets and dim in dets:
            event["determinations"] = [{"requirement": k, "value": v} for k, v in dets[dim].items()]
        events.append(event)
    if gate_fired:
        events.append(
            {
                "type": "gate_event",
                "triggers": triggers or ["hard_unmet"],
                "mode": "eval",
                "action": "auto_resume",
                "resolution": "auto",
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


def _corpus(cases: list[Case]) -> Corpus:
    return Corpus(cases=cases, excluded=[])


REF_GATED = {
    ("train", 1): {
        "pair": {"split": "train", "row": 1},
        "gate_expected": True,
        "gate_reasons": ["hard_unmet"],
    },
    ("train", 2): {
        "pair": {"split": "train", "row": 2},
        "gate_expected": False,
        "gate_reasons": [],
    },
}


# --- gate integrity ---


def test_clean_gate_matrix() -> None:
    cases = [_run(f"r{i}", 1) for i in range(3)] + [
        _run(f"s{i}", 2, gate_fired=False) for i in range(3)
    ]
    result = gate_integrity_scorer(_corpus(cases), REF_GATED)
    assert result.metrics["confusion_by_pair_majority_SECONDARY"] == {"TP": 1, "TN": 1}
    assert result.metrics["fired_for_wrong_reason"] == 0
    assert result.stability is not None and result.stability.unstable_pairs == []


def test_catches_wrong_reason_firing() -> None:
    # SEMANTIC-BOUNDARY: gate fires (counted TP by any binary matrix) but the
    # trigger is 'boundary' while the reference reason is 'hard_unmet' —
    # exactly P1's train 596. A scorer without attribution calls this perfect.
    cases = [_run(f"r{i}", 1, triggers=["boundary"]) for i in range(3)]
    result = gate_integrity_scorer(_corpus(cases), REF_GATED)
    # the SECONDARY (majority-vote) view calls this a clean TP...
    assert result.metrics["confusion_by_pair_majority_SECONDARY"] == {"TP": 1}
    assert result.metrics["fired_for_wrong_reason"] == 1  # attribution view: caught
    assert result.metrics["trigger_attribution_ok"] == "0/1"


def test_reports_gate_instability_across_k() -> None:
    cases = [_run("r1", 1), _run("r2", 1, gate_fired=False), _run("r3", 1)]
    result = gate_integrity_scorer(_corpus(cases), REF_GATED)
    assert result.stability is not None
    assert result.stability.unstable_pairs == ["train:1"]
    # the across-runs matrix carries the spread the by-pair majority hides
    assert result.metrics["confusion_across_all_runs_PRIMARY"] == {"TP": 2, "FN": 1}


# --- ledger consistency ---


def test_catches_ledger_contradiction() -> None:
    # the finding-008 known-positive pattern (pre-v1.2 provenance, see module docstring)
    cases = [
        _run(
            "r1",
            1,
            dets={"skills_coverage": {"R1": "absent"}, "hard_requirements": {"R1": "covered"}},
        )
    ]
    result = ledger_consistency_scorer(_corpus(cases), {})
    assert result.metrics["contradictions_total"] == 1
    assert (
        result.rows[0]["source_value"] == "absent" and result.rows[0]["ledger_value"] == "covered"
    )


def test_consistent_but_wrong_is_not_flagged() -> None:
    # SEMANTIC-BOUNDARY: internally coherent, both dimensions agree — and both
    # may be wrong vs the reference. This scorer must stay silent; correctness
    # belongs to the agreement scorers (finding 008's caveat).
    cases = [
        _run(
            "r1",
            1,
            dets={"skills_coverage": {"R1": "covered"}, "hard_requirements": {"R1": "covered"}},
        )
    ]
    result = ledger_consistency_scorer(_corpus(cases), {})
    assert result.metrics["contradictions_total"] == 0
    assert "not correctness" in result.notes


# --- tool-call correctness ---


def test_clean_tool_sequence() -> None:
    result = tool_call_correctness_scorer(_corpus([_run("r1", 1)]), {})
    assert result.metrics["structurally_correct"] == "1/1"


def test_catches_missing_dimension_call() -> None:
    case = _run(
        "r1", 1, tools=["parse_resume", "parse_jd", *["get_rubric", "assess_dimension"] * 3]
    )
    result = tool_call_correctness_scorer(_corpus([case]), {})
    assert result.metrics["structurally_correct"] == "0/1"
    assert any("get_rubric called 3x" in p for p in result.rows[0]["problems"])


def test_catches_wrong_order_with_right_multiset() -> None:
    # SEMANTIC-BOUNDARY: the tool multiset is exactly right; only the ORDER is
    # wrong (assessment before parsing). A counting-only scorer sees nothing.
    case = _run(
        "r1", 1, tools=[*["get_rubric", "assess_dimension"] * 4, "parse_resume", "parse_jd"]
    )
    result = tool_call_correctness_scorer(_corpus([case]), {})
    assert any("after assess_dimension" in p for p in result.rows[0]["problems"])


# --- error recovery ---


def test_degraded_escalates_is_recorded() -> None:
    case = _run("r1", 1, degraded=["skills_coverage"], triggers=["insufficient_evidence"])
    result = error_recovery_scorer(_corpus([case]), {})
    assert result.metrics["degraded_escalated_to_gate"] == "1/1"


def test_catches_degraded_that_never_reaches_the_gate() -> None:
    # SEMANTIC-BOUNDARY: the run degrades but the gate never hears about it —
    # decision 3-ii's escalation contract silently broken.
    case = _run("r1", 1, degraded=["skills_coverage"], triggers=["boundary"])
    result = error_recovery_scorer(_corpus([case]), {})
    assert result.metrics["degraded_escalated_to_gate"] == "0/1"


def test_coverage_caveat_is_always_surfaced() -> None:
    # a corpus that never exercises the failure path must NOT read as a pass
    cases = [_run(f"r{i}", 1) for i in range(5)]
    result = error_recovery_scorer(_corpus(cases), {})
    assert result.metrics["exercised_on"] == "0/5"
    assert "COVERAGE CAVEAT" in result.notes
