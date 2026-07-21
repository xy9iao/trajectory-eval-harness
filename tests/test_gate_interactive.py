"""Stage G contract: interactive gate — interrupt, review artifact, resume.

The interrupt e2e tests skip until the owner implements
`agent.hitl.request_human_decision` (Stage G slot #1). The resume CLI
(slot #2) is exercised by the owner's hands-on run, not here — these tests
prove the library-level chain: interrupt -> review file -> Command(resume)
-> resolution in state and trajectory, seq monotonic across the break.
"""

import inspect
from pathlib import Path
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent.graph import RESOLUTION_BY_DECISION, build_graph
from agent.hitl import request_human_decision
from agent.review import read_decision, write_review_file
from agent.run import SYNTHETIC_JD, SYNTHETIC_RESUME, initial_state, run_pair
from agent.tools import SyntheticSource
from agent.trajectory_writer import TrajectoryWriter
from agent.types import PairRef
from eval.trajectory import load_trajectory, validate_trajectory

hitl_implemented = "NotImplementedError" not in inspect.getsource(request_human_decision)
needs_hitl = pytest.mark.skipif(
    not hitl_implemented,
    reason="Stage G slot #1: owner implements request_human_decision",
)


# --- review artifact (no slot needed) ---


def _payload() -> dict[str, Any]:
    return {
        "pair": {"split": "train", "row": 0},
        "triggers": ["hard_indeterminate", "boundary"],
        "dimensions": [
            {
                "dimension": "skills_coverage",
                "score": 3,
                "degraded": False,
                "veto_state": None,
                "evidence": [{"doc": "resume", "span": "0:20", "text": "synthetic evidence x"}],
                "notes": "",
            }
        ],
        "aggregate_raw": 3.0,
        "aggregate_capped": 3.0,
        "veto": "indeterminate",
        "machine_draft": "flagged",
    }


def test_review_file_renders_and_parses(tmp_path: Path) -> None:
    path = write_review_file(tmp_path, "rtest-1", _payload())
    text = path.read_text(encoding="utf-8")
    assert "hard_indeterminate" in text and "raw=3.0" in text
    assert read_decision(tmp_path, "rtest-1") is None  # 'pending' is not a decision
    decided = text.replace("decision: pending", "decision: approve")
    path.write_text(decided, encoding="utf-8")
    assert read_decision(tmp_path, "rtest-1") == "approve"


def test_review_file_idempotent_by_existence(tmp_path: Path) -> None:
    path = write_review_file(tmp_path, "rtest-2", _payload())
    edited = path.read_text(encoding="utf-8").replace("decision: pending", "decision: reject")
    path.write_text(edited, encoding="utf-8")
    write_review_file(tmp_path, "rtest-2", _payload())  # re-execution must not clobber
    assert read_decision(tmp_path, "rtest-2") == "reject"


def test_writer_resumes_seq(tmp_path: Path) -> None:
    w1 = TrajectoryWriter(tmp_path, run_id="rtest-3")
    w1.emit("run_start", schema_version="0.2")
    w1.emit("error", where="x", kind="other", recovered=True, detail="")
    w2 = TrajectoryWriter(tmp_path, run_id="rtest-3")  # reopen same run
    w2.emit("error", where="y", kind="other", recovered=True, detail="")
    events = load_trajectory(w2.path)
    assert [e["seq"] for e in events] == [0, 1, 2]


def test_resolution_mapping_covers_decisions() -> None:
    assert RESOLUTION_BY_DECISION == {
        "approve": "approved",
        "edit": "edited",
        "reject": "rejected",
    }


# --- the interrupt/resume chain (Stage G acceptance; needs slot #1) ---


@needs_hitl
def test_interactive_interrupts_and_resumes(tmp_path: Path) -> None:
    runs, review = tmp_path / "runs", tmp_path / "review"
    saver = InMemorySaver()
    source = SyntheticSource(SYNTHETIC_RESUME, SYNTHETIC_JD)
    pair = PairRef(split="train", row=0)

    first, writer = run_pair(
        source, pair, "interactive", runs, checkpointer=saver, review_dir=review
    )
    assert "__interrupt__" in first
    review_path = review / f"{writer.run_id}.md"
    assert review_path.exists()
    assert read_decision(review, writer.run_id) is None  # pending

    # the human decides
    decided = review_path.read_text(encoding="utf-8").replace(
        "decision: pending", "decision: approve"
    )
    review_path.write_text(decided, encoding="utf-8")

    # resume: same run_id (writer seq continues), same checkpointer + thread
    resumed_writer = TrajectoryWriter(runs, writer.run_id)
    app = build_graph(source, resumed_writer, checkpointer=saver, review_dir=review)
    config: Any = {"configurable": {"thread_id": writer.run_id}}
    final = app.invoke(Command(resume="approve"), config=config)

    gate = final["gate"]
    assert gate is not None and gate.resolution == "approved"
    assert gate.action == "interrupt" and gate.mode == "interactive"
    assert final["recommendation"] == "flagged"

    events = load_trajectory(resumed_writer.path)
    assert validate_trajectory(events) == []  # seq monotonic across the break
    gate_events = [e for e in events if e["type"] == "gate_event"]
    assert len(gate_events) == 1 and gate_events[0]["resolution"] == "approved"


@needs_hitl
def test_interactive_reject_resolution(tmp_path: Path) -> None:
    runs, review = tmp_path / "runs", tmp_path / "review"
    saver = InMemorySaver()
    source = SyntheticSource(SYNTHETIC_RESUME, SYNTHETIC_JD)
    _, writer = run_pair(
        source,
        PairRef(split="train", row=0),
        "interactive",
        runs,
        checkpointer=saver,
        review_dir=review,
    )
    resumed_writer = TrajectoryWriter(runs, writer.run_id)
    app = build_graph(source, resumed_writer, checkpointer=saver, review_dir=review)
    config: Any = {"configurable": {"thread_id": writer.run_id}}
    final = app.invoke(Command(resume="reject"), config=config)
    gate = final["gate"]
    assert gate is not None and gate.resolution == "rejected"
    assert validate_trajectory(load_trajectory(resumed_writer.path)) == []


@needs_hitl
def test_eval_mode_unaffected(tmp_path: Path) -> None:
    """Interactive machinery must not leak into eval mode (D15)."""
    final, writer = run_pair(
        SyntheticSource(SYNTHETIC_RESUME, SYNTHETIC_JD),
        PairRef(split="train", row=0),
        "eval",
        tmp_path / "runs",
        review_dir=tmp_path / "review",
    )
    gate = final["gate"]
    assert gate is not None and gate.resolution == "auto" and gate.action == "auto_resume"
    assert not (tmp_path / "review").exists()  # no review artifacts in eval mode
    assert initial_state(PairRef(split="train", row=0), "eval")["mode"] == "eval"
