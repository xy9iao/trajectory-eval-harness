"""View a single resume–JD pair from the raw dataset by split + row index.

The raw CSVs are gitignored (Decision 5); the reference file stores row
indices, never text, so labeling and review re-attach text from data/raw/
by index. This is that lookup tool.

Indices are 0-based (the header row is not counted): index 0 is the first
data row. An index is only stable against the byte-identical CSV that
download_dataset.py pins and checksums — reorder the file and the index
points elsewhere.

Anchor-span workflow: `--find` locates text and prints its start:end char
offsets; `--span` prints exactly the slice at given offsets so a recorded
anchor can be re-verified. Offsets are always into the RAW string; the only
display transformation is newline → "⏎", which is 1:1 so offsets stay true.

Usage:
    python data/view_pair.py train 4699
    python data/view_pair.py train 4699 --find "Docker"
    python data/view_pair.py train 4699 --doc resume --find "Applied Computing"
    python data/view_pair.py train 4699 --doc jd --span 210:255
"""

import argparse
import sys

from corpus import DOC_COLUMNS, FIND_CONTEXT, SPLITS, find_offsets, load_row, show


def render(split: str, index: int, row: dict[str, str]) -> str:
    jd = row[DOC_COLUMNS["jd"]]
    resume = row[DOC_COLUMNS["resume"]]
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


def run_find(row: dict[str, str], docs: list[str], needle: str) -> int:
    hits = 0
    for doc in docs:
        text = row[DOC_COLUMNS[doc]]
        for start, end in find_offsets(text, needle):
            context = show(text[max(0, start - FIND_CONTEXT) : end + FIND_CONTEXT])
            print(f"{doc}  {start}:{end}  …{context}…")
            hits += 1
    if hits == 0:
        print(f"no match for {needle!r} in {'/'.join(docs)}")
    return 0 if hits else 1


def run_span(row: dict[str, str], doc: str, span: str) -> int:
    start_s, sep, end_s = span.partition(":")
    if not sep or not start_s.isdigit() or not end_s.isdigit():
        print(f"--span expects START:END with integers, got {span!r}")
        return 2
    start, end = int(start_s), int(end_s)
    text = row[DOC_COLUMNS[doc]]
    if not 0 <= start < end <= len(text):
        print(f"span {start}:{end} out of bounds for {doc} (0..{len(text)})")
        return 1
    print(f"{doc}[{start}:{end}] = {show(text[start:end])!r}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("split", choices=SPLITS)
    parser.add_argument("row", type=int)
    parser.add_argument("--doc", choices=list(DOC_COLUMNS), help="restrict to one document")
    parser.add_argument("--find", metavar="TEXT", help="case-insensitive; prints start:end offsets")
    parser.add_argument("--span", metavar="START:END", help="print exactly that slice (verify)")
    args = parser.parse_args()

    if args.row < 0:
        print("row index must be >= 0 (0-based)")
        return 2
    if args.span is not None and args.doc is None:
        print("--span requires --doc (a span is per-document)")
        return 2
    try:
        row = load_row(args.split, args.row)
    except (FileNotFoundError, IndexError) as e:
        print(e)
        return 1

    if args.find is not None:
        docs = [args.doc] if args.doc else list(DOC_COLUMNS)
        return run_find(row, docs, args.find)
    if args.span is not None:
        return run_span(row, args.doc, args.span)
    print(render(args.split, args.row, row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
