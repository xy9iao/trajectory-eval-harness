"""Profile the unique JD corpus by occupational field and industry sector.

Evidence generator for docs/findings/001. Deterministic over the pinned,
checksummed train.csv (download_dataset.py), so the finding's numbers are
regenerable: `python data/profile_jd_domains.py`.

Method note recorded honestly in the finding: keyword matching is coarse and
cross-axis terms (e.g. "financial") can hit both an occupation and an
industry, so counts are directional, not exact.
"""

import csv
import re
import sys
from collections import Counter
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw" / "train.csv"
csv.field_size_limit(sys.maxsize)

OCCUPATION = {
    "software eng": [
        "software engineer",
        "software developer",
        "full stack",
        "backend",
        "back-end",
        "frontend",
        "front-end",
    ],
    "data/ML": ["data engineer", "data analyst", "data scientist", "machine learning"],
    "devops/infra": ["devops", "site reliability", "cloud engineer", "platform engineer"],
    "hardware eng": [
        "electrical engineer",
        "electronic engineer",
        "mechanical engineer",
        "hardware",
    ],
    "accounting/fin": ["accountant", "accounting", "bookkeeper", "financial analyst", "auditor"],
    "business/PM": ["business analyst", "product manager", "project manager", "program manager"],
    "sales/mktg": ["sales", "marketing", "account executive"],
    "healthcare": ["nurse", "physician", "clinical", "medical assistant"],
    "hr/admin": ["human resources", "recruiter", "office manager", "administrative"],
}
INDUSTRY = [
    "finance",
    "financial",
    "banking",
    "bank",
    "fintech",
    "healthcare",
    "health care",
    "medical",
    "hospital",
    "insurance",
    "retail",
    "e-commerce",
    "government",
    "federal",
    "defense",
    "manufacturing",
    "automotive",
    "telecom",
    "education",
    "pharmaceutical",
    "energy",
    "oil",
    "aerospace",
]


def word(term: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def main() -> int:
    if not RAW.exists():
        print(f"{RAW} not found — run `python data/download_dataset.py` first")
        return 1
    with RAW.open(newline="", encoding="utf-8") as f:
        jds = [row["job_description_text"] for row in csv.DictReader(f)]
    uniq = list(dict.fromkeys(jds))
    low = [j.lower() for j in uniq]
    n = len(uniq)
    print(f"train rows: {len(jds)} | unique JDs: {n}")

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
