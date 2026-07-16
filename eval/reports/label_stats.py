"""Generate P0 label statistics from the reference JSONL (p0 report §3–§5).

Every number in the p0 report's label-statistics, disagreement, and
mentor-agreement sections is produced by this script — regenerable, no
raw dataset needed (the reference file carries indices and scores only):

    python eval/reports/label_stats.py

Reads data/reference/labels-v1.jsonl; if labels-v1-mentor.jsonl exists,
also emits the inter-annotator agreement section over the shared pairs.

Disagreement operationalization (recorded here, cited by the report):
a pair is flagged owner-vs-dataset divergent when the dataset says
"Good Fit" but the owner's weighted mean is < 2.5, or the dataset says
"No Fit" but the owner's weighted mean is >= 3.5. Band edges follow the
rubric scale's passing floor (3) with a half-band margin.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LABELS = ROOT / "data" / "reference" / "labels-v1.jsonl"
MENTOR = ROOT / "data" / "reference" / "labels-v1-mentor.jsonl"

DIMENSIONS = ["skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"]
LABEL_ORDER = ["No Fit", "Potential Fit", "Good Fit"]


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def divergent(rec: dict[str, Any]) -> bool:
    mean = float(rec["aggregate"]["weighted_mean"])
    label = rec["dataset_label"]
    return (label == "Good Fit" and mean < 2.5) or (label == "No Fit" and mean >= 3.5)


def score_table(recs: list[dict[str, Any]]) -> None:
    print("\n## Score distribution per dimension (count per band)\n")
    print("| dimension | 0 | 1 | 2 | 3 | 4 | 5 | mean |")
    print("|---|---|---|---|---|---|---|---|")
    for dim in DIMENSIONS:
        scores = [r["dimensions"][dim]["score"] for r in recs]
        counts = Counter(scores)
        cells = " | ".join(str(counts.get(b, 0)) for b in range(6))
        print(f"| {dim} | {cells} | {sum(scores) / len(scores):.2f} |")


def aggregate_table(recs: list[dict[str, Any]]) -> None:
    means = sorted(r["aggregate"]["weighted_mean"] for r in recs)
    print("\n## Aggregate (weighted mean over scoring dimensions)\n")
    print(f"- min {means[0]} · median {means[len(means) // 2]} · max {means[-1]}")
    buckets = Counter(int(m) for m in means)
    line = " · ".join(f"[{b},{b + 1}): {buckets.get(b, 0)}" for b in range(6))
    print(f"- histogram: {line}")
    veto = Counter(r["aggregate"]["veto"] for r in recs)
    print(f"- veto: {dict(veto)}")


def gate_table(recs: list[dict[str, Any]]) -> None:
    n_gate = sum(1 for r in recs if r["gate_expected"])
    reasons = Counter(reason for r in recs for reason in r["gate_reasons"])
    print("\n## gate_expected ground truth\n")
    print(f"- gate_expected: {n_gate}/{len(recs)}")
    print(f"- reasons (a pair can carry several): {dict(reasons.most_common())}")


def crosstab(recs: list[dict[str, Any]]) -> None:
    print("\n## Dataset label × owner veto\n")
    print("| dataset label | met | indeterminate | unmet | n |")
    print("|---|---|---|---|---|")
    for label in LABEL_ORDER:
        sub = [r for r in recs if r["dataset_label"] == label]
        v = Counter(r["aggregate"]["veto"] for r in sub)
        print(
            f"| {label} | {v.get('met', 0)} | {v.get('indeterminate', 0)}"
            f" | {v.get('unmet', 0)} | {len(sub)} |"
        )
    flagged = [r for r in recs if divergent(r)]
    print("\n## Owner-vs-dataset divergence (operationalization in script docstring)\n")
    print(f"- divergent pairs: {len(flagged)}/{len(recs)}")
    for r in flagged:
        print(
            f"  - train {r['pair']['row']} ({r['occupation']}): dataset {r['dataset_label']!r}"
            f" vs owner mean {r['aggregate']['weighted_mean']} veto {r['aggregate']['veto']}"
        )


def hesitation_table(recs: list[dict[str, Any]]) -> None:
    n = sum(1 for r in recs if r["hesitations"].strip())
    geo = sum(1 for r in recs if "geometry undefined" in r["hesitations"])
    print("\n## Hesitations\n")
    print(f"- pairs with hesitation notes: {n}/{len(recs)}")
    print(f"- no-skill-musts (geometry undefined, v1.1 derived-musts rule): {geo}/{len(recs)}")


def mentor_agreement(recs: list[dict[str, Any]], mentor: list[dict[str, Any]]) -> None:
    owner_by_key = {(r["pair"]["split"], r["pair"]["row"]): r for r in recs}
    shared = [
        (owner_by_key[(m["pair"]["split"], m["pair"]["row"])], m)
        for m in mentor
        if (m["pair"]["split"], m["pair"]["row"]) in owner_by_key
    ]
    print(f"\n## Mentor agreement (blind, {len(shared)} shared pairs)\n")
    print("| dimension | exact | within 1 band |")
    print("|---|---|---|")
    for dim in DIMENSIONS:
        pairs = [(o["dimensions"][dim]["score"], m["dimensions"][dim]["score"]) for o, m in shared]
        exact = sum(1 for a, b in pairs if a == b)
        within = sum(1 for a, b in pairs if abs(a - b) <= 1)
        print(f"| {dim} | {exact}/{len(pairs)} | {within}/{len(pairs)} |")
    gate = sum(1 for o, m in shared if o["gate_expected"] == m["gate_expected"])
    print(f"\n- gate_expected agreement: {gate}/{len(shared)}")
    diverging = [
        (o, m, dim)
        for o, m in shared
        for dim in DIMENSIONS
        if o["dimensions"][dim]["score"] != m["dimensions"][dim]["score"]
    ]
    for o, m, dim in diverging:
        print(
            f"  - train {o['pair']['row']} {dim}: owner {o['dimensions'][dim]['score']}"
            f" vs mentor {m['dimensions'][dim]['score']}"
        )


def main() -> int:
    if not LABELS.exists():
        print(f"{LABELS} not found")
        return 1
    recs = load(LABELS)
    print(f"# Label statistics — {len(recs)} records ({LABELS.name})")
    score_table(recs)
    aggregate_table(recs)
    gate_table(recs)
    crosstab(recs)
    hesitation_table(recs)
    if MENTOR.exists():
        mentor_agreement(recs, load(MENTOR))
    else:
        print("\n(mentor file not present — agreement section pending touchpoint 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
