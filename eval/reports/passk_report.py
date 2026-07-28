"""pass^k report: variance table + figure (eval-design decisions 1 and 2c).

One reproducible command over a pass^k batch manifest:

    python eval/reports/passk_report.py runs/passk-<run_id>.json [--out NAME.png]

Emits the per-dimension run-to-run variance table (markdown) and renders
the figure with matplotlib default styles into
docs/phase-reports/figures/ — figures are generated output, never
hand-made, so the "one command" acceptance covers them.

Model name and output filename come from the manifest / --out, so the
same script renders the cross-model counterpart later and the two figures
sit side by side in the report without hand-editing.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIGURES = ROOT / "docs" / "phase-reports" / "figures"


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from eval.scorers import Corpus
    from eval.scorers.passk import passk_scorer

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--out", default=None, help="figure filename (default: passk-<model>.png)")
    args = ap.parse_args()

    manifest = args.manifest
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    model = str(meta.get("model", "unknown-model"))
    corpus = Corpus.from_manifest(ROOT / "runs", manifest)
    result = passk_scorer(corpus, {})

    print(f"# pass^k stability — {manifest.name}\n")
    if corpus.excluded:
        print(f"**{len(corpus.excluded)} case(s) excluded at load (validation failures):**")
        for run_id, reason in corpus.excluded:
            print(f"- {run_id}: {reason}")
        print()
    print("## Metrics\n")
    for key, value in result.metrics.items():
        print(f"- {key}: {value}")

    print("\n## Per-dimension run-to-run stability\n")
    print(
        "| dimension | all runs agree | agree rate | mean within-pair stdev | max stdev |"
        " pairs with a degraded run |"
    )
    print("|---|---|---|---|---|---|")
    for row in result.rows:
        print(
            f"| {row['dimension']} | {row['all_agree']} | {row['all_agree_rate']} |"
            f" {row['mean_within_pair_stdev']} | {row['max_within_pair_stdev']} |"
            f" {row['pairs_with_a_degraded_run']} |"
        )
    print(f"\n{result.notes}\n")

    FIGURES.mkdir(parents=True, exist_ok=True)
    import random

    dims = [r["dimension"] for r in result.rows]
    means = [r["mean_within_pair_stdev"] or 0.0 for r in result.rows]
    rates = [(r["all_agree_rate"] or 0.0) for r in result.rows]
    per_pair = [r["per_pair_stdevs"] for r in result.rows]
    k_values = result.metrics["k_seen"]
    k_label = str(k_values[0]) if len(k_values) == 1 else "/".join(map(str, k_values))
    n_pairs = result.metrics["pairs_scored"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Left: mean bar + every pair's own stdev as a jittered strip. The strip
    # (not a whisker) carries the distribution shape — a bimodal dimension (most
    # pairs flat, a few swinging hard) reads at a glance instead of collapsing
    # into the mean, and the topmost point IS the max, so no extra encoding.
    ax1.bar(dims, means, color="lightsteelblue", label="mean within-pair stdev")
    jitter = random.Random(0)  # deterministic jitter: the figure is regenerable
    for i, values in enumerate(per_pair):
        xs = [i + jitter.uniform(-0.18, 0.18) for _ in values]
        ax1.scatter(xs, values, s=18, alpha=0.55, color="darkslateblue", zorder=3)
    ax1.scatter([], [], s=18, alpha=0.55, color="darkslateblue", label="one pair")
    ax1.set_ylabel("within-pair score stdev (k runs, same input)")
    ax1.set_title("Run-to-run variance by dimension")
    ax1.tick_params(axis="x", rotation=20)
    ax1.legend(loc="upper left", fontsize=8)

    ax2.bar(dims, rates, color="lightsteelblue")
    ax2.set_ylim(0, 1)
    # "self-consistency", never "agreement": agreement in this project means
    # scores vs the human reference (mentor/owner labels). This panel is
    # zero-reference — the model vs itself. The cross-validation argument in
    # finding 011 depends on the two being distinct measurements.
    ax2.set_ylabel("fraction of pairs where all k runs are identical")
    ax2.set_title("Self-consistency rate (all k runs identical)")
    ax2.tick_params(axis="x", rotation=20)

    fig.suptitle(f"pass^k stability — k={k_label}, n={n_pairs} pairs, {model}")
    fig.tight_layout()
    out = FIGURES / (args.out or f"passk-{model}.png")
    fig.savefig(out, dpi=150)
    print(f"figure: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
