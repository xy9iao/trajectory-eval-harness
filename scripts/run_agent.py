"""Run the triage agent — smoke test (Phase 0) or a single labeled case (Phase 1)."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# make `src` importable when run as a script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


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


async def _run_case_async(case_id: str, decision: str) -> int:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    from src.agent.graph import build_graph
    from src.agent.tools import make_mcp_client

    case = _load_case(case_id)
    client = make_mcp_client()
    tools = await client.get_tools()
    graph = build_graph(tools=tools, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": case_id}}

    print(f"=== CASE {case_id} ===")
    print("ticket:", case["ticket_text"])

    state = await graph.ainvoke(
        {"ticket_id": case_id, "ticket_text": case["ticket_text"]}, config
    )

    snap = graph.get_state(config)
    if snap.next:  # paused at the HITL gate (durable interrupt)
        print("\n-- PAUSED at gate (durable interrupt; nothing executed yet) --")
        print("category:        ", snap.values.get("category"))
        print("proposed_action: ", snap.values.get("proposed_action"))
        print("gate_required:   ", snap.values.get("gate_required"))
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
    args = p.parse_args()

    if args.smoke:
        return run_smoke()
    if args.case:
        return asyncio.run(_run_case_async(args.case, "reject" if args.reject else "approve"))
    p.error("nothing to do: pass --smoke or --case <id>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
