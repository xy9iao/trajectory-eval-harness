"""Profile the unique JD corpus by requirement-pattern prevalence.

Evidence generator for the rubric v1 weight rationale (p0 report §2): what
fraction of unique JDs carry explicit must/required language, a stated years
requirement, and a degree mention. Deterministic over the pinned, checksummed
train.csv (download_dataset.py): `python data/profile_jd_requirements.py`.

The patterns live in data/taxonomy.py (shared with the labeling cockpit's
candidate highlighting), together with the recorded pattern notes that make
the counts auditable, not just regenerable.
"""

import sys

from corpus import unique_jds
from taxonomy import PATTERNS


def main() -> int:
    try:
        total, uniq = unique_jds("train")
    except FileNotFoundError as e:
        print(e)
        return 1
    low = [j.lower() for j in uniq]
    n = len(uniq)
    print(f"train rows: {total} | unique JDs: {n}")
    for label, pat in PATTERNS.items():
        c = sum(1 for j in low if pat.search(j))
        print(f"  {c:3d}/{n} = {c / n:5.1%}  {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
