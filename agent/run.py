"""Skeleton runner: one pair through the stub graph, one trajectory out.

Stage E scope — eval mode, stub assessments, no LLM, no checkpointer wiring
(interactive interrupt/resume lands in Stage G). Real pairs need the local
dataset; --synthetic runs without it.

Usage:
    python -m agent.run --synthetic
    python -m agent.run --pair train:596
"""

import argparse
import sys
from pathlib import Path

from agent.graph import ADVANCE_THRESHOLD, BOUNDARY_FLOOR, VETO_CAP, build_graph, config_digest
from agent.state import AgentState
from agent.tools import CorpusSource, DocumentSource, SyntheticSource
from agent.trajectory_writer import TrajectoryWriter
from agent.types import PairRef

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"
RUBRIC_VERSION = "1.1"

SYNTHETIC_RESUME = (
    "Synthetic resume for the skeleton runner. Seven years of data platform work: "
    "batch and streaming pipelines, orchestration, warehouse modeling, and on-call "
    "ownership of ingestion reliability across three product teams. " * 2
)
SYNTHETIC_JD = (
    "Synthetic job description for the skeleton runner. We are hiring a data engineer "
    "to design, build, and operate pipelines feeding analytics and ML features; four "
    "or more years of relevant experience required. " * 2
)


def initial_state(pair: PairRef, mode: str) -> AgentState:
    return {
        "pair": pair,
        "mode": mode,  # type: ignore[typeddict-item]
        "rubric_version": RUBRIC_VERSION,
        "resume_text": "",
        "jd_text": "",
        "anomalies": [],
        "extraction": None,
        "dimensions_remaining": [],
        "assessments": {},
        "aggregate": None,
        "gate": None,
        "recommendation": None,
    }


def run_pair(
    source: DocumentSource,
    pair: PairRef,
    mode: str,
    runs_dir: Path,
    provider: str = "stub",
    model: str = "stub",
) -> tuple[AgentState, TrajectoryWriter]:
    writer = TrajectoryWriter(runs_dir)
    writer.emit(
        "run_start",
        schema_version="0.2",
        pair=pair.model_dump(),
        rubric_version=RUBRIC_VERSION,
        agent_mode=mode,
        provider=provider,
        model=model,
        config_digest=config_digest(
            {
                "advance": ADVANCE_THRESHOLD,
                "boundary_floor": BOUNDARY_FLOOR,
                "veto_cap": VETO_CAP,
                "rubric_version": RUBRIC_VERSION,
                "stub": provider == "stub",
            }
        ),
    )
    app = build_graph(source, writer)
    final = app.invoke(initial_state(pair, mode))
    return final, writer  # type: ignore[return-value]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--pair", metavar="SPLIT:ROW", help="e.g. train:596 (needs local data)")
    group.add_argument("--synthetic", action="store_true")
    ap.add_argument("--mode", choices=["eval"], default="eval")  # interactive lands Stage G
    args = ap.parse_args()

    source: DocumentSource
    if args.synthetic:
        source, pair = (
            SyntheticSource(SYNTHETIC_RESUME, SYNTHETIC_JD),
            PairRef(split="train", row=0),
        )
    else:
        split, _, row = args.pair.partition(":")
        source = CorpusSource()
        pair = PairRef.model_validate({"split": split, "row": int(row)})

    final, writer = run_pair(source, pair, args.mode, RUNS_DIR)
    aggregate = final["aggregate"]
    print(f"run_id: {writer.run_id}")
    print(f"trajectory: {writer.path.relative_to(Path.cwd())}")
    print(f"aggregate: {aggregate.model_dump() if aggregate else None}")
    print(f"gate: {final['gate'].triggers if final['gate'] else 'not fired'}")
    print(f"recommendation: {final['recommendation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
