"""Skeleton runner: one pair through the stub graph, one trajectory out.

Stage E scope — eval mode, stub assessments, no LLM, no checkpointer wiring
(interactive interrupt/resume lands in Stage G). Real pairs need the local
dataset; --synthetic runs without it.

Usage:
    python -m agent.run --synthetic
    python -m agent.run --pair train:596
"""

import argparse
import functools
import json
import os
import sys
from pathlib import Path

from eval.trajectory import load_trajectory, validate_data_hygiene, validate_trajectory

from agent.client import make_completer, provider_config
from agent.graph import (
    ADVANCE_THRESHOLD,
    BOUNDARY_FLOOR,
    VETO_CAP,
    Assessor,
    Extractor,
    build_graph,
    config_digest,
)
from agent.llm_tools import assess_dimension_llm, extract_requirements
from agent.state import AgentState
from agent.tools import CorpusSource, DocumentSource, SyntheticSource
from agent.trajectory_writer import TrajectoryWriter
from agent.types import PairRef


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (stdlib-only; values never logged — D14)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


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
    extractor: Extractor | None = None,
    assessor: Assessor | None = None,
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
    app = build_graph(source, writer, extractor=extractor, assessor=assessor)
    final = app.invoke(initial_state(pair, mode))
    return final, writer  # type: ignore[return-value]


def run_batch(
    runs_dir: Path,
    provider: str,
    model: str,
    extractor: Extractor | None,
    assessor: Assessor | None,
) -> int:
    """Run every pair in the reference sample (eval mode), one trajectory
    each, validating structure + hygiene inline. Summary lines carry indices
    and scores only — no document text."""
    sample_path = Path(__file__).resolve().parents[1] / "data" / "reference" / "sample-v1.json"
    pairs = json.loads(sample_path.read_text(encoding="utf-8"))["pairs"]
    source = CorpusSource()
    print(f"batch: {len(pairs)} pairs | provider={provider} model={model}")
    failures = 0
    for n, entry in enumerate(pairs, 1):
        pair = PairRef.model_validate({"split": entry["split"], "row": entry["row"]})
        final, writer = run_pair(
            source, pair, "eval", runs_dir, provider, model, extractor, assessor
        )
        events = load_trajectory(writer.path)
        problems = validate_trajectory(events)
        resume_text, jd_text = source.load(pair)
        hygiene = validate_data_hygiene(events, {"resume": resume_text, "jd": jd_text})
        aggregate = final["aggregate"]
        gate = final["gate"]
        status = (
            "OK"
            if not problems and not hygiene
            else (f"INVALID×{len(problems)}" if problems else f"HYGIENE×{len(hygiene)}")
        )
        if problems or hygiene:
            failures += 1
        mean = aggregate.weighted_mean if aggregate else None
        print(
            f"[{n:2d}/{len(pairs)}] {pair.split}:{pair.row:<5} {writer.run_id}"
            f" mean={mean if mean is not None else 'null':<5} veto={aggregate.veto if aggregate else '?':<13}"
            f" gate={','.join(gate.triggers) if gate else '-':<40}"
            f" rec={final['recommendation']:<14} {status}",
            flush=True,
        )
    print(f"batch done: {len(pairs) - failures}/{len(pairs)} clean")
    return 0 if failures == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--pair", metavar="SPLIT:ROW", help="e.g. train:596 (needs local data)")
    group.add_argument("--synthetic", action="store_true")
    group.add_argument(
        "--batch",
        action="store_true",
        help="run all pairs in data/reference/sample-v1.json (eval mode)",
    )
    ap.add_argument("--mode", choices=["eval"], default="eval")  # interactive lands Stage G
    ap.add_argument(
        "--live",
        action="store_true",
        help="use the real LLM via .env provider config (Stage F); default is the stub",
    )
    args = ap.parse_args()

    provider = model = "stub"
    extractor: Extractor | None = None
    assessor: Assessor | None = None
    if args.live:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        cfg = provider_config()
        completer = make_completer(cfg)
        provider, model = cfg.provider, cfg.model
        extractor = functools.partial(extract_requirements, cfg, completer)
        assessor = functools.partial(assess_dimension_llm, cfg, completer)

    if args.batch:
        return run_batch(RUNS_DIR, provider, model, extractor, assessor)

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

    final, writer = run_pair(
        source, pair, args.mode, RUNS_DIR, provider, model, extractor, assessor
    )
    aggregate = final["aggregate"]
    print(f"run_id: {writer.run_id}")
    print(f"trajectory: {writer.path.relative_to(Path.cwd())}")
    print(f"aggregate: {aggregate.model_dump() if aggregate else None}")
    print(f"gate: {final['gate'].triggers if final['gate'] else 'not fired'}")
    print(f"recommendation: {final['recommendation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
