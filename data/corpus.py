"""Access layer for the pinned raw dataset (Decision 5, Route A).

Single home for the conventions every data/ tool shares: raw-CSV paths,
document columns, 0-based row identity, and the find/span primitives that
keep recorded char offsets true to the raw string. The raw CSVs are
gitignored; download_dataset.py pins and checksums them — a row index or
span offset is only meaningful against those byte-identical files.
"""

import csv
import sys
from collections.abc import Iterator
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent / "raw"
SPLITS = ("train", "test")
DOC_COLUMNS = {"jd": "job_description_text", "resume": "resume_text"}
FIND_CONTEXT = 40

# Resume cells run to several thousand characters; the default field limit
# raises _csv.Error on them.
csv.field_size_limit(sys.maxsize)


def _split_path(split: str) -> Path:
    path = RAW_DIR / f"{split}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — run `python data/download_dataset.py` first")
    return path


def read_rows(split: str) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield (0-based row index, row) from the pinned CSV."""
    with _split_path(split).open(newline="", encoding="utf-8") as f:
        yield from enumerate(csv.DictReader(f))


def load_row(split: str, index: int) -> dict[str, str]:
    for i, row in read_rows(split):
        if i == index:
            return row
    raise IndexError(f"{split}.csv has no row index {index} (0-based)")


def unique_jds(split: str) -> tuple[int, list[str]]:
    """(total row count, unique JD texts in first-occurrence order)."""
    jds = [row[DOC_COLUMNS["jd"]] for _, row in read_rows(split)]
    return len(jds), list(dict.fromkeys(jds))


def show(text: str) -> str:
    """1:1 char replacement — printed offsets stay true to the raw string."""
    return text.replace("\n", "⏎")


def find_offsets(text: str, needle: str, limit: int | None = None) -> list[tuple[int, int]]:
    """Case-insensitive occurrences of needle in text as (start, end) offsets."""
    lowered, target = text.lower(), needle.lower()
    spans: list[tuple[int, int]] = []
    start = lowered.find(target)
    while start != -1 and (limit is None or len(spans) < limit):
        spans.append((start, start + len(needle)))
        start = lowered.find(target, start + 1)
    return spans
