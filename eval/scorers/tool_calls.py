"""Tool-call structural correctness + error recovery.

Both reuse `eval/trajectory.py`'s invariant vocabulary rather than
re-implementing it (eval-design 2a): the validator decides legality, these
scorers measure quality on already-legal trajectories.

**Coverage caveat on error recovery (recorded up front so the report cannot
read as "passed"):** degradation is rare in the live corpus — P1 saw 5
degraded assessments before calibration and 1 after. A near-perfect recovery
rate here means "the failure path was almost never exercised", NOT "recovery
is verified". Real coverage waits on the variant stage; until then this
scorer's assurance comes from its planted defects, and the metric carries
`exercised_on` so nobody mistakes silence for evidence.
"""

from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult, StabilityNote
from eval.trajectory import DEFAULT_DIMENSIONS

EXPECTED_TOOLS = {"parse_resume", "parse_jd", "get_rubric", "assess_dimension"}


def tool_call_correctness_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    rows: list[dict[str, Any]] = []
    clean_runs = 0
    for case in corpus.cases:
        calls = case.tool_calls()
        names = [str(c.get("tool")) for c in calls]
        problems: list[str] = []

        # every rubric dimension assessed exactly once (same invariant the
        # validator enforces; here it becomes a measured rate)
        assessed = [d for d in case.dimension_scores()]
        for dim in DEFAULT_DIMENSIONS:
            if assessed.count(dim) != 1:
                problems.append(f"{dim} assessed {assessed.count(dim)}x")

        # get_rubric once per dimension, and assess_dimension likewise
        for tool, want in (
            ("get_rubric", len(DEFAULT_DIMENSIONS)),
            ("assess_dimension", len(DEFAULT_DIMENSIONS)),
        ):
            if names.count(tool) != want:
                problems.append(f"{tool} called {names.count(tool)}x (want {want})")

        # parse before assess: ordering is part of the contract
        if "parse_resume" in names and "assess_dimension" in names:
            if names.index("parse_resume") > names.index("assess_dimension"):
                problems.append("parse_resume after assess_dimension")

        # argument validity: dataset-text-free summaries carrying the keys we log by
        for call in calls:
            summary = call.get("args_summary")
            if not isinstance(summary, dict):
                problems.append(f"{call.get('tool')}: args_summary not a dict")

        unknown = set(names) - EXPECTED_TOOLS
        if unknown:
            problems.append(f"unknown tool(s): {sorted(unknown)}")

        if problems:
            rows.append(
                {
                    "run_id": case.run_id,
                    "pair": f"{case.pair[0]}:{case.pair[1]}",
                    "problems": problems,
                }
            )
        else:
            clean_runs += 1

    n = len(corpus.cases)
    return ScorerResult(
        name="tool-call correctness",
        metrics={
            "runs_scored": n,
            "structurally_correct": f"{clean_runs}/{n}",
            "rate": round(clean_runs / n, 3) if n else None,
        },
        rows=rows,
        notes="Reuses the trajectory validator's invariants; measures rate, not legality.",
        stability=StabilityNote(
            basis="across-k",
            detail="computed per run over all repeats; no single-run snapshot is involved.",
        ),
    )


def error_recovery_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    rows: list[dict[str, Any]] = []
    runs_with_retry = runs_recovered = runs_degraded = 0
    escalated_correctly = 0

    for case in corpus.cases:
        calls = case.llm_calls()
        retried = [c for c in calls if int(c.get("attempt", 1)) > 1]
        degraded = case.degraded_dimensions()
        if retried:
            runs_with_retry += 1
            if not degraded:
                runs_recovered += 1
        if degraded:
            runs_degraded += 1
            # the 3-ii contract: a degraded dimension MUST escalate to the gate
            if "insufficient_evidence" in case.gate_triggers():
                escalated_correctly += 1
            rows.append(
                {
                    "run_id": case.run_id,
                    "pair": f"{case.pair[0]}:{case.pair[1]}",
                    "degraded": degraded,
                    "escalated": "insufficient_evidence" in case.gate_triggers(),
                }
            )

    n = len(corpus.cases)
    exercised = runs_with_retry + runs_degraded
    return ScorerResult(
        name="error recovery",
        metrics={
            "runs_scored": n,
            "exercised_on": f"{exercised}/{n}",
            "runs_with_retry": runs_with_retry,
            "retry_recovered": f"{runs_recovered}/{runs_with_retry}" if runs_with_retry else "0/0",
            "runs_degraded": runs_degraded,
            "degraded_escalated_to_gate": (
                f"{escalated_correctly}/{runs_degraded}" if runs_degraded else "0/0"
            ),
        },
        rows=rows,
        notes=(
            "COVERAGE CAVEAT: the failure path is rarely exercised in the live corpus "
            f"({exercised}/{n} runs here). A high rate means the path was seldom taken, not "
            "that recovery is verified — real coverage comes from the variant stage; today's "
            "assurance is the planted-defect tests."
        ),
        stability=StabilityNote(
            basis="across-k",
            detail="per-run measurement across all repeats; rarity, not variance, is the limit.",
        ),
    )
