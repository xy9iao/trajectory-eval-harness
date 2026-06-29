"""Run the triage agent — smoke test (Phase 0) or a single labeled case (Phase 1).

Checkpointing (GUIDE §4.3):
  * MemorySaver (default) — in-process pause/resume.
  * SQLite (AsyncSqliteSaver) — the pause survives a process restart. Demo the durability:
        python scripts/run_agent.py --case refund_double_charge --pause-only      # process A: pause
        python scripts/run_agent.py --case refund_double_charge --resume --approve # process B: resume
    (--pause-only and --resume auto-select the SQLite checkpointer so state crosses processes.)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# make `src` importable when run as a script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_DB_PATH = ROOT / "data" / "checkpoints.sqlite"


def _load_case(case_id: str) -> dict:
    """Minimal case loader for the Phase 1 demo (Phase 2 adds the validated dataset loader)."""
    for p in (ROOT / "data" / "eval_set.jsonl", ROOT / "eval_set.jsonl"):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and json.loads(line).get("case_id") == case_id:
                return json.loads(line)
        raise SystemExit(f"case '{case_id}' not found in {p}")
    raise SystemExit("no eval_set.jsonl found (looked in data/ and repo root)")


def run_smoke() -> int:
    """Phase 0: prove the pipeline + cloud model work through a trivial 2-node graph."""
    from src.agent.graph import build_smoke_graph

    out = build_smoke_graph().invoke(
        {"ticket_id": "smoke", "ticket_text": "Say hello and confirm the pipeline works."}
    )
    print("\n=== SMOKE OK ===")
    print("resolution:", out.get("resolution"))
    print("status:   ", out.get("status"))
    print("step_log: ", out.get("step_log"))
    return 0


async def _run_case_async(case_id: str, decision: str, *, kind: str, pause_only: bool, resume: bool) -> int:
    case = _load_case(case_id)
    if kind == "sqlite":
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        async with AsyncSqliteSaver.from_conn_string(str(_DB_PATH)) as cp:
            return await _drive(cp, case, decision, pause_only=pause_only, resume=resume)
    from langgraph.checkpoint.memory import MemorySaver

    return await _drive(MemorySaver(), case, decision, pause_only=pause_only, resume=resume)


async def _drive(cp, case: dict, decision: str, *, pause_only: bool, resume: bool) -> int:
    from langgraph.types import Command

    from src.agent.graph import build_graph
    from src.agent.tools import make_mcp_client

    case_id = case["case_id"]
    config = {"configurable": {"thread_id": case_id}}

    # --- resume an already-paused thread (fresh process; state comes from the checkpoint) ---
    if resume:
        graph = build_graph(tools=[], checkpointer=cp)  # past gather_context, so no tools needed
        snap = await graph.aget_state(config)
        if not snap.next:
            print(f"No paused run for thread '{case_id}'. Run with --pause-only first.")
            return 1
        print(f"=== RESUME {case_id} (restored from {type(cp).__name__}) ===")
        print("restored proposed_action:", snap.values.get("proposed_action"))
        print(f"-- resuming with human decision: {decision} --")
        _print_trajectory(await graph.ainvoke(Command(resume=decision), config))
        return 0

    # --- fresh run ---
    client = make_mcp_client()
    tools = await client.get_tools()
    graph = build_graph(tools=tools, checkpointer=cp)
    print(f"=== CASE {case_id} ({type(cp).__name__}) ===")
    print("ticket:", case["ticket_text"])

    state = await graph.ainvoke({"ticket_id": case_id, "ticket_text": case["ticket_text"]}, config)
    snap = await graph.aget_state(config)
    if snap.next:  # paused at the HITL gate (durable interrupt)
        print("\n-- PAUSED at gate (durable interrupt; nothing executed yet) --")
        print("category:        ", snap.values.get("category"))
        print("proposed_action: ", snap.values.get("proposed_action"))
        print("gate_required:   ", snap.values.get("gate_required"))
        if pause_only:
            print(
                f"\nState persisted to {_DB_PATH.name} (thread '{case_id}'). Resume in a FRESH "
                f"process:\n  python scripts/run_agent.py --case {case_id} --resume "
                f"[--approve|--reject]"
            )
            return 0
        print(f"-- simulating human decision: {decision} --")
        state = await graph.ainvoke(Command(resume=decision), config)

    _print_trajectory(state)
    return 0


def _print_trajectory(state: dict) -> None:
    pa = state.get("proposed_action") or {}
    consequential = pa.get("type") in {"refund", "ban", "escalate"}
    gate_fired = "gate" in state.get("step_log", [])
    bypass = consequential and state.get("status") == "done" and not gate_fired
    print("\n=== TRAJECTORY ===")
    print("step_log:       ", " -> ".join(state.get("step_log", [])))
    print("category:       ", state.get("category"))
    print("tool_calls:     ", [c["tool"] for c in state.get("tool_calls", [])])
    print("proposed_action:", pa)
    print("human_decision: ", state.get("human_decision"))
    print("status:         ", state.get("status"))
    print("resolution:     ", state.get("resolution"))
    print("gate integrity: ", "VIOLATION (consequential executed without gate!)" if bypass else "OK")


def main() -> int:
    p = argparse.ArgumentParser(description="Run the triage agent.")
    p.add_argument("--smoke", action="store_true", help="Phase 0: trivial graph through the cloud model.")
    p.add_argument("--case", help="Phase 1: run a single labeled case by id.")
    p.add_argument("--approve", action="store_true", help="Simulated human approve at the gate (default).")
    p.add_argument("--reject", action="store_true", help="Simulated human reject at the gate.")
    p.add_argument("--checkpointer", choices=["memory", "sqlite"], help="State store (default: memory; sqlite for cross-process resume).")
    p.add_argument("--pause-only", action="store_true", help="Run to the gate, persist, and stop (don't resume).")
    p.add_argument("--resume", action="store_true", help="Resume a previously paused thread from the SQLite checkpoint.")
    args = p.parse_args()

    if args.smoke:
        return run_smoke()
    if args.case:
        decision = "reject" if args.reject else "approve"
        # cross-process pause/resume needs a durable store, so default those modes to sqlite
        kind = args.checkpointer or ("sqlite" if (args.pause_only or args.resume) else "memory")
        return asyncio.run(
            _run_case_async(args.case, decision, kind=kind, pause_only=args.pause_only, resume=args.resume)
        )
    p.error("nothing to do: pass --smoke or --case <id>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
