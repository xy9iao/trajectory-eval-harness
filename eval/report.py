"""One command, one eval report.

    uv run python -m eval.report --manifest runs/<batch>.json

Runs every registered scorer over one explicitly-scoped batch and emits a
markdown report. The runner is a **dumb pipe** (`for scorer in REGISTRY`):
iteration and I/O live here, all judgment lives in the scorers, which stay
pure functions of `(corpus, reference)`. Adding a scorer is one REGISTRY line.

Three contracts this file is responsible for, each of which exists because
skipping it produced a real wrong number earlier in the project:

1. **Explicit scope.** A batch is named by its run-id manifest, never by
   scanning `runs/`. A directory scan silently mixed 114 historical runs into
   a 150-run pass^k batch once; the numbers had no error and were wrong.
2. **Validation exclusion, surfaced not swallowed.** Invalid trajectories are
   excluded from every scorer AND printed in the header with their run ids.
   Scorers may assume valid input because something asserts it, not because
   everyone remembered to.
3. **Variant isolation (eval-design 3c gate 4).** Constructed variants and the
   live corpus never share a table. The manifest declares its own kind, and a
   variant batch is reported under a banner that says so — enforced here in
   code rather than trusted to whoever writes the report.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from eval.scorers import Corpus, Reference, Scorer, ScorerResult, load_reference
from eval.scorers.agreement import agreement_scorer
from eval.scorers.evidence_coverage import evidence_coverage_scorer
from eval.scorers.gate_integrity import gate_integrity_scorer
from eval.scorers.ledger_consistency import ledger_consistency_scorer
from eval.scorers.passk import passk_scorer
from eval.scorers.tool_calls import tool_call_correctness_scorer

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
REFERENCE = ROOT / "data" / "reference" / "labels-v1.jsonl"

REGISTRY: list[Scorer] = [
    gate_integrity_scorer,
    agreement_scorer,
    passk_scorer,
    ledger_consistency_scorer,
    tool_call_correctness_scorer,
    evidence_coverage_scorer,
]

VARIANT_BANNER = (
    "> **CONSTRUCTED VARIANTS — these numbers never merge with live-corpus numbers.**\n"
    "> Gate negatives here are hand-built perturbations of real pairs, not observed\n"
    "> outcomes. A combined confusion matrix would let constructed cases borrow the\n"
    "> credibility of measured ones (eval-design 3c gate 4).\n"
)


def _fmt_value(value: Any, indent: str = "") -> str:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return "\n" + "\n".join(f"{indent}  - `{json.dumps(v)}`" for v in value)
    if isinstance(value, dict):
        return "\n" + "\n".join(f"{indent}  - **{k}**: {v}" for k, v in value.items())
    return f"`{value}`"


def render(result: ScorerResult, max_rows: int) -> str:
    out = [f"### {result.name}", ""]
    for key, value in result.metrics.items():
        out.append(f"- **{key}**: {_fmt_value(value)}")
    if result.stability is None:
        # finding 011: a number computed over runs without a statement about
        # its run-to-run stability is a number without an error bar.
        out.append("")
        out.append("> **WARNING — no stability note.** This scorer reports a figure over runs")
        out.append("> without declaring how it moves between them. Treat the value as")
        out.append("> unqualified until the scorer supplies a StabilityNote.")
    else:
        out.append("")
        out.append(f"- **stability ({result.stability.basis})**: {result.stability.detail}")
        if result.stability.unstable_pairs:
            out.append(f"- **unstable pairs**: {', '.join(result.stability.unstable_pairs)}")
    if result.notes:
        out.append("")
        out.append(f"*{result.notes}*")
    if result.rows:
        shown = result.rows[:max_rows]
        out.append("")
        out.append(f"<details><summary>rows ({len(shown)} of {len(result.rows)})</summary>")
        out.append("")
        for row in shown:
            out.append(f"- `{json.dumps(row)}`")
        out.append("")
        out.append("</details>")
    out.append("")
    return "\n".join(out)


def build_report(manifest_path: Path, reference: Reference, max_rows: int) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Run directories normally live in runs/, but a self-contained batch keeps
    # them beside its own manifest (examples/sample-batch). Resolve against the
    # manifest's directory when the runs are there, so a committed sample batch
    # works from a fresh clone where runs/ does not exist at all.
    beside = manifest_path.parent
    run_ids = manifest["run_ids"]
    runs_dir = beside if run_ids and (beside / run_ids[0]).is_dir() else RUNS
    corpus = Corpus.from_manifest(runs_dir, manifest_path)
    kind = manifest.get("kind", "batch")

    head = [
        f"# Eval report — `{manifest_path.name}`",
        "",
        f"- **batch kind**: {kind}",
        f"- **provider / model**: {manifest.get('provider')} / {manifest.get('model')}",
        f"- **runs in manifest**: {len(manifest['run_ids'])}",
        f"- **cases scored**: {len(corpus.cases)}",
        f"- **excluded (validation)**: {len(corpus.excluded)}",
        "",
    ]
    if manifest.get("partial"):
        head += [
            f"> **PARTIAL RUN** — only {', '.join(manifest['partial'])} were run. "
            "Not the full batch; do not read these as batch results.",
            "",
        ]
    if kind == "variants":
        head += [VARIANT_BANNER, ""]
    if corpus.excluded:
        head += ["**Excluded runs** (surfaced, not silently dropped):", ""]
        head += [f"- `{run_id}` — {reason}" for run_id, reason in corpus.excluded]
        head += [""]
    if not corpus.cases:
        head += ["**No valid cases in this batch — nothing was scored.**", ""]
        return "\n".join(head)

    body = [render(scorer(corpus, reference), max_rows) for scorer in REGISTRY]
    return "\n".join(head + body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="run-id manifest, e.g. runs/passk-<id>.json")
    ap.add_argument("--reference", default=str(REFERENCE))
    ap.add_argument("--out", help="write markdown here instead of stdout")
    ap.add_argument("--max-rows", type=int, default=25, help="per-scorer row detail cap")
    args = ap.parse_args()

    report = build_report(Path(args.manifest), load_reference(Path(args.reference)), args.max_rows)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
