"""Trajectory JSONL contract — schema v0.2 (docs/trajectory-schema.md).

The validator enforces the schema's invariants; each check is the seed of a
P2 structural scorer. It returns a list of problem strings (empty = valid)
rather than raising, so scorers and tests can count and classify defects.

`validate_data_hygiene` (invariant 7) is separate because it needs the raw
documents, which only exist locally (Decision 5) — callers skip it where
the data is absent, same rule as the anchor in-bounds test.
"""

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.2"
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
HYGIENE_MIN_SUBSTRING = 20

Event = dict[str, Any]


def load_trajectory(path: Path) -> list[Event]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _check_envelope(events: list[Event], problems: list[str]) -> None:
    run_ids = {e.get("run_id") for e in events}
    if len(run_ids) != 1:
        problems.append(f"multiple run_ids: {sorted(map(str, run_ids))}")
    if [e.get("seq") for e in events] != list(range(len(events))):
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


def _check_dimensions(
    assessed: list[Event], dimensions: tuple[str, ...], problems: list[str]
) -> None:
    seen = [e.get("dimension") for e in assessed]
    for dim in dimensions:
        if seen.count(dim) != 1:
            problems.append(f"dimension {dim!r} assessed {seen.count(dim)} times (want 1)")
    for stray in set(seen) - set(dimensions):
        problems.append(f"unknown dimension assessed: {stray!r}")
    for e in assessed:
        name, score, degraded = e.get("dimension"), e.get("score"), bool(e.get("degraded"))
        if degraded and score is not None:
            problems.append(f"{name}: degraded but score={score!r} (must be null)")
        if not degraded and not (isinstance(score, int) and 0 <= score <= 5):
            problems.append(f"{name}: non-degraded score {score!r} not an int in 0..5")


def _check_evidence(assessed: list[Event], problems: list[str]) -> None:
    for e in assessed:
        dim, degraded = e.get("dimension"), bool(e.get("degraded"))
        spans = e.get("evidence_spans") or []
        if not degraded and not spans:
            problems.append(f"{dim}: no evidence spans on a non-degraded assessment")
        for s in spans:
            if not (
                isinstance(s.get("start"), int)
                and isinstance(s.get("end"), int)
                and 0 <= s["start"] < s["end"]
            ):
                problems.append(f"{dim}: malformed span {s}")


def _check_gate(events: list[Event], assessed: list[Event], problems: list[str]) -> None:
    gates = [e for e in events if e.get("type") == "gate_event"]
    ends = [e for e in events if e.get("type") == "run_end"]
    aggregate: dict[str, Any] = (ends[0].get("aggregate") or {}) if ends else {}
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
    if hard and aggregate and aggregate.get("veto") != veto:
        problems.append(f"aggregate.veto={aggregate.get('veto')!r} != veto_state {veto!r}")
    for g in gates:
        if g.get("mode") == "eval" and g.get("resolution") != "auto":
            problems.append(f"eval-mode gate_event resolved {g.get('resolution')!r} (want 'auto')")
    degraded_dims = [str(e.get("dimension")) for e in assessed if e.get("degraded")]
    if degraded_dims and not any(
        "insufficient_evidence" in (g.get("triggers") or []) for g in gates
    ):
        problems.append(
            f"degraded dimensions {degraded_dims} but no gate_event with"
            " trigger 'insufficient_evidence'"
        )
    if aggregate:
        partial = bool(aggregate.get("partial"))
        mean_null = aggregate.get("weighted_mean") is None
        missing = aggregate.get("missing") or []
        if not (partial == mean_null == bool(missing)):
            problems.append(
                f"partial/weighted_mean/missing incoherent: partial={partial},"
                f" weighted_mean_null={mean_null}, missing={missing}"
            )


def _check_totals(events: list[Event], problems: list[str]) -> None:
    calls = [e for e in events if e.get("type") == "llm_call"]
    ends = [e for e in events if e.get("type") == "run_end"]
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


def validate_trajectory(
    events: list[Event], dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS
) -> list[str]:
    """Invariants 1–6 (structural; no raw data needed)."""
    problems: list[str] = []
    if not events:
        return ["empty trajectory"]
    assessed = [e for e in events if e.get("type") == "dimension_assessed"]
    _check_envelope(events, problems)
    _check_dimensions(assessed, dimensions, problems)
    _check_evidence(assessed, problems)
    _check_gate(events, assessed, problems)
    _check_totals(events, problems)
    return problems


def _strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings_in(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings_in(v)]
    return []


def shares_doc_substring(
    value: str, documents: dict[str, str], min_len: int = HYGIENE_MIN_SUBSTRING
) -> str | None:
    """Name of the first document sharing a >= min_len verbatim substring with
    value, else None. Single source for the invariant-7 check — used by the
    validator below AND by the agent's post_validate (finding 007: model-
    authored labels must be paraphrases, never document text)."""
    if len(value) >= min_len:
        for doc_name, doc in documents.items():
            for i in range(len(value) - min_len + 1):
                if value[i : i + min_len] in doc:
                    return doc_name
    return None


def validate_data_hygiene(
    events: list[Event],
    documents: dict[str, str],
    min_len: int = HYGIENE_MIN_SUBSTRING,
) -> list[str]:
    """Invariant 7: no event string carries a >= min_len verbatim substring of
    any raw document — on ANY status branch (error.detail is the named
    high-risk path). Counts allowed, text never."""
    problems: list[str] = []
    for e in events:
        for s in _strings_in(e):
            doc_name = shares_doc_substring(s, documents, min_len)
            if doc_name is not None:
                problems.append(
                    f"seq {e.get('seq')} ({e.get('type')}): event text shares a"
                    f" {min_len}-char substring with {doc_name}"
                )
    return problems
