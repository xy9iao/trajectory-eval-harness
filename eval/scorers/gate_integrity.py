"""Gate-integrity scorer: should-gate x did-gate, WITH trigger attribution.

Ground truth is P0's `gate_expected` + `gate_reasons` (labels-v1.jsonl).

Two levels, because P1 surfaced that the binary matrix hides a real failure:
train 596 fired for the WRONG reason (boundary, while the reference reason
was hard_unmet) and still counted as a true positive. The binary matrix
alone would call that a success — so this scorer also reports
**trigger-attribution correctness** on the pairs it counts as TP.

Stability (finding 011's constraint): the confusion matrix is computed
ACROSS the k repeats when the corpus carries them. Per-pair gate decisions
that are not constant across k are reported as `unstable` — a matrix built
from one run per pair is a snapshot whose TP/FN membership churns (P1: the
FN count stayed 2 while its members changed), so this scorer refuses to
present a single-run matrix without saying which pairs move.
"""

from collections import Counter
from typing import Any

from eval.scorers import Corpus, Reference, ScorerResult, StabilityNote


def _majority_gate(fired: list[bool]) -> bool:
    return sum(fired) * 2 >= len(fired)


def gate_integrity_scorer(corpus: Corpus, reference: Reference) -> ScorerResult:
    groups = corpus.by_pair()
    cells: Counter[str] = Counter()
    unstable: list[str] = []
    per_run_cells: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    attribution_ok = attribution_checked = 0
    wrong_reason: list[dict[str, Any]] = []

    for pair, cases in sorted(groups.items(), key=lambda kv: kv[0][1]):
        ref = reference.get(pair)
        if ref is None:
            continue
        expected = bool(ref["gate_expected"])
        fired_per_run = [c.gate_fired for c in cases]
        label = f"{pair[0]}:{pair[1]}"

        # per-run cells: the matrix computed ACROSS all k repeats
        for fired in fired_per_run:
            per_run_cells[
                "TP"
                if (expected and fired)
                else "FN"
                if (expected and not fired)
                else "FP"
                if fired
                else "TN"
            ] += 1

        # per-pair cell uses the majority decision, and instability is named
        if len(set(fired_per_run)) > 1:
            unstable.append(label)
        fired = _majority_gate(fired_per_run)
        cell = (
            "TP"
            if (expected and fired)
            else "FN"
            if (expected and not fired)
            else "FP"
            if fired
            else "TN"
        )
        cells[cell] += 1

        # trigger attribution on pairs counted as TP: firing is not enough,
        # the REASON must match the reference (the 596 lesson)
        ref_reasons = set(ref.get("gate_reasons") or [])
        run_reasons = [set(c.gate_triggers()) for c in cases]
        matched = [bool(r & ref_reasons) for r in run_reasons]
        if cell == "TP":
            attribution_checked += 1
            if all(matched):
                attribution_ok += 1
            else:
                wrong_reason.append(
                    {
                        "pair": label,
                        "reference_reasons": sorted(ref_reasons),
                        "agent_reasons": sorted({t for r in run_reasons for t in r}),
                        "runs_matching": f"{sum(matched)}/{len(matched)}",
                    }
                )
        rows.append(
            {
                "pair": label,
                "expected": expected,
                "fired_across_k": f"{sum(fired_per_run)}/{len(fired_per_run)}",
                "cell": cell,
                "stable": len(set(fired_per_run)) == 1,
                "reference_reasons": sorted(ref_reasons),
            }
        )

    n = sum(cells.values())
    return ScorerResult(
        name="gate integrity",
        metrics={
            "pairs_scored": n,
            "confusion_by_pair_majority": dict(cells),
            "confusion_across_all_runs": dict(per_run_cells),
            "trigger_attribution_ok": (
                f"{attribution_ok}/{attribution_checked}" if attribution_checked else "0/0"
            ),
            "fired_for_wrong_reason": len(wrong_reason),
        },
        rows=rows,
        notes=(
            f"{len(wrong_reason)} pair(s) fired without matching the reference's gate reason: "
            + (
                "; ".join(
                    f"{w['pair']} (ref {w['reference_reasons']} vs agent {w['agent_reasons']})"
                    for w in wrong_reason
                )
                or "none"
            )
        ),
        stability=StabilityNote(
            basis="across-k",
            detail=(
                f"{len(unstable)}/{n} pairs flip their gate decision across the k repeats; "
                "the by-pair matrix uses the majority decision, and the across-all-runs matrix "
                "carries the full spread. A single-run matrix would hide this churn "
                "(finding 011)."
            ),
            unstable_pairs=unstable,
        ),
    )
