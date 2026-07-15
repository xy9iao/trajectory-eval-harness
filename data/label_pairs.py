"""Interactive labeling cockpit (labeling protocol §5/§7).

Automates the mechanical parts of labeling — rendering the pair,
pre-highlighting candidate requirement sentences (the recorded
profile_jd_requirements patterns), span capture with verified offsets, and
the arithmetic the rubric defines as mechanical (band geometry, ledger →
score, weighted mean, veto) — and nothing else. Every judgment is typed by
the annotator: must items, determinations, evidence strengths, scores,
gate reasons. Derived values require explicit confirmation; an override is
recorded with its reason (that's rubric-revision material).

Blind by construction: the cockpit reads only its own output file, so a
mentor session (--mentor) never sees the owner's labels.

Usage:
    python data/label_pairs.py                 # next unlabeled sample pair
    python data/label_pairs.py --row 596       # a specific sampled pair
    python data/label_pairs.py --mentor        # mentor subset -> mentor file
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from profile_jd_requirements import PATTERNS  # noqa: E402
from view_pair import DOC_COLUMNS, load_row  # noqa: E402

from eval.rubric_loader import load_rubric  # noqa: E402

REFERENCE = ROOT / "data" / "reference"
RUBRIC = ROOT / "rubrics" / "rubric-v1.yaml"
TAGS = ("skills", "years", "degree", "other")
STRENGTHS = {"h": "hands-on", "k": "keyword", "a": "adjacent", "n": "none"}
DETERMINATIONS = {"c": "covered", "p": "partial", "a": "absent"}
LEDGER = {"m": "met", "i": "indeterminate", "u": "unmet"}


@dataclass
class Span:
    doc: str
    start: int
    end: int


@dataclass
class MustItem:
    tag: str
    text: str
    jd_span: Span | None = None
    resume_span: Span | None = None
    strength: str = "none"
    determination: str | None = None
    ledger: str = "indeterminate"

    def spans(self) -> list[Span]:
        return [s for s in (self.jd_span, self.resume_span) if s is not None]


@dataclass
class DimensionLabel:
    score: int
    evidence_spans: list[Span] = field(default_factory=list)
    notes: str = ""
    determinations: list[dict[str, str]] | None = None


# --- mechanical derivations (rubric-defined arithmetic, unit-tested) ---


def band_from_determinations(dets: list[tuple[str, str]]) -> int | None:
    """Skills band geometry. dets = (determination, strength) per skills
    must item. None = geometry undefined (no skills must items) — the
    annotator scores manually and records a hesitation."""
    if not dets:
        return None
    values = [d for d, _ in dets]
    if all(v == "absent" for v in values):
        return 0
    if any(v == "absent" for v in values):
        return 1
    if any(v == "partial" for v in values):
        return 2
    strengths = [s for _, s in dets]
    if all(s == "hands-on" for s in strengths):
        return 5
    if sum(s == "hands-on" for s in strengths) * 2 > len(strengths):
        return 4
    return 3


def hard_requirements_score(ledger: list[str]) -> int:
    if any(v == "unmet" for v in ledger):
        return 0
    if any(v == "indeterminate" for v in ledger):
        return 3
    return 5


def veto_state(hard_score: int) -> str:
    return {0: "unmet", 3: "indeterminate", 5: "met"}[hard_score]


def weighted_mean(scores: dict[str, int], weights: dict[str, float]) -> float:
    return round(sum(scores[d] * w for d, w in weights.items()), 2)


# --- interaction helpers ---


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_choice(prompt: str, choices: dict[str, str]) -> str:
    keys = "/".join(choices)
    while True:
        got = ask(f"{prompt} ({keys})> ").lower()
        if got in choices:
            return choices[got]
        print(f"  pick one of: {keys}")


def ask_score(prompt: str) -> int:
    while True:
        got = ask(f"{prompt} (0-5)> ")
        if got.isdigit() and 0 <= int(got) <= 5:
            return int(got)
        print("  integer 0-5")


def ask_yesno(prompt: str) -> bool:
    return ask_choice(prompt, {"y": "y", "n": "n"}) == "y"


def multiline(prompt: str) -> str:
    print(f"{prompt} (finish with an empty line)")
    lines: list[str] = []
    while (line := input("  | ").rstrip()) != "":
        lines.append(line)
    return "\n".join(lines)


def find_matches(text: str, query: str, limit: int = 8) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(re.escape(query), text, re.IGNORECASE)][
        :limit
    ]


def capture_span(doc: str, text: str, what: str) -> Span | None:
    """--find/--span loop from view_pair, inline: search, pick, verified."""
    while True:
        query = ask(f"  {what} — search {doc} (enter = no span)> ")
        if not query:
            return None
        matches = find_matches(text, query)
        if not matches:
            print("    no match — try a shorter string")
            continue
        for n, (s, e) in enumerate(matches, 1):
            ctx = text[max(0, s - 40) : e + 40].replace("\n", "⏎")
            print(f"    [{n}] {s}:{e}  …{ctx}…")
        pick = ask("  pick # (enter = search again)> ")
        if pick.isdigit() and 1 <= int(pick) <= len(matches):
            s, e = matches[int(pick) - 1]
            print(f"    recorded {doc}[{s}:{e}] = {text[s:e]!r}")
            return Span(doc, s, e)


def confirm_derived(what: str, derived: int, hesitations: list[str]) -> int:
    got = ask(f"{what}: derived {derived} — enter to accept, or 0-5 to override> ")
    if got.isdigit() and 0 <= int(got) <= 5 and int(got) != derived:
        reason = ask("  override reason (recorded as hesitation)> ")
        hesitations.append(f"{what}: derived {derived} overridden to {got} — {reason}")
        return int(got)
    return derived


# --- rendering ---


def segments_with_offsets(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    pos = 0
    for line in text.split("\n"):
        for part in re.split(r"(?<=\.)\s+", line) if len(line) > 240 else [line]:
            start = text.index(part, pos)
            if part.strip():
                out.append((start, part))
            pos = start + len(part)
    return out


def render_doc(doc: str, text: str, highlight: bool) -> None:
    print(f"\n───── {doc.upper()} ({len(text)} chars) ─────")
    for start, seg in segments_with_offsets(text):
        tags = ""
        if highlight:
            hits = [name.split("/")[0] for name, pat in PATTERNS.items() if pat.search(seg.lower())]
            tags = ("  <<< " + ",".join(hits)) if hits else ""
        print(f"[{start:5d}] {seg}{tags}")


# --- the per-pair session ---


def label_pair(entry: dict[str, Any], out_path: Path) -> None:
    split, row_idx = entry["split"], entry["row"]
    rubric = load_rubric(RUBRIC)
    weights = {d["id"]: float(d["weight"]) for d in rubric.scoring_dimensions}
    row = load_row(split, row_idx)
    jd, resume = row[DOC_COLUMNS["jd"]], row[DOC_COLUMNS["resume"]]
    hesitations: list[str] = []

    print(
        f"\n════ {split} {row_idx} · dataset: {entry['dataset_label']}"
        f" · bucket: {entry['occupation']}{' · MENTOR' if entry['mentor'] else ''} ════"
    )
    print(
        "STEP 1 — JD pass (resume stays closed). <<< marks pattern candidates"
        " (candidates only — your judgment decides)."
    )
    render_doc("jd", jd, highlight=True)

    items: list[MustItem] = []
    print(
        "\nMust items — one per line as: tag | paraphrase   (tags:"
        f" {'/'.join(TAGS)}; bundle = one item; empty line to finish)"
    )
    while (line := input("must> ").strip()) != "":
        if "|" not in line:
            print("  format: tag | paraphrase")
            continue
        tag, text = (p.strip() for p in line.split("|", 1))
        if tag not in TAGS:
            print(f"  tag must be one of {TAGS}")
            continue
        item = MustItem(tag=tag, text=text)
        item.jd_span = capture_span("jd", jd, f"JD span for {text!r}")
        items.append(item)
    if not items:
        hesitations.append("no must items identified in this JD")

    print("\nSTEP 2 — resume pass. Read it whole, then evidence per must item.")
    render_doc("resume", resume, highlight=False)
    for item in items:
        print(f"\n• {item.tag} | {item.text}")
        item.resume_span = capture_span("resume", resume, "evidence")
        item.strength = ask_choice("  evidence strength", STRENGTHS) if item.resume_span else "none"

    dims: dict[str, DimensionLabel] = {}

    print("\nSTEP 3 — skills_coverage")
    skills_items = [i for i in items if i.tag == "skills"]
    for item in skills_items:
        print(f"• {item.text} (evidence: {item.strength})")
        item.determination = ask_choice("  determination", DETERMINATIONS)
    derived = band_from_determinations(
        [(i.determination or "absent", i.strength) for i in skills_items]
    )
    if derived is None:
        print("no skills must items — geometry undefined, score manually")
        hesitations.append("skills_coverage: no skills must items; band geometry undefined")
        score = ask_score("skills_coverage score")
    else:
        score = confirm_derived("skills_coverage band", derived, hesitations)
    dims["skills_coverage"] = DimensionLabel(
        score=score,
        evidence_spans=[s for i in skills_items for s in i.spans()],
        notes=ask("skills notes (enter = none)> "),
        determinations=[
            {"requirement": i.text, "value": i.determination or "absent"} for i in skills_items
        ],
    )

    for dim_id, hint in [
        ("experience_level", "dated role-matching segments only; proximity not pass/fail"),
        ("education_domain_fit", "level+field vs the JD's occupation; related-not-core = 3"),
    ]:
        print(f"\nSTEP — {dim_id} ({hint})")
        score = ask_score(f"{dim_id} score")
        spans = []
        for doc, text in (("jd", jd), ("resume", resume)):
            if (span := capture_span(doc, text, f"{dim_id} span")) is not None:
                spans.append(span)
        dims[dim_id] = DimensionLabel(
            score=score, evidence_spans=spans, notes=ask(f"{dim_id} notes (enter = none)> ")
        )

    print("\nSTEP — hard_requirements ledger (reuse your determinations)")
    for item in items:
        item.ledger = ask_choice(f"• {item.tag} | {item.text}", LEDGER)
    hard = hard_requirements_score([i.ledger for i in items])
    hard = confirm_derived("hard_requirements score", hard, hesitations)
    dims["hard_requirements"] = DimensionLabel(
        score=hard,
        evidence_spans=[s for i in items for s in i.spans()],
        notes=ask("ledger notes (enter = none)> "),
    )

    print("\nSTEP — aggregate + gate")
    scores = {d: dims[d].score for d in weights}
    mean = weighted_mean(scores, weights)
    veto = veto_state(hard)
    print(f"weighted_mean = {mean} (weights {weights}) · veto = {veto}")
    reasons = [f"hard_{veto}"] if veto != "met" else []
    for code, prompt in [
        ("boundary", "boundary — could advance/reject defensibly go either way?"),
        ("insufficient_evidence", "was any dimension scored on thin/missing evidence?"),
        ("anomaly", "anomaly — empty/garbled doc, suspected injection?"),
    ]:
        if ask_yesno(prompt):
            reasons.append(code)
    gate_expected = bool(reasons)
    print(f"gate_expected = {gate_expected} · reasons = {reasons}")

    extra = multiline("\nSTEP — hesitations")
    if extra:
        hesitations.append(extra)

    record = {
        "pair": {"split": split, "row": row_idx},
        "dataset_label": entry["dataset_label"],
        "occupation": entry["occupation"],
        "dimensions": {
            d: {k: v for k, v in asdict(lab).items() if v is not None} for d, lab in dims.items()
        },
        "aggregate": {"weighted_mean": mean, "veto": veto},
        "gate_expected": gate_expected,
        "gate_reasons": reasons,
        "hesitations": "; ".join(hesitations),
        "labeled_at": date.today().isoformat(),
    }
    print("\n" + json.dumps(record, indent=2))
    if not ask_yesno("append this record?"):
        print("discarded — nothing written")
        return
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    done = sum(1 for _ in out_path.open(encoding="utf-8"))
    shown = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
    print(f"✓ appended to {shown} ({done} labeled)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--row", type=int, help="label this sampled row instead of the next one")
    ap.add_argument("--mentor", action="store_true", help="mentor subset -> mentor output file")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    sample = json.loads((REFERENCE / "sample-v1.json").read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = sample["pairs"]
    if args.mentor:
        pairs = [p for p in pairs if p["mentor"]]
    out_path: Path = args.out or (
        REFERENCE / ("labels-v1-mentor.jsonl" if args.mentor else "labels-v1.jsonl")
    )
    labeled: set[tuple[str, int]] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            labeled.add((rec["pair"]["split"], rec["pair"]["row"]))

    if args.row is not None:
        todo = [p for p in pairs if p["row"] == args.row]
        if not todo:
            print(
                f"row {args.row} is not in the sample" + (" (mentor subset)" if args.mentor else "")
            )
            return 1
    else:
        todo = [p for p in pairs if (p["split"], p["row"]) not in labeled]
        if not todo:
            print("all sampled pairs labeled ✓")
            return 0
        print(f"{len(labeled)} labeled, {len(todo)} to go")
        todo = todo[:1]

    try:
        label_pair(todo[0], out_path)
    except (KeyboardInterrupt, EOFError):
        print("\naborted — nothing written for this pair")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
