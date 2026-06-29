"""Dataset: the eval cases and their ground truth (GUIDE §7).

The taxonomy — five categories, five actions, and the difficulty axis — is the RA-designed instrument.
Each case encodes a hypothesis about where a *stateful* triage agent fails: classification under
ambiguity, graceful handling of missing data, prompt-injection robustness, and multi-tool sequencing.
Anyone can run an off-the-shelf benchmark; the design judgment baked into these cases is the point.

Loading is pure Python: it validates the schema and the taxonomy WITHOUT a model or the agent, so a
malformed or self-inconsistent case fails fast in a unit test rather than silently skewing the metrics.

The label space (`CATEGORIES`, `ACTIONS`) is imported from the agent's prompts, and the gate predicate
mirrors the agent's runtime rule, so the dataset can never drift from what the agent actually does —
scoring a category the agent can't emit, or a gate the agent wouldn't fire, would be meaningless.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.agent.prompts import ACTIONS, CATEGORIES

# Difficulty axis (GUIDE §7) — the RA's design dimension; it lives with the dataset, not the agent.
DIFFICULTIES = ("straightforward", "ambiguous", "missing_info", "multi_step", "adversarial")

# Canonical read-only tool names. Mirrors the @mcp.tool wrappers in src/mcp/server.py;
# every entry in a case's expected_tools must be one of these.
VALID_TOOLS = ("get_account", "get_order", "get_ticket_history", "get_policy")

# Consequential actions require the HITL gate; informational ones never do. This MUST equal
# GATE_ACTIONS in src/agent/nodes.py — the deterministic gate rule the agent runs. We keep a local
# copy so this module stays dependency-light (no langgraph import), and a test asserts the two agree.
CONSEQUENTIAL_ACTIONS = ("refund", "ban", "escalate")

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "eval_set.jsonl"


@dataclass(frozen=True)
class GroundTruth:
    """The expected outcome for a case — what a correct, safe run should produce."""

    category: str
    action: str
    gate_required: bool
    expected_tools: tuple[str, ...]


@dataclass(frozen=True)
class Case:
    """One eval case: an untrusted ticket plus its ground truth and design metadata."""

    case_id: str
    ticket_text: str
    difficulty: str
    ground_truth: GroundTruth
    notes: str = ""


class DatasetError(ValueError):
    """Raised when a case violates the schema or the taxonomy."""


def _parse_case(obj: dict, *, line_no: int) -> Case:
    try:
        gt = obj["ground_truth"]
        case = Case(
            case_id=obj["case_id"],
            ticket_text=obj["ticket_text"],
            difficulty=obj["difficulty"],
            ground_truth=GroundTruth(
                category=gt["category"],
                action=gt["action"],
                gate_required=bool(gt["gate_required"]),
                expected_tools=tuple(gt.get("expected_tools", [])),
            ),
            notes=obj.get("notes", ""),
        )
    except KeyError as e:
        raise DatasetError(f"line {line_no}: missing required field {e}") from e
    _validate_case(case, line_no=line_no)
    return case


def _validate_case(case: Case, *, line_no: int) -> None:
    """Reject anything that would make the metrics lie (GUIDE §6.1: 'if the trace is lossy, the eval lies')."""
    gt = case.ground_truth
    where = f"line {line_no} ({case.case_id})"
    if not case.case_id or not case.ticket_text:
        raise DatasetError(f"{where}: empty case_id or ticket_text")
    if case.difficulty not in DIFFICULTIES:
        raise DatasetError(f"{where}: bad difficulty {case.difficulty!r}; expected one of {DIFFICULTIES}")
    if gt.category not in CATEGORIES:
        raise DatasetError(f"{where}: bad category {gt.category!r}; expected one of {CATEGORIES}")
    if gt.action not in ACTIONS:
        raise DatasetError(f"{where}: bad action {gt.action!r}; expected one of {ACTIONS}")
    bad_tools = sorted(set(gt.expected_tools) - set(VALID_TOOLS))
    if bad_tools:
        raise DatasetError(f"{where}: unknown expected_tools {bad_tools}; valid: {list(VALID_TOOLS)}")
    # Validity guard: gate_required must match the deterministic rule, or the gate-integrity metric
    # would be scored against an impossible expectation.
    expect_gate = gt.action in CONSEQUENTIAL_ACTIONS
    if gt.gate_required != expect_gate:
        raise DatasetError(
            f"{where}: gate_required={gt.gate_required} is inconsistent with action {gt.action!r} "
            f"(the rule gates exactly {CONSEQUENTIAL_ACTIONS}, so expected {expect_gate})"
        )


def load_cases(path: Path | str = DATASET_PATH) -> list[Case]:
    """Load and validate every case from a JSONL file. Raises DatasetError on the first bad line."""
    path = Path(path)
    cases: list[Case] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                raise DatasetError(f"line {line_no}: invalid JSON ({e})") from e
            case = _parse_case(obj, line_no=line_no)
            if case.case_id in seen:
                raise DatasetError(f"line {line_no}: duplicate case_id {case.case_id!r}")
            seen.add(case.case_id)
            cases.append(case)
    if not cases:
        raise DatasetError(f"no cases loaded from {path}")
    return cases


# --------------------------------------------------------------------------------------
# Self-test / coverage report: `python -m src.eval.dataset` — prints the taxonomy breakdown
# you cite in the report. No model or network needed.
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    from collections import Counter

    cases = load_cases()
    by_diff = Counter(c.difficulty for c in cases)
    by_cat = Counter(c.ground_truth.category for c in cases)
    by_act = Counter(c.ground_truth.action for c in cases)
    print(f"{len(cases)} cases loaded and validated from {DATASET_PATH}\n")
    print("by difficulty:", dict(by_diff))
    print("by category:  ", dict(by_cat))
    print("by action:    ", dict(by_act))
    gated = sum(c.ground_truth.gate_required for c in cases)
    print(f"\ngate_required: {gated} gated / {len(cases) - gated} not gated")
