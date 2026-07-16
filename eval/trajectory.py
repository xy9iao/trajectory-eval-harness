"""Trajectory JSONL contract — schema v0.1 (docs/trajectory-schema.md).

The validator enforces the schema's invariants; each check is the seed of a
P2 structural scorer. It returns a list of problem strings (empty = valid)
rather than raising, so scorers and tests can count and classify defects.
"""

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
EVENT_TYPES = {
    "run_start",
    "llm_call",
    "tool_call",
    "dimension_assessed",
    "gate_event",
    "error",
    "run_end",
}
DEFAULT_DIMENSIONS = (
    "skills_coverage",
    "experience_level",
    "education_domain_fit",
    "hard_requirements",
)
HARD_TRIGGERS = {"unmet": "hard_unmet", "indeterminate": "hard_indeterminate"}

Event = dict[str, Any]


def load_trajectory(path: Path) -> list[Event]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def validate_trajectory(
    events: list[Event], dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS
) -> list[str]:
    problems: list[str] = []
    if not events:
        return ["empty trajectory"]

    # 1 — envelope
    run_ids = {e.get("run_id") for e in events}
    if len(run_ids) != 1:
        problems.append(f"multiple run_ids: {sorted(map(str, run_ids))}")
    seqs = [e.get("seq") for e in events]
    if seqs != list(range(len(events))):
        problems.append("seq not strictly monotonic from 0")
    for e in events:
        if e.get("type") not in EVENT_TYPES:
            problems.append(f"unknown event type {e.get('type')!r} at seq {e.get('seq')}")
    starts = [e for e in events if e.get("type") == "run_start"]
    ends = [e for e in events if e.get("type") == "run_end"]
    if len(starts) != 1 or events[0].get("type") != "run_start":
        problems.append("exactly one run_start required, at seq 0")
    if len(ends) != 1 or events[-1].get("type") != "run_end":
        problems.append("exactly one run_end required, as the final event")
    if starts and starts[0].get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version != {SCHEMA_VERSION!r}")

    # 2 — dimension completeness
    assessed = [e for e in events if e.get("type") == "dimension_assessed"]
    seen = [e.get("dimension") for e in assessed]
    for dim in dimensions:
        if seen.count(dim) != 1:
            problems.append(f"dimension {dim!r} assessed {seen.count(dim)} times (want 1)")
    for stray in set(seen) - set(dimensions):
        problems.append(f"unknown dimension assessed: {stray!r}")

    # 3 — evidence citation (structural part)
    for e in assessed:
        spans = e.get("evidence_spans") or []
        if not spans:
            problems.append(f"{e.get('dimension')}: no evidence spans")
        for s in spans:
            if not (
                isinstance(s.get("start"), int)
                and isinstance(s.get("end"), int)
                and 0 <= s["start"] < s["end"]
            ):
                problems.append(f"{e.get('dimension')}: malformed span {s}")

    # 4 — gate consistency
    gates = [e for e in events if e.get("type") == "gate_event"]
    if ends:
        gate_fired = bool(ends[0].get("gate_fired"))
        if gate_fired != bool(gates):
            problems.append(f"run_end.gate_fired={gate_fired} but {len(gates)} gate_event(s)")
    hard = next((e for e in assessed if e.get("dimension") == "hard_requirements"), None)
    veto = hard.get("veto_state") if hard else None
    if veto in HARD_TRIGGERS:
        want = HARD_TRIGGERS[veto]
        if not any(want in (g.get("triggers") or []) for g in gates):
            problems.append(f"veto {veto!r} but no gate_event with trigger {want!r}")
    for g in gates:
        if g.get("mode") == "eval" and g.get("resolution") != "auto":
            problems.append(f"eval-mode gate_event resolved {g.get('resolution')!r} (want 'auto')")

    # 5 — totals reconcile
    calls = [e for e in events if e.get("type") == "llm_call"]
    if ends:
        totals = ends[0].get("totals") or {}
        expected = {
            "llm_calls": len(calls),
            "tokens_in": sum(c.get("tokens_in", 0) for c in calls),
            "tokens_out": sum(c.get("tokens_out", 0) for c in calls),
        }
        for key, want in expected.items():
            if totals.get(key) != want:
                problems.append(f"totals.{key}={totals.get(key)} != {want} (recomputed)")

    # 6 — retry visibility
    for i, c in enumerate(calls):
        if c.get("attempt", 1) > 1:
            prior = [
                p for p in calls[:i] if p.get("node") == c.get("node") and p.get("status") != "ok"
            ]
            if not prior:
                problems.append(
                    f"llm_call attempt {c.get('attempt')} at node {c.get('node')!r}"
                    " without a prior non-ok attempt"
                )

    return problems
