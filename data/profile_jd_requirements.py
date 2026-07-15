"""Profile the unique JD corpus by requirement-pattern prevalence.

Evidence generator for the rubric v1 weight rationale (p0 report §2): what
fraction of unique JDs carry explicit must/required language, a stated years
requirement, and a degree mention. Deterministic over the pinned, checksummed
train.csv (download_dataset.py): `python data/profile_jd_requirements.py`.

Pattern notes (recorded so the numbers are auditable, not just regenerable):
- must-language counts must / require / requires / required / requirement(s).
- years counts numeric year phrases incl. ranges ("5+ years", "3-5 years",
  "3 to 5 years") and the bare "years of experience" idiom.
- degrees counts degree-level tokens only. Bare "ms"/"bs" are excluded (32
  unique JDs match \\bms\\b, dominated by "MS Office"/"MS SQL"); "associate"
  is excluded ("sales associate" job titles); "associate degree" is still
  caught via "degree".
"""

import csv
import re
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw" / "train.csv"
csv.field_size_limit(sys.maxsize)

PATTERNS = {
    "must/required language": re.compile(r"\b(must|require[sd]?|requirements?)\b"),
    "years requirement": re.compile(
        r"\b\d+\s*(?:\+|-|–|to\s*\d+)?\s*years?\b|\byears?\s+of\s+experience\b"
    ),
    "degree mention": re.compile(r"\b(bachelor'?s?|master'?s?|degree|ph\.?d|doctorate|mba|bsms)\b"),
}


def main() -> int:
    if not RAW.exists():
        print(f"{RAW} not found — run `python data/download_dataset.py` first")
        return 1
    with RAW.open(newline="", encoding="utf-8") as f:
        jds = [row["job_description_text"] for row in csv.DictReader(f)]
    uniq = [j.lower() for j in dict.fromkeys(jds)]
    n = len(uniq)
    print(f"train rows: {len(jds)} | unique JDs: {n}")
    for label, pat in PATTERNS.items():
        c = sum(1 for j in uniq if pat.search(j))
        print(f"  {c:3d}/{n} = {c / n:5.1%}  {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
