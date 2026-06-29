"""Offline smoke tests — graph construction only. No API calls, so these run without a key."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_smoke_graph_compiles():
    from src.agent.graph import build_smoke_graph

    graph = build_smoke_graph()
    assert "echo" in graph.get_graph().nodes


def test_triage_graph_compiles():
    """The full topology compiles (nodes are Phase-1 stubs; compile must not call them)."""
    from src.agent.graph import build_graph

    nodes = set(build_graph().get_graph().nodes)
    for n in ("classify", "gather_context", "decide_action", "gate", "execute"):
        assert n in nodes
