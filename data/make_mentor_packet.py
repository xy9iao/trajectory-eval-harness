"""Generate the mentor review packet (labeling protocol §6) into review/.

review/ is gitignored — the packet contains raw pair text (Decision 5:
never committed). Blind by construction: the packet carries pair text,
rubric pointer, and blank scoring forms; the owner's labels are never
read. The mentor's completed forms are transcribed into
data/reference/labels-v1-mentor.jsonl via the cockpit (--mentor) or by
the owner typing her values verbatim.

Usage: python data/make_mentor_packet.py
"""

import json
import sys
from pathlib import Path

from corpus import DOC_COLUMNS, load_row

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "review" / "mentor-packet"
SAMPLE = ROOT / "data" / "reference" / "sample-v1.json"

FORM = """
## Scoring form (fill per rubric v{rubric_version} — rubrics/rubric-v1.yaml)

| dimension | score (0-5) | evidence (quote the phrase) | notes |
|---|---|---|---|
| skills_coverage |  |  |  |
| experience_level |  |  |  |
| education_domain_fit |  |  |  |
| hard_requirements (0/3/5) |  |  |  |

- gate_expected (should a reviewer see this pair?): yes / no
- reasons (any that apply): hard_unmet · hard_indeterminate · boundary · insufficient_evidence · anomaly
- hesitations (anything you re-read twice, any band you could defend two ways):
"""

INSTRUCTIONS = """# Mentor review packet — blind labeling of 10 pairs

Thank you! This packet holds 10 resume-JD pairs. Please score each against the rubric
(rubrics/rubric-v1.yaml in the repo, or the copy provided) following the labeling protocol
(docs/labeling-protocol.md §5: read the JD first, list its must/required items, then read the
resume and score the four dimensions, citing the phrase each score rests on).

Two things make this scientifically useful:
1. **Blind:** please don't ask for or look at the owner's scores until your 10 are done —
   agreement between independent reads is the measurement.
2. **Hesitations are data:** wherever the rubric felt ambiguous, write one line about it —
   disagreement and hesitation feed the analysis; there are no wrong answers.

Files: one markdown file per pair, each ending with a scoring form.
"""


def main() -> int:
    import sys as _sys

    _sys.path.insert(0, str(ROOT))
    from eval.rubric_loader import load_rubric

    rubric_version = load_rubric(ROOT / "rubrics" / "rubric-v1.yaml").version
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    mentor_pairs = [p for p in sample["pairs"] if p["mentor"]]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "README.md").write_text(INSTRUCTIONS, encoding="utf-8")
    for n, p in enumerate(mentor_pairs, 1):
        row = load_row(p["split"], p["row"])
        jd, resume = row[DOC_COLUMNS["jd"]], row[DOC_COLUMNS["resume"]]
        form = FORM.format(rubric_version=rubric_version)
        body = "\n".join(
            [
                f"# Pair {n} of {len(mentor_pairs)} — {p['split']} row {p['row']}",
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
                "",
                "---",
                form,
            ]
        )
        (OUT_DIR / f"pair-{n:02d}-{p['split']}-{p['row']}.md").write_text(body, encoding="utf-8")
    print(f"wrote {len(mentor_pairs)} pair files + README to {OUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
