"""Run the triage agent — smoke test (Phase 0) or a single labeled case (Phase 1+)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# make `src` importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run_smoke() -> int:
    """Phase 0: prove the pipeline + cloud model work through a trivial 2-node graph."""
    from src.agent.graph import build_smoke_graph

    graph = build_smoke_graph()
    out = graph.invoke(
        {"ticket_id": "smoke", "ticket_text": "Say hello and confirm the pipeline works."}
    )
    print("\n=== SMOKE OK ===")
    print("resolution:", out.get("resolution"))
    print("status:   ", out.get("status"))
    print("step_log: ", out.get("step_log"))
    return 0


def run_case(case_id: str, approve: bool) -> int:
    print(f"--case is implemented in Phase 1. Requested case: {case_id} (approve={approve})")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description="Run the triage agent.")
    p.add_argument("--smoke", action="store_true", help="Phase 0: trivial graph through the cloud model.")
    p.add_argument("--case", help="Phase 1+: run a single labeled case by id.")
    p.add_argument("--approve", action="store_true", help="Simulated human approve at the gate.")
    p.add_argument("--reject", action="store_true", help="Simulated human reject at the gate.")
    args = p.parse_args()

    if args.smoke:
        return run_smoke()
    if args.case:
        return run_case(args.case, approve=not args.reject)
    p.error("nothing to do: pass --smoke or --case <id>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
