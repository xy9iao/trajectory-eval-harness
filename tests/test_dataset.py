"""Offline tests for the dataset loader + validator (GUIDE §7). No model or network needed.

These prove the instrument is sound before it measures anything: the real eval_set.jsonl loads and
validates, the validator actually rejects malformed/self-inconsistent cases, and the dataset's gate
rule matches the agent's runtime gate rule (so ground-truth gate_required can't silently drift).
"""
from __future__ import annotations

import json

import pytest

from src.eval.dataset import (
    ACTIONS,
    CATEGORIES,
    CONSEQUENTIAL_ACTIONS,
    DIFFICULTIES,
    VALID_TOOLS,
    Case,
    DatasetError,
    load_cases,
)

# A minimal well-formed case dict; tests mutate one field at a time to exercise the validator.
GOOD = {
    "case_id": "x1",
    "ticket_text": "I was charged twice for order #10231.",
    "difficulty": "straightforward",
    "ground_truth": {
        "category": "billing",
        "action": "refund",
        "gate_required": True,
        "expected_tools": ["get_order", "get_policy"],
    },
    "notes": "synthetic",
}


def _write(tmp_path, *objs) -> str:
    p = tmp_path / "cases.jsonl"
    p.write_text("\n".join(json.dumps(o) for o in objs), encoding="utf-8")
    return str(p)


# ---------- the real dataset ----------

def test_real_dataset_loads_and_validates():
    cases = load_cases()
    assert len(cases) >= 13
    assert all(isinstance(c, Case) for c in cases)
    # Loader guarantees uniqueness; assert it held on the real file.
    assert len({c.case_id for c in cases}) == len(cases)


def test_real_dataset_taxonomy_in_bounds():
    for c in load_cases():
        assert c.ground_truth.category in CATEGORIES
        assert c.ground_truth.action in ACTIONS
        assert c.difficulty in DIFFICULTIES
        assert set(c.ground_truth.expected_tools) <= set(VALID_TOOLS)


def test_gate_rule_matches_agent_runtime():
    """The dataset's notion of 'consequential' must equal the agent's deterministic gate rule.

    If these ever diverge, gate-integrity scoring would be measured against the wrong expectation.
    """
    from src.agent.nodes import GATE_ACTIONS

    assert set(CONSEQUENTIAL_ACTIONS) == set(GATE_ACTIONS)


# ---------- the validator rejects bad cases ----------

def test_accepts_good_case(tmp_path):
    cases = load_cases(_write(tmp_path, GOOD))
    assert cases[0].case_id == "x1"
    assert cases[0].ground_truth.expected_tools == ("get_order", "get_policy")


def test_rejects_bad_category(tmp_path):
    bad = {**GOOD, "ground_truth": {**GOOD["ground_truth"], "category": "nonsense"}}
    with pytest.raises(DatasetError, match="bad category"):
        load_cases(_write(tmp_path, bad))


def test_rejects_bad_action(tmp_path):
    bad = {**GOOD, "ground_truth": {**GOOD["ground_truth"], "action": "delete_account"}}
    with pytest.raises(DatasetError, match="bad action"):
        load_cases(_write(tmp_path, bad))


def test_rejects_bad_difficulty(tmp_path):
    bad = {**GOOD, "difficulty": "trivial"}
    with pytest.raises(DatasetError, match="bad difficulty"):
        load_cases(_write(tmp_path, bad))


def test_rejects_unknown_tool(tmp_path):
    bad = {**GOOD, "ground_truth": {**GOOD["ground_truth"], "expected_tools": ["delete_order"]}}
    with pytest.raises(DatasetError, match="unknown expected_tools"):
        load_cases(_write(tmp_path, bad))


def test_rejects_gate_inconsistent_with_action(tmp_path):
    # refund is consequential, so gate_required must be True; False is self-inconsistent.
    bad = {**GOOD, "ground_truth": {**GOOD["ground_truth"], "gate_required": False}}
    with pytest.raises(DatasetError, match="inconsistent"):
        load_cases(_write(tmp_path, bad))

    # reply is informational, so gate_required must be False; True is self-inconsistent.
    bad2 = {
        **GOOD,
        "ground_truth": {"category": "bug_report", "action": "reply", "gate_required": True, "expected_tools": []},
    }
    with pytest.raises(DatasetError, match="inconsistent"):
        load_cases(_write(tmp_path, bad2))


def test_rejects_duplicate_case_id(tmp_path):
    with pytest.raises(DatasetError, match="duplicate case_id"):
        load_cases(_write(tmp_path, GOOD, GOOD))


def test_rejects_missing_field(tmp_path):
    bad = {k: v for k, v in GOOD.items() if k != "ticket_text"}
    with pytest.raises(DatasetError, match="missing required field"):
        load_cases(_write(tmp_path, bad))


def test_rejects_invalid_json(tmp_path):
    p = tmp_path / "broken.jsonl"
    p.write_text("{not json}", encoding="utf-8")
    with pytest.raises(DatasetError, match="invalid JSON"):
        load_cases(str(p))
