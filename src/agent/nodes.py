"""Node implementations for the triage graph.

Phase 0: these are STUBS so `src.agent.graph` imports cleanly for the smoke test (build_graph
references them at module load). Phase 1 fills them per GUIDE §4.1. Do not add node logic before
Phase 1 — the smoke path does not use these.
"""
from __future__ import annotations

from src.agent.state import TriageState

_PHASE1 = "Implemented in Phase 1 (see GUIDE §4.1)."


def classify(state: TriageState) -> dict:
    raise NotImplementedError(_PHASE1)


def gather_context(state: TriageState) -> dict:
    raise NotImplementedError(_PHASE1)


def decide_action(state: TriageState) -> dict:
    raise NotImplementedError(_PHASE1)


def gate(state: TriageState) -> dict:
    raise NotImplementedError(_PHASE1)


def execute(state: TriageState) -> dict:
    raise NotImplementedError(_PHASE1)


def route_after_decide(state: TriageState) -> str:
    raise NotImplementedError(_PHASE1)


def route_after_gate(state: TriageState) -> str:
    raise NotImplementedError(_PHASE1)
