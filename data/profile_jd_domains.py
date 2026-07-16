"""Profile the unique JD corpus by occupational field and industry sector.

Evidence generator for docs/findings/001. Deterministic over the pinned,
checksummed train.csv (download_dataset.py), so the finding's numbers are
regenerable: `python data/profile_jd_domains.py`.

The keyword buckets live in data/taxonomy.py (shared with the requirement
scan and the reference sampler), together with the recorded method caveat:
keyword matching is coarse and cross-axis terms (e.g. "financial") can hit
both an occupation and an industry, so counts are directional, not exact.
"""

import sys
from collections import Counter

from corpus import unique_jds
from taxonomy import INDUSTRY, OCCUPATION, word


def main() -> int:
    try:
        total, uniq = unique_jds("train")
    except FileNotFoundError as e:
        print(e)
        return 1
    low = [j.lower() for j in uniq]
    n = len(uniq)
    print(f"train rows: {total} | unique JDs: {n}")

    print("\n=== occupational field (unique JDs mentioning) ===")
    for label, terms in OCCUPATION.items():
        c = sum(1 for j in low if any(word(t, j) for t in terms))
        print(f"  {c:3d}  {label}")

    print("\n=== industry/sector keyword frequency ===")
    ind: Counter[str] = Counter()
    for j in low:
        for t in INDUSTRY:
            if word(t, j):
                ind[t] += 1
    for t, c in ind.most_common():
        print(f"  {c:3d}  {t}")

    any_ind = sum(1 for j in low if any(word(t, j) for t in INDUSTRY))
    print(f"\nunique JDs with >=1 industry word: {any_ind}/{n} (no industry signal: {n - any_ind})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
