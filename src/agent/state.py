"""Typed graph state + reducers (GUIDE §3).

The reducer choice IS the design:
  * Audit fields (context, tool_calls, errors, step_log) use the APPEND reducer (operator.add).
    They are an immutable audit trail — never overwritten — and they ARE the eval's input.
  * Scalars (category, proposed_action, resolution, ...) are last-write-wins (no reducer): exactly
    one writer each, so there is no merge ambiguity.
  * gate_required is computed deterministically from the action type (a RULE, not the LLM) — the
    model proposes, but routing to a human is rule-based, so it can't talk its way past the gate.
"""
from __future__ import annotations

from operator import add
from typing import Annotated, NotRequired, TypedDict


class TriageState(TypedDict):
    # --- inputs ---
    ticket_id: str
    ticket_text: str

    # --- working memory (accumulated, append-only audit trail) ---
    category: NotRequired[str]              # set by classify
    context: Annotated[list[dict], add]     # appended by gather_context (tool results)
    tool_calls: Annotated[list[dict], add]  # audit log of every tool call (name, args, ok/err)

    # --- decision ---
    proposed_action: NotRequired[dict]      # {type: refund|ban|escalate|reply|close, params: {...}}
    gate_required: NotRequired[bool]        # computed from proposed_action.type (RULE)
    human_decision: NotRequired[str]        # approve | reject | (None until gate resumed)

    # --- output ---
    resolution: NotRequired[str]            # customer-facing text
    status: NotRequired[str]                # done | rejected | error

    # --- bookkeeping for eval ---
    errors: Annotated[list[dict], add]      # tool/LLM errors encountered
    step_log: Annotated[list[str], add]     # ordered list of nodes visited
