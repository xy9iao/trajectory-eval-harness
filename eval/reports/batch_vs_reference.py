"""Dev-batch vs reference-label comparison (P1; findings 007/008 evidence).

Selects the latest non-stub run per pair from runs/, validates each
trajectory (structure + hygiene, needs the local dataset), joins to
data/reference/labels-v1.jsonl, and reports: per-dimension agreement, the
gate confusion matrix against gate_expected, ledger contradictions (hard
vs skills determinations on shared item ids — finding 008), and the
three-class failure breakdown for the single calibration round.

Regenerable: `python eval/reports/batch_vs_reference.py` (requires local
runs/ and data/raw/ — same standing as the raw CSVs).
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
LABELS = ROOT / "data" / "reference" / "labels-v1.jsonl"
DIMENSIONS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))


def latest_runs_per_pair() -> dict[tuple[str, int], list[dict[str, Any]]]:
    from eval.trajectory import load_trajectory

    best: dict[tuple[str, int], tuple[str, list[dict[str, Any]]]] = {}
    for path in sorted(RUNS.glob("*/trajectory.jsonl")):
        events = load_trajectory(path)
        start = events[0]
        if start.get("type") != "run_start" or start.get("provider") == "stub":
            continue
        key = (start["pair"]["split"], start["pair"]["row"])
        run_id = str(start.get("run_id"))
        if key not in best or run_id > best[key][0]:
            best[key] = (run_id, events)
    return {k: v[1] for k, v in best.items()}


def main() -> int:
    from corpus import DOC_COLUMNS, load_row  # type: ignore[import-not-found]

    from eval.trajectory import validate_data_hygiene, validate_trajectory

    refs = {
        (r["pair"]["split"], r["pair"]["row"]): r
        for r in (
            json.loads(x) for x in LABELS.read_text(encoding="utf-8").splitlines()
        )
    }
    runs = latest_runs_per_pair()
    print(f"# Batch vs reference — {len(runs)} runs joined to {len(refs)} labels\n")

    struct_bad = hygiene_bad = 0
    dim_match: Counter[str] = Counter()
    dim_total: Counter[str] = Counter()
    confusion: Counter[tuple[bool, bool]] = Counter()  # (expected, fired)
    degraded_pairs: list[Any] = []
    ledger_contradictions: list[Any] = []
    gate_misses: list[Any] = []
    semantic_divergent: list[Any] = []
    tokens_in = tokens_out = 0

    for key, events in sorted(runs.items(), key=lambda kv: kv[0][1]):
        ref = refs.get(key)
        if ref is None:
            continue
        row = load_row(*key)
        docs = {"resume": row[DOC_COLUMNS["resume"]], "jd": row[DOC_COLUMNS["jd"]]}
        if validate_trajectory(events):
            struct_bad += 1
        if validate_data_hygiene(events, docs):
            hygiene_bad += 1

        assessed = {
            e["dimension"]: e for e in events if e["type"] == "dimension_assessed"
        }
        end = events[-1]
        calls = [e for e in events if e["type"] == "llm_call"]
        tokens_in += sum(c["tokens_in"] for c in calls)
        tokens_out += sum(c["tokens_out"] for c in calls)

        mismatched_dims = []
        for dim in DIMENSIONS:
            agent = assessed.get(dim, {})
            if agent.get("degraded"):
                degraded_pairs.append((key[1], dim))
                continue
            dim_total[dim] += 1
            if agent.get("score") == ref["dimensions"][dim]["score"]:
                dim_match[dim] += 1
            else:
                mismatched_dims.append(
                    f"{dim}:{agent.get('score')}vs{ref['dimensions'][dim]['score']}"
                )
        if mismatched_dims:
            semantic_divergent.append((key[1], mismatched_dims))

        expected = bool(ref["gate_expected"])
        fired = bool(end.get("gate_fired"))
        confusion[(expected, fired)] += 1
        if expected != fired:
            gate_misses.append((key[1], "miss" if expected else "false_alarm"))

        skills_dets = {
            d["requirement"]: d["value"]
            for d in assessed.get("skills_coverage", {}).get("determinations") or []
        }
        for det in assessed.get("hard_requirements", {}).get("determinations") or []:
            rid = det["requirement"]
            if rid in skills_dets and skills_dets[rid] != det["value"]:
                ledger_contradictions.append(
                    (key[1], rid, f"skills={skills_dets[rid]} hard={det['value']}")
                )

    print(f"validation: structural clean {len(runs) - struct_bad}/{len(runs)}"
          f" · hygiene clean {len(runs) - hygiene_bad}/{len(runs)}")
    print(f"cost: {tokens_in} in / {tokens_out} out tokens\n")
    print("## Per-dimension exact agreement (non-degraded)\n")
    for dim in DIMENSIONS:
        print(f"- {dim}: {dim_match[dim]}/{dim_total[dim]}")
    print(f"- degraded (excluded): {degraded_pairs or 'none'}\n")
    print("## Gate confusion (reference gate_expected vs agent gate_fired)\n")
    print(f"- expected+fired (TP): {confusion[(True, True)]}")
    print(f"- expected+silent (FN — miss): {confusion[(True, False)]}")
    print(f"- unexpected+fired (FP): {confusion[(False, True)]}")
    print(f"- unexpected+silent (TN): {confusion[(False, False)]}")
    print(f"- misses: {gate_misses or 'none'}\n")
    print("## Ledger contradictions (finding 008; shared ids, differing values)\n")
    print(f"- {ledger_contradictions or 'none'}\n")
    print("## Semantic divergence (>=1 dimension score mismatch)\n")
    print(f"- {len(semantic_divergent)}/{len(runs)} pairs")
    for row_id, dims in semantic_divergent:
        print(f"  - train {row_id}: {', '.join(dims)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
