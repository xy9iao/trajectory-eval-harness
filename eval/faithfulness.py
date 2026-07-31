"""Faithfulness spot-check cockpit (eval-design 3d).

Renders sampled assessments — score, cited evidence, and the surrounding
raw document context — and records the owner's verdict. The judgment is
human by necessity: asking a model whether a model's evidence supports its
own conclusion is self-assessment, and D7 is the project's core promise
about evidence.

Sampling is STRATIFIED (3d): 3 education, 3 veto-swing pairs, 2
degraded/resolution-failure, 2 random. The resulting number answers "how
does faithfulness behave on known weak spots", NOT "what is the overall
faithfulness rate" — the report must carry that distinction.

Usage:
    python -m eval.faithfulness --manifest runs/passk-<id>.json      # sample + judge
    python -m eval.faithfulness --manifest runs/passk-<id>.json --show   # re-read verdicts
"""

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

OUT = ROOT / "data" / "reference" / "faithfulness-v1.jsonl"
VETO_SWING_PAIRS = {596, 970, 5084, 6220}  # finding 011 §3
CONTEXT = 220
VERDICTS = {"s": "supports", "p": "partially_supports", "n": "does_not_support"}


def _sample(corpus: Any, rng: random.Random) -> list[dict[str, Any]]:
    """Stratified draw per eval-design 3d. Each item is one (run, dimension)."""
    pool: list[dict[str, Any]] = []
    for case in corpus.cases:
        for event in case.events:
            if event.get("type") != "dimension_assessed":
                continue
            pool.append(
                {
                    "run_id": case.run_id,
                    "pair": case.pair,
                    "dimension": event["dimension"],
                    "score": event.get("score"),
                    "degraded": bool(event.get("degraded")),
                    "resolution_failures": int(event.get("resolution_failures", 0)),
                    "spans": event.get("evidence_spans") or [],
                }
            )

    def draw(candidates: list[dict[str, Any]], n: int, taken: set[tuple[str, str]]) -> list[Any]:
        fresh = [c for c in candidates if (c["run_id"], c["dimension"]) not in taken]
        rng.shuffle(fresh)
        picked = fresh[:n]
        taken.update((c["run_id"], c["dimension"]) for c in picked)
        return picked

    # Strata are drawn in order and are mutually exclusive by construction:
    # later strata exclude the dimensions/pairs an earlier stratum owns, so the
    # education and veto quotas stay at 3 each instead of being padded by the
    # later draws (education is both the most failure-prone dimension and a
    # quarter of the pool, so an unguarded draw returns ~7 education samples —
    # a stratified design that silently collapses into one stratum).
    non_education = [c for c in pool if c["dimension"] != "education_domain_fit"]
    non_veto = [
        c
        for c in non_education
        if not (c["pair"][1] in VETO_SWING_PAIRS and c["dimension"] == "hard_requirements")
    ]
    taken: set[tuple[str, str]] = set()
    strata = [
        ("education", [c for c in pool if c["dimension"] == "education_domain_fit"], 3),
        (
            "veto_swing",
            [
                c
                for c in pool
                if c["pair"][1] in VETO_SWING_PAIRS and c["dimension"] == "hard_requirements"
            ],
            3,
        ),
        (
            "degraded_or_failures",
            [c for c in non_veto if c["degraded"] or c["resolution_failures"] > 0],
            2,
        ),
        ("random", [c for c in non_veto if not c["degraded"] and c["resolution_failures"] == 0], 2),
    ]
    sample: list[dict[str, Any]] = []
    for name, candidates, n in strata:
        for item in draw(candidates, n, taken):
            sample.append(item | {"stratum": name})
    return sample


def _render(item: dict[str, Any], docs: dict[str, str]) -> str:
    lines = [
        f"stratum: {item['stratum']}  |  {item['pair'][0]}:{item['pair'][1]}  |  run {item['run_id']}",
        f"dimension: {item['dimension']}   score: {item['score']}"
        + ("  [DEGRADED]" if item["degraded"] else "")
        + (
            f"  resolution_failures={item['resolution_failures']}"
            if item["resolution_failures"]
            else ""
        ),
        "",
        "CITED EVIDENCE (with surrounding context):",
    ]
    if not item["spans"]:
        lines.append("  (no evidence spans on this assessment)")
    for span in item["spans"]:
        text = docs[span["doc"]]
        s, e = span["start"], span["end"]
        before = text[max(0, s - CONTEXT) : s].replace("\n", " ")
        cited = text[s:e].replace("\n", " ")
        after = text[e : e + CONTEXT].replace("\n", " ")
        lines += [
            f"  [{span['doc']} {s}:{e}]",
            f"    ...{before}",
            f"    >>> {cited} <<<",
            f"    {after}...",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    from corpus import DOC_COLUMNS, load_row

    from eval.scorers import Corpus

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--show", action="store_true", help="print recorded verdicts and exit")
    ap.add_argument("--seed", type=int, default=20260728)
    args = ap.parse_args()

    if args.show:
        if not OUT.exists():
            print("no verdicts recorded yet")
            return 1
        for line in OUT.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            print(
                f"{rec['stratum']:22s} {rec['pair']} {rec['dimension']:22s} "
                f"score={rec['score']} -> {rec['verdict']}"
                + (f"  ({rec['reason']})" if rec.get("reason") else "")
            )
        return 0

    corpus = Corpus.from_manifest(ROOT / "runs", args.manifest)
    sample = _sample(corpus, random.Random(args.seed))
    print(f"Faithfulness spot-check — {len(sample)} stratified samples (design: eval-design 3d)")
    print("For each: does the cited evidence support the score at that band?\n")

    records = []
    for n, item in enumerate(sample, 1):
        row = load_row(*item["pair"])
        docs = {"resume": row[DOC_COLUMNS["resume"]], "jd": row[DOC_COLUMNS["jd"]]}
        print(f"\n{'=' * 78}\n[{n}/{len(sample)}] {_render(item, docs)}")
        while True:
            got = input("verdict — (s)upports / (p)artially / (n)o> ").strip().lower()
            if got in VERDICTS:
                break
            print("  s / p / n")
        reason = ""
        if got == "p":
            # a middle category without a reason is unanalyzable (3d)
            while not reason:
                reason = input(
                    "  what is missing? (quote too weak for the band / "
                    "quote correct but points the wrong way / other)> "
                ).strip()
        records.append(
            {
                "run_id": item["run_id"],
                "pair": f"{item['pair'][0]}:{item['pair'][1]}",
                "dimension": item["dimension"],
                "score": item["score"],
                "stratum": item["stratum"],
                "spans": item["spans"],
                "verdict": VERDICTS[got],
                "reason": reason,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(r) for r in records) + "\n"
    OUT.write_text(payload, encoding="utf-8")
    counts: dict[str, int] = {}
    for r in records:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"\nrecorded {len(records)} verdicts to {OUT.relative_to(ROOT)}: {counts}")
    print(
        "NOTE: stratified sample — describes behavior on known weak spots, "
        "not an overall faithfulness rate."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
