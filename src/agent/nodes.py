"""Node implementations for the triage graph (GUIDE §4.1).

Dependencies (model, tools) are injected by build_graph, so nodes stay unit-testable and the model
can be mocked for the Phase 3 determinism tests. Every node appends to the audit trail (step_log /
tool_calls / context / errors) — that trail is the eval's input, so it is never overwritten.
"""
from __future__ import annotations

import json
from typing import Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from src.agent.prompts import CLASSIFY_SYSTEM, DECIDE_SYSTEM, GATHER_SYSTEM
from src.agent.state import TriageState

# The deterministic guardrail: these action types ALWAYS require the human gate (GUIDE §3).
GATE_ACTIONS = {"refund", "ban", "escalate"}
MAX_TOOL_ITERS = 5


# ---------- structured-output schemas ----------

class Classification(BaseModel):
    category: Literal["billing", "account_access", "abuse_report", "bug_report", "general_question"]


class ActionParams(BaseModel):
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None


class Decision(BaseModel):
    action: Literal["refund", "ban", "escalate", "reply", "close"]
    params: ActionParams = Field(default_factory=ActionParams)
    reason: str = Field(description="one-sentence justification grounded in the gathered facts")
    resolution: str = Field(description="concise customer-facing message")


# ---------- helpers ----------

def _parse_tool_result(raw: object) -> object:
    """MCP-adapter results arrive as content blocks [{'type':'text','text': <json>}]; recover the dict."""
    text: Optional[str] = None
    if isinstance(raw, str):
        text = raw
    elif isinstance(raw, list):
        parts = [b.get("text") for b in raw if isinstance(b, dict) and b.get("type") == "text"]
        text = "\n".join(p for p in parts if p) if parts else None
    if text is None:
        return raw
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return text


# ---------- nodes ----------

async def classify(state: TriageState, *, model) -> dict:
    structured = model.with_structured_output(Classification)
    result = await structured.ainvoke(
        [SystemMessage(CLASSIFY_SYSTEM), HumanMessage(state["ticket_text"])]
    )
    return {"category": result.category, "step_log": ["classify"]}


async def gather_context(state: TriageState, *, model, tools) -> dict:
    """LLM-driven, bounded tool loop. Appends results to the audit trail; records errors for recovery.

    The recovery cycle is an *in-node* bounded loop (cleaner than a graph self-edge and keeps step
    counting deterministic): on a tool error we record it and let the model retry or try an alternate
    source, capped by MAX_TOOL_ITERS so a stuck model can't loop forever.
    """
    tools_by_name = {t.name: t for t in tools}
    model_with_tools = model.bind_tools(tools) if tools else model

    messages = [
        SystemMessage(GATHER_SYSTEM),
        HumanMessage(f"Category: {state.get('category')}\nTicket: {state['ticket_text']}"),
    ]
    context, tool_calls, errors, steps = [], [], [], []

    for _ in range(MAX_TOOL_ITERS):
        ai: AIMessage = await model_with_tools.ainvoke(messages)
        messages.append(ai)
        if not getattr(ai, "tool_calls", None):
            break
        for tc in ai.tool_calls:
            name, args, tc_id = tc["name"], tc.get("args", {}), tc.get("id")
            tool = tools_by_name.get(name)
            if tool is None:
                errors.append({"tool": name, "error": "unknown_tool"})
                messages.append(ToolMessage(content="error: unknown tool", tool_call_id=tc_id))
                continue
            try:
                parsed = _parse_tool_result(await tool.ainvoke(args))
                ok = True
            except Exception as e:  # record for the recovery metric; let the model retry/alternate
                parsed = f"error: {e}"
                ok = False
                errors.append({"tool": name, "args": args, "error": str(e)})
            context.append({"tool": name, "args": args, "result": parsed, "ok": ok})
            tool_calls.append({"tool": name, "args": args, "ok": ok})
            steps.append(f"tool:{name}")
            messages.append(ToolMessage(content=json.dumps(parsed, default=str)[:2000], tool_call_id=tc_id))

    return {
        "context": context,
        "tool_calls": tool_calls,
        "errors": errors,
        "step_log": ["gather_context", *steps],
    }


async def decide_action(state: TriageState, *, model) -> dict:
    facts = [c.get("result") for c in state.get("context", [])]
    human = HumanMessage(
        f"Category: {state.get('category')}\nTicket: {state['ticket_text']}\n"
        f"Gathered facts: {json.dumps(facts, default=str)[:4000]}"
    )
    d: Decision = await model.with_structured_output(Decision).ainvoke(
        [SystemMessage(DECIDE_SYSTEM), human]
    )
    action = {"type": d.action, "params": d.params.model_dump(exclude_none=True)}
    return {
        "proposed_action": action,
        "gate_required": d.action in GATE_ACTIONS,  # RULE, not the LLM
        "resolution": d.resolution,
        "step_log": ["decide_action"],
    }


def gate(state: TriageState) -> dict:
    """HITL stop. interrupt() suspends the graph (state persisted by the checkpointer); the resume
    value is the human decision. Nothing consequential has executed when we pause here."""
    decision = interrupt(
        {
            "ticket_id": state.get("ticket_id"),
            "proposed_action": state.get("proposed_action"),
            "ask": "approve or reject this consequential action",
        }
    )
    update = {"human_decision": decision, "step_log": ["gate"]}
    if decision != "approve":
        update["status"] = "rejected"
        update["resolution"] = "Action rejected at the human gate; routed for manual handling."
    return update


def execute(state: TriageState) -> dict:
    """Perform the action (mock side-effect) and finalize. Reached only on approve or a low-risk action."""
    action = state.get("proposed_action") or {}
    atype = action.get("type")
    return {
        "status": "done",
        "resolution": state.get("resolution") or f"Action '{atype}' completed.",
        "tool_calls": [
            {"tool": f"execute:{atype}", "args": action.get("params", {}), "ok": True,
             "consequential": atype in GATE_ACTIONS}
        ],
        "step_log": ["execute"],
    }


# ---------- routers (pure rules — no model) ----------

def route_after_decide(state: TriageState) -> str:
    return "gate" if state.get("gate_required") else "execute"


def route_after_gate(state: TriageState) -> str:
    return "execute" if state.get("human_decision") == "approve" else "end"
