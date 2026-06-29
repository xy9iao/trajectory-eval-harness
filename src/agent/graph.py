"""Assemble the triage StateGraph: nodes, conditional edges, checkpointer.

Topology (see GUIDE §4):
    classify -> gather_context -> decide_action -> {gate -> execute | execute} -> END

The checkpointer is what makes the gate's interrupt() durable: state is snapshotted on
pause and reloaded on resume, even across process restarts.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    classify,
    decide_action,
    execute,
    gather_context,
    gate,
    route_after_decide,
    route_after_gate,
)
from src.agent.state import TriageState


def build_graph(checkpointer=None):
    """Compile the triage graph. Pass a checkpointer to enable durable HITL pauses.

    For Phase 1 start with MemorySaver; switch to SqliteSaver to survive restarts:

        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.checkpoint.sqlite import SqliteSaver
    """
    g = StateGraph(TriageState)

    g.add_node("classify", classify)
    g.add_node("gather_context", gather_context)
    g.add_node("decide_action", decide_action)
    g.add_node("gate", gate)
    g.add_node("execute", execute)

    g.add_edge(START, "classify")
    g.add_edge("classify", "gather_context")
    g.add_edge("gather_context", "decide_action")
    g.add_conditional_edges("decide_action", route_after_decide, {"gate": "gate", "execute": "execute"})
    g.add_conditional_edges("gate", route_after_gate, {"execute": "execute"})
    g.add_edge("execute", END)

    return g.compile(checkpointer=checkpointer)


def build_smoke_graph(checkpointer=None):
    """Phase 0: a trivial 2-node graph to prove the pipeline + cloud API work."""
    from src.config import make_model

    def echo(state: TriageState):
        model = make_model()
        resp = model.invoke(f"Reply in one short sentence to: {state['ticket_text']}")
        return {"resolution": resp.content, "status": "done", "step_log": ["echo"]}

    g = StateGraph(TriageState)
    g.add_node("echo", echo)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    return g.compile(checkpointer=checkpointer)
