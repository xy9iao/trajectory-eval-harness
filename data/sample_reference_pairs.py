"""Deterministically sample the 30-pair reference set (labeling protocol §2).

Stratified: 10 pairs per dataset label class, round-robin across the
data/taxonomy.py occupation buckets (the 001 corpus scan), no two pairs
sharing a JD, rubric anchor pairs excluded (they defined the scale —
scoring them against it is circular). Fixed seed; output committed as
data/reference/sample-v1.json so the sample is regenerable and auditable:
`python data/sample_reference_pairs.py`.

The first MENTOR_COUNTS[label] pairs of each label's round-robin selection
form the mentor-review subset (protocol §6) — first-k preserves the bucket
spread the round-robin established.
"""

import json
import random
import sys
from pathlib import Path

from corpus import DOC_COLUMNS, read_rows
from taxonomy import OCCUPATION, occupation_bucket

OUT = Path(__file__).resolve().parent / "reference" / "sample-v1.json"

SEED = 20260715
PER_LABEL = 10
LABELS = ["No Fit", "Potential Fit", "Good Fit"]
MENTOR_COUNTS = {"No Fit": 3, "Potential Fit": 3, "Good Fit": 4}
ANCHOR_ROWS = {("train", 4699), ("train", 3143)}  # rubric v1 anchors — excluded
BUCKETS = [*OCCUPATION, "none"]


def main() -> int:
    rng = random.Random(SEED)
    by_label_bucket: dict[str, dict[str, list[tuple[int, str]]]] = {
        lab: {b: [] for b in BUCKETS} for lab in LABELS
    }
    try:
        for i, row in read_rows("train"):
            if ("train", i) in ANCHOR_ROWS:
                continue
            jd = row[DOC_COLUMNS["jd"]]
            by_label_bucket[row["label"]][occupation_bucket(jd.lower())].append((i, jd))
    except FileNotFoundError as e:
        print(e)
        return 1

    used_jds: set[str] = set()
    selected: list[dict[str, object]] = []
    for lab in LABELS:
        for bucket in BUCKETS:
            rng.shuffle(by_label_bucket[lab][bucket])
        picked = 0
        while picked < PER_LABEL:
            progressed = False
            for bucket in BUCKETS:
                if picked == PER_LABEL:
                    break
                pool = by_label_bucket[lab][bucket]
                while pool:
                    i, jd = pool.pop()
                    if jd not in used_jds:
                        used_jds.add(jd)
                        selected.append(
                            {
                                "split": "train",
                                "row": i,
                                "dataset_label": lab,
                                "occupation": bucket,
                                "mentor": picked < MENTOR_COUNTS[lab],
                            }
                        )
                        picked += 1
                        progressed = True
                        break
            if not progressed:
                print(f"exhausted candidates for label {lab!r} at {picked}/{PER_LABEL}")
                return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"seed": SEED, "anchor_rows_excluded": sorted(ANCHOR_ROWS), "pairs": selected}
    text = json.dumps(payload, indent=2) + "\n"
    OUT.write_text(text, encoding="utf-8")
    mentor = sum(1 for p in selected if p["mentor"])
    print(f"wrote {OUT.relative_to(Path.cwd())}: {len(selected)} pairs ({mentor} mentor-review)")
    for lab in LABELS:
        buckets = [str(p["occupation"]) for p in selected if p["dataset_label"] == lab]
        print(f"  {lab}: " + ", ".join(sorted(buckets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
