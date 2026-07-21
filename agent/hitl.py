"""The interactive-gate interrupt — OWNER-IMPLEMENTED (Stage G slot #1).

Contract (tests/test_gate_interactive.py, skipped until implemented):

`request_human_decision(payload)` is called INSIDE the gate node, only when
mode == "interactive" and triggers are nonempty. It must:

1. Call `langgraph.types.interrupt(payload)` — on FIRST execution this
   suspends the whole graph (the checkpointer saves state, including the
   by-value documents: the paused run is hermetic, decision 2a's payoff).
2. On RESUME — `Command(resume=<decision>)` — the SAME interrupt() call
   RETURNS <decision>. The suspension point is the return point; that is
   the entire HITL pivot.
3. Return the decision string ("approve" | "edit" | "reject"). Validation
   of the value belongs to the caller (gate node), not here.

Re-execution warning (the trap to feel once, deliberately): everything in
the gate node BEFORE the interrupt() call runs AGAIN on resume. The
scaffold already ordered side effects accordingly (review file write is
idempotent-by-existence; gate_event is emitted only AFTER interrupt
returns, because there is no resolution to record until then). If you add
side effects, they go after the interrupt or they must be idempotent.
"""

from typing import Any
from langgraph.types import interrupt


def request_human_decision(payload: dict[str, Any]) -> str:
    decision = interrupt(payload)
    return str(decision)
