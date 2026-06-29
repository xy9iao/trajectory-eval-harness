"""Assemble the triage StateGraph: nodes, conditional edges, checkpointer (GUIDE §4).

Topology:
    classify -> gather_context -> decide_action -> {gate -> execute | END(reject)} | execute -> END

The checkpointer makes the gate's interrupt() durable: state is snapshotted on pause and reloaded on
resume, even across process restarts. The model is created lazily (first node call) so the graph
COMPILES without a key — handy for offline structure tests and the Phase 3 determinism replays.
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


def build_graph(tools=None, model=None, checkpointer=None):
    """Compile the triage graph. Pass `tools` (from the MCP client) to enable gather_context, and a
    `checkpointer` to enable durable HITL pauses (MemorySaver for Phase 1; SqliteSaver to survive
    restarts). `model` may be injected (e.g. a mock) — otherwise it is built lazily on first use.
    """
    tools = tools or []
    _model = {"m": model}

    def _get_model():
        if _model["m"] is None:
            from src.config import make_model

            _model["m"] = make_model()
        return _model["m"]

    async def _classify(state):
        return await classify(state, model=_get_model())

    async def _gather(state):
        return await gather_context(state, model=_get_model(), tools=tools)

    async def _decide(state):
        return await decide_action(state, model=_get_model())

    g = StateGraph(TriageState)
    g.add_node("classify", _classify)
    g.add_node("gather_context", _gather)
    g.add_node("decide_action", _decide)
    g.add_node("gate", gate)
    g.add_node("execute", execute)

    g.add_edge(START, "classify")
    g.add_edge("classify", "gather_context")
    g.add_edge("gather_context", "decide_action")
    g.add_conditional_edges("decide_action", route_after_decide, {"gate": "gate", "execute": "execute"})
    # gate routes to execute on approve, or straight to END on reject (status set in the gate node).
    g.add_conditional_edges("gate", route_after_gate, {"execute": "execute", "end": END})
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
