"""View a single resume–JD pair from the raw dataset by split + row index.

The raw CSVs are gitignored (Decision 5); the reference file stores row
indices, never text, so labeling and review re-attach text from data/raw/
by index. This is that lookup tool.

Indices are 0-based (the header row is not counted): index 0 is the first
data row. An index is only stable against the byte-identical CSV that
download_dataset.py pins and checksums — reorder the file and the index
points elsewhere.

Usage:
    python data/view_pair.py train 4699
    python data/view_pair.py test 12
"""

import csv
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent / "raw"
SPLITS = ("train", "test")

# Resume cells run to several thousand characters; the default field limit
# raises _csv.Error on them.
csv.field_size_limit(sys.maxsize)


def load_row(split: str, index: int) -> dict[str, str]:
    path = RAW_DIR / f"{split}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — run `python data/download_dataset.py` first")
    with path.open(newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i == index:
                return row
    raise IndexError(f"{split}.csv has no row index {index} (0-based)")


def render(split: str, index: int, row: dict[str, str]) -> str:
    jd = row["job_description_text"]
    resume = row["resume_text"]
    return "\n".join(
        [
            f"# {split}.csv — row index {index} (0-based)",
            "",
            f"**Dataset label:** {row['label']}",
            "",
            "---",
            "",
            f"## JOB DESCRIPTION ({len(jd)} chars)",
            "",
            jd,
            "",
            "---",
            "",
            f"## RESUME ({len(resume)} chars)",
            "",
            resume,
        ]
    )


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in SPLITS:
        print(f"usage: python data/view_pair.py {{{'|'.join(SPLITS)}}} <row_index>")
        return 2
    split = sys.argv[1]
    try:
        index = int(sys.argv[2])
    except ValueError:
        print(f"row index must be an integer, got {sys.argv[2]!r}")
        return 2
    if index < 0:
        print("row index must be >= 0 (0-based)")
        return 2
    try:
        row = load_row(split, index)
    except (FileNotFoundError, IndexError) as e:
        print(e)
        return 1
    print(render(split, index, row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
